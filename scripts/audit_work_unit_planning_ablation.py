"""Audit an archived work-unit planning runtime and reused complete-method references."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path

import summarize_cumulative_component_ablations as common
from summarize_cumulative_component_ablations import read
CONDITIONS = ('full', 'no_work_unit_planning')
def summarize(root):
    original_conditions, original_labels = common.CONDITIONS, common.LABELS
    try:
        common.CONDITIONS, common.LABELS = CONDITIONS, ('Full (reused)', 'Without Repair Dependency Graph Planning')
        result = common.summarize(root)
        result['all_conditions_terminal'] = len(result['rows']) == 4 and all(r['status'] not in ('not_run', 'running') for r in result['rows'])
        result['definition'] = 'Two new Repair Dependency Graph Planning ablations and two byte-preserved full references from the prior Repository Structural Analysis ablation. Fixed inputs, budgets, backend and complete acceptance; no new full-method calls.'
        for row in result['rows']:
            row['reused_full_reference'] = row['condition'] == 'full'
        new = [r for r in result['rows'] if r['condition'] != 'full']
        reused = [r for r in result['rows'] if r['condition'] == 'full']
        result['physical_ledger'] = {
            'new_model_calls': sum(r.get('calls') or 0 for r in new),
            'new_measured_tokens': sum(r.get('repair_tokens') or 0 for r in new),
            'new_completion_tokens': sum((r.get('usage') or {}).get('completion_tokens', 0) for r in new),
            'unknown_usage_calls': sum(r.get('unknown_usage_calls') or 0 for r in new),
            'new_translation_calls': 0, 'new_full_method_calls': 0,
            'reused_full_reference_calls': sum(r.get('calls') or 0 for r in reused),
            'reused_full_reference_repair_tokens': sum(r.get('repair_tokens') or 0 for r in reused)}
        return result
    finally:
        common.CONDITIONS, common.LABELS = original_conditions, original_labels


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hashes(root):
    return {p.relative_to(root).as_posix(): digest(p) for p in sorted(root.rglob('*'))
            if p.is_file() and not any(x.startswith('.') or x == '__pycache__' for x in p.relative_to(root).parts)}


def audit(snapshot, reference_snapshot=None):
    root = snapshot / 'experiments/work_unit_planning_ablation_20260922/results'
    freeze = read(root / 'freeze.json')
    declared_protocol = read(root / 'protocol.json')
    summary = summarize(root)
    checks = {'offline_passed': read(root / 'offline.json')['passed'],
              'offline_no_model_calls': read(root / 'offline.json')['model_calls'] == 0,
              'protocol_unchanged': digest(root / 'protocol.json') == freeze['protocol_sha256'],
              'reuse_consistency_passed': read(root / 'reuse_consistency.json')['passed'],
              'all_terminal': summary['all_conditions_terminal'],
              'all_runs_completed_without_infrastructure_error': all(r['status'] == 'completed' for r in summary['rows'])}
    checks['runtime_code_unchanged'] = all(digest(snapshot / name) == expected
                                         for name, expected in freeze['code_hashes'].items())
    scheduler = read(root / 'scheduler.json')
    checks['scheduler_completed'] = scheduler['status'] == 'completed'
    pairs = {(repo, 'no_work_unit_planning') for repo in ('timeseries', 'twotower')}
    jobs = scheduler['jobs']
    checks['only_two_new_ablation_jobs'] = len(jobs) == 2 and {(r['repository'], r['condition']) for r in jobs} == pairs
    checks['all_processes_exited_normally'] = all(r['exit_code'] == 0 for r in jobs)
    for repo in ('timeseries', 'twotower'):
        checks[f'{repo}:task_unchanged'] = digest(root / repo / 'task.json') == freeze['tasks'][repo]
        for name, expected in freeze['inputs'][repo].items():
            checks[f'{repo}:input_unchanged:{name}'] = hashes(root / repo / name) == expected
        if reference_snapshot is not None:
            reference = reference_snapshot / 'experiments/repository_map_ablation_20260922/results'
            reused_files = hashes(root / repo / 'conditions/full')
            reused_files.pop('reuse_origin.json')
            checks[f'{repo}:reused_full_evidence_byte_preserved'] = reused_files == hashes(reference / repo / 'conditions/full')
            checks[f'{repo}:translation_generation_and_usage_byte_preserved'] = digest(root / repo / 'translation/result.json') == digest(reference / repo / 'translation/result.json')
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
        checks[prefix + 'same_freeze'] = protocol['freeze_sha256'] == digest(root / ('reference_protocol/freeze.json' if condition == 'full' else 'freeze.json'))
        if condition == 'full':
            origin = read(folder / 'reuse_origin.json')
            checks[prefix + 'original_result_byte_preserved'] = digest(folder / 'result.json') == origin['result_sha256']
            checks[prefix + 'original_protocol_byte_preserved'] = digest(folder / 'protocol.json') == origin['protocol_sha256']
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
        checks[prefix + 'automatic_map_retained'] = all('files' in value for value in map_results)
        removed = {'plan_units', 'focus_unit', 'checkpoint_unit'}
        if condition == 'no_work_unit_planning':
            checks[prefix + 'no_unit_guidance_all_calls'] = all('Explicit work-unit planning, focus constraints and unit checkpoints are disabled.' in request['messages'][0]['content'] for request in requests.values())
            checks[prefix + 'no_original_unit_guidance'] = all('Propose semantic work units using plan_units' not in request['messages'][0]['content'] for request in requests.values())
            checks[prefix + 'no_unit_boundary_rebuilds'] = all(e['reason'] != 'unit_boundary' for e in row['repository_context_rebuilds'])
            state = read(folder / 'evidence/repository_state.json')
            checks[prefix + 'no_unit_state'] = state['units'] == {} and state['active'] is None and state['checkpoints'] == []
        for request in requests.values():
            names = {tool['function']['name'] for tool in request.get('tools', [])}
            if names:
                checks.setdefault(prefix + 'independent_tools_retained', True)
                checks[prefix + 'independent_tools_retained'] &= {'repository_evidence','repository_map','notebook','read','edit','run_test'}.issubset(names)
                checks.setdefault(prefix + 'planning_tool_switch', True)
                checks[prefix + 'planning_tool_switch'] &= (not (names & removed)) if condition == 'no_work_unit_planning' else removed.issubset(names)
        c = row['protocol_checks']
        checks[prefix + 'fixed_check_denominator'] = c['expected'] == (69 if repo == 'timeseries' else 145)
        checks[prefix + 'accepted_checks_complete'] = not row['accepted'] or c['passed'] == c['expected']
    return {'passed': all(checks.values()), 'checks': checks,
            'original_reference_archive_checked': reference_snapshot is not None,
            'run_count': len(summary['rows']), 'physical_ledger': summary['physical_ledger'],
            'result_sha256': summary['result_sha256']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('--reference-snapshot', type=Path,
                        help='Original map-ablation archive for complete reused evidence and generation-state checks')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.snapshot, args.reference_snapshot)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': result['passed'], 'checks': len(result['checks']),
                      'failed': [k for k, v in result['checks'].items() if not v]}))
    if not result['passed']:
        raise SystemExit(1)
