"""Count existing repository checks on fixed protocol grids without rerunning experiments."""
import argparse
import hashlib
import json
from pathlib import Path


VARIANTS = ('base', 'history', 'position', 'user', 'debias', 'reward')
SIGNALS = ('user_embedding', 'item_embedding', 'loss', 'epoch_loss', 'gradient', 'update')
METHODS = ('ladim', 'swe', 'matchfix')


def count(checks, expected):
    expected = list(expected)
    values = {key: checks.get(key) for key in expected}
    passed = sum(value is True for value in values.values())
    failed = [key for key, value in values.items() if value is False]
    missing = [key for key, value in values.items() if value is None]
    assert passed + len(failed) + len(missing) == len(expected)
    return {'passed': passed, 'expected': len(expected), 'failed': failed,
            'not_measured': missing, 'passed_fraction': passed / len(expected)}


def analyze(root):
    # These keys follow the frozen compare() and source behaviors in the protocol.
    # No keys are selected or removed according to a method's outcome.
    training = [f'{variant}_step{step}_{signal}' for variant in VARIANTS
                for step in (1, 2, 3) for signal in SIGNALS]
    retrieval = [f'{variant}_retrieval' for variant in VARIANTS]
    status = [f'{variant}_{check}' for variant in VARIANTS
              for check in ('inference_status', 'training_status', 'three_steps', 'native_autodiff')]
    source_behavior = ['ranker_inference_status', 'ranker_inference_exception',
                       'ranker_training_status', 'ranker_training_exception',
                       'distillation_inference_status', 'distillation_inference_exception',
                       'distillation_training_status']
    protocol = training + retrieval + status + source_behavior
    assert len(set(protocol)) == 145
    timeseries_keys = ['preprocessing_' + key for key in ('normalized', 'windows', 'unseen', 'labels', 'inverse')]
    timeseries_keys += [f'step_{step}_{signal}' for step in (1, 2, 3)
                       for signal in ('prediction_max_abs', 'loss_abs', 'gradient_vector_l2',
                                      'parameter_update_relative_l2', 'native_autodiff')]
    timeseries_keys += ['three_steps', 'learning_rate_boundaries', 'parameter_count']
    assert len(timeseries_keys) == 23
    output = {
        'definition': 'Post-run descriptive counts of existing checks. A check is not an independent migration task. Missing checks remain null and are listed separately; the full declared denominator is retained.',
        'twotower_protocol': {'training_checks': 108, 'retrieval_checks': 6, 'status_checks': 24,
                             'source_behavior_checks': 7, 'total_checks': 145, 'public_seed': 101},
        'input_sha256': {}, 'twotower': {}, 'timeseries': {},
    }
    for repository in ('timeseries', 'twotower'):
        for method in METHODS:
            path = root / repository / 'conditions' / method / 'result.json'
            result = json.loads(path.read_text())
            output['input_sha256'][str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
            public = result['final']['public']
            checks = public['numeric']['checks']
            row = {'complete_acceptance': result['accepted'], 'repair_calls': result['calls'],
                   'end_to_end_tokens': result['end_to_end_tokens']}
            if repository == 'twotower':
                assert not set(checks) - set(protocol), set(checks) - set(protocol)
                row['protocol_checks'] = count(checks, protocol)
                row['numerical_checks'] = count(checks, training + retrieval)
                row['training_checks'] = count(checks, training)
                row['retrieval_checks'] = count(checks, retrieval)
                row['training_signals'] = {signal: count(checks, [f'{variant}_step{step}_{signal}'
                    for variant in VARIANTS for step in (1, 2, 3)]) for signal in SIGNALS}
                row['training_steps_complete'] = count({f'{variant}_step{step}':
                    all(checks[f'{variant}_step{step}_{signal}'] for signal in SIGNALS)
                    if all(f'{variant}_step{step}_{signal}' in checks for signal in SIGNALS) else None
                    for variant in VARIANTS for step in (1, 2, 3)},
                    [f'{variant}_step{step}' for variant in VARIANTS for step in (1, 2, 3)])
                tests = public['tests']['tests']
                row['original_tests'] = {
                    'expected': 10, 'observed_outcomes': tests['tests'], 'exit_code': tests['exit_code'],
                    'passed': sum(t['outcome'] == 'passed' for t in tests['tests']),
                    'status': 'collected' if tests['tests'] else 'collection_failed',
                }
                row['workflow_accepted'] = public['workflow']['accepted']
                row['coverage_accepted'] = public['coverage']['accepted']
                row['documentation_accepted'] = public['documentation']['accepted']
            else:
                assert set(checks) == set(timeseries_keys)
                seed_checks = [('public', checks)] + [(f'confirmation_{i}', x['observation']['numeric']['checks'])
                    for i, x in enumerate(result['final']['confirmations'], 1)]
                assert len(seed_checks) == 3
                row['public_checks'] = count(checks, timeseries_keys)
                row['all_seed_checks'] = count({f'{seed}:{key}': c.get(key) for seed, c in seed_checks
                    for key in timeseries_keys}, [f'{seed}:{key}' for seed, _ in seed_checks for key in timeseries_keys])
            output[repository][method] = row
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence_root', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    summary = analyze(args.evidence_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n')
    for method, row in summary['twotower'].items():
        print(method, {key: f"{row[key]['passed']}/{row[key]['expected']}" for key in
              ('protocol_checks', 'numerical_checks', 'training_checks', 'training_steps_complete')})
    for method, row in summary['timeseries'].items():
        print('timeseries', method, row['all_seed_checks']['passed'], row['all_seed_checks']['expected'])
