"""Prepare current cross-language episodes and preserve completed translation calls."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from autofix.autonomous.evaluation import Evaluator, dump, source_hashes
from experiments.unified_migration50_20260918.prepare_review import REPAIR


BASE = Path('/media/main/whj/projects/torch4ms')
REPO = BASE / 'ascend-torch4ms-intertrans-completion-20260918'
N18 = REPO / 'experiments/experiment_request_20260820/14_experiment_N_real_cross_language/n18'
INDEX = BASE / 'ascend-torch4ms-n18-348e8cd/artifacts/evidence_index.json'
INITIAL = BASE / 'ascend-torch4ms-n18-remediation-3eb9150/artifacts/n18_prepared_20260917'
ASSETS = BASE / 'intertrans-completion-20260918/intertrans_visible_assets/public'
IMAGE = 'sha256:b5b52bdfd12169868b09c3cb0f499a68bffb8ba53d124183d6e9362bbd99453e'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CrossLanguageEvaluator(Evaluator):
    def __init__(self, workspace, evidence, python, *, task, reference):
        super().__init__(workspace, evidence, python)
        self.task, self.reference = task, Path(reference)

    def paired(self, *, seed=None, timeout=240):
        seed = self.params['seed'] if seed is None else seed
        self.calls += 1
        output = self.evidence / f'measurement_{self.calls:04d}'
        output.mkdir(parents=True)
        command = [str(self.python), str(Path(__file__).with_name('extension_worker.py')),
                   '--repo', str(REPO), '--pairing', str(N18 / 'pairing'),
                   '--candidate', str(self.workspace / 'candidate.py'),
                   '--reference', str(self.reference), '--task', self.task,
                   '--seed', str(seed), '--output', str(output)]
        env = {key: value for key, value in os.environ.items()
               if not any(part in key.upper() for part in ('API_KEY', 'TOKEN', 'SECRET', 'PASSWORD', 'CREDENTIAL'))}
        env.update(PYTHONPATH=str(REPO), OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
                   AUTOFIX_CANDIDATE_IMAGE=IMAGE)
        try:
            proc = subprocess.run(command, env=env, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, timeout=timeout + 30)
            (output / 'process.log').write_text(proc.stdout)
            file = output / 'wrapper_result.json'
            report = json.loads(file.read_text()) if file.exists() else {
                'passed': False, 'error': proc.stdout[-16000:], 'stage': 'execution_failed', 'steps': []}
        except subprocess.TimeoutExpired:
            report = {'passed': False, 'error': 'Evaluation timeout', 'stage': 'execution_failed', 'steps': []}
        immutable = source_hashes(self.workspace) == self.immutable
        accepted = report.get('passed') is True and immutable
        observation = {'execution': report.get('stage'), 'steps': report.get('steps', []),
                       'error': report.get('error'), 'source_immutable': immutable,
                       'acceptance': {'accepted': accepted}, 'scope': self.params['evaluation']['scope']}
        self.last_result = {'observation': observation, 'accepted': accepted, 'seed': seed, 'measurement': str(output)}
        dump(output / 'observation.json', self.last_result)
        return self.last_result

    def confirm(self):
        return [self.paired(seed=seed) for seed in (202, 303)]


def prepare(output):
    if output.exists():
        raise FileExistsError(output)
    sys.path.insert(0, str(N18))
    from source_prompt import source_text
    sources = json.loads((N18 / 'sources/manifest.json').read_text())['sources']
    index = json.loads(INDEX.read_text())['tasks']
    freeze = json.loads((INITIAL / 'freeze.json').read_text())
    rows, cells = [], []
    for number, item in enumerate(sources, 1):
        task, public_id = item['task_id'], f'task_{number:03d}'
        assert item['sha256'] == freeze['sources'][task]
        initial = INITIAL / 'direct_llm' / task / 'initial'
        generation = json.loads((initial / 'generation.json').read_text())
        assert generation['status'] == 'generated'
        assert sha(initial / 'candidate.py') == generation['candidate_sha256']
        destination = output / 'private_inputs' / public_id
        destination.mkdir(parents=True)
        (destination / 'source.py').write_text(source_text(item))
        shutil.copy2(initial / 'candidate.py', destination / 'candidate.py')
        fixture = json.loads((ASSETS / task / 'fixture.json').read_text())
        dump(destination / 'task.json', {'source_language': 'java', 'target_language': 'python',
            'source_framework': 'Java/DJL', 'target_framework': 'Python/PyTorch', 'seed': 101,
            'source_reference': 'source.py contains the complete original Java source or all notebook cells as UTF-8 reference text.',
            'interface': (N18 / 'training_interface.txt').read_text(),
            'public_context': fixture['context'],
            'evaluation': {'final_seeds': [101, 202, 303],
                'scope': 'Two consecutive post-preprocessing training steps: outputs, loss, gradients, parameter updates and observed optimizer states.'},
            'editable': ['candidate.py'], 'tests': ['public']})
        rows.append({'anonymous_id': public_id, 'original_id': task,
                     'source_sha256': sha(destination / 'source.py'),
                     'upstream_source_sha256': item['sha256'], 'candidate_sha256': sha(destination / 'candidate.py'),
                     'contract_sha256': sha(destination / 'task.json'), 'reference_root': index[task]['reference_root']})
        for method in ('ladim', 'direct', 'swe', 'matchfix', 'test_repair', 'intertrans'):
            cells.append({'task': task, 'method': method,
                          'action': 'reuse_existing' if method in ('direct', 'intertrans') else 'awaiting_review'})
    assert len(rows) == 18 and len(cells) == 108
    manifest = {**REPAIR, 'benchmark': 'unified_cross_language', 'tasks': rows,
        'formal_execution_authorized': False, 'real_model_calls': 0, 'runtime': 'torch',
        'task_kind': 'framework_migration', 'source_framework': 'Java/DJL', 'target_framework': 'Python/PyTorch',
        'memory_policy': {'autonomous_layered': 'evidence'},
        'workflow_policy': {'autonomous_layered': 'progress_loop'},
        'index_sha256': sha(INDEX), 'interface_sha256': sha(N18 / 'training_interface.txt'),
        'reused_conditions': 36, 'new_protocol_conditions': 72,
        'generation_reuse': 'All 18 completed Direct candidate bytes and original generation costs retained.'}
    manifest['candidate_image'] = IMAGE
    dump(output / 'manifest.json', manifest)
    dump(output / 'matrix.json', cells)
    return {'prepared_tasks': 18, 'reused': 36, 'pending_review': 72, 'real_model_calls': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args().out)))
