"""Frozen work-unit planning ablation with unchanged complete-method references."""
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
from unit_adapter import NoWorkUnitTools, NoWorkUnitAgent, REPOSITORY_GUIDANCE, NO_UNIT_GUIDANCE, REMOVED_TOOLS

RUN = ROOT / 'experiments/work_unit_planning_ablation_20260922/results'
CONDITIONS = ('no_work_unit_planning',)
REFERENCE = Path('/media/main/whj/projects/torch4ms/ascend-torch4ms-map-ablation-20260922/experiments/repository_map_ablation_20260922/results')
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
    tools_cls = base.RepositoryTools if condition == 'full' else NoWorkUnitTools
    agent_cls = base.RepositoryAgent if condition == 'full' else NoWorkUnitAgent
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
        'replicate': 1, 'jobs': 2, 'reused_conditions': ['full'], 'max_parallel_jobs': 1,
        'repair_budget': base.main.BUDGET, 'external_submissions': 4,
        'full_reference': str(REFERENCE),
        'full_reuse': 'User requested reuse of the unchanged complete-method runs from the map ablation; no new full-method API calls. Reused outcomes and usage are separately labelled and excluded from newly incurred costs.',
        'contrast': 'Remove explicit work-unit planning and its dependent execution rules: plan/focus/checkpoint tools, dependency-ready gating, unit-scoped edit guard, checkpoint invalidation propagation and unit-boundary context rebuilds.',
        'retained': 'Same automatic file/import/symbol/notebook inventory, ordinary read/search/edit/tests, notebook edit transactions and syntax guards, immutable sources, versioned evidence, capacity-triggered context rebuilds, verifier and independent handoff, initial translation and generation state, acceptance and budgets. Working-set reads retain matching file hashes with identical character cap across the whole workspace when no unit is active.',
        'prompt_change': {'before': REPOSITORY_GUIDANCE, 'after': NO_UNIT_GUIDANCE},
        'schedule': 'Same cumulative runner: diagnosis 6 calls/64000 output; first repair <=16 calls; remaining allowance divided over remaining submissions. No budget reset.',
        'outcomes': 'Primary: complete repository acceptance on both fixed tasks. Descriptive: checks passed at every submission (69/145 fixed), calls and tokens, final failures, map/planning/checkpoint/edit/test trajectories. Checks are not independent samples.',
        'cost': 'All calls and failures counted; reused historical common translation added once for end-to-end attribution, no new translation calls.',
        'future_repetitions': 'No additional repeats dispatched. Report every run and any future authorized repeats without best-of selection; complete-method references are reused as explicitly requested.',
        'sampling': 'Same backend configuration; no seed or temperature added. Evaluation seeds unchanged. First replication is exploratory and does not establish a stable causal effect.',
        'created': time.time()})
    checks = {}
    reference_freeze = base.read(REFERENCE / 'freeze.json')
    reference_protocol = base.read(REFERENCE / 'protocol.json')
    checks['reference_budget_identical'] = reference_protocol['repair_budget'] == base.main.BUDGET
    checks['reference_core_code_identical'] = all(base.digest(ROOT / name) == digest for name, digest in reference_freeze['code_hashes'].items() if name.startswith(('scripts/', 'autofix/autonomous/')))
    (RUN / 'reference_protocol').mkdir()
    for name in ('freeze.json', 'protocol.json'):
        shutil.copy2(REFERENCE / name, RUN / 'reference_protocol' / name)
    for repo in base.main.REPOSITORIES:
        checks[f'{repo}:reference_task_identical'] = base.digest(RUN / repo / 'task.json') == reference_freeze['tasks'][repo]
        for name, expected in reference_freeze['inputs'][repo].items():
            checks[f'{repo}:reference_input_identical:{name}'] = base.hashes(RUN / repo / name) == expected
        source = REFERENCE / repo / 'conditions/full'
        shutil.copytree(source, RUN / repo / 'conditions/full')
        base.save(RUN / repo / 'conditions/full/reuse_origin.json', {'reused': True, 'source': str(source), 'result_sha256': base.digest(source / 'result.json'), 'protocol_sha256': base.digest(source / 'protocol.json'), 'new_model_calls': 0})
    def no_model(*args, **kwargs):
        raise AssertionError('Offline validation attempted API call')
    for repo in base.main.REPOSITORIES:
        agents = {}
        for condition in ('full',) + CONDITIONS:
            ws, ev, agent = make_agent(repo, condition, RUN / 'offline' / repo / condition, no_model)
            agents[condition] = agent
            checks[f'{repo}:{condition}:initial'] = base.hashes(ws / 'target') == base.hashes(RUN / repo / 'translation/target')
            inventory = agent.tools.execute('repository_map', {}, readonly=True)
            checks[f'{repo}:{condition}:map'] = bool(inventory.get('files'))
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
            checks[f'{repo}:{condition}:coordination_switch'] = (set(x['function']['name'] for x in agent.tools.schemas()) & REMOVED_TOOLS) == (REMOVED_TOOLS if condition == 'full' else set())
            checks[f'{repo}:{condition}:context_method'] = type(agent)._rebuild_context is base.RepositoryAgent._rebuild_context
        full, ablated = agents['full'], agents['no_work_unit_planning']
        left, right = copy.deepcopy(full.tools.schemas()), copy.deepcopy(ablated.tools.schemas())
        left = [x for x in left if x['function']['name'] not in REMOVED_TOOLS]
        for schema in left + right:
            if schema['function']['name'] in ('repository_map', 'edit'):
                schema['function']['description'] = 'normalized'
        checks[f'{repo}:identical_automatic_map'] = full.tools.inventory()['files'] == ablated.tools.inventory()['files']
        checks[f'{repo}:full_original_classes'] = type(full) is base.RepositoryAgent and type(full.tools) is base.RepositoryTools
        checks[f'{repo}:identical_other_schemas'] = left == right
        checks[f'{repo}:identical_config'] = full.config == ablated.config
        checks[f'{repo}:prompt_only_expected_delta'] = full.history[0]['content'].replace(REPOSITORY_GUIDANCE, NO_UNIT_GUIDANCE) == ablated.history[0]['content']
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
    allowed = sorted(os.sched_getaffinity(0))
    assert 4 in allowed and 5 in allowed, 'Reserved CPUs 4 and 5 unavailable'
    os.sched_setaffinity(0, {4, 5})
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
    base.save(scheduler, {'status': 'running', 'pid': os.getpid(), 'jobs': jobs, 'max_parallel_jobs': 1, 'started': time.time()})
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
    with ThreadPoolExecutor(max_workers=1) as pool:
        records = list(pool.map(job, jobs))
    base.save(scheduler, {'status': 'completed', 'pid': os.getpid(), 'jobs': records, 'max_parallel_jobs': 1})


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
