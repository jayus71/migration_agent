"""Descriptive paired analysis of existing results; never launches experiments."""
from collections import Counter
import hashlib
import json
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'data/audits/unified50-preflight-20260918/formal_launch/results_audit_final.json'
OUT = ROOT / 'output/experiment-analysis-20260920'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main():
    audit = read(AUDIT)
    details = read(OUT / 'remote_verified_details.json')
    raw = {r['id']: r for r in details['rows']}
    assert details['verified_result_hashes'] == len(raw) == 391
    rows = audit['rows']
    assert all(raw[r['id']]['result_sha256'] == r['result_sha256'] for r in rows)
    calls = audit['provider_calls']
    initial = {r['group']: r['accepted'] for r in rows if r['phase'] == 'main' and r['method'] == 'direct'}
    cross_manifest = read(ROOT / 'data/audits/unified50-preflight-20260918/final_review/cross_language/manifest.json')
    names = {r['anonymous_id']: r['original_id'] for r in cross_manifest['tasks']}
    cross_initial = {r['task']: r['accepted'] for r in audit['historical_reused_conditions'] if r['method'] == 'direct_llm'}

    def tokens(row, field='total_tokens', incremental=False):
        return sum(calls[k]['usage'][field] for k in set(row['incremental_call_keys' if incremental else 'end_to_end_call_keys']))

    def healthy(row):
        return cross_initial[names[row['task']]] if row['phase'] == 'cross_language' else initial[row['group']]

    summaries = {}
    for key, aggregate in audit['aggregates'].items():
        subset = [r for r in rows if r['variant'] + '/' + r['method'] == key]
        repairs = [r for r in subset if not healthy(r)]
        preserves = [r for r in subset if healthy(r)]
        # The shared initial is an independently verified checkpoint. Native
        # episodes can subsequently damage it, so final retention is separate.
        cumulative = {}
        for budget in (1, 2, 4):
            cumulative[str(budget)] = sum(healthy(r) or any(a['accepted'] and a['attempt'] <= budget for a in r['attempts']) for r in subset)
        summaries[key] = {
            'n': len(subset), 'accepted': sum(r['accepted'] is True for r in subset),
            'initial_healthy': len(preserves), 'healthy_retained': sum(r['accepted'] is True for r in preserves),
            'healthy_lost': [r['task'] for r in preserves if r['accepted'] is False],
            'initial_faults': len(repairs), 'repaired': sum(r['accepted'] is True for r in repairs),
            'failed': [r['task'] for r in subset if r['accepted'] is False],
            'interrupted': [r['task'] for r in subset if r['accepted'] is None],
            'ever_accepted_at_budget_including_initial': cumulative if subset[0]['method'] in ('ladim', 'swe', 'matchfix') else None,
            'repair_attempt_histogram': dict(Counter(len(r['attempts']) for r in subset)),
            'e2e_tokens': sum(tokens(r) for r in subset),
            'median_condition_tokens': median(tokens(r) for r in subset),
            'healthy_incremental_tokens': sum(tokens(r, incremental=True) for r in preserves),
            'faulty_incremental_tokens': sum(tokens(r, incremental=True) for r in repairs),
            'e2e_input_tokens': sum(tokens(r, 'prompt_tokens') for r in subset),
            'e2e_output_tokens': sum(tokens(r, 'completion_tokens') for r in subset),
            'e2e_cache_miss_tokens': sum(tokens(r, 'prompt_cache_miss_tokens') for r in subset),
            'stage_end_statuses': dict(Counter(a['stage_status'] for r in subset for a in raw[r['id']]['attempts'])),
        }
        if subset[0]['method'] in ('direct', 'cte', 'msadapter'):
            for field in ('initial_healthy', 'healthy_retained', 'healthy_lost', 'initial_faults',
                          'repaired', 'healthy_incremental_tokens', 'faulty_incremental_tokens'):
                summaries[key][field] = None
    paired = {}
    for key in summaries:
        if key in ('main/ladim', 'cross_language/ladim'):
            continue
        subset = [r for r in rows if r['variant'] + '/' + r['method'] == key]
        is_cross = subset[0]['phase'] == 'cross_language'
        reference = {r['task']: r for r in rows if r['variant'] == ('cross_language' if is_cross else 'main') and r['method'] == 'ladim'}
        bins = Counter()
        for row in subset:
            ours = reference[row['task']]
            bins[str(ours['accepted']) + '/' + str(row['accepted'])] += 1
        paired[key] = {'outcomes_ladim_vs_other': dict(bins),
                       'ladim_lower_tokens': sum(tokens(reference[r['task']]) < tokens(r) for r in subset),
                       'ladim_only': [r['task'] for r in subset if reference[r['task']]['accepted'] is True and r['accepted'] is False],
                       'other_only': [r['task'] for r in subset if reference[r['task']]['accepted'] is False and r['accepted'] is True]}
    cross_rows = []
    for task, name in names.items():
        entry = {'task': task, 'name': name, 'initial_accepted': cross_initial[name]}
        for method in ('ladim', 'swe', 'matchfix', 'test_repair'):
            row = next(r for r in rows if r['phase'] == 'cross_language' and r['task'] == task and r['method'] == method)
            detail = raw[row['id']]
            entry[method] = {'accepted': row['accepted'], 'tokens': tokens(row),
                             'attempts': detail['attempts'], 'checkpoints': detail['checkpoints'],
                             'final': detail['final'], 'error': detail['error']}
        cross_rows.append(entry)
    result = {'audit_sha256': hashlib.sha256(AUDIT.read_bytes()).hexdigest(),
              'verified_remote_results': 391, 'summaries': summaries, 'paired': paired,
              'cross_language_tasks': cross_rows,
              'notes': ['All analysis is descriptive, with one observed trajectory per condition.',
                        '29 source-contract groups derive from 24 source files; aliases are not independent samples.',
                        'Ever-accepted curves include a valid initial and can differ from the final submitted program.',
                        'Raw unknown/interrupted outcomes remain null. No experiment was rerun.']}
    result['cross_failure_terminal_statuses'] = dict(Counter(
        r['ladim']['attempts'][-1]['stage_status'] for r in cross_rows if not r['ladim']['accepted']))
    result['cross_ladim_failure_token_fraction'] = sum(r['ladim']['tokens'] for r in cross_rows if not r['ladim']['accepted']) / summaries['cross_language/ladim']['e2e_tokens']
    result['main_fault_only_incremental_saving_vs_matchfix'] = 1 - summaries['main/ladim']['faulty_incremental_tokens'] / summaries['main/matchfix']['faulty_incremental_tokens']
    (OUT / 'analysis.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'summaries': summaries, 'paired': paired,
                      'cross_outcomes': [{**{'name': r['name']}, **{m: r[m]['accepted'] for m in ('ladim', 'swe', 'matchfix', 'test_repair')}} for r in cross_rows]}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
