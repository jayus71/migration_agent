"""Produce trusted native traces and optional backend controls without any LLM."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import copy
import json
import os
from pathlib import Path
import subprocess
import sys

from score import compare


def execute(bundle, root, group, item, seed, runtime):
    folder = root / group / runtime / str(seed)
    folder.mkdir(parents=True, exist_ok=False)
    task = bundle / 'public' / item['task']
    output = folder / 'measurement.json'
    command = [sys.executable, str(Path(__file__).with_name('measure.py')),
               '--program', str(task / 'source.py'), '--contract', str(task / 'task.json'),
               '--kind', item['input_form'], '--runtime', runtime, '--seed', str(seed), '--out', str(output)]
    environment = {k: v for k, v in os.environ.items() if not any(
        key in k.upper() for key in ('API_KEY', 'TOKEN', 'SECRET', 'PASSWORD'))}
    environment.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1',
                       PYTHONPATH=str(Path(__file__).resolve().parents[2]))
    try:
        result = subprocess.run(command, env=environment, cwd=Path(__file__).parents[2],
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
        (folder / 'process.log').write_text(result.stdout)
        measured = json.loads(output.read_text()) if output.exists() else {'status': 'process_failed'}
    except subprocess.TimeoutExpired:
        measured = {'status': 'timeout'}
    return {'group': group, 'representative': item['task'], 'runtime': runtime, 'seed': seed,
            'status': measured['status'], 'path': str(output),
            'error': measured.get('error')}


def calibration(reference):
    positive = copy.deepcopy(reference)
    positive['backend'] = {'observed': True}
    rows = [{'mutation': 'healthy', 'expected': True, 'actual': compare(reference, positive)['accepted']}]
    for prefix in ('forward/', 'gradient/', 'update/'):
        keys = [key for key, value in positive['values'].items() if key.startswith(prefix) and value is not None]
        if not keys:
            continue
        for mutation in ('offset', 'missing', 'nonfinite'):
            modified = copy.deepcopy(positive)
            key = keys[0]
            if mutation == 'missing':
                modified['values'][key] = None
            else:
                import numpy as np
                value = np.asarray(modified['values'][key], dtype=float)
                modified['values'][key] = (value + (1.0 if mutation == 'offset' else float('nan'))).tolist()
            rows.append({'mutation': prefix + mutation, 'expected': False,
                         'actual': compare(reference, modified)['accepted']})
    modified = copy.deepcopy(positive)
    modified['backend']['observed'] = False
    rows.append({'mutation': 'missing_backend', 'expected': False,
                 'actual': compare(reference, modified)['accepted']})
    modified = {'status': 'execution_failed'}
    failure = compare(reference, modified)
    rows.append({'mutation': 'execution_failure', 'expected': False, 'actual': failure['accepted'],
                 'unmeasured_preserved': bool(failure['unavailable'])})
    assert all(row['expected'] == row['actual'] for row in rows)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--runtimes', nargs='+', default=['torch'])
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--tasks', nargs='*')
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    manifest = json.loads((args.bundle / 'manifest.json').read_text())
    items = {row['task']: row for row in manifest['tasks']}
    jobs = []
    for index, group in enumerate(manifest['shared_translation_groups'], 1):
        task = group['tasks'][0]
        if args.tasks and not set(group['tasks']).intersection(args.tasks):
            continue
        for runtime in args.runtimes:
            for seed in (101, 202, 303):
                jobs.append((f'group_{index:03d}', items[task], seed, runtime))
    rows = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(execute, args.bundle, args.out, *job) for job in jobs]
        for future in as_completed(futures):
            row = future.result()
            rows.append(row)
            print(json.dumps({k: row[k] for k in ('group', 'representative', 'runtime', 'seed', 'status')}), flush=True)
    controls = []
    for row in rows:
        if row['runtime'] == 'torch' and row['status'] == 'completed':
            reference = json.loads(Path(row['path']).read_text())
            controls.append({'group': row['group'], 'seed': row['seed'], 'checks': calibration(reference)})
    summary = {'real_model_calls': 0, 'jobs': len(rows),
               'completed': sum(row['status'] == 'completed' for row in rows),
               'rows': sorted(rows, key=lambda row: (row['group'], row['runtime'], row['seed'])),
               'score_calibration': controls}
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k not in ('rows', 'score_calibration')}))


if __name__ == '__main__':
    main()
