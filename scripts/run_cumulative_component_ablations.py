"""Cumulative LaDiM components on the two frozen repository migrations.

Run from a separate runtime snapshot. No historical candidate or baseline is edited.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
import hashlib
import json
import math
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import time
import traceback

import repository_migration_experiment as main
from autofix.autonomous.agent import AutonomousAgent
from autofix.autonomous.repository import RepositoryAgent, RepositoryTools
from autofix.autonomous.tools import WorkspaceTools, ToolError

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'experiments/cumulative_components_20260922'
ORIGINAL = Path('/media/main/whj/projects/torch4ms/ascend-torch4ms-repository-20260921/experiments/repository_migration_20260921')
CONDITIONS = ('repair', 'investigation', 'handoff', 'repository_context')
main.RUN = RUN
save, read, hashes, digest = main.save, main.read, main.hashes, main.digest


class ContinuousAgent(AutonomousAgent):
    """Retain the same session when the independent handoff is disabled."""
    def repair(self, observation, attempt=1):
        if type(attempt) is not int or attempt < 1:
            raise ValueError('attempt must be a positive integer')
        self.active_role = 'continuous_agent'
        return self._stage('repair', observation, attempt=attempt)


def make_agent(repository, condition, folder, client=None):
    root = main.bind(repository)
    ws = main.make_workspace(root, folder, root / 'translation/target')
    ev = main.evaluator(repository, ws, folder / 'evidence')
    config = main.configuration('ladim')
    common = dict(named_tests=main.named_tests(repository), validate_syntax=True)
    if condition == 'repository_context':
        tools = RepositoryTools(ws, ev.tool, state_path=folder / 'evidence/repository_state.json', **common)
        cls = RepositoryAgent
    else:
        tools = WorkspaceTools(ws, ev.tool, **common)
        cls = AutonomousAgent if condition == 'handoff' else ContinuousAgent
    agent = cls(tools, folder / 'evidence/agent', config=config, client=client)
    if condition == 'repository_context':
        agent.set_generation_state(read(root / 'translation/result.json').get('file_states', {}))
    return ws, ev, agent


def code_hashes():
    return {str(p.relative_to(ROOT)): digest(p) for directory in ('scripts', 'autofix/autonomous')
            for p in sorted((ROOT / directory).glob('*.py'))}


def prepare():
    RUN.mkdir(parents=True, exist_ok=False)
    for repository in main.REPOSITORIES:
        source, target = ORIGINAL / repository, RUN / repository
        target.mkdir()
        for name in ('source', 'translation', 'private_reference' if repository == 'timeseries' else 'references'):
            if name == 'translation':
                (target / name).mkdir()
                shutil.copytree(source / name / 'target', target / name / 'target')
                shutil.copy2(source / name / 'result.json', target / name / 'result.json')
            else:
                shutil.copytree(source / name, target / name)
        for name in ('task.json', 'manifest.json'):
            shutil.copy2(source / name, target / name)
    save(RUN / 'protocol.json', {
        'repositories': main.REPOSITORIES, 'conditions': CONDITIONS, 'replicates': 1,
        'jobs': 8, 'max_parallel_jobs': 3, 'repair_budget': main.BUDGET, 'external_submissions': 4,
        'condition_definition': {
            'repair': 'Same evidence-based repair prompt, shared tools, syntax guards, evidence compression and progress reminders; no separate read-only diagnosis stage or independent handoff.',
            'investigation': 'Add the original six-call read-only verifier investigation; repair continues the same conversation.',
            'handoff': 'Additionally use the original independent verifier evidence handoff into a new repair conversation.',
            'repository_context': 'Additionally use the original repository dependency planning, checkpoints, versioned evidence retrieval and context rebuilding; the complete current method.'},
        'fixed': 'Identical public sources, initial translations, task requirements, evaluation inputs, states, seeds, thresholds, all training signals, backend and lifetime budgets. Existing edit-format behavior and progress reminders held fixed.',
        'schedule': 'Original diagnosis limit of six calls and 64000 output tokens when enabled; repair allocation divides remaining allowance over remaining submissions, with a 16-call first repair cap. No counters reset.',
        'cost': 'All model calls including failures. End-to-end totals additionally attribute one historical common translation to each condition. No new translation calls.',
        'outcomes': 'Complete repository acceptance; declared checks passed (69 and 145); model calls; total tokens; errors and missing measurements. One new run per repository and condition, no best-of selection.',
        'historical_results': 'Not pooled with these new runs. No baseline is rerun or changed.',
        'created': time.time()})
    checks = {}
    def no_model(*args, **kwargs):
        raise AssertionError('offline check attempted an API call')
    for repository in main.REPOSITORIES:
        for condition in CONDITIONS:
            folder = RUN / 'offline' / repository / condition
            ws, ev, agent = make_agent(repository, condition, folder, no_model)
            checks[f'{repository}:{condition}:initial'] = hashes(ws / 'target') == hashes(RUN / repository / 'translation/target')
            for name in ('task.json', read(RUN / repository / 'task.json')['source_entry']):
                try:
                    agent.tools.execute('edit', {'edits': [{'path': name, 'old': '', 'new': 'bad'}]})
                except ToolError:
                    checks[f'{repository}:{condition}:readonly:{name}'] = True
                else:
                    raise AssertionError('Immutable public input is editable')
            if condition != 'repository_context':
                entry = read(RUN / repository / 'task.json')['target_entry']
                try:
                    agent.tools.execute('edit', {'edits': [{'path': entry, 'old': '', 'new': 'bad'}]}, readonly=True)
                except ToolError:
                    checks[f'{repository}:{condition}:diagnosis_readonly'] = True
                else:
                    raise AssertionError('Diagnosis mutated production code')
            before = agent.history
            agent._stage = lambda *args, **kwargs: ('stub', args, kwargs)
            agent.repair({'accepted': False}, 1)
            checks[f'{repository}:{condition}:handoff'] = (agent.verifier_history is not None) == (condition in ('handoff', 'repository_context'))
            checks[f'{repository}:{condition}:history'] = (agent.history is before) == (condition in ('repair', 'investigation'))
            checks[f'{repository}:{condition}:no_calls'] = agent.calls == 0
        root = main.bind(repository)
        folder = RUN / 'offline' / repository / 'evaluation'
        ws = main.make_workspace(root, folder, root / 'translation/target')
        result = main.evaluator(repository, ws, folder / 'evidence').final()
        save(folder / 'initial.json', result)
        checks[f'{repository}:initial_rejected'] = not result['accepted']
    save(RUN / 'offline.json', {'passed': all(checks.values()), 'checks': checks, 'model_calls': 0})
    assert all(checks.values()), checks
    save(RUN / 'freeze.json', {'code_hashes': code_hashes(), 'protocol_sha256': digest(RUN / 'protocol.json'),
        'inputs': {repo: {name: hashes(RUN / repo / name) for name in ('source', 'translation/target', 'private_reference' if repo == 'timeseries' else 'references')}
                   for repo in main.REPOSITORIES},
        'tasks': {repo: digest(RUN / repo / 'task.json') for repo in main.REPOSITORIES}})
    print(json.dumps({'prepared': True, 'offline_checks': len(checks), 'run': str(RUN)}), flush=True)


def assert_frozen():
    frozen = read(RUN / 'freeze.json')
    assert frozen['code_hashes'] == code_hashes()
    assert frozen['protocol_sha256'] == digest(RUN / 'protocol.json')
    for repo in main.REPOSITORIES:
        assert frozen['tasks'][repo] == digest(RUN / repo / 'task.json')
        for name, expected in frozen['inputs'][repo].items():
            assert hashes(RUN / repo / name) == expected, (repo, name)


def run(repository, condition):
    assert_frozen()
    root = main.bind(repository)
    folder = root / 'conditions' / condition
    ws, ev, agent = make_agent(repository, condition, folder)
    translation = read(root / 'translation/result.json')
    result = {'repository': repository, 'condition': condition, 'status': 'running', 'accepted': False, 'attempts': [], 'pid': os.getpid(), 'started': time.time()}
    save(folder / 'protocol.json', {'config': asdict(agent.config), 'freeze_sha256': digest(RUN / 'freeze.json'),
        'initial_target_hashes': hashes(ws / 'target'), 'translation_usage': translation['usage']})
    save(folder / 'result.json', result)
    try:
        current = ev.final()
        result['initial'] = current
        save(folder / 'result.json', result)
        if not current['accepted']:
            if condition != 'repair':
                base = agent.config
                agent.config = replace(base, max_output_tokens=64000)
                result['diagnosis'] = asdict(agent.diagnose(current['observation']))
                agent.config = base
            for attempt in range(1, 5):
                if agent._budget_status():
                    break
                base = agent.config
                calls = math.ceil((base.max_calls - agent.calls) / (5 - attempt))
                if attempt == 1:
                    calls = min(16, calls)
                output = math.ceil((base.max_output_tokens - agent.output_tokens) / (5 - attempt))
                agent.config = replace(base, repair_calls_per_stage=max(2, calls), max_output_tokens=agent.output_tokens + output)
                stage = agent.repair(current['observation'], attempt)
                agent.config = base
                current = ev.final()
                result['attempts'].append({'attempt': attempt, 'stage': asdict(stage), 'evaluation': current, 'calls': agent.calls, 'usage': agent.usage()})
                result.update(calls=agent.calls, usage=agent.usage(), accepted=current['accepted'])
                save(folder / 'result.json', result)
                if current['accepted'] or agent._budget_status() or stage.status in ('api_error', 'infrastructure_error', 'error', 'not_applicable'):
                    break
        result.update(status='completed', accepted=current['accepted'], final=current, stop_reason=agent._budget_status())
    except Exception as exc:
        result.update(status='infrastructure_error', error=str(exc), traceback=traceback.format_exc())
    finally:
        result.update(finished=time.time(), calls=agent.calls, usage=agent.usage(), final_target_hashes=hashes(ws / 'target'),
            source_unchanged=hashes(ws / 'source') == hashes(root / 'source'), task_unchanged=digest(ws / 'task.json') == digest(root / 'task.json'),
            translation_usage=translation['usage'], end_to_end_tokens=agent.usage()['total_tokens'] + translation['usage']['total_tokens'])
        save(folder / 'result.json', result)
    print(json.dumps({k: result.get(k) for k in ('repository', 'condition', 'status', 'accepted', 'calls', 'end_to_end_tokens', 'error')}), flush=True)


def suite():
    assert_frozen()
    for line in (Path.home() / '.autofix_llm_env').read_text().splitlines():
        parts = shlex.split(line, comments=True)
        if parts and parts[0] == 'export':
            parts = parts[1:]
        if len(parts) == 1 and '=' in parts[0]:
            key, value = parts[0].split('=', 1)
            if key.startswith('AUTOFIX_LLM_'):
                os.environ[key] = value
    assert os.environ.get('AUTOFIX_LLM_API_KEY')
    assert os.environ.get('AUTOFIX_LLM_MODEL') == 'deepseek-v4-flash'
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
        os.environ[key] = '1'
    scheduler = RUN / 'scheduler.json'
    if scheduler.exists():
        raise FileExistsError('Suite already dispatched')
    jobs = [(repo, condition) for condition in CONDITIONS for repo in main.REPOSITORIES]
    save(scheduler, {'status': 'running', 'pid': os.getpid(), 'jobs': jobs, 'max_parallel_jobs': 3})
    def job(pair):
        repo, condition = pair
        with (RUN / f'{repo}_{condition}.log').open('x') as log:
            p = subprocess.Popen([sys.executable, __file__, 'run', '--repository', repo, '--condition', condition], cwd=ROOT, env=os.environ.copy(), stdout=log, stderr=subprocess.STDOUT)
            code = p.wait()
        record = {'repository': repo, 'condition': condition, 'exit_code': code}
        save(RUN / f'{repo}_{condition}_process.json', record)
        return record
    with ThreadPoolExecutor(max_workers=3) as pool:
        records = list(pool.map(job, jobs))
    save(scheduler, {'status': 'completed', 'pid': os.getpid(), 'jobs': records, 'max_parallel_jobs': 3})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('prepare', 'suite', 'run'))
    parser.add_argument('--repository', choices=main.REPOSITORIES)
    parser.add_argument('--condition', choices=CONDITIONS)
    args = parser.parse_args()
    if args.command == 'run':
        run(args.repository, args.condition)
    else:
        globals()[args.command]()
