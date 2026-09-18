"""Read-only verification of the complete review package; no inference imports."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--review', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    review = args.review.resolve()
    manifest = read(review / 'manifest.json')
    index = read(review / 'review_index.json')
    assert sha(review / 'manifest.json') == index['main_manifest_sha256']
    assert sha(review / 'cross_language/manifest.json') == index['cross_language_manifest_sha256']
    manifests = [review / 'manifest.json', review / 'cross_language/manifest.json']
    manifests += list((review / 'analyses').glob('*/manifest.json'))
    files = {}
    for path in manifests:
        value = read(path)
        assert value['formal_execution_authorized'] is False
        assert not (path.parent / 'review_approval.json').exists()
        assert not (path.parent / 'conditions').exists()
        if path.parent.parent.name == 'analyses':
            assert sha(path) == index['analysis_manifests'][path.parent.name]
        for filename, expected in value['frozen_files'].items():
            if filename in files:
                assert files[filename] == expected
            files[filename] = expected
    for filename, expected in files.items():
        assert sha(Path(filename)) == expected, filename
    bundle = Path(manifest['source_bundle'])
    assert sha(bundle / 'manifest.json') == manifest['source_manifest_sha256']
    assert len(manifest['tasks']) == 50
    assert len(manifest['translation_reuse']) == 29
    for group in manifest['translation_reuse']:
        task = group['tasks'][0]
        public = bundle / 'public' / task
        request_file = review / 'requests' / group['group'] / 'direct.json'
        assert sha(request_file) == group['request_sha256']
        request = read(request_file)
        expected = json.dumps(read(public / 'task.json'), ensure_ascii=False) + '\n\nsource.py:\n' + (public / 'source.py').read_text()
        assert request['messages'][1] == {'role': 'user', 'content': expected}
        assert request['model'] == 'deepseek-v4-flash'
        for alias in group['tasks']:
            assert sha(bundle / 'public' / alias / 'source.py') == group['source_sha256']
            assert sha(bundle / 'public' / alias / 'task.json') == group['contract_sha256']
    matrix = read(review / 'matrix.json')
    assert len(matrix) == len({(r['task'], r['method']) for r in matrix}) == 300
    assert set(Counter(r['method'] for r in matrix).values()) == {50}
    analyses = read(review / 'analysis_matrix.json')
    assert len(analyses) == 145
    assert set(Counter(r['analysis'] for r in analyses).values()) == {29}
    extension = read(review / 'cross_language/manifest.json')
    assert len(extension['tasks']) == 18
    for row in extension['tasks']:
        public = review / 'cross_language/private_inputs' / row['anonymous_id']
        for filename, key in [('source.py', 'source_sha256'), ('candidate.py', 'candidate_sha256'), ('task.json', 'contract_sha256')]:
            assert sha(public / filename) == row[key]
    package = Path(__file__).resolve().parent
    # The runner must reject this unapproved package before constructing any client.
    result = subprocess.run([sys.executable, '-m', 'experiments.unified_migration50_20260918.run_plan',
        '--review', str(review)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    assert result.returncode != 0 and 'requires the user review receipt' in result.stdout, result.stdout
    report = {'passed': True, 'real_model_calls': 0, 'frozen_files_checked': len(files),
              'review_manifests': len(manifests), 'public_requests': 29,
              'main_display_cells': 300, 'unique_main_conditions': 174, 'analysis_conditions': 145,
              'cross_language_display_cells': 108, 'cross_language_reused': 36,
              'cross_language_missing': 72, 'approval_guard_rejected_launch': True,
              'main_manifest_sha256': sha(review / 'manifest.json')}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
