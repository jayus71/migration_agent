"""Audit completed offline evidence, native baseline identities and frozen assets."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

from experiments.unified_migration50_20260918.score import compare


BASE = Path('/media/main/whj/projects/torch4ms')


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    package = args.package.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    bundle = read(package / 'bundle/manifest.json')
    source = read(package / 'source_preflight.json')
    assert source['checks'] == source['passed'] == 150
    checks = []
    for i, group in enumerate(bundle['shared_translation_groups'], 1):
        ident = f'group_{i:03d}'
        calibration = 'family_calibration_serialization' if i <= 4 else 'family_calibration_backend'
        for seed in (101, 202, 303):
            reference = package / 'reference_complete' / ident / 'torch' / str(seed) / 'measurement.json'
            candidate = package / calibration / ident / str(seed) / 'measurement.json'
            verdict = compare(read(reference), read(candidate))
            assert verdict['accepted'], (ident, seed, verdict)
            checks.append({'group': ident, 'seed': seed, 'accepted': True,
                           'reference_sha256': sha(reference), 'calibration_sha256': sha(candidate)})
    controls = read(package / 'native_calibration_complete/summary.json')
    assert controls['passed'] and controls['controls'] == 24
    for name in ('isolated_smoke_absolute', 'cross_language_smoke', 'cross_language_native_hosts', 'cte_clean_runtime_verified'):
        assert read(package / name / 'summary.json')['passed'], name
    assert read(package / 'cte_clean_runtime_verified/summary.json')['native_public_tests_passed']
    for name in ('controller_smoke_complete', 'plugin_controller_smoke'):
        summary = read(package / name / 'summary.json')
        assert all(r['accepted'] and r['status'] == 'completed' and r['real_model_calls'] == 0 for r in summary['rows'])
    tests = ET.parse(package / 'final_integration_tests.xml').getroot()
    suites = list(tests.iter('testsuite'))
    assert sum(int(s.attrib.get('failures', 0)) + int(s.attrib.get('errors', 0)) for s in suites) == 0
    baselines = {}
    for name, root, expected in (
        ('matchfix', BASE / 'external_baselines/MatchFixAgent-66a52a5', '66a52a5'),
        ('msadapter', BASE / 'third_party/MSAdapter-native-e-20260918', '0a6d11d'),
        ('cte', BASE / 'third_party/CodeTransEngine-native-unified50-20260918', 'e97e4ff')):
        commit = git(root, 'rev-parse', 'HEAD')
        assert commit.startswith(expected)
        assert not git(root, 'diff', 'HEAD', '--'), name
        baselines[name] = {'root': str(root), 'commit': commit, 'tracked_diff_empty': True}
    swe = BASE / 'external_baselines/SWE-agent-v1.1.0'
    native = read(package / 'controller_smoke_complete/swe_native_isolated/conditions/task_035/swe_native_isolated/evidence/agent/baseline_manifest.json')
    baselines['swe'] = {'commit': git(swe, 'rev-parse', 'HEAD'), 'installed_changes_ignored': True,
                        'archive_manifest': native, 'source': 'git archive of fixed upstream commit'}
    old_cte = BASE / 'third_party/CodeTransEngine-exp-e'
    (args.out / 'historical_cte_patch.diff').write_text(git(old_cte, 'diff', '--', 'algo/algo.go') + '\n')
    (args.out / 'integration_changes.diff').write_text(git(package.parents[1], 'diff', '--',
                                                        'autofix/autonomous/baselines.py', 'autofix/autonomous/swe_upstream.py') + '\n')
    report = {'passed': True, 'real_model_calls': 0, 'source_preflight': {'passed': 150, 'total': 150},
              'target_calibration': {'passed': len(checks), 'total': len(checks), 'rows': checks},
              'independent_mutation_controls': {'passed': 24, 'total': 24},
              'native_controller_methods': 3, 'plugin_native_hosts': 2,
              'unit_and_integration_tests': sum(int(s.attrib.get('tests', 0)) for s in suites),
              'skipped_tests': sum(int(s.attrib.get('skipped', 0)) for s in suites),
              'baselines': baselines, 'cte_binary_sha256': sha(package / 'cte-native'),
              'cte_runtime_image': subprocess.check_output(['docker', 'image', 'inspect', 'unified50/cte-python:20260918',
                                                           '--format', '{{.Id}}'], text=True).strip(),
              'historical_results': 'preserved under actual protocols; no result reranking or inference replay',
              'formal_execution_authorized': False}
    import importlib.metadata
    report['python_packages'] = {name: importlib.metadata.version(name) for name in ('torch', 'mindspore', 'numpy', 'pytest', 'protobuf')}
    (args.out / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('baselines', 'target_calibration')}, indent=2))


if __name__ == '__main__':
    main()
