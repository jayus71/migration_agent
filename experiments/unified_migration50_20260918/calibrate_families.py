"""Calibrate private targets across the complete frozen collection without APIs."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import subprocess
import sys

from score import compare


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--groups', nargs='*')
    args = parser.parse_args()
    package, out = args.package.resolve(), args.out.resolve()
    assert not out.exists()
    manifest = json.loads((package / 'bundle/manifest.json').read_text())
    tasks = {row['task']: row for row in manifest['tasks']}
    template = (package / 'native_family_controls.py').read_text()
    def job(group, task, seed):
        public = package / 'bundle/public' / task
        contract = json.loads((public / 'task.json').read_text())
        source = (public / 'source.py').read_text()
        kind = tasks[task]['input_form']
        code = template.replace("KIND = 'execution'", f'KIND = {kind!r}')
        code = code.replace("MODEL_VARIANT = 'mlp'", f"MODEL_VARIANT = {contract['model_variant']!r}")
        if 'def workload(value)' in source:
            code = code.replace("NATIVE_FORM = 'attention'", "NATIVE_FORM = 'relu'")
        if 'def embedding_workload' in source:
            code = code.replace('HAS_EMBEDDING = False', 'HAS_EMBEDDING = True')
        folder = out / group / str(seed)
        folder.mkdir(parents=True)
        candidate, measured = folder / 'candidate.py', folder / 'measurement.json'
        candidate.write_text(code)
        process = subprocess.run([sys.executable, str(package / 'measure.py'),
            '--program', str(candidate), '--contract', str(public / 'task.json'), '--kind', kind,
            '--runtime', 'mindspore', '--seed', str(seed), '--out', str(measured)],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=180)
        (folder / 'process.log').write_text(process.stdout)
        actual = json.loads(measured.read_text()) if measured.exists() else {'status': 'process_failed'}
        reference = json.loads((package / 'reference_complete' / group / 'torch' / str(seed) / 'measurement.json').read_text())
        result = compare(reference, actual)
        return {'group': group, 'task': task, 'kind': kind, 'seed': seed,
                'accepted': result['accepted'], 'status': actual['status'],
                'failed_checks': [k for k, v in result['checks'].items() if not v],
                'error': actual.get('error', '')[-2500:]}
    rows = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = [pool.submit(job, f'group_{i:03d}', group['tasks'][0], seed)
                for i, group in enumerate(manifest['shared_translation_groups'], 1)
                if not args.groups or f'group_{i:03d}' in args.groups
                for seed in (101, 202, 303)]
        for future in as_completed(jobs):
            row = future.result()
            rows.append(row)
            print(json.dumps({k: v for k, v in row.items() if k != 'error'}), flush=True)
    report = {'real_model_calls': 0, 'passed': all(row['accepted'] for row in rows),
              'accepted': sum(row['accepted'] is True for row in rows), 'total': len(rows),
              'rows': sorted(rows, key=lambda row: (row['group'], row['seed']))}
    (out / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    if not report['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
