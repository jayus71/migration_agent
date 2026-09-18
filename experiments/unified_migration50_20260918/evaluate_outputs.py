"""Apply the same acceptance contract to the three non-agent migration methods."""

import argparse
import json
from pathlib import Path
import shutil
import sys

from experiments.unified_migration50_20260918.evaluator import UnifiedEvaluator
from experiments.unified_migration50_20260918.integration import require_approval
from experiments.unified_migration50_20260918.native_imports import convert
from experiments.unified_migration50_20260918.msadapter_smoke import ADAPTER, NUMPY
from experiments.unified_migration50_20260918.prepare_review import sha


def evaluate_output(review, bundle, references, generations, group_id, method):
    manifest = require_approval(review)
    group = next(row for row in manifest['translation_reuse'] if row['group'] == group_id)
    task = group['tasks'][0]
    row = next(row for row in manifest['tasks'] if row['task'] == task)
    output = review / 'nonagent_conditions' / group_id / method
    if (output / 'result.json').exists():
        return json.loads((output / 'result.json').read_text())
    if output.exists():
        raise RuntimeError('Incomplete prior evaluation requires inspection: ' + str(output))
    workspace = output / 'workspace'
    public = bundle / 'public' / task
    if sha(public / 'source.py') != group['source_sha256'] or sha(public / 'task.json') != group['contract_sha256']:
        raise ValueError('Public input changed')
    shutil.copytree(public, workspace)
    (workspace / 'scratch_tests').mkdir()
    usage, generation_path = None, None
    if method == 'msadapter':
        (workspace / 'candidate.py').write_text(convert((workspace / 'source.py').read_text()))
        usage = {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
    else:
        generation_path = generations / group_id / method
        generation = json.loads((generation_path / 'generation.json').read_text())
        usage = generation.get('usage')
        if generation['status'] != 'generated':
            result = {'method': method, 'group': group_id, 'tasks': group['tasks'], 'accepted': False,
                      'status': 'generation_failed', 'usage': usage, 'generation': str(generation_path), 'measurements': None}
            (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
            return result
        if sha(generation_path / 'candidate.py') != generation['candidate_sha256']:
            raise ValueError('Generated candidate changed')
        shutil.copy2(generation_path / 'candidate.py', workspace / 'candidate.py')
    evaluator = UnifiedEvaluator(workspace, output / 'evidence', Path(sys.executable), kind=row['input_form'],
        runtime='msadapter' if method == 'msadapter' else 'mindspore',
        references=references / group_id / 'torch',
        extra_reads=[str(ADAPTER), str(NUMPY)] if method == 'msadapter' else (),
        module_paths=[str(NUMPY), str(ADAPTER)] if method == 'msadapter' else ())
    checks = [evaluator.paired()] + evaluator.confirm()
    result = {'method': method, 'group': group_id, 'tasks': group['tasks'], 'accepted': all(r['accepted'] for r in checks),
              'status': 'completed', 'checks': checks, 'usage': usage, 'generation': str(generation_path) if generation_path else None,
              'candidate_sha256': sha(workspace / 'candidate.py')}
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('review', 'bundle', 'references', 'generations'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--group', required=True)
    parser.add_argument('--method', choices=['direct', 'cte', 'msadapter'], required=True)
    args = parser.parse_args()
    print(json.dumps(evaluate_output(args.review, args.bundle, args.references, args.generations, args.group, args.method)))
