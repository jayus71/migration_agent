"""Assemble reviewed input bytes after initial translation, without inference."""

import argparse
import json
from pathlib import Path
import shutil

from experiments.unified_migration50_20260918.prepare_review import sha


def assemble(review, bundle, references, generations):
    manifest = json.loads((review / 'manifest.json').read_text())
    if sha(bundle / 'manifest.json') != manifest['source_manifest_sha256']:
        raise ValueError('Source manifest changed')
    rows = []
    for group in manifest['translation_reuse']:
        generation = generations / group['group'] / 'direct'
        result_path = generation / 'generation.json'
        if not result_path.exists():
            rows.append({'group': group['group'], 'status': 'initial_translation_pending'})
            continue
        result = json.loads(result_path.read_text())
        if result['status'] != 'generated':
            rows.append({'group': group['group'], 'status': 'initial_generation_failed',
                         'action': 'count failed for all dependent methods; no replacement generation'})
            continue
        candidate = generation / 'candidate.py'
        if sha(candidate) != result['candidate_sha256']:
            raise ValueError('Initial candidate changed')
        for task in group['tasks']:
            destination = review / 'private_inputs' / task
            if destination.exists():
                for name, expected in [('source.py', group['source_sha256']),
                                       ('task.json', group['contract_sha256']),
                                       ('candidate.py', result['candidate_sha256'])]:
                    if sha(destination / name) != expected:
                        raise ValueError('An existing input changed: ' + task + '/' + name)
            else:
                shutil.copytree(bundle / 'public' / task, destination)
                shutil.copy2(candidate, destination / 'candidate.py')
            for seed in (101, 202, 303):
                source = references / group['group'] / 'torch' / str(seed) / 'measurement.json'
                target = review / 'private_references' / task / str(seed) / 'measurement.json'
                value = json.loads(source.read_text())
                if value['status'] != 'completed' or value['seed'] != seed:
                    raise ValueError('Reference incomplete')
                if target.exists() and sha(target) != sha(source):
                    raise ValueError('Reference changed')
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        rows.append({'group': group['group'], 'status': 'materialized',
                     'tasks': group['tasks'], 'candidate_sha256': sha(candidate)})
    (review / 'materialization.json').write_text(json.dumps(rows, indent=2) + '\n')
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('review', 'bundle', 'references', 'generations'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(assemble(args.review, args.bundle, args.references, args.generations)))
