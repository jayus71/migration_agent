"""Single-task integration of the existing ordinary-test whole-file repair control."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys

from experiments.unified_migration50_20260918.extensions import N18, IMAGE
from experiments.unified_migration50_20260918.integration import require_approval


def native_module():
    sys.path[:0] = [str(N18), str(N18 / 'pairing')]
    spec = importlib.util.spec_from_file_location('ordinary_native_n18', N18 / 'run.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(review, task_id):
    manifest = require_approval(review)
    row = next(row for row in manifest['tasks'] if row['anonymous_id'] == task_id)
    module = native_module()
    item = next(item for item in json.loads((N18 / 'sources/manifest.json').read_text())['sources']
                if item['task_id'] == row['original_id'])
    public = review / 'private_inputs' / task_id
    contract = json.loads((public / 'task.json').read_text())
    prompt = (module.translation_prompt(item, module.source_text(item)) + '\n\nCOMMON INTERFACE:\n'
              + contract['interface'] + '\nPUBLIC METADATA:\n' + json.dumps(contract['public_context']))
    case = review / 'conditions' / task_id / 'ordinary_test_repair'
    if case.exists():
        raise FileExistsError('Preserve all completed or interrupted conditions')
    case.mkdir(parents=True)
    candidate = public / 'candidate.py'
    attempts, failure = [], None
    os.environ['AUTOFIX_CANDIDATE_IMAGE'] = IMAGE
    os.environ['AUTOFIX_LLM_MODEL'] = 'deepseek-v4-flash'
    os.environ['AUTOFIX_LLM_MAX_TOKENS'] = '131072'
    for round_id in range(5):
        checkpoint = case / f'checkpoint_{round_id}'
        report = module.evaluate(candidate, Path(row['reference_root']), checkpoint / 'visible', row['original_id'], 101)
        held = []
        if round_id in (0, 1, 2, 4) or report['passed']:
            held = [module.evaluate(candidate, Path(row['reference_root']), checkpoint / f'held_{seed}',
                                    row['original_id'], seed) for seed in (202, 303)]
        attempts.append({'round': round_id, 'visible_passed': report['passed'],
                         'held_out_passed': all(r['passed'] for r in held) if held else None,
                         'candidate_sha256': module.digest(candidate)})
        module.save(case / 'checkpoints.json', attempts)
        if report['passed'] or round_id == 4:
            break
        feedback = {key: report[key] for key in ('passed', 'error') if key in report}
        if 'steps' in report:
            feedback['failed_tests'] = [{'step': index, 'checks': {key: [r for r in step[key] if not r['passed']]
                for key in ('forward', 'backward', 'optimizer')}} for index, step in enumerate(report['steps'])]
        request = (prompt + '\nRepair the complete candidate using these visible test failures. Return the complete file.\n'
                   + json.dumps(feedback) + '\nCURRENT CANDIDATE:\n' + candidate.read_text())
        destination = case / f'repair_{round_id + 1}'
        generation = module.call([{'role': 'user', 'content': request}], destination)
        if generation['status'] != 'generated':
            failure = generation
            break
        candidate = destination / 'candidate.py'
    result = {'task': row['original_id'], 'method': 'ordinary_test_repair', 'checkpoints': attempts,
              'status': 'generation_error' if failure else 'evaluated', 'generation_failure': failure,
              'accepted': False if failure else bool(attempts[-1]['visible_passed'] and attempts[-1]['held_out_passed']),
              'native_result_passed': None if failure else bool(attempts[-1]['visible_passed'] and attempts[-1]['held_out_passed'])}
    module.save(case / 'result.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--review', type=Path, required=True)
    parser.add_argument('--task', required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.review, args.task)))
