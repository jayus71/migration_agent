"""Create one review package from frozen inputs and completed offline evidence."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

from experiments.unified_migration50_20260918.extensions import prepare, INDEX, N18
from experiments.unified_migration50_20260918.prepare_review import dump, sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    package, output = args.package.resolve(), args.out.resolve()
    readiness = json.loads((package / 'readiness/summary.json').read_text())
    assert readiness['passed']
    subprocess.run([sys.executable, '-m', 'experiments.unified_migration50_20260918.prepare_review',
        '--bundle', str(package / 'bundle'), '--references', str(package / 'reference_complete'),
        '--out', str(output)], check=True)
    main_manifest = json.loads((output / 'manifest.json').read_text())
    extension = output / 'cross_language'
    prepare(extension)
    manifest = json.loads((extension / 'manifest.json').read_text())
    manifest['frozen_files'] = dict(main_manifest['frozen_files'])
    manifest['native_baselines'] = main_manifest['native_baselines']
    manifest['container_images'] = main_manifest['container_images']
    additional = list((extension / 'private_inputs').rglob('*')) + [INDEX, N18 / 'training_interface.txt', N18 / 'run.py']
    additional += list((N18 / 'pairing').glob('*.py'))
    additional += list((N18.parents[3] / 'autofix/backends').glob('*.py'))
    for file in additional:
        if file.is_file():
            manifest['frozen_files'][str(file)] = sha(file)
    manifest['container_images'][manifest['candidate_image']] = manifest['candidate_image']
    manifest['ordinary_test_repair'] = {'max_repair_calls': 4, 'max_output_tokens_per_call': 131072,
        'temperature': .1, 'native_visible_stop_rule_retained': True,
        'algorithm_source_sha256': sha(N18 / 'run.py')}
    dump(extension / 'manifest.json', manifest)
    dump(extension / 'budgets.json', {'reused_conditions': 36, 'new_shared_initial_calls': 0,
        'new_agent_episodes': 54, 'new_ordinary_test_episodes': 18,
        'maximum_calls': 54 * 40 + 18 * 4,
        'maximum_output_tokens': 54 * 120000 + 18 * 4 * 131072,
        'native_method_limits_retained': True, 'formal_execution_authorized': False})
    dump(output / 'readiness.json', readiness)
    dump(output / 'review_index.json', {
        'formal_execution_authorized': False, 'real_model_calls': 0,
        'main_manifest_sha256': sha(output / 'manifest.json'),
        'cross_language_manifest_sha256': sha(extension / 'manifest.json'),
        'analysis_manifests': {p.parent.name: sha(p) for p in sorted((output / 'analyses').glob('*/manifest.json'))},
        'main_display_cells': 300, 'main_distinct_method_conditions': 174,
        'cross_language_reused': 36, 'cross_language_pending': 72,
        'plugin_pending_optional': 58, 'final_ablation_pending_optional': 87,
        'jax': {'reuse_existing': 12, 'current_method_optional': 6, 'new_runs_prepared': False,
                'decision': 'Retain the actual completed implementation; do not rerun JAX for a version label.'},
        'historical_evidence': {'original_repair50': 150, 'paired_source12': 24,
                                'natural_translations': 'retain completed results',
                                'training_signal_controls': 64, 'full_model_migration': 60}})
    print(json.dumps({'review': str(output), 'main_manifest_sha256': sha(output / 'manifest.json'),
                      'cross_language_manifest_sha256': sha(extension / 'manifest.json'), 'real_model_calls': 0}))


if __name__ == '__main__':
    main()
