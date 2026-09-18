"""Combine declared replacement episodes while retaining every earlier cost."""
from collections import Counter
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from report_maintext_ablations import condition


def read(path):
    return json.loads(path.read_text())


def summarize(rows, planned):
    statuses = Counter(row['status'] for row in rows)
    complete = statuses['completed'] == planned and len(rows) == planned
    usage, events = Counter(), Counter()
    for row in rows:
        usage.update(row['usage'])
        events.update(row['events'])
    accepted = sum(row['accepted'] is True and row['status'] == 'completed' for row in rows)
    known = usage['prompt_tokens'] + usage['completion_tokens']
    healthy = sum(row['initially_accepted'] is True for row in rows)
    retained = sum(row['initially_accepted'] is True and row['accepted'] is True for row in rows)
    return {'planned': planned, 'recorded': len(rows), 'complete': complete,
        'statuses': dict(statuses), 'accepted': accepted, 'acceptance_rate': accepted / planned if complete else None,
        'initially_healthy': healthy, 'healthy_retained': retained, 'actual_faults_repaired': accepted - retained,
        'accepted_at': {str(attempt): sum(row['accepted'] is True and row['accepted_at'] is not None
            and row['accepted_at'] <= attempt for row in rows) for attempt in (1, 2, 4)},
        'usage': dict(usage), 'known_tokens': known,
        'tokens_per_accepted': known / accepted if complete and accepted and not usage['unknown_usage_calls'] else None,
        'calls': sum(row['calls'] for row in rows), 'events': dict(events),
        'ledger_mismatches': [row['path'] for row in rows if row['ledger_mismatch']],
        'treatment_violations': [{'task': row['task'], **item} for row in rows for item in row['request_treatment_violations']],
        'rows': rows}


def report(root, recovery):
    plan = read(recovery / 'recovery_plan.json')
    lookup = {}
    for job in plan['jobs']:
        source_study = job['study'].replace('_history_v4', '_v3')
        key = (source_study, job['variant'], job['task'])
        if key in lookup:
            raise ValueError('Duplicate selected job')
        lookup[key] = job
        if job.get('original_result'):
            current = hashlib.sha256(Path(job['original_result']).read_bytes()).hexdigest()
            if current != job['original_result_sha256']:
                raise ValueError('Original result changed')
    cache = {}
    def measured(path):
        key = str(path)
        if key not in cache:
            row = condition(path)
            original = read(path)
            budget = original.get('budget', {})
            row['ledger_mismatch'] = row['ledger_mismatch'] or (row['status'] in ('completed', 'infrastructure_error', 'unsupported') and (
                budget.get('calls') != row['calls'] or
                budget.get('usage', {}).get('unknown_usage_calls', 0) != row['usage'].get('unknown_usage_calls', 0)))
            cache[key] = row
        return cache[key]
    groups = []
    for study in ('fixed50_v3', 'natural10_v3', 'signal12_v3'):
        original_root = root / study
        source_plan = read(original_root / 'plan.json')
        for variant in source_plan['variants']:
            tasks = read(original_root / variant / 'manifest.json')['tasks']
            selected, all_paths = [], set()
            for task in tasks:
                name = task['anonymous_id']
                original = original_root / variant / 'conditions' / name / 'autonomous_layered/result.json'
                all_paths.add(original)
                job = lookup.get((study, variant, name))
                path = Path(job['run']) / 'conditions' / name / 'autonomous_layered/result.json' if job else original
                if path.exists():
                    all_paths.add(path)
                    selected.append({**measured(path), 'selected_source': 'declared_replacement' if job else 'original'})
            group = summarize(selected, len(tasks))
            all_rows = [measured(path) for path in sorted(all_paths)]
            all_usage = Counter()
            for row in all_rows:
                all_usage.update(row['usage'])
            all_tokens = all_usage['prompt_tokens'] + all_usage['completion_tokens']
            group.update(study=study, variant=variant, all_recorded_episodes=len(all_rows),
                all_attempts_usage=dict(all_usage), all_attempts_known_tokens=all_tokens,
                all_attempts_tokens_per_accepted=all_tokens / group['accepted'] if group['complete']
                    and group['accepted'] and not all_usage['unknown_usage_calls'] else None,
                replacement_policy='full60_history_correction' if variant == 'without_repair_history' else 'infrastructure_only',
                all_attempts_ledger_mismatches=[row['path'] for row in all_rows if row['ledger_mismatch']])
            if source_plan.get('source_run'):
                control = Path(source_plan['source_run'])
                reference = [measured(control / 'conditions' / task['anonymous_id'] / 'autonomous_layered/result.json') for task in tasks]
                group['reference_v4'] = summarize(reference, len(tasks))
                if group['complete']:
                    mapping = {row['task']: row for row in reference}
                    pairs = [(row, mapping[row['task']]) for row in selected]
                    group['paired_with_reference'] = {
                        'variant_only': [a['task'] for a, b in pairs if a['accepted'] and not b['accepted']],
                        'reference_only': [a['task'] for a, b in pairs if b['accepted'] and not a['accepted']],
                        'both': sum(a['accepted'] and b['accepted'] for a, b in pairs),
                        'neither': sum(not a['accepted'] and not b['accepted'] for a, b in pairs)}
            groups.append(group)
    return {'created_at': datetime.now(timezone.utc).isoformat(),
        'groups': groups, 'complete': all(group['complete'] for group in groups),
        'selected_planned': sum(group['planned'] for group in groups),
        'selected_completed': sum(group['statuses'].get('completed', 0) for group in groups),
        'ledger_mismatches': sum(len(group['all_attempts_ledger_mismatches']) for group in groups),
        'treatment_violations': sum(len(group['treatment_violations']) for group in groups),
        'recovery_plan_sha256': hashlib.sha256((recovery / 'recovery_plan.json').read_bytes()).hexdigest(),
        'interpretation': 'Signal12 repeats three fixtures four times and lacks an initially execution-passing '
                          'gradient-only failure. Continuous-role changes both role handoff and conversation '
                          'representation. Format assistance includes prior examples and error feedback. '
                          'Corrected history removes repair conversation, retaining workspace and initial handoff.'}


def markdown(report):
    lines = ['# Main-text ablation recovery', '',
        '| Study | Treatment | Completed/planned | Accepted | Actual faults repaired | Selected known tokens | All-attempt unknown calls |',
        '| --- | --- | ---: | ---: | ---: | ---: | ---: |']
    for group in report['groups']:
        lines.append(f"| {group['study']} | {group['variant']} | {group['statuses'].get('completed', 0)}/{group['planned']} | "
            f"{group['accepted'] if group['complete'] else 'pending'} | {group['actual_faults_repaired'] if group['complete'] else 'pending'} | "
            f"{group['known_tokens']:,} | {group['all_attempts_usage'].get('unknown_usage_calls', 0)} |")
    lines += ['', report['interpretation'], '', 'Every old episode is retained in total cost. Unknown usage is not zero. '
              'A selected episode uses its own original-size budget; earlier interrupted episodes are additional.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--recovery', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    value = report(args.root.resolve(), args.recovery.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.with_suffix('.json').write_text(json.dumps(value, indent=2) + '\n')
    args.output.with_suffix('.md').write_text(markdown(value))
    print(json.dumps({key: value[key] for key in ('complete', 'selected_planned', 'selected_completed', 'ledger_mismatches', 'treatment_violations')}))


if __name__ == '__main__':
    main()
