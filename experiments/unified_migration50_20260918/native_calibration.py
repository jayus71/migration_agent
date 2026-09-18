"""Measure healthy/forward/gradient/update controls on the actual target backend."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from score import compare


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    assert not args.out.exists()
    args.out.mkdir(parents=True)
    template = Path(__file__).with_name('native_control.py').read_text()
    variants = {
        'healthy': template,
        'forward': template.replace('return self.fc2(ops.relu(self.fc1(x)))',
                                    'return self.fc2(ops.relu(self.fc1(x))) + 0.25'),
        'gradient': template.replace('return self.fc2(ops.relu(self.fc1(x)))',
                                     'value = self.fc2(ops.relu(self.fc1(x)))\n        return value * 2 - ops.stop_gradient(value)'),
        'update': template.replace('learning_rate=.2', 'learning_rate=.3'),
    }
    rows = []
    for task, variant in [('task_035', 'transformer'), ('task_037', 'cnn')]:
        source = args.bundle / 'public' / task
        for seed in (101, 202, 303):
            reference = args.out / f'{task}_{seed}_reference.json'
            base = [sys.executable, str(Path(__file__).with_name('measure.py')),
                    '--contract', str(source / 'task.json'), '--kind', 'training', '--seed', str(seed)]
            subprocess.run(base + ['--program', str(source / 'source.py'), '--runtime', 'torch', '--out', str(reference)],
                           check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
            ref = json.loads(reference.read_text())
            assert ref['status'] == 'completed', ref
            for name, code in variants.items():
                folder = args.out / task / str(seed) / name
                folder.mkdir(parents=True)
                program = folder / 'candidate.py'
                program.write_text(code.replace("MODEL_VARIANT = 'transformer'", f'MODEL_VARIANT = {variant!r}'))
                output = folder / 'measurement.json'
                process = subprocess.run(base + ['--program', str(program), '--runtime', 'mindspore', '--out', str(output)],
                                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=120)
                (folder / 'process.log').write_text(process.stdout)
                measured = json.loads(output.read_text())
                result = compare(ref, measured)
                rows.append({'task': task, 'seed': seed, 'control': name, 'accepted': result['accepted'],
                             'expected': name == 'healthy', 'status': measured['status'],
                             'backend': measured.get('backend'),
                             'failed_checks': [k for k, v in result['checks'].items() if not v],
                             'error': measured.get('error'), 'measurement_sha256': hashlib.sha256(output.read_bytes()).hexdigest()})
                print(json.dumps(rows[-1]), flush=True)
    result = {'real_model_calls': 0, 'controls': len(rows),
              'passed': all(row['accepted'] == row['expected'] and row['status'] == 'completed' for row in rows), 'rows': rows}
    (args.out / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
