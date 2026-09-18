"""Native adapter identity and isolated forward/backward smoke, with no model."""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from experiments.unified_migration50_20260918.evaluator import UnifiedEvaluator
from experiments.unified_migration50_20260918.native_imports import convert


ROOT = Path('/media/main/whj/projects/torch4ms')
ADAPTER = ROOT / 'third_party/MSAdapter-native-e-20260918'
NUMPY = ROOT / 'e-baselines-current-20260918/deps/numpy126'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    package, out = args.package.resolve(), args.out.resolve()
    assert not out.exists()
    commit = subprocess.check_output(['git', '-C', str(ADAPTER), 'rev-parse', 'HEAD'], text=True).strip()
    assert commit == '0a6d11d6d00243141e2bdd01f086782b37b49a21'
    assert not subprocess.check_output(['git', '-C', str(ADAPTER), 'diff', 'HEAD', '--'])
    manifest = json.loads((package / 'bundle/manifest.json').read_text())
    task = next(row['task'] for row in manifest['tasks'] if row['source_retained']
                and 'def workload(value)' in (package / 'bundle/public' / row['task'] / 'source.py').read_text())
    group = next(f'group_{index:03d}' for index, row in enumerate(manifest['shared_translation_groups'], 1)
                 if task in row['tasks'])
    workspace = out / 'workspace'
    shutil.copytree(package / 'bundle/public' / task, workspace)
    (workspace / 'scratch_tests').mkdir()
    (workspace / 'candidate.py').write_text(convert((workspace / 'source.py').read_text()))
    evaluator = UnifiedEvaluator(workspace, out / 'evidence', Path(sys.executable), kind='native',
        runtime='msadapter', references=package / 'reference_strict' / group / 'torch',
        extra_reads=[str(ADAPTER), str(NUMPY)], module_paths=[str(NUMPY), str(ADAPTER)])
    result = evaluator.paired()
    report = {'real_model_calls': 0, 'adapter_commit': commit, 'upstream_tracked_diff_empty': True,
              'task': task, 'accepted': result['accepted'], 'observation': result['observation']}
    (out / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
