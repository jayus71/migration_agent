"""Independent, API-free checks of frozen source traces and repair evidence.

Run after final_audit_summary.json is complete. This does not modify a candidate,
the evaluator, acceptance thresholds, or any original evidence file.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

import numpy as np

sys.dont_write_bytecode = True


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def check_array(reference, actual, initial=False):
    a, b = np.asarray(reference), np.asarray(actual)
    if a.shape != b.shape or a.dtype != b.dtype:
        return {'accepted': False, 'reason': 'shape_or_dtype',
                'reference': [list(a.shape), str(a.dtype)],
                'actual': [list(b.shape), str(b.dtype)]}
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        return {'accepted': False, 'reason': 'nonfinite'}
    difference = np.abs(a - b)
    tolerance = 0 if initial else 1e-7 + 1e-5 * np.abs(a)
    return {'accepted': bool(np.all(difference <= tolerance)),
            'bitwise_equal': bool(np.array_equal(a, b)),
            'max_abs_difference': float(difference.max(initial=0)),
            'mismatched_elements': int(np.count_nonzero(difference > tolerance))}


def replay_source(run, task, seed):
    import torch
    torch.set_num_threads(1)
    workspace = run / 'private_inputs' / task
    spec = importlib.util.spec_from_file_location('audited_source', workspace / 'source.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    model = module.build_model()
    observed = {}
    with np.load(workspace / 'inputs' / f'{seed}.npz') as public:
        state = {k[2:]: torch.from_numpy(public[k].copy()) for k in public.files
                 if k.startswith(('p:', 'b:'))}
        model.load_state_dict(state, strict=True)
        array = lambda v: v.detach().cpu().numpy().copy()
        observed.update({'initial:p:' + k: array(v) for k, v in model.named_parameters()})
        observed.update({'initial:b:' + k: array(v) for k, v in model.named_buffers()})
        optimizer = module.build_optimizer(model.parameters())
        for step in range(3):
            batch = {k.split(':', 2)[2]: torch.from_numpy(public[k].copy())
                     for k in public.files if k.startswith(f'batch:{step}:')}
            optimizer.zero_grad()
            loss, outputs = module.loss_and_outputs(task, model, batch)
            loss.backward()
            before = {k: array(v) for k, v in model.named_parameters()}
            gradients = {k: array(v.grad) if v.grad is not None else np.zeros_like(before[k])
                         for k, v in model.named_parameters()}
            optimizer.step()
            observed[f'{step}:loss'] = array(loss)
            outputs = dict(enumerate(outputs)) if isinstance(outputs, (tuple, list)) else {0: outputs}
            groups = {'outputs': {str(k): array(v) for k, v in outputs.items()},
                      'gradients': gradients,
                      'updates': {k: array(v) - before[k] for k, v in model.named_parameters()},
                      'parameters': {k: array(v) for k, v in model.named_parameters()},
                      'buffers': {k: array(v) for k, v in model.named_buffers()}}
            for group, values in groups.items():
                observed.update({f'{step}:{group}:{k}': v for k, v in values.items()})
    with np.load(run / 'private_reference' / task / f'{seed}.npz') as reference:
        keys_equal = set(reference.files) == set(observed)
        checks = {k: check_array(reference[k], observed[k], k.startswith('initial:'))
                  for k in reference.files if k in observed}
    return {'task': task, 'seed': seed, 'keys_equal': keys_equal,
            'checked_arrays': len(checks),
            'accepted': keys_equal and all(x['accepted'] for x in checks.values()),
            'all_bitwise_equal': all(x.get('bitwise_equal', False) for x in checks.values()),
            'maximum_absolute_difference': max(x.get('max_abs_difference', 0) for x in checks.values()),
            'failures': {k: v for k, v in checks.items() if not v['accepted']}}


def usage_check(folder, result):
    directory = folder / 'evidence' / 'agent'
    metadata = sorted(directory.glob('call_*_metadata.json'))
    responses = sorted(directory.glob('call_*_response.json'))
    requests = sorted(directory.glob('call_*_request.json'))
    identities = lambda paths: {p.name.split('_')[1] for p in paths}
    totals = Counter()
    models = Counter()
    stages = {}
    for path in responses:
        data = json.loads(path.read_text())
        metadata_path = path.with_name(path.name.replace('_response', '_metadata'))
        stage_name = json.loads(metadata_path.read_text()).get('stage') if metadata_path.exists() else 'missing_metadata'
        stage = stages.setdefault(stage_name, Counter())
        stage['calls'] += 1
        for key in ('prompt_tokens', 'completion_tokens', 'total_tokens'):
            totals[key] += data['usage'][key]
            stage[key] += data['usage'][key]
        models[data.get('model')] += 1
    budget = result['budget']
    return {'metadata_count': len(metadata), 'response_count': len(responses),
            'request_count': len(requests),
            'triplets_match': identities(requests) == identities(metadata) == identities(responses),
            'reported_calls': budget['calls'], 'raw_usage': dict(totals),
            'actual_models': dict(models),
            'usage_by_stage': {key: dict(value) for key, value in stages.items()},
            'calls_match': len(metadata) == len(responses) == budget['calls'],
            'usage_matches': all(value == budget['usage'][key] for key, value in totals.items()),
            'within_call_budget': budget['calls'] <= 40,
            'within_output_budget': totals['completion_tokens'] <= 120000,
            'within_submission_budget': len(result['attempts']) <= 4,
            'unknown_usage_calls': budget['usage'].get('unknown_usage_calls'),
            'unknown_prompt_usage_calls': budget['usage'].get('unknown_prompt_usage_calls'),
            'unknown_completion_usage_calls': budget['usage'].get('unknown_completion_usage_calls'),
            'elapsed_seconds': budget['usage']['elapsed_seconds']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('run', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise RuntimeError('Refusing to replace an independent audit')
    run = args.run.resolve()
    final = json.loads((run / 'final_audit_summary.json').read_text())
    if not final['complete']:
        raise RuntimeError('Original final audit is incomplete')
    frozen = []
    for name in ('pretranslation_hashes.json', 'translated_hashes.json'):
        for path, expected in json.loads((run / name).read_text()).items():
            frozen.append({'manifest': name, 'path': path, 'matches': sha(run / path) == expected})
    sources = [replay_source(run, task, seed)
               for task in json.loads((run / 'repair_selection.json').read_text())['repair_tasks']
               for seed in (8101, 8102, 8103)]
    conditions = []
    for row in final['conditions']:
        folder = run / 'conditions' / row['task'] / row['method']
        result = json.loads((folder / 'result.json').read_text())
        prefix = 'private_inputs/' + row['task'] + '/'
        immutable = [p[len(prefix):] for p in json.loads((run / 'translated_hashes.json').read_text())
                     if p.startswith(prefix) and not p.endswith('/candidate.py')]
        immutable_match = all(sha(run / 'private_inputs' / row['task'] / p) ==
                              sha(folder / 'workspace' / p) for p in immutable)
        seeds = []
        for measurement in row['checks']:
            path = Path(measurement['measurement'])
            target = path / 'target.npz'
            if not target.exists():
                seeds.append({'seed': measurement['seed'], 'accepted': False,
                              'execution_status': measurement['observation']['execution'],
                              'checked_arrays': 0})
                continue
            with np.load(run / 'private_reference' / row['task'] / f"{measurement['seed']}.npz") as ref, np.load(target) as got:
                keys_equal = set(ref.files) == set(got.files)
                checks = {k: check_array(ref[k], got[k], k.startswith('initial:'))
                          for k in ref.files if k in got.files}
            reported = {x['quantity']: x['accepted'] for x in json.loads((path / 'checks.json').read_text())}
            failures = {k: v for k, v in checks.items() if not v['accepted']}
            seeds.append({'seed': measurement['seed'], 'keys_equal': keys_equal,
                          'accepted': keys_equal and not failures, 'checked_arrays': len(checks),
                          'per_array_verdict_matches': keys_equal and all(reported.get(k) == v['accepted'] for k, v in checks.items()),
                          'failures': failures})
        accepted = all(s['accepted'] for s in seeds)
        conditions.append({'task': row['task'], 'method': row['method'], 'seeds': seeds,
                           'accepted': accepted, 'matches_original': accepted == result['accepted'],
                           'immutable_files_match': immutable_match,
                           'usage': usage_check(folder, result)})
    translations = []
    for folder in sorted((run / 'translations').iterdir()):
        response = json.loads((folder / 'response.json').read_text())
        result = json.loads((folder / 'result.json').read_text())
        translations.append({'task': folder.name, 'status': result['status'],
                             'request_exists': (folder / 'request.json').exists(),
                             'usage': response['usage'],
                             'usage_matches': response['usage'] == result['usage']})
    translation_totals = {key: sum(row['usage'][key] for row in translations)
                          for key in ('prompt_tokens', 'completion_tokens', 'total_tokens')}
    summary = json.loads((run / 'formal_summary.json').read_text())
    payload = {'scope': 'No API calls; independent replay of six public-source traces and independent NumPy rescoring of final target artifacts.',
               'script_sha256': sha(Path(__file__)), 'run': str(run),
               'frozen_files': len(frozen), 'frozen_files_match': all(x['matches'] for x in frozen),
               'frozen_mismatches': [x for x in frozen if not x['matches']],
               'source_replays': sources, 'conditions': conditions,
               'translations': translations, 'translation_totals': translation_totals,
               'translation_ledger_matches': len(translations) == 12 and
                    all(x['usage_matches'] and x['request_exists'] for x in translations) and
                    translation_totals == summary['source_pool_translation_usage'],
               'original_final_audit_flags': {key: final[key] for key in
                    ('all_acceptances_reproduced', 'all_immutable', 'all_repair_usage_reconciled', 'backend_flags')},
               'all_source_replays_pass': all(x['accepted'] for x in sources),
               'all_acceptances_match': all(x['matches_original'] for x in conditions),
               'all_per_array_verdicts_match': all(seed.get('per_array_verdict_matches',
                    seed.get('checked_arrays') == 0 and not seed['accepted'])
                    for row in conditions for seed in row['seeds']),
               'all_immutable_files_match': all(x['immutable_files_match'] for x in conditions),
               'all_usage_matches': all(x['usage']['calls_match'] and x['usage']['triplets_match'] and
                    x['usage']['usage_matches'] and x['usage']['unknown_usage_calls'] == 0 and
                    x['usage']['unknown_prompt_usage_calls'] == 0 and
                    x['usage']['unknown_completion_usage_calls'] == 0 for x in conditions)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + '\n')
    print(json.dumps({k: v for k, v in payload.items() if k not in ('source_replays', 'conditions', 'translations')}))


if __name__ == '__main__':
    os.environ.setdefault('OMP_NUM_THREADS', '1')
    os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
    main()
