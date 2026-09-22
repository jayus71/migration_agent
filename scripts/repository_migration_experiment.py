"""Frozen common-input repository comparison, with auditable native baselines."""
from __future__ import annotations

import argparse
import copy
from dataclasses import asdict, replace
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import repository_timeseries_pilot as ts
import repository_entrypoint_evaluation as entries
import run_repository_twotower as tt
from repository_timeseries_pilot import save, read, hashes, digest, BASE, TARGET_PY
from autofix.autonomous.agent import AgentConfig, AutonomousAgent
from autofix.autonomous.tools import WorkspaceTools, ToolError
from autofix.autonomous.repository import RepositoryAgent, RepositoryTools
from autofix.autonomous.swe_upstream import SWEAgentNative, _validate_workspace
from autofix.autonomous.baselines import MatchFixFullOrchestration
from repository_shared_translation import translate

RUN = ROOT / 'experiments/repository_migration_20260921'
OLD = BASE / 'ascend-torch4ms-repository-pilot-20260920/experiments'
REPOSITORIES = ('timeseries', 'twotower')
METHODS = ('ladim', 'swe', 'matchfix')
BUDGET = dict(model='deepseek-v4-flash', max_calls=80, max_output_tokens=480000,
              max_seconds=3600, per_call_output_tokens=32768)


def bind(repository):
    root = RUN / repository
    ts.ROOT = entries.ROOT = ROOT
    ts.RUN = entries.RUN = root
    ts.WORKER = ROOT / 'scripts/repository_timeseries_worker.py'
    tt.RUN = root
    tt.WORKER = ROOT / 'scripts/repository_twotower_candidate_worker.py'
    return root


def configuration(method):
    return AgentConfig(**BUDGET, method='layered' if method == 'ladim' else 'single',
        memory_policy='evidence' if method == 'ladim' else 'native',
        workflow_policy='progress_loop' if method == 'ladim' else 'standard',
        diagnosis_policy='evidence', diagnosis_calls_per_stage=6, repair_calls_per_stage=18)


def documentation(target):
    errors = []
    readme = target / 'README.md'
    requirements = target / 'requirements.txt'
    if not readme.exists() or 'mindspore' not in readme.read_text().lower():
        errors.append('README must describe the native MindSpore framework and installation.')
    if not requirements.exists() or not re.search(r'^\s*mindspore(?:\s|[<>=!~;\[]|$)', requirements.read_text(), re.M | re.I):
        errors.append('requirements.txt must declare MindSpore.')
    if requirements.exists() and re.search(r'^\s*(torch|torchvision|torchaudio|torch4ms|torchax|jax|flax)(?:\s|[<>=!~;\[]|$)', requirements.read_text(), re.M | re.I):
        errors.append('requirements.txt still requires a source or alternate execution framework.')
    return {'accepted': not errors, 'errors': errors}


class TimeSeriesEvaluator(entries.RepositoryEvaluator):
    def public(self):
        core = self.evaluate()['observation']
        extra = self.entrypoints()
        docs = documentation(self.workspace / 'target')
        return {**core, 'entrypoints': extra, 'documentation': docs,
                'accepted': core['accepted'] and extra['accepted'] and docs['accepted']}

    def tool(self, args):
        name = args['test']
        if name == 'public':
            return self.public()
        if name == 'coverage':
            code, docs = ts.coverage(self.workspace / 'target'), documentation(self.workspace / 'target')
            return {'accepted': code['passed'] and docs['accepted'], 'code': code, 'documentation': docs}
        return super().tool(args)

    def final(self):
        public = self.public()
        confirmations = [self.evaluate(seed=s, full=False) for s in (202, 303)] if public['accepted'] else []
        accepted = public['accepted'] and all(x['accepted'] for x in confirmations)
        observation = public if accepted or not public['accepted'] else next(x['observation'] for x in confirmations if not x['accepted'])
        return {'accepted': accepted, 'public': public, 'confirmations': confirmations, 'observation': observation}


class TwoTowerEvaluator(tt.Evaluator):
    def tool(self, args):
        if args['test'] == 'coverage':
            code, docs = tt.file_coverage(self.workspace / 'source', self.workspace / 'target'), documentation(self.workspace / 'target')
            return {'accepted': code['accepted'] and docs['accepted'], 'code': code, 'documentation': docs}
        return super().tool(args)

    def evaluate(self, seed=101, full=True):
        result = copy.deepcopy(super().evaluate(seed, full))
        if full:
            result['documentation'] = documentation(self.workspace / 'target')
            result['accepted'] = result['accepted'] and result['documentation']['accepted']
        return result


def evaluator(repository, workspace, evidence):
    return (TimeSeriesEvaluator if repository == 'timeseries' else TwoTowerEvaluator)(workspace, evidence)


def named_tests(repository):
    return ('paired', 'workflow', 'entrypoints', 'coverage', 'public') if repository == 'timeseries' else ('base', 'paired', 'tests', 'workflow', 'coverage', 'public')


def adapter_for(method, agent):
    if method == 'swe':
        return SWEAgentNative(agent, upstream_root=BASE / 'external_baselines/SWE-agent-v1.1.0',
            python='/media/main/whj/miniconda3/envs/sweagent110/bin/python', target_python=TARGET_PY,
            vendor=BASE / 'experiments/autonomous_verifier_20260917/swe_native_vendor')
    return MatchFixFullOrchestration(agent, upstream_root=BASE / 'external_baselines/MatchFixAgent-66a52a5',
            python='/media/main/whj/miniconda3/envs/matchfixagent/bin/python')


def make_workspace(root, folder, initial):
    ws = folder / 'workspace'
    ws.mkdir(parents=True, exist_ok=False)
    shutil.copytree(root / 'source', ws / 'source')
    shutil.copytree(initial, ws / 'target', ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))
    shutil.copy2(root / 'task.json', ws / 'task.json')
    (ws / 'scratch_tests').mkdir()
    return ws


def prepare():
    if (RUN / 'protocol.json').exists():
        raise FileExistsError('Existing protocol is not overwritten')
    for repository in REPOSITORIES:
        root = bind(repository)
        root.mkdir(parents=True, exist_ok=False)
        old = OLD / ('repository_' + repository + '_20260920')
        shutil.copytree(old / 'source', root / 'source')
        refs = 'private_reference' if repository == 'timeseries' else 'references'
        shutil.copytree(old / refs, root / refs)
        task = read(old / 'task.json')
        task.setdefault('tools', {}).update({'public': 'All declared public checks, including execution entries, numeric training, file coverage and documentation.',
            'coverage': 'Code scope plus README and target dependency checks.'})
        task['documentation_check'] = 'README describes native MindSpore and installation. requirements.txt includes MindSpore and excludes source or alternate execution frameworks.'
        if repository == 'timeseries':
            task['tools']['entrypoints'] = 'Execute notebook cells and instructional snippets in their original sequential order.'
            task['acceptance']['entrypoints'] = 'The notebook and sequential snippets must each complete the original training and plotting workflow on the fixed local data fixture.'
            folder = root / 'translation'
            folder.mkdir()
            shutil.copytree(old / 'translation/target', folder / 'target')
            record = read(old / 'staged_translation_result.json')
            save(folder / 'result.json', {'status': 'reused', 'historical_record': str(old / 'staged_translation_result.json'),
                'calls': 3, 'usage': {'total_tokens': 163661}, 'original_record': record,
                'file_states': {name: 'reused_initial_candidate' for name in hashes(folder / 'target')}})
            assert hashes(folder / 'target') == record['files']
        else:
            task.update(source_entry='source/train/train.py', target_entry='target/train/train.py')
            task['interfaces']['train.train.train_one_epoch'] = 'Keep (model,dataloader,optimizer,device), accept the optimizer returned by make_optimizer and device string CPU. One native value_and_grad per training batch, preserve source loss and averaging.'
            task['interfaces']['train.train.make_optimizer'] = 'Expose make_optimizer(model, learning_rate=0.001), returning the native target optimizer with source training semantics. Use this same factory in the training CLI. The paired probe calls this candidate factory and observes actual updates.'
        save(root / 'task.json', task)
        save(root / 'manifest.json', {'source_hashes': hashes(root / 'source'), 'task_sha256': digest(root / 'task.json'),
            'reference_hashes': hashes(root / refs), 'source_origin': str(old / 'source')})
    save(RUN / 'protocol.json', {'repositories': REPOSITORIES, 'methods': METHODS, 'repair_budget': BUDGET,
        'external_submissions': 4, 'translation_budget': {**BUDGET, 'max_calls': 48, 'max_output_tokens': 240000},
        'translation_per_unit_calls': 2, 'translation_evaluation_feedback': False,
        'translation_cost': 'Every generation call, including failures, attributed to each end-to-end condition; physical generation occurs once.',
        'baseline_policy': 'Pinned native algorithms, prompts, parsers, tools and retries. Only shared backend/workspace integration.',
        'ladim_schedule': 'Six diagnosis calls; remaining repair calls divided over four submissions with a 16-call first-stage cap. Output quota of each stage reserves remaining output for later submissions; counters never reset.',
        'observations': 'Same public tool suite from the first call. Confirmatory seeds after all public checks pass.',
        'progress_snapshots': 'Save current candidate at or after 40 calls and 240000 output tokens. No extra model calls or implied lower-budget reruns.'})
    print(json.dumps({'prepared': True, 'run': str(RUN)}))


def offline():
    checks = {}
    def no_model(*a, **kw):
        raise AssertionError('Offline check attempted a model call')
    for repository in REPOSITORIES:
        root = bind(repository)
        folder = root / 'preflight'
        initial = root / 'translation/target' if repository == 'timeseries' else root / 'source'
        ws = make_workspace(root, folder, initial)
        ev = evaluator(repository, ws, folder / 'evidence')
        tools = WorkspaceTools(ws, ev.tool, named_tests=named_tests(repository), validate_syntax=False)
        _validate_workspace(ws)
        for name in ('task.json', read(root / 'task.json')['source_entry']):
            try:
                tools.execute('edit', {'edits': [{'path': name, 'old': '', 'new': 'bad'}]})
            except ToolError:
                checks[repository + ':readonly:' + name] = True
            else:
                raise AssertionError('Immutable input became editable')
        for method in ('swe', 'matchfix'):
            agent = AutonomousAgent(tools, folder / method, config=configuration(method), client=no_model)
            adapter = adapter_for(method, agent)
            try:
                checks[repository + ':' + method + ':ready'] = adapter.initialize({'phase': 'offline'}).status == 'ready'
                if method == 'matchfix':
                    fragment = adapter._fragment()
                    checks[repository + ':genuine_pair'] = fragment['source_function'] == (ws / fragment['source_path']).read_text().splitlines() and fragment['target_function'] == (ws / fragment['target_path']).read_text().splitlines()
                    checks[repository + ':no_healthy_target'] = fragment['ground_truth_target_function'] == ''
                checks[repository + ':' + method + ':no_calls'] = agent.calls == 0
            finally:
                if hasattr(adapter, 'close'):
                    adapter.close()
        outcome = ev.final()
        save(folder / 'initial_evaluation.json', outcome)
        checks[repository + ':initial_rejected'] = not outcome['accepted']
        checks[repository + ':source_unchanged'] = hashes(ws / 'source') == read(root / 'manifest.json')['source_hashes']
        checks[repository + ':target_unchanged'] = hashes(ws / 'target') == hashes(initial)
        generator = AutonomousAgent(WorkspaceTools(ws, lambda x: {}, named_tests=('public',), validate_syntax=True),
            folder / 'generator', config=replace(configuration('swe'), max_calls=48, max_output_tokens=240000), client=no_model)
        checks[repository + ':generator_constructed_without_model'] = generator.calls == 0
    save(RUN / 'offline.json', {'passed': all(checks.values()), 'checks': checks, 'model_calls': 0})
    if not all(checks.values()):
        raise AssertionError(checks)
    print(json.dumps({'offline_passed': True, 'checks': checks}))


def code_hashes():
    return {str(p.relative_to(ROOT)): digest(p) for directory in ('scripts', 'autofix/autonomous')
            for p in sorted((ROOT / directory).glob('*.py'))}


def freeze():
    assert read(RUN / 'offline.json')['passed']
    assert read(RUN / 'optimizer_controls.json')['passed']
    assert read(RUN / 'context_checks.json')['passed']
    assert read(RUN / 'generation_checks.json')['passed']
    save(RUN / 'freeze.json', {'code_hashes': code_hashes(), 'protocol_sha256': digest(RUN / 'protocol.json'),
        'manifests': {r: digest(RUN / r / 'manifest.json') for r in REPOSITORIES},
        'checks': {name: digest(RUN / (name + '.json')) for name in ('offline', 'optimizer_controls', 'context_checks', 'generation_checks')}})
    print(json.dumps({'frozen': True}))


def assert_frozen():
    frozen = read(RUN / 'freeze.json')
    assert frozen['code_hashes'] == code_hashes(), 'Implementation changed after freeze'
    assert frozen['protocol_sha256'] == digest(RUN / 'protocol.json')
    for repository in REPOSITORIES:
        root = RUN / repository
        m = read(root / 'manifest.json')
        assert digest(root / 'manifest.json') == frozen['manifests'][repository]
        assert hashes(root / 'source') == m['source_hashes']
        assert digest(root / 'task.json') == m['task_sha256']


def generate():
    assert_frozen()
    root = bind('twotower')
    folder = root / 'translation'
    folder.mkdir(exist_ok=False)
    ws = make_workspace(root, folder, root / 'source')
    config = replace(configuration('swe'), max_calls=48, max_output_tokens=240000)
    agent = AutonomousAgent(WorkspaceTools(ws, lambda x: {}, named_tests=('public',), validate_syntax=True), folder / 'evidence/agent', config=config)
    save(folder / 'status.json', {'status': 'running', 'pid': os.getpid()})
    try:
        result = translate(agent, ws, read(root / 'task.json'), save, folder)
        shutil.copytree(ws / 'target', folder / 'target')
        result['target_hashes'] = hashes(folder / 'target')
        save(folder / 'result.json', result)
        save(folder / 'status.json', {'status': 'completed', 'calls': agent.calls, 'usage': agent.usage()})
    except Exception:
        save(folder / 'status.json', {'status': 'error', 'traceback': traceback.format_exc(), 'calls': agent.calls, 'usage': agent.usage()})
        raise


def run(repository, method):
    assert_frozen()
    root = bind(repository)
    translation = read(root / 'translation/result.json')
    expected_initial = translation.get('target_hashes', translation.get('original_record', {}).get('files'))
    assert expected_initial and hashes(root / 'translation/target') == expected_initial, 'Shared initial translation changed'
    folder = root / 'conditions' / method
    folder.mkdir(parents=True, exist_ok=False)
    ws = make_workspace(root, folder, root / 'translation/target')
    assert hashes(ws / 'target') == expected_initial
    ev = evaluator(repository, ws, folder / 'evidence')
    ours = method == 'ladim'
    tool_args = dict(named_tests=named_tests(repository), validate_syntax=ours)
    if ours:
        tool_args['state_path'] = folder / 'evidence/repository_state.json'
    tools = (RepositoryTools if ours else WorkspaceTools)(ws, ev.tool, **tool_args)
    agent = (RepositoryAgent if ours else AutonomousAgent)(tools, folder / 'evidence/agent', config=configuration(method))
    adapter = None if ours else adapter_for(method, agent)
    if ours:
        agent.set_generation_state(translation.get('file_states', {}))
    save(folder / 'protocol.json', {'config': asdict(agent.config), 'freeze_sha256': digest(RUN / 'freeze.json'),
        'initial_target_hashes': hashes(ws / 'target'), 'translation_result_sha256': digest(root / 'translation/result.json'),
        'translation_usage': translation['usage'], 'pid': os.getpid()})
    result = {'status': 'running', 'repository': repository, 'method': method, 'accepted': False, 'attempts': []}
    save(folder / 'result.json', result)
    original_snapshot = agent._snapshot
    def progress_snapshot():
        original_snapshot()
        for label, reached in [('calls40', agent.calls >= 40), ('output240000', agent.output_tokens >= 240000)]:
            checkpoint = folder / 'progress' / label
            if reached and not checkpoint.exists():
                checkpoint.mkdir(parents=True)
                shutil.copytree(ws / 'target', checkpoint / 'target', ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))
                save(checkpoint / 'state.json', {'calls': agent.calls, 'usage': agent.usage(), 'target_hashes': hashes(ws / 'target'),
                    'measurement_status': 'candidate snapshot; acceptance measured at normal external submissions'})
    agent._snapshot = progress_snapshot
    try:
        current = ev.final()
        result['initial'] = current
        save(folder / 'result.json', result)
        # Evaluation time is included in the common lifetime clock.
        if not current['accepted']:
            if ours:
                base_config = agent.config
                agent.config = replace(base_config, max_output_tokens=min(64000, base_config.max_output_tokens))
                result['diagnosis'] = asdict(agent.diagnose(current['observation']))
                agent.config = base_config
            else:
                ready = adapter.initialize(current['observation'])
                result['initialization'] = asdict(ready)
                if ready.status != 'ready':
                    raise RuntimeError('Baseline initialization: ' + ready.status)
            for attempt in range(1, 5):
                if agent._budget_status():
                    break
                if ours:
                    base_config = agent.config
                    submissions_left = 5 - attempt
                    calls = math.ceil((base_config.max_calls - agent.calls) / submissions_left)
                    if attempt == 1:
                        calls = min(16, calls)
                    output = math.ceil((base_config.max_output_tokens - agent.output_tokens) / submissions_left)
                    agent.config = replace(base_config, repair_calls_per_stage=max(2, calls), max_output_tokens=agent.output_tokens + output)
                    stage = agent.repair(current['observation'], attempt)
                    agent.config = base_config
                else:
                    stage = adapter.repair(current['observation'], attempt)
                current = ev.final()
                result['attempts'].append({'attempt': attempt, 'stage': asdict(stage), 'evaluation': current,
                    'calls': agent.calls, 'usage': agent.usage()})
                result.update(calls=agent.calls, usage=agent.usage(), accepted=current['accepted'])
                save(folder / 'result.json', result)
                if current['accepted'] or agent._budget_status() or stage.status in ('api_error', 'infrastructure_error', 'error', 'not_applicable'):
                    break
        result.update(status='completed', accepted=current['accepted'], final=current, stop_reason=agent._budget_status())
    except Exception as exc:
        result.update(status='infrastructure_error', error=str(exc), traceback=traceback.format_exc())
    finally:
        if adapter and hasattr(adapter, 'close'):
            adapter.close()
        result.update(calls=agent.calls, usage=agent.usage(), final_target_hashes=hashes(ws / 'target'),
            source_unchanged=hashes(ws / 'source') == read(root / 'manifest.json')['source_hashes'],
            task_unchanged=digest(ws / 'task.json') == read(root / 'manifest.json')['task_sha256'],
            translation_usage=translation['usage'], end_to_end_tokens=agent.usage()['total_tokens'] + translation['usage']['total_tokens'])
        save(folder / 'result.json', result)
    print(json.dumps({k: result.get(k) for k in ('repository', 'method', 'status', 'accepted', 'calls', 'usage', 'error')}), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('command', choices=['prepare', 'offline', 'freeze', 'generate', 'run'])
    p.add_argument('--repository', choices=REPOSITORIES)
    p.add_argument('--method', choices=METHODS)
    a = p.parse_args()
    if a.command == 'run':
        run(a.repository, a.method)
    else:
        globals()[a.command]()
