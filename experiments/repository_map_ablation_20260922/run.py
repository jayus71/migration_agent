"""Frozen first paired replication of automatic repository-map ablation."""
from pathlib import Path
import argparse
import copy
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT))
import run_cumulative_component_ablations as base
from map_adapter import NoAutomaticMapTools, NoAutomaticMapAgent, MAP_GUIDANCE, NO_MAP_GUIDANCE

RUN = ROOT / 'experiments/repository_map_ablation_20260922/results'
CONDITIONS = ('full', 'no_automatic_map')
base.RUN = base.main.RUN = RUN
original_code_hashes = base.code_hashes


def code_hashes():
    result = original_code_hashes()
    result.update({str(p.relative_to(ROOT)): base.digest(p)
                   for p in Path(__file__).parent.glob('*.py')})
    return result


def make_agent(repository, condition, folder, client=None):
    root = base.main.bind(repository)
    ws = base.main.make_workspace(root, folder, root / 'translation/target')
    ev = base.main.evaluator(repository, ws, folder / 'evidence')
    tools_cls = base.RepositoryTools if condition == 'full' else NoAutomaticMapTools
    agent_cls = base.RepositoryAgent if condition == 'full' else NoAutomaticMapAgent
    tools = tools_cls(ws, ev.tool, state_path=folder / 'evidence/repository_state.json',
                      named_tests=base.main.named_tests(repository), validate_syntax=True)
    agent = agent_cls(tools, folder / 'evidence/agent', config=base.main.configuration('ladim'), client=client)
    agent.set_generation_state(base.read(root / 'translation/result.json').get('file_states', {}))
    return ws, ev, agent


base.code_hashes = code_hashes
base.make_agent = make_agent


def prepare():
    RUN.mkdir(parents=True, exist_ok=False)
    for repository in base.main.REPOSITORIES:
        source, target = base.ORIGINAL / repository, RUN / repository
        target.mkdir()
        for name in ('source', 'private_reference' if repository == 'timeseries' else 'references'):
            shutil.copytree(source / name, target / name)
        (target / 'translation').mkdir()
        shutil.copytree(source / 'translation/target', target / 'translation/target')
        shutil.copy2(source / 'translation/result.json', target / 'translation/result.json')
        for name in ('task.json', 'manifest.json'):
            shutil.copy2(source / name, target / name)
    base.save(RUN / 'protocol.json', {
        'repositories': base.main.REPOSITORIES, 'conditions': CONDITIONS,
        'replicate': 1, 'jobs': 4, 'max_parallel_jobs': 2,
        'repair_budget': base.main.BUDGET, 'external_submissions': 4,
        'contrast': 'Only automatic structure inventory removed: files, imports, symbols, notebook cell metadata and automatic unassigned-file list. Agent-generated work-unit graph remains.',
        'retained': 'Same public read/search/notebook tools, plan/focus/checkpoint, notebook edits, versioned evidence, context rebuilding, verifier, independent handoff, initial translation and generation-state handoff, all acceptance tests and all budgets.',
        'prompt_change': {'before': MAP_GUIDANCE, 'after': NO_MAP_GUIDANCE},
        'schedule': 'Same cumulative runner: diagnosis 6 calls/64000 output; first repair <=16 calls; remaining allowance divided over remaining submissions. No budget reset.',
        'outcomes': 'Primary: complete repository acceptance on both fixed tasks. Descriptive: checks passed at every submission (69/145 fixed), calls and tokens, final failures, map/planning/checkpoint/edit/test trajectories. Checks are not independent samples.',
        'cost': 'All calls and failures counted; reused historical common translation added once for end-to-end attribution, no new translation calls.',
        'future_repetitions': 'Prespecified recommendation, not dispatched: replicas 2 and 3, each both conditions on both repositories (8 additional jobs), identical budgets and no outcome-dependent selection. Report every run; no best-of selection.',
        'sampling': 'Same backend configuration; no seed or temperature added. Evaluation seeds unchanged. First replication is exploratory and does not establish a stable causal effect.',
        'created': time.time()})
    checks = {}
    def no_model(*args, **kwargs):
        raise AssertionError('Offline validation attempted API call')
    for repo in base.main.REPOSITORIES:
        agents = {}
        for condition in CONDITIONS:
            ws, ev, agent = make_agent(repo, condition, RUN / 'offline' / repo / condition, no_model)
            agents[condition] = agent
            checks[f'{repo}:{condition}:initial'] = base.hashes(ws / 'target') == base.hashes(RUN / repo / 'translation/target')
            inventory = agent.tools.execute('repository_map', {}, readonly=True)
            checks[f'{repo}:{condition}:map'] = ('files' in inventory) == (condition == 'full')
            checks[f'{repo}:{condition}:no_calls'] = agent.calls == 0
            for name in ('task.json', base.read(RUN / repo / 'task.json')['source_entry']):
                try:
                    agent.tools.execute('edit', {'edits': [{'path': name, 'old': '', 'new': 'bad'}]})
                except base.ToolError:
                    checks[f'{repo}:{condition}:readonly:{name}'] = True
                else:
                    raise AssertionError('Immutable input editable')
            # Verify independent handoff uses the same original implementation.
            checks[f'{repo}:{condition}:handoff_method'] = type(agent).repair is base.RepositoryAgent.repair
            checks[f'{repo}:{condition}:planning_method'] = type(agent.tools)._plan is base.RepositoryTools._plan
            checks[f'{repo}:{condition}:context_method'] = type(agent)._rebuild_context is base.RepositoryAgent._rebuild_context
        full, ablated = agents['full'], agents['no_automatic_map']
        left, right = copy.deepcopy(full.tools.schemas()), copy.deepcopy(ablated.tools.schemas())
        for schema in left + right:
            if schema['function']['name'] == 'repository_map':
                schema['function']['description'] = 'normalized'
        checks[f'{repo}:identical_other_schemas'] = left == right
        checks[f'{repo}:identical_config'] = full.config == ablated.config
        checks[f'{repo}:prompt_only_expected_delta'] = full.history[0]['content'].replace(MAP_GUIDANCE, NO_MAP_GUIDANCE) == ablated.history[0]['content']
        checks[f'{repo}:generation_state_same'] = full.generation_state['observation'] == ablated.generation_state['observation']
        root = base.main.bind(repo)
        folder = RUN / 'offline' / repo / 'evaluation'
        ws = base.main.make_workspace(root, folder, root / 'translation/target')
        result = base.main.evaluator(repo, ws, folder / 'evidence').final()
        base.save(folder / 'initial.json', result)
        checks[f'{repo}:initial_rejected'] = not result['accepted']
    base.save(RUN / 'offline.json', {'passed': all(checks.values()), 'checks': checks, 'model_calls': 0})
    assert all(checks.values()), checks
    base.save(RUN / 'freeze.json', {'code_hashes': code_hashes(), 'protocol_sha256': base.digest(RUN / 'protocol.json'),
        'inputs': {repo: {name: base.hashes(RUN / repo / name) for name in ('source', 'translation/target', 'private_reference' if repo == 'timeseries' else 'references')} for repo in base.main.REPOSITORIES},
        'tasks': {repo: base.digest(RUN / repo / 'task.json') for repo in base.main.REPOSITORIES}})
    print(json.dumps({'prepared': True, 'checks': len(checks), 'run': str(RUN)}), flush=True)


def suite():
    base.assert_frozen()
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
        raise FileExistsError('Already dispatched; inspect persisted run without resetting counters')
    jobs = [(repo, condition) for repo in base.main.REPOSITORIES for condition in CONDITIONS]
    base.save(scheduler, {'status': 'running', 'pid': os.getpid(), 'jobs': jobs, 'max_parallel_jobs': 2, 'started': time.time()})
    def job(pair):
        repo, condition = pair
        record = {'repository': repo, 'condition': condition, 'status': 'running', 'started': time.time()}
        record_path = RUN / f'{repo}_{condition}_process.json'
        with (RUN / f'{repo}_{condition}.log').open('x') as log:
            process = subprocess.Popen([sys.executable, __file__, 'run', '--repository', repo, '--condition', condition], cwd=ROOT, env=os.environ.copy(), stdout=log, stderr=subprocess.STDOUT)
            record['pid'] = process.pid
            base.save(record_path, record)
            record['exit_code'] = process.wait()
        record.update(status='completed' if record['exit_code'] == 0 else 'process_error', finished=time.time())
        base.save(record_path, record)
        return record
    with ThreadPoolExecutor(max_workers=2) as pool:
        records = list(pool.map(job, jobs))
    base.save(scheduler, {'status': 'completed', 'pid': os.getpid(), 'jobs': records, 'max_parallel_jobs': 2})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('prepare', 'suite', 'run'))
    parser.add_argument('--repository', choices=base.main.REPOSITORIES)
    parser.add_argument('--condition', choices=CONDITIONS)
    args = parser.parse_args()
    if args.command == 'run':
        base.run(args.repository, args.condition)
    else:
        globals()[args.command]()
