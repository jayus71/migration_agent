"""Run each approved condition once, at most three jobs concurrently."""
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

from repository_migration_experiment import ROOT, RUN, assert_frozen, save, read


def main():
    assert_frozen()
    # Read the same private backend configuration used by prior experiments.
    for line in (Path.home() / '.autofix_llm_env').read_text().splitlines():
        parts = shlex.split(line, comments=True)
        if parts and parts[0] == 'export':
            parts = parts[1:]
        if len(parts) == 1 and '=' in parts[0]:
            key, value = parts[0].split('=', 1)
            if key.startswith('AUTOFIX_LLM_'):
                os.environ[key] = value
    assert os.environ.get('AUTOFIX_LLM_API_KEY')
    assert os.environ.get('AUTOFIX_LLM_MODEL') == 'deepseek-v4-flash'
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
        os.environ[key] = '1'
    records = []
    scheduler = RUN / 'scheduler.json'
    if scheduler.exists():
        raise FileExistsError('This suite was already dispatched; inspect its results before any continuation')
    save(scheduler, {'status': 'running', 'pid': os.getpid(), 'max_parallel_jobs': 3, 'jobs': []})
    def run_job(repository, method):
        label = repository + '_' + method
        args = [sys.executable, str(ROOT / 'scripts/repository_migration_experiment.py')]
        args += ['generate'] if method == 'translation' else ['run', '--repository', repository, '--method', method]
        logpath = RUN / (label + '.log')
        with logpath.open('x') as log:
            process = subprocess.Popen(args, cwd=ROOT, env=os.environ.copy(), stdout=log, stderr=subprocess.STDOUT)
            record = {'repository': repository, 'method': method, 'pid': process.pid, 'status': 'running', 'started': time.time()}
            records.append(record)
            save(RUN / (label + '_process.json'), record)
            code = process.wait()
            record.update(status='completed' if code == 0 else 'process_error', returncode=code, finished=time.time())
            save(RUN / (label + '_process.json'), record)
        return record
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(run_job, 'twotower', 'translation'): ('twotower', 'translation')}
        for method in ('ladim', 'swe', 'matchfix'):
            futures[pool.submit(run_job, 'timeseries', method)] = ('timeseries', method)
        while futures:
            done, _ = wait(futures, timeout=20, return_when=FIRST_COMPLETED)
            for future in done:
                repository, method = futures.pop(future)
                result = future.result()
                if method == 'translation' and result['returncode'] == 0:
                    for target in ('ladim', 'swe', 'matchfix'):
                        futures[pool.submit(run_job, 'twotower', target)] = ('twotower', target)
            save(scheduler, {'status': 'running' if futures else 'completed', 'pid': os.getpid(),
                'max_parallel_jobs': 3, 'jobs': records, 'queued_or_running': list(futures.values())})
    results = {}
    for repository in ('timeseries', 'twotower'):
        for method in ('ladim', 'swe', 'matchfix'):
            path = RUN / repository / 'conditions' / method / 'result.json'
            results[repository + ':' + method] = read(path) if path.exists() else {'status': 'not_run'}
    save(RUN / 'results.json', results)


if __name__ == '__main__':
    main()
