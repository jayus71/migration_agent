"""Resume only declared conditions; missing approval prevents any formal action."""

import argparse
import fcntl
import json
from pathlib import Path
import subprocess
import sys

from experiments.unified_migration50_20260918.integration import require_approval, run_repair
from experiments.unified_migration50_20260918.materialize import assemble
from experiments.unified_migration50_20260918.evaluate_outputs import evaluate_output


def execute(review, generations):
    manifest = require_approval(review)
    lock = (review / 'dispatch.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        if manifest.get('benchmark') == 'unified_cross_language':
            from experiments.unified_migration50_20260918.ordinary_repair import run
            for row in manifest['tasks']:
                for method in ('autonomous_layered', 'swe_native_isolated', 'matchfix_full_orchestration', 'ordinary_test_repair'):
                    output = review / 'conditions' / row['anonymous_id'] / method
                    if (output / 'result.json').exists():
                        continue
                    if output.exists():
                        raise RuntimeError('Inspect interrupted condition before resuming: ' + str(output))
                    result = run(review, row['anonymous_id']) if method == 'ordinary_test_repair' else run_repair(
                        review, row['anonymous_id'], method, Path(sys.executable))
                    if result['status'] == 'infrastructure_error':
                        raise RuntimeError('Infrastructure interruption; no automatic restart')
            return
        if generations is None:
            raise ValueError('--generations is required for the main collection and its analyses')
        bundle, references = Path(manifest['source_bundle']), Path(manifest['reference_directory'])
        for group in manifest['translation_reuse']:
            required = []
            if any(m['mode'].startswith('shared_initial') for m in manifest['methods'].values()):
                required.append('direct')
            if 'cte' in manifest['methods']:
                required.append('cte')
            for method in required:
                generation = generations / group['group'] / method
                if (generation / 'generation.json').exists():
                    continue
                if method not in manifest['methods']:
                    raise RuntimeError('Analysis reuses the completed main initial translation')
                subprocess.run([sys.executable, '-m', 'experiments.unified_migration50_20260918.translation',
                    '--review', str(review), '--bundle', str(bundle), '--group', group['group'],
                    '--method', method, '--out', str(generation)], check=True)
            assemble(review, bundle, references, generations)
            for method, settings in manifest['methods'].items():
                if 'adapter' not in settings:
                    evaluate_output(review, bundle, references, generations, group['group'], method)
                    continue
                task, adapter = group['tasks'][0], settings['adapter']
                output = review / 'conditions' / task / adapter
                if (output / 'result.json').exists():
                    continue
                if output.exists():
                    raise RuntimeError('Inspect interrupted condition before resuming: ' + str(output))
                initial = json.loads((generations / group['group'] / 'direct/generation.json').read_text())
                if initial['status'] != 'generated':
                    output.mkdir(parents=True)
                    (output / 'result.json').write_text(json.dumps({'task': task, 'method': adapter,
                        'status': 'initial_generation_failed', 'accepted': False, 'budget': {'calls': 0, 'usage': None}}, indent=2))
                    continue
                result = run_repair(review, task, adapter, Path(sys.executable),
                                    variant=manifest.get('variant'), plugin=manifest.get('plugin', False))
                if result['status'] == 'infrastructure_error':
                    raise RuntimeError('Infrastructure interruption; no automatic restart')
    finally:
        lock.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--review', type=Path, required=True)
    parser.add_argument('--generations', type=Path)
    args = parser.parse_args()
    execute(args.review.resolve(), args.generations.resolve() if args.generations else None)
