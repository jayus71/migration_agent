"""Summarize the frozen cumulative-component runs without calling a model."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from analyze_repository_partial_results import VARIANTS, SIGNALS, count as count_existing_checks

CONDITIONS = ('repair', 'investigation', 'handoff', 'repository_context')
LABELS = ('Repair agent', '+ Verifier investigation', '+ Independent handoff', '+ Repository context')


def read(path):
    return json.loads(path.read_text())


def count(checks, expected):
    result = count_existing_checks(checks, expected)
    result['measured'] = result['expected'] - len(result['not_measured'])
    if result['measured'] == 0:
        result['passed'] = None
        result['passed_fraction'] = None
    return result


def expected_checks():
    training = [f'{variant}_step{step}_{signal}' for variant in VARIANTS
                for step in (1, 2, 3) for signal in SIGNALS]
    retrieval = [f'{variant}_retrieval' for variant in VARIANTS]
    status = [f'{variant}_{check}' for variant in VARIANTS for check in
              ('inference_status', 'training_status', 'three_steps', 'native_autodiff')]
    behavior = ['ranker_inference_status', 'ranker_inference_exception',
                'ranker_training_status', 'ranker_training_exception',
                'distillation_inference_status', 'distillation_inference_exception',
                'distillation_training_status']
    ts = ['preprocessing_' + key for key in ('normalized', 'windows', 'unseen', 'labels', 'inverse')]
    ts += [f'step_{step}_{signal}' for step in (1, 2, 3) for signal in
           ('prediction_max_abs', 'loss_abs', 'gradient_vector_l2',
            'parameter_update_relative_l2', 'native_autodiff')]
    ts += ['three_steps', 'learning_rate_boundaries', 'parameter_count']
    assert len(training + retrieval + status + behavior) == 145 and len(ts) == 23
    return training, retrieval, status, behavior, ts


def summarize(root):
    training, retrieval, status, behavior, ts = expected_checks()
    rows = []
    hashes = {}
    for condition, label in zip(CONDITIONS, LABELS):
        for repository in ('timeseries', 'twotower'):
            folder = root / repository / 'conditions' / condition
            result_path = folder / 'result.json'
            row = {'repository': repository, 'condition': condition, 'label': label,
                   'status': 'not_run', 'replicate': 1}
            if not result_path.exists():
                rows.append(row)
                continue
            hashes[str(result_path.relative_to(root))] = hashlib.sha256(result_path.read_bytes()).hexdigest()
            result = read(result_path)
            final = result.get('final', {})
            public = final.get('public', {})
            numeric = public.get('numeric', {})
            checks = numeric.get('checks', {})
            responses = [read(p) for p in sorted((folder / 'evidence/agent').glob('call_*_response.json'))]
            requests = list((folder / 'evidence/agent').glob('call_*_request.json'))
            row.update({key: result.get(key) for key in ('status', 'accepted', 'calls', 'usage',
                'end_to_end_tokens', 'translation_usage', 'source_unchanged', 'task_unchanged',
                'stop_reason', 'error')})
            row['repair_tokens'] = (result.get('usage') or {}).get('total_tokens')
            translation_path = root / repository / 'translation/result.json'
            row['translation_calls'] = read(translation_path).get('calls') if translation_path.exists() else None
            row['end_to_end_calls'] = row['calls'] + row['translation_calls'] if row.get('calls') is not None and row['translation_calls'] is not None else None
            row['submissions'] = len(result.get('attempts', []))
            row['stage_statuses'] = [a['stage']['status'] for a in result.get('attempts', [])]
            last_stage = row['stage_statuses'][-1] if row['stage_statuses'] else None
            row['termination'] = ('accepted' if row.get('accepted') else
                row.get('stop_reason') or (last_stage if last_stage in ('context_budget_exhausted',
                'api_error', 'infrastructure_error', 'error', 'not_applicable') else
                'submission_budget_exhausted' if row['submissions'] == 4 else row['status']))
            row['diagnosis_status'] = (result.get('diagnosis') or {}).get('status')
            row['recorded_request_count'] = len(requests)
            row['recorded_response_count'] = len(responses)
            valid_usage = [r.get('usage') for r in responses if isinstance(r, dict) and isinstance(r.get('usage'), dict)]
            row['response_usage_total'] = sum(u.get('total_tokens', 0) for u in valid_usage)
            row['response_prompt_and_completion_total'] = sum(u.get('prompt_tokens', 0) + u.get('completion_tokens', 0)
                                                              for u in valid_usage)
            row['api_errors'] = [read(p) for p in sorted((folder / 'evidence/agent').glob('call_*_error.json'))]
            metadata = [read(p) for p in sorted((folder / 'evidence/agent').glob('call_*_metadata.json'))]
            row['recorded_metadata_count'] = len(metadata)
            row['diagnosis_calls'] = sum(m.get('stage') == 'diagnose' for m in metadata)
            row['repair_stage_calls'] = sum(m.get('stage') == 'repair' for m in metadata)
            row['role_handoffs'] = len(list((folder / 'evidence/agent').glob('event_*_role_handoff.json')))
            row['repository_context_rebuilds'] = [{key: event.get('data', {}).get(key) for key in
                ('reason', 'generation', 'messages_sent', 'prepared_chars', 'calls_used', 'output_tokens_used')}
                for event in [read(p) for p in sorted((folder / 'evidence/agent').glob('event_*_repository_context.json'))]]
            row['context_budget_events'] = len(list((folder / 'evidence/agent').glob('event_*_context_budget_exhausted.json')))
            row['elapsed_seconds'] = result.get('finished', 0) - result.get('started', 0) if result.get('finished') else None
            row['documentation_accepted'] = public.get('documentation', {}).get('accepted')
            row['workflow_accepted'] = public.get('workflow', {}).get('accepted')
            row['coverage_accepted'] = public.get('coverage', {}).get('accepted')
            row['entrypoints_accepted'] = public.get('entrypoints', {}).get('accepted')
            row['numeric_execution'] = numeric.get('execution')
            row['unknown_usage_calls'] = (result.get('usage') or {}).get('unknown_usage_calls')
            if repository == 'timeseries':
                assert not set(checks) - set(ts), set(checks) - set(ts)
                seed_checks = {'public': checks}
                for i, confirmation in enumerate(final.get('confirmations', []), 1):
                    seed_checks[f'confirmation_{i}'] = confirmation.get('observation', {}).get('numeric', {}).get('checks', {})
                combined = {f'{seed}:{key}': data.get(key) for seed, data in seed_checks.items() for key in ts}
                row['protocol_checks'] = count(combined, [f'{seed}:{key}' for seed in
                    ('public', 'confirmation_1', 'confirmation_2') for key in ts])
                row['public_checks'] = count(checks, ts)
                row['confirmations'] = len(final.get('confirmations', []))
            else:
                protocol = training + retrieval + status + behavior
                assert not set(checks) - set(protocol), set(checks) - set(protocol)
                row['protocol_checks'] = count(checks, protocol)
                row['numerical_checks'] = count(checks, training + retrieval)
                row['training_signals'] = {signal: count(checks, [f'{variant}_step{step}_{signal}'
                    for variant in VARIANTS for step in (1, 2, 3)]) for signal in SIGNALS}
                tests = public.get('tests', {}).get('tests', {})
                observed_tests = tests.get('tests', [])
                row['original_tests'] = {'expected': 10, 'passed': sum(t['outcome'] == 'passed'
                    for t in observed_tests) if observed_tests else None,
                    'observed_outcomes': observed_tests, 'exit_code': tests.get('exit_code')}
            rows.append(row)
    terminal = len(rows) == 8 and all(r['status'] not in ('not_run', 'running') for r in rows)
    measured = [r for r in rows if r.get('usage')]
    ledger = {'new_model_calls': sum(r['calls'] for r in measured),
              'new_measured_tokens': sum(r['repair_tokens'] for r in measured),
              'new_completion_tokens': sum(r['usage']['completion_tokens'] for r in measured),
              'unknown_usage_calls': sum(r.get('unknown_usage_calls') or 0 for r in measured),
              'new_translation_calls': 0,
              'historical_translation_tokens_per_condition': {'timeseries': 163661, 'twotower': 368368},
              'historical_translation_calls_per_condition': {'timeseries': 3, 'twotower': 20}}
    return {'rows': rows, 'all_conditions_terminal': terminal, 'physical_ledger': ledger,
            'result_sha256': hashes,
            'definition': 'Eight new runs: two fixed repositories, four cumulative conditions, one run per cell. '
                'Check denominators are 69 and 145. Checks are descriptive outcomes, not independent tasks. '
                'Unmeasured checks remain null in the raw observations and are listed as not_measured. '
                'Every model call, including failed calls, remains in the cost ledger; unknown usage is explicit. '
                'End-to-end tokens attribute the historical common initial translation once to each run.'}


def write_outputs(summary, output):
    output.mkdir(parents=True, exist_ok=True)
    (output / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n')
    fields = ('repository', 'condition', 'status', 'accepted', 'checks_passed', 'checks_expected',
              'checks_failed', 'checks_not_measured', 'calls', 'repair_tokens', 'translation_calls',
              'translation_tokens', 'end_to_end_calls', 'end_to_end_tokens', 'submissions', 'unknown_usage_calls')
    with (output / 'summary.csv').open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in summary['rows']:
            flat = {key: row.get(key) for key in fields}
            c = row.get('protocol_checks', {})
            flat.update(checks_passed=c.get('passed'), checks_expected=c.get('expected'),
                        checks_failed=len(c['failed']) if c else None,
                        checks_not_measured=len(c['not_measured']) if c else None,
                        translation_tokens=(row.get('translation_usage') or {}).get('total_tokens'))
            writer.writerow(flat)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    summary = summarize(args.root)
    write_outputs(summary, args.output)
    print(json.dumps({'terminal': summary['all_conditions_terminal'], 'ledger': summary['physical_ledger']}))
