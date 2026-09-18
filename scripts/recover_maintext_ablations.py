"""Declared infrastructure recovery and complete corrected-history reruns."""
from __future__ import annotations
import argparse
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.error
import urllib.request


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(data, indent=2) + '\n')
    temp.replace(path)


def load(path):
    spec = importlib.util.spec_from_file_location('frozen_treatment', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def eligible(run, variant):
    if variant == 'without_repair_history':
        return []
    manifest = read(run / variant / 'manifest.json')
    selected = []
    for task in manifest['tasks']:
        path = run / variant / 'conditions' / task['anonymous_id'] / 'autonomous_layered/result.json'
        row = read(path)
        if row['status'] == 'infrastructure_error':
            selected.append({'task': task['anonymous_id'], 'variant': variant,
                             'original_result': str(path), 'original_result_sha256': sha(path),
                             'selection_reason': 'infrastructure_error'})
        elif row['status'] != 'completed':
            raise ValueError('Unexpected original state')
    return selected


def prepare(root, output, corrected_runner):
    if output.exists():
        raise ValueError('Output must be new')
    output.mkdir(parents=True)
    shutil.copy2(__file__, output / Path(__file__).name)
    shutil.copy2(corrected_runner, output / 'corrected_history_runner.py')
    jobs, copies = [], []
    for study in ('natural10_v3', 'signal12_v3', 'fixed50_v3'):
        original = root / study
        plan = read(original / 'plan.json')
        runner_name = 'run_signal_ablations.py' if study.startswith('signal') else 'run_maintext_ablations.py'
        copied = output / study
        copied.mkdir()
        shutil.copy2(original / runner_name, copied / runner_name)
        shutil.copy2(original / 'plan.json', copied / 'plan.json')
        module = load(copied / runner_name)
        for variant in plan['variants']:
            selected = eligible(original, variant)
            if not selected:
                continue
            target = copied / variant
            target.mkdir()
            for filename in ('manifest.json', 'frozen_hashes.json'):
                shutil.copy2(original / variant / filename, target / filename)
            for directory in ('private_inputs', 'private_cases', 'code_snapshot'):
                source = original / variant / directory
                if source.exists():
                    shutil.copytree(source, target / directory,
                                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            verifier = module.verify if study.startswith('signal') else module.verify_frozen
            verifier(target)
            copies.append({'run': str(target), 'original': str(original / variant),
                           'manifest_sha256': sha(target / 'manifest.json'),
                           'file_inventory_sha256': sha(target / 'frozen_hashes.json')})
            jobs.extend({**row, 'study': study, 'run': str(target), 'runner': str(copied / runner_name)}
                        for row in selected)
    history = load(output / 'corrected_history_runner.py')
    for study in ('natural10_v3', 'fixed50_v3'):
        source = Path(read(root / study / 'plan.json')['source_run'])
        target = output / study.replace('_v3', '_history_v4')
        history.prepare(source, target, ['without_repair_history'])
        run = target / 'without_repair_history'
        for task in read(run / 'manifest.json')['tasks']:
            jobs.append({'study': target.name, 'variant': 'without_repair_history',
                         'task': task['anonymous_id'], 'run': str(run),
                         'runner': str(target / 'run_maintext_ablations.py'),
                         'selection_reason': 'complete_treatment_rerun_after_history_prompt_correction'})
    jobs.sort(key=lambda row: ('fixed50' in row['study'], row['task'], row['study'], row['variant']))
    value = {'created_at': datetime.now(timezone.utc).isoformat(), 'root': str(root),
             'launcher_sha256': sha(output / Path(__file__).name), 'jobs': jobs, 'copied_runs': copies,
             'policy': 'Only declared infrastructure failures restart with independent original-size budgets. '
                       'The history treatment reruns all 60 tasks with an accurate history contract. '
                       'All prior results and costs are retained. No completed functional failure is retried.'}
    save(output / 'recovery_plan.json', value)
    return value


def worker(run, runner, task):
    condition = run / 'conditions' / task / 'autonomous_layered'
    if condition.exists():
        raise ValueError('Condition already exists')
    original = urllib.request.urlopen
    attempts = []
    def observed(*args, **kwargs):
        try:
            return original(*args, **kwargs)
        except Exception as error:
            attempts.append({'recorded_at': datetime.now(timezone.utc).isoformat(),
                             'error_type': type(error).__name__,
                             'http_status': error.code if isinstance(error, urllib.error.HTTPError) else None})
            save(condition / 'transport_failures.json', attempts)
            raise
    urllib.request.urlopen = observed
    return load(runner).worker(run, task)


def execute(output, workers):
    lock = (output / 'dispatch.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    plan = read(output / 'recovery_plan.json')
    if sha(Path(__file__)) != plan['launcher_sha256']:
        raise ValueError('Launcher changed')
    for job in plan['jobs']:
        if (Path(job['run']) / 'conditions' / job['task']).exists():
            raise ValueError('Existing job artifacts; implicit restart prohibited')
        if job.get('original_result') and sha(Path(job['original_result'])) != job['original_result_sha256']:
            raise ValueError('Original result changed')
    def one(job):
        run = Path(job['run'])
        config = read(run / 'manifest.json')
        env = os.environ.copy()
        env.update(AUTOFIX_LLM_MODEL=config['model'], AUTOFIX_LLM_TEMPERATURE=str(config['temperature']),
                   OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
        path = output / 'worker_logs' / (job['study'] + '_' + job['variant'] + '_' + job['task'] + '.log')
        path.parent.mkdir(exist_ok=True)
        with path.open('x') as log:
            process = subprocess.run([sys.executable, str(Path(__file__).resolve()), 'worker', '--run', str(run),
                '--runner', job['runner'], '--task', job['task']], cwd=run / 'code_snapshot', env=env,
                stdout=log, stderr=subprocess.STDOUT)
        path = run / 'conditions' / job['task'] / 'autonomous_layered/result.json'
        result = read(path) if path.exists() else {}
        return {**job, 'status': result.get('status', 'missing_result'),
                'accepted': result.get('accepted'), 'returncode': process.returncode, 'result': str(path)}
    pending, completed, blocked = list(plan['jobs']), [], False
    with ThreadPoolExecutor(max_workers=workers) as pool:
        active = set()
        while pending or active:
            blocked = blocked or any(output.glob('*/*/conditions/*/*/transport_failures.json'))
            while pending and len(active) < workers and not blocked:
                active.add(pool.submit(one, pending.pop(0)))
            if not active:
                break
            done, active = wait(active, timeout=1, return_when=FIRST_COMPLETED)
            for future in done:
                row = future.result()
                completed.append(row)
                if row['status'] != 'completed' or row['returncode'] != 0:
                    blocked = True
                print(json.dumps({k: row[k] for k in ('study', 'variant', 'task', 'status', 'accepted')}), flush=True)
            save(output / 'progress.json', {'planned': len(plan['jobs']), 'completed': completed,
                'active': len(active), 'pending': len(pending), 'blocked': blocked})
    save(output / 'dispatch_result.json', {'completed': completed, 'not_started': pending, 'blocked': blocked})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'execute', 'worker'])
    parser.add_argument('--root', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--corrected-runner', type=Path)
    parser.add_argument('--run', type=Path)
    parser.add_argument('--runner', type=Path)
    parser.add_argument('--task')
    parser.add_argument('--workers', type=int, default=6)
    args = parser.parse_args()
    if args.action == 'prepare':
        print(json.dumps({'jobs': len(prepare(args.root.resolve(), args.output.resolve(), args.corrected_runner.resolve())['jobs'])}))
    elif args.action == 'execute':
        execute(args.output.resolve(), args.workers)
    else:
        worker(args.run.resolve(), args.runner.resolve(), args.task)


if __name__ == '__main__':
    main()
