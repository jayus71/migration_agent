"""Read-only source, candidate and configuration audit for extension reuse."""

from collections import Counter
import hashlib
import json
from pathlib import Path


BASE = Path('/media/main/whj/projects/torch4ms')
OLD = BASE / 'ascend-torch4ms-n18-348e8cd/artifacts/n18_training'
CURRENT = BASE / 'ascend-torch4ms-n18-remediation-3eb9150/artifacts/n18_prepared_20260917'
INTER = BASE / 'intertrans-completion-20260918'
OUT = BASE / 'ascend-torch4ms-unified50-preflight-20260918/experiments/unified_migration50_20260918/extension_reuse.json'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def main():
    assert not OUT.exists(), 'Preserve the previous audit'
    old_freeze, current_freeze, inter_freeze = [read(p / 'freeze.json') for p in (OLD, CURRENT, INTER)]
    shared = ('sources', 'protocol_sha256', 'interface_sha256', 'index_sha256')
    agreement = {name: {'old_equal': old_freeze[name] == current_freeze[name],
                        'intertrans_equal': inter_freeze[name] == current_freeze[name]} for name in shared}
    inter_protocol_path = BASE / 'ascend-torch4ms-intertrans-completion-20260918/experiments/experiment_request_20260820/14_experiment_N_real_cross_language/n18/protocol.json'
    current_protocol = read(CURRENT / 'run_direct.json')['protocol']
    inter_protocol = read(inter_protocol_path)
    changes = {key: {'direct': current_protocol.get(key), 'intertrans': inter_protocol.get(key)}
               for key in current_protocol.keys() | inter_protocol.keys()
               if current_protocol.get(key) != inter_protocol.get(key)}
    assert changes.keys() == {'interface', 'max_output_tokens'}, changes
    assert all(v['intertrans_equal'] for k, v in agreement.items() if k != 'protocol_sha256')
    direct = read(CURRENT / 'direct_summary.json')
    assert direct['completed'] == direct['expected'] == 18
    direct_rows = {r['task']: r for r in direct['rows']}
    assert len(direct_rows) == 18 and direct_rows.keys() == current_freeze['sources'].keys()
    rows = []
    for task in sorted(direct_rows):
        initial = CURRENT / 'direct_llm' / task / 'initial'
        candidate = initial / 'candidate.py'
        assert candidate.is_file()
        entry = direct_rows[task]
        assert entry['status'] == 'evaluated' and len(entry['seeds']) == 3
        request, response, generation = [read(initial / name) for name in ('request.json', 'response.json', 'generation.json')]
        assert request['model'] == 'deepseek-v4-flash'
        assert generation.get('usage') and response.get('usage')
        rows.append({'task': task, 'method': 'direct_llm', 'action': 'reuse_existing',
                     'accepted': entry['passed'], 'candidate': str(candidate), 'candidate_sha256': sha(candidate),
                     'source_sha256': current_freeze['sources'][task],
                     'request_sha256': sha(initial / 'request.json'), 'response_sha256': sha(initial / 'response.json'),
                     'response_id': response.get('id'), 'usage': response['usage']})
        for method in ('full_method', 'direct_llm_test_repair', 'direct_llm_sweagent', 'direct_llm_matchfixagent'):
            root = OLD / method / task
            path = root / 'result.json'
            old_result = read(path) if path.exists() else {}
            first = root / 'candidate_0.py'
            match = sha(first) == sha(candidate) if first.exists() else False
            reasons = []
            if any(not v['old_equal'] for v in agreement.values()):
                reasons.append('old_frozen_source_or_acceptance_contract_differs')
            if not match:
                reasons.append('different_or_missing_shared_initial_candidate')
            if old_result.get('status') != 'evaluated':
                reasons.append('no_complete_evaluated_old_run')
            if method == 'full_method':
                reasons.append('different_method_implementation')
            rows.append({'task': task, 'method': method,
                         'action': 'new_condition_for_current_protocol' if reasons else 'native_configuration_audit_required',
                         'reasons': reasons, 'old_status': old_result.get('status'),
                         'old_accepted': old_result.get('passed'),
                         'old_initial_candidate': str(first), 'old_initial_sha256': sha(first),
                         'current_initial_sha256': sha(candidate), 'initial_candidate_equal': match,
                         'old_result': str(path), 'old_result_sha256': sha(path),
                         'old_evidence_retained': True})
        inter = next(r for r in read(INTER / 'paper_results.json')['rows'] if r['task'] == task)
        assert inter['valid_outcome']
        rows.append({'task': task, 'method': 'intertrans', 'action': 'reuse_existing',
                     'accepted': inter['accepted'], 'result': inter['result_path'],
                     'result_sha256': inter['result_sha256']})
    assert len(rows) == 108
    report = {'real_model_calls': 0, 'candidate_executions': 0, 'freeze_agreement': agreement,
              'protocol_text_changes': changes,
              'protocol_compatibility': 'Same source, interface bytes, reference index, seeds and acceptance scope; interface path renamed and max_output_tokens made explicit.',
              'task_count': 18, 'conditions': len(rows),
              'action_counts': dict(Counter(r['action'] for r in rows)),
              'by_method': {method: dict(Counter(r['action'] for r in rows if r['method'] == method))
                            for method in sorted({r['method'] for r in rows})},
              'evidence': {str(p): sha(p) for p in [OLD / 'freeze.json', CURRENT / 'freeze.json',
                           CURRENT / 'direct_summary.json', INTER / 'freeze.json', INTER / 'paper_results.json']},
              'rows': rows}
    OUT.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('rows', 'evidence')}, indent=2))


if __name__ == '__main__':
    main()
