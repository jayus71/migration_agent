"""Public observations from isolated measurements and private source traces."""

import hashlib
import json
from pathlib import Path

from autofix.autonomous.evaluation import Evaluator, dump, source_hashes
from autofix.autonomous.sandbox import run_isolated

from experiments.unified_migration50_20260918.score import compare


class UnifiedEvaluator(Evaluator):
    def __init__(self, workspace, evidence, python, *, kind, runtime, references,
                 extra_reads=(), module_paths=()):
        super().__init__(workspace, evidence, python)
        self.kind = kind
        self.runtime = runtime
        self.references = Path(references).resolve()
        self.extra_reads = list(extra_reads)
        self.module_paths = list(module_paths)
        self.measure = Path(__file__).with_name('measure.py').resolve()

    def paired(self, *, seed=None, timeout=180):
        seed = self.params['seed'] if seed is None else seed
        self.calls += 1
        folder = self.evidence / f'measurement_{self.calls:04d}'
        folder.mkdir(parents=True)
        target = folder / 'measurement.json'
        reference_path = self.references / str(seed) / 'measurement.json'
        reference = json.loads(reference_path.read_text())
        if reference['status'] != 'completed':
            raise RuntimeError('Trusted source measurement is unavailable')
        args = ['--program', str(self.workspace / 'candidate.py'),
                '--contract', str(self.workspace / 'task.json'), '--kind', self.kind,
                '--runtime', self.runtime, '--seed', str(seed), '--out', str(target)]
        launcher = folder / 'launcher.py'
        launcher.write_text(
            'import runpy, sys\n'
            f'sys.path[:0] = {self.module_paths!r}\n'
            f'sys.argv = {[str(self.measure)] + args!r}\n'
            f'runpy.run_path({str(self.measure)!r}, run_name="__main__")\n')
        process = run_isolated(self.workspace, self.python, launcher, timeout=timeout,
            extra_reads=[str(self.measure)] + self.extra_reads, extra_writes=[str(folder)])
        dump(folder / 'process.json', process)
        measured = json.loads(target.read_text()) if target.exists() else {
            'status': 'execution_failed', 'seed': seed, 'values': None,
            'schema': None, 'backend': {'observed': False},
            'error': process['stdout'][-16000:]}
        if process['returncode'] != 0:
            measured['status'] = 'execution_failed'
        verdict = compare(reference, measured)
        immutable = source_hashes(self.workspace) == self.immutable
        verdict['checks']['source_immutable'] = immutable
        verdict['accepted'] = verdict['accepted'] is True and immutable
        error = measured.get('error')
        if error:
            error = error.replace(str(self.workspace), '.').replace(str(folder), 'verification')[-16000:]
        # The reference arrays and private evaluator paths never enter the observation.
        observation = {'execution': measured['status'], 'error': error,
            'measurements': [{'name': name, 'max_abs_difference': delta,
                              'passed': verdict['checks'][name]}
                             for name, delta in verdict.get('differences', {}).items()],
            'unavailable': verdict.get('unavailable', []),
            'target_backend_observed': measured.get('backend', {}).get('observed') is True,
            'source_immutable': immutable, 'acceptance': verdict}
        self.last_result = {'observation': observation, 'accepted': verdict['accepted'],
                            'measurement': str(folder), 'seed': seed,
                            'reference_sha256': hashlib.sha256(reference_path.read_bytes()).hexdigest()}
        dump(folder / 'observation.json', self.last_result)
        return self.last_result

    def confirm(self):
        return [self.paired(seed=seed) for seed in self.params['evaluation']['final_seeds']
                if seed != self.params['seed']]
