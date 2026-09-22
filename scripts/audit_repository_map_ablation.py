"""Audit an archived repository-map runtime and its four paired results."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path

import summarize_cumulative_component_ablations as common
from summarize_cumulative_component_ablations import read
CONDITIONS = ('full', 'no_automatic_map')
def summarize(root):
    original_conditions, original_labels = common.CONDITIONS, common.LABELS
    try:
        common.CONDITIONS, common.LABELS = CONDITIONS, ('Full', 'Without automatic map')
        result = common.summarize(root)
        result['all_conditions_terminal'] = len(result['rows']) == 4 and all(r['status'] not in ('not_run', 'running') for r in result['rows'])
        result['definition'] = 'Four new paired runs, two fixed repositories and automatic map on/off. All other repository coordination components retained.'
        return result
    finally:
        common.CONDITIONS, common.LABELS = original_conditions, original_labels


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hashes(root):
    return {p.relative_to(root).as_posix(): digest(p) for p in sorted(root.rglob('*'))
            if p.is_file() and not any(x.startswith('.') or x == '__pycache__' for x in p.relative_to(root).parts)}


def audit(snapshot):
    root = snapshot / 'experiments/repository_map_ablation_20260922/results'
    freeze = read(root / 'freeze.json')
    declared_protocol = read(root / 'protocol.json')
    summary = summarize(root)
    checks = {'offline_passed': read(root / 'offline.json')['passed'],
              'offline_no_model_calls': read(root / 'offline.json')['model_calls'] == 0,
              'protocol_unchanged': digest(root / 'protocol.json') == freeze['protocol_sha256'],
              'all_terminal': summary['all_conditions_terminal'],
              'all_runs_completed_without_infrastructure_error': all(r['status'] == 'completed' for r in summary['rows'])}
    checks['runtime_code_unchanged'] = all(digest(snapshot / name) == expected
                                         for name, expected in freeze['code_hashes'].items())
    scheduler = read(root / 'scheduler.json')
    checks['scheduler_completed'] = scheduler['status'] == 'completed'
    pairs = {(repo, condition) for repo in ('timeseries', 'twotower') for condition in CONDITIONS}
    jobs = scheduler['jobs']
    checks['four_distinct_jobs'] = len(jobs) == 4 and {(r['repository'], r['condition']) for r in jobs} == pairs
    checks['all_processes_exited_normally'] = all(r['exit_code'] == 0 for r in jobs)
    for repo in ('timeseries', 'twotower'):
        checks[f'{repo}:task_unchanged'] = digest(root / repo / 'task.json') == freeze['tasks'][repo]
        for name, expected in freeze['inputs'][repo].items():
            checks[f'{repo}:input_unchanged:{name}'] = hashes(root / repo / name) == expected
    for row in summary['rows']:
        repo, condition = row['repository'], row['condition']
        prefix = f'{repo}:{condition}:'
        folder = root / repo / 'conditions' / condition
        protocol = read(folder / 'protocol.json')
        result = read(folder / 'result.json')
        agent = folder / 'evidence/agent'
        requests = {p.stem.split('_')[1]: read(p) for p in agent.glob('call_*_request.json')}
        responses = {p.stem.split('_')[1]: read(p) for p in agent.glob('call_*_response.json')}
        metadata = {p.stem.split('_')[1]: read(p) for p in agent.glob('call_*_metadata.json')}
        errors = {p.stem.split('_')[1] for p in agent.glob('call_*_error.json')}
        starts = [read(p) for p in agent.glob('event_*_api_start.json')]
        checks[prefix + 'initial_candidate_identical'] = protocol['initial_target_hashes'] == freeze['inputs'][repo]['translation/target']
        checks[prefix + 'declared_budget_config'] = all(protocol['config'][key] == value
                                                      for key, value in declared_protocol['repair_budget'].items())
        checks[prefix + 'same_freeze'] = protocol['freeze_sha256'] == digest(root / 'freeze.json')
        checks[prefix + 'source_unchanged'] = hashes(folder / 'workspace/source') == freeze['inputs'][repo]['source']
        checks[prefix + 'task_unchanged'] = digest(folder / 'workspace/task.json') == freeze['tasks'][repo]
        checks[prefix + 'final_candidate_preserved'] = hashes(folder / 'workspace/target') == result['final_target_hashes']
        checks[prefix + 'all_requests_counted'] = row['recorded_request_count'] == row['calls']
        checks[prefix + 'request_sequence'] = set(requests) == {f'{i:04d}' for i in range(1, row['calls'] + 1)}
        checks[prefix + 'metadata_correspondence'] = set(metadata) == set(requests)
        checks[prefix + 'responses_or_errors_accounted'] = set(responses) | errors == set(requests)
        checks[prefix + 'request_metadata_hashes'] = all(
            hashlib.sha256(json.dumps(request, ensure_ascii=False, sort_keys=True, allow_nan=False).encode()).hexdigest()
            == metadata[ident]['request_sha256'] for ident, request in requests.items())
        checks[prefix + 'per_call_output_limit'] = all(0 < request['max_tokens'] <= 32768 for request in requests.values())
        checks[prefix + 'fixed_model_parameters'] = all(request['model'] == 'deepseek-v4-flash' and
            request.get('thinking') == {'type': 'enabled'} and request.get('reasoning_effort') == 'high' and
            'temperature' not in request and 'seed' not in request for request in requests.values())
        checks[prefix + 'calls_started_within_wall_budget'] = len(starts) == row['calls'] and all(
            0 < event['data']['timeout_seconds'] <= 3600 and
            datetime.fromisoformat(event['time']).timestamp() - result['started'] <= 3600 for event in starts)
        checks[prefix + 'stage_calls_reconcile'] = row['diagnosis_calls'] + row['repair_stage_calls'] == row['calls']
        checks[prefix + 'investigation_switch'] = 0 < row['diagnosis_calls'] <= 6
        checks[prefix + 'handoff_switch'] = row['role_handoffs'] == 1
        checks[prefix + 'context_switch'] = bool(row['repository_context_rebuilds'])
        checks[prefix + 'measured_tokens_reconcile'] = row['response_prompt_and_completion_total'] == row['repair_tokens']
        checks[prefix + 'end_to_end_cost_reconciles'] = row['end_to_end_tokens'] == row['repair_tokens'] + row['translation_usage']['total_tokens']
        checks[prefix + 'call_budget'] = row['calls'] <= 80
        checks[prefix + 'output_budget'] = row['usage']['budget_output_tokens'] <= 480000
        checks[prefix + 'submission_budget'] = row['submissions'] <= 4
        map_results = [read(p)['data'].get('result', {}) for p in agent.glob('event_*_tool.json') if read(p)['data'].get('name') == 'repository_map']
        if condition == 'no_automatic_map':
            checks[prefix + 'no_automatic_map_payload'] = all('files' not in value and 'unassigned_target_code_files' not in value for value in map_results)
            checks[prefix + 'no_map_guidance_all_calls'] = all('automatic structure extraction is disabled' in request['messages'][0]['content'] for request in requests.values())
            checks[prefix + 'no_original_map_guidance'] = all('Use repository_map to inspect public interfaces, imports and notebook structure.' not in request['messages'][0]['content'] for request in requests.values())
        else:
            checks[prefix + 'map_payload_if_used'] = all('files' in value for value in map_results)
        for request in requests.values():
            names = {tool['function']['name'] for tool in request.get('tools', [])}
            if names:
                checks.setdefault(prefix + 'coordination_tools_retained', True)
                checks[prefix + 'coordination_tools_retained'] &= {'plan_units','focus_unit','checkpoint_unit','repository_evidence','repository_map','notebook'}.issubset(names)
        c = row['protocol_checks']
        checks[prefix + 'fixed_check_denominator'] = c['expected'] == (69 if repo == 'timeseries' else 145)
        checks[prefix + 'accepted_checks_complete'] = not row['accepted'] or c['passed'] == c['expected']
    return {'passed': all(checks.values()), 'checks': checks,
            'run_count': len(summary['rows']), 'physical_ledger': summary['physical_ledger'],
            'result_sha256': summary['result_sha256']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.snapshot)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': result['passed'], 'checks': len(result['checks']),
                      'failed': [k for k, v in result['checks'].items() if not v]}))
    if not result['passed']:
        raise SystemExit(1)
