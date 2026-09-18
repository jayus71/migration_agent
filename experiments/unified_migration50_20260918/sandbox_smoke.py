"""Exercise the same evaluator boundary used by agent tools, without inference."""

import argparse
import json
from pathlib import Path
import shutil
import sys

from experiments.unified_migration50_20260918.evaluator import UnifiedEvaluator


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.package = args.package.resolve()
    args.out = args.out.resolve()
    if args.out.exists():
        raise FileExistsError(args.out)
    rows = []
    for task, group in [('task_035', 'group_019'), ('task_037', 'group_021')]:
        for control in ('healthy', 'update'):
            workspace = args.out / task / control / 'workspace'
            shutil.copytree(args.package / 'bundle/public' / task, workspace)
            (workspace / 'scratch_tests').mkdir()
            source = args.package / 'native_calibration_strict' / task / '101' / control / 'candidate.py'
            shutil.copy2(source, workspace / 'candidate.py')
            evaluator = UnifiedEvaluator(workspace, workspace.parent / 'evidence', Path(sys.executable),
                kind='training', runtime='mindspore', references=args.package / 'reference_strict' / group / 'torch')
            first = evaluator.paired()
            checks = [first] + evaluator.confirm()
            expected = control == 'healthy'
            assert all(row['accepted'] == expected for row in checks), checks
            private = args.package / 'native_control.py'
            probe = workspace / 'scratch_tests' / 'private_read.py'
            probe.write_text('from pathlib import Path\n'
                             f'path = Path({str(private)!r})\n'
                             'try:\n    path.read_bytes()\n'
                             'except PermissionError:\n    print("PRIVATE_READ_DENIED")\n'
                             'else:\n    raise AssertionError("Private calibration target was readable")\n')
            isolation = evaluator.tool({'test': 'scratch_tests/private_read.py'})
            assert isolation['returncode'] == 0 and 'PRIVATE_READ_DENIED' in isolation['stdout'], isolation
            rows.append({'task': task, 'control': control, 'seeds': [r['seed'] for r in checks],
                         'accepted': [r['accepted'] for r in checks], 'private_read_denied': True})
            print(json.dumps(rows[-1]), flush=True)
    (args.out / 'summary.json').write_text(json.dumps({'passed': True, 'real_model_calls': 0,
                                                      'rows': rows}, indent=2) + '\n')


if __name__ == '__main__':
    main()
