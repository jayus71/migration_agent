"""Replay saved cross-language candidates through the newly connected evaluator."""

import argparse
import json
from pathlib import Path
import shutil
import sys
from unittest.mock import patch

from experiments.unified_migration50_20260918 import integration
from experiments.unified_migration50_20260918.extensions import CrossLanguageEvaluator
from experiments.unified_migration50_20260918.test_preparation import response


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--review', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--hosts', action='store_true')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((args.review / 'manifest.json').read_text())
    records = []
    # A completed passing translation and a completed failing one cover both routes.
    cases = [] if args.hosts else [('d2l_linear_regression_scratch', True), ('d2l_lenet', False)]
    for task, expected in cases:
        row = next(row for row in manifest['tasks'] if row['original_id'] == task)
        workspace = args.out / task / 'workspace'
        shutil.copytree(args.review / 'private_inputs' / row['anonymous_id'], workspace)
        (workspace / 'scratch_tests').mkdir()
        evaluator = CrossLanguageEvaluator(workspace, workspace.parent / 'evidence', Path(sys.executable),
                                          task=task, reference=row['reference_root'])
        checks = [evaluator.paired()] + evaluator.confirm()
        record = {'task': task, 'accepted': [r['accepted'] for r in checks],
                  'expected': expected, 'real_model_calls': 0}
        records.append(record)
        (args.out / 'summary.json').write_text(json.dumps({'rows': records, 'real_model_calls': 0}, indent=2))
        print(json.dumps(record), flush=True)
        assert all(r['accepted'] == expected for r in checks), checks
    passing = next(row for row in manifest['tasks'] if row['original_id'] == 'd2l_linear_regression_scratch')
    methods = ('swe_native_isolated', 'matchfix_full_orchestration') if args.hosts else ('autonomous_layered',)
    for method in methods:
        run = args.out / method
        shutil.copytree(args.review / 'private_inputs' / passing['anonymous_id'], run / 'private_inputs' / passing['anonymous_id'])
        limited = dict(manifest, tasks=[passing], max_repair_attempts=1)
        (run / 'manifest.json').write_text(json.dumps(limited))
        requests = []
        def scripted(request, timeout):
            requests.append(request)
            if method == 'swe_native_isolated':
                return response('Offline cross-language integration', [{'id': 'offline_' + str(len(requests)),
                    'type': 'function', 'function': {'name': 'submit', 'arguments': '{}'}}])
            if method == 'matchfix_full_orchestration':
                return response('<final_response_format>{"is_equivalent":"yes","explanation":"Offline fixture"}</final_response_format>')
            return response('{"diagnosis":{"observations":["public test passed"]},"summary":"completed"}')
        with patch.object(integration, 'require_approval', lambda path: limited), \
             patch('autofix.autonomous.agent.OpenAICompatibleClient', lambda: scripted):
            result = integration.run_repair(run, passing['anonymous_id'], method, Path(sys.executable))
        assert result['accepted'] and result['status'] == 'completed', result
        if method == 'autonomous_layered':
            assert 'Python/PyTorch for' in requests[0]['messages'][0]['content']
        print(json.dumps({'method': method, 'accepted': result['accepted'], 'scripted_calls': len(requests), 'real_model_calls': 0}), flush=True)
    report = {'passed': True, 'rows': records, 'controller_accepted': True, 'methods': list(methods), 'real_model_calls': 0}
    (args.out / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
