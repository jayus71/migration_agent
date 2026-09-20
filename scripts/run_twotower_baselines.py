"""Two-tower baselines on the same source and acceptance at the larger budget."""
from __future__ import annotations
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

ROOT=Path('/media/main/whj/projects/torch4ms/ascend-torch4ms-repository-pilot-20260920')
RUN=ROOT/'experiments/repository_twotower_20260920'
BASELINE=RUN/'baseline_comparison'
RUNTIME=BASELINE/'runtime'
sys.path.insert(0,str(RUNTIME))
from autofix.autonomous.agent import AgentConfig,AutonomousAgent
from autofix.autonomous.tools import WorkspaceTools,ToolError
from autofix.autonomous.swe_upstream import SWEAgentNative,_validate_workspace
from autofix.autonomous.baselines import MatchFixFullOrchestration
from run_repository_twotower import Evaluator,BASE,TARGET_PY,WORKER,read,save,hashes,digest

NAMES=('base','paired','tests','workflow','coverage','public')


def configuration():
    return AgentConfig(method='single',model='deepseek-v4-flash',memory_policy='native',workflow_policy='standard',
                       max_calls=40,max_output_tokens=240000,max_seconds=1800,per_call_output_tokens=32768)


def make_workspace(folder):
    ws=folder/'workspace';ws.mkdir(parents=True)
    for name in ('source','target'):
        shutil.copytree(RUN/'source',ws/name,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache'))
    shutil.copy2(BASELINE/'task.json',ws/'task.json');(ws/'scratch_tests').mkdir()
    return ws


def adapter_for(method,agent):
    if method=='swe':
        return SWEAgentNative(agent,upstream_root=BASE/'external_baselines/SWE-agent-v1.1.0',
            python='/media/main/whj/miniconda3/envs/sweagent110/bin/python',target_python=TARGET_PY,
            vendor=BASE/'experiments/autonomous_verifier_20260917/swe_native_vendor')
    return MatchFixFullOrchestration(agent,upstream_root=BASE/'external_baselines/MatchFixAgent-66a52a5',
                                    python='/media/main/whj/miniconda3/envs/matchfixagent/bin/python')


def assert_frozen():
    m=read(RUN/'manifest.json');p=read(BASELINE/'preparation.json')
    assert hashes(RUN/'source')==m['source_hashes']
    assert digest(WORKER)==m['worker_sha256']
    assert digest(ROOT/'scripts/run_repository_twotower.py')==m['controller_sha256']
    assert digest(BASELINE/'task.json')==p['baseline_task_sha256']
    task=read(BASELINE/'task.json');task.pop('source_entry');task.pop('target_entry')
    assert task==read(RUN/'task.json')
    for name,value in p['original_runtime_hashes'].items():assert digest(ROOT/'autofix/autonomous'/name)==value
    for name,value in p['baseline_runtime_hashes'].items():assert digest(RUNTIME/'autofix/autonomous'/name)==value
    assert Path(sys.modules['autofix.autonomous.swe_upstream'].__file__).is_relative_to(RUNTIME)


def preflight():
    assert_frozen();folder=BASELINE/'preflight';folder.mkdir(exist_ok=False)
    ws=make_workspace(folder);ev=Evaluator(ws,folder/'evidence');checks={}
    tools=WorkspaceTools(ws,ev.tool,named_tests=NAMES,validate_syntax=False)
    checks['same_source_and_initial_target']=hashes(ws/'source')==hashes(ws/'target')==read(RUN/'manifest.json')['source_hashes']
    checks['all_public_tests_available']=set(tools.named_tests)==set(NAMES)
    _validate_workspace(ws);checks['declared_training_entry_accepted']=True
    for name in ('source/train/train.py','task.json'):
        try:tools.execute('edit',{'edits':[{'path':name,'old':'','new':'bad'}]})
        except ToolError:checks['readonly_'+name]=True
        else:raise AssertionError('Immutable input became editable')
    def no_model(*args,**kwargs):raise AssertionError('Offline integration check attempted a model call')
    mfagent=AutonomousAgent(tools,folder/'matchfix',config=configuration(),client=no_model)
    matchfix=adapter_for('matchfix',mfagent)
    ready=matchfix.initialize({'execution':'offline integration preflight'})
    fragment=matchfix._fragment()
    checks['matchfix_initialized']=ready.status=='ready'
    checks['matchfix_genuine_entry_pair']=(fragment['source_path']=='source/train/train.py'
        and fragment['target_path']=='target/train/train.py'
        and fragment['source_function']==(ws/'source/train/train.py').read_text().splitlines()
        and fragment['target_function']==fragment['source_function'])
    checks['matchfix_no_healthy_target']=fragment['ground_truth_target_function']==''
    sweagent=AutonomousAgent(tools,folder/'swe',config=configuration(),client=no_model)
    swe=adapter_for('swe',sweagent)
    try:checks['swe_native_worker_ready']=swe.initialize({'execution':'offline integration preflight'}).status=='ready'
    finally:swe.close()
    # Paired test execution is intentionally expected to reject the untranslated
    # source. This confirms it reaches the native target evaluator.
    observation=ev.final()
    checks['raw_source_rejected']=not observation['accepted']
    checks['no_model_calls']=sweagent.calls==mfagent.calls==0
    checks['inputs_remain_unchanged']=hashes(ws/'source')==hashes(ws/'target')==read(RUN/'manifest.json')['source_hashes']
    save(folder/'initial_evaluation.json',observation)
    save(BASELINE/'preflight.json',{'passed':all(checks.values()),'checks':checks,'model_calls':0})
    if not all(checks.values()):raise RuntimeError('Offline integration failed: '+json.dumps(checks))
    save(BASELINE/'launch_freeze.json',{'preparation_sha256':digest(BASELINE/'preparation.json'),
        'controller_sha256':digest(Path(__file__)),'worker_sha256':digest(WORKER),
        'source_hashes':read(RUN/'manifest.json')['source_hashes'],
        'baseline_task_sha256':digest(BASELINE/'task.json'),'preflight_sha256':digest(BASELINE/'preflight.json')})
    print(json.dumps({'preflight_passed':True,'checks':checks}))


def execute(method):
    assert_frozen();freeze=read(BASELINE/'launch_freeze.json')
    assert read(BASELINE/'preflight.json')['passed']
    assert digest(Path(__file__))==freeze['controller_sha256']
    folder=BASELINE/method;folder.mkdir(exist_ok=False);ws=make_workspace(folder)
    ev=Evaluator(ws,folder/'evidence')
    tools=WorkspaceTools(ws,ev.tool,named_tests=NAMES,validate_syntax=False)
    agent=AutonomousAgent(tools,folder/'evidence/agent',config=configuration());adapter=adapter_for(method,agent)
    save(folder/'protocol.json',{'config':asdict(agent.config),'launch_freeze_sha256':digest(BASELINE/'launch_freeze.json'),
        'initial_target_hashes':hashes(ws/'target'),'source_hashes':hashes(ws/'source'),
        'task_sha256':digest(ws/'task.json'),'initial_candidate':'untranslated frozen source copy',
        'acceptance_contract_sha256':digest(RUN/'task.json'),'external_submissions':4,
        'generation_policy':'Baseline native tool workflow performs its own translation; no LaDiM generation or partial target supplied.'})
    result={'method':method,'status':'running','accepted':False,'attempts':[]};save(folder/'result.json',result)
    started=time.monotonic()
    try:
        current=ev.final();result['initial']=current
        ready=adapter.initialize(current['observation']);result['initialization']=asdict(ready)
        if ready.status!='ready':raise RuntimeError('Baseline did not initialize: '+ready.status)
        for attempt in range(1,5):
            if agent._budget_status():break
            stage=adapter.repair(current['observation'],attempt=attempt);current=ev.final()
            result['attempts'].append({'attempt':attempt,'stage':asdict(stage),'evaluation':current})
            result.update(calls=agent.calls,usage=agent.usage(),accepted=current['accepted']);save(folder/'result.json',result)
            if current['accepted'] or agent._budget_status() or stage.status in ('api_error','infrastructure_error','error','not_applicable'):break
        result.update(status='completed',accepted=current['accepted'],final=current)
    except Exception as exc:result.update(status='infrastructure_error',error=str(exc),traceback=traceback.format_exc())
    finally:
        if hasattr(adapter,'close'):adapter.close()
        result.update(calls=agent.calls,usage=agent.usage(),seconds=time.monotonic()-started,
            final_target_hashes=hashes(ws/'target'),source_unchanged=hashes(ws/'source')==freeze['source_hashes'],
            task_unchanged=digest(ws/'task.json')==freeze['baseline_task_sha256'])
        save(folder/'result.json',result)
    print(json.dumps({k:result.get(k) for k in ('method','status','accepted','calls','usage','seconds','error')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['preflight','run'])
    parser.add_argument('--method',choices=['swe','matchfix']);args=parser.parse_args()
    preflight() if args.command=='preflight' else execute(args.method)
