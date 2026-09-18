"""Real controller/native hosts with real isolated evaluation and scripted responses."""

import argparse
import json
from pathlib import Path
import shutil
import sys
from unittest.mock import patch

from experiments.unified_migration50_20260918 import integration
from experiments.unified_migration50_20260918.prepare_review import REPAIR
from experiments.unified_migration50_20260918.test_preparation import response


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--plugin', action='store_true')
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    args.out.mkdir(parents=True)
    rows = []
    methods = ('swe_native_isolated', 'matchfix_full_orchestration') if args.plugin else ('autonomous_layered', 'swe_native_isolated', 'matchfix_full_orchestration')
    for method in methods:
        run = args.out / method
        public = run / 'private_inputs/task_035'
        shutil.copytree(args.package / 'bundle/public/task_035', public)
        # A private calibration candidate is used only inside this offline fixture.
        shutil.copy2(args.package / 'native_calibration_complete/task_035/101/healthy/candidate.py', public / 'candidate.py')
        shutil.copytree(args.package / 'reference_complete/group_019/torch', run / 'private_references/task_035')
        manifest = {**REPAIR, 'runtime': 'mindspore', 'tasks': [{'anonymous_id': 'task_035', 'input_form': 'training'}],
                    'max_repair_attempts': 1, 'formal_execution_authorized': False, 'plugin': args.plugin}
        (run / 'manifest.json').write_text(json.dumps(manifest))
        requests = []
        def scripted(request, timeout):
            requests.append(request)
            if args.plugin and len(requests) == 1:
                return response('{"diagnosis":{"observations":["public test passed"]},"summary":"completed"}')
            if method == 'swe_native_isolated':
                name, arguments = ('bash', {'command': 'run_public_test public'}) if len(requests) == 1 + int(args.plugin) else ('submit', {})
                return response('Offline controller integration', [{'id': 'offline_' + str(len(requests)),
                    'type': 'function', 'function': {'name': name, 'arguments': json.dumps(arguments)}}])
            if method == 'matchfix_full_orchestration':
                return response('<final_response_format>{"is_equivalent":"yes","explanation":"Offline fixture"}</final_response_format>')
            return response('{"diagnosis":{"observations":["public test passed"]},"summary":"completed"}')
        with patch.object(integration, 'require_approval', lambda path: manifest), \
             patch('autofix.autonomous.agent.OpenAICompatibleClient', lambda: scripted):
            result = integration.run_repair(run, 'task_035', method, Path(sys.executable), plugin=args.plugin)
        row = {'method': method, 'accepted': result['accepted'], 'status': result['status'],
               'scripted_calls': len(requests), 'real_model_calls': 0, 'plugin': args.plugin, 'error': result.get('error')}
        rows.append(row)
        (args.out / 'summary.json').write_text(json.dumps({'rows': rows, 'real_model_calls': 0}, indent=2))
        print(json.dumps(row), flush=True)
        assert result['accepted'] and result['status'] == 'completed', result
        assert len(requests) == result['budget']['calls']


if __name__ == '__main__':
    main()
