"""Run our repository mechanism as a separate condition from the original pilot."""
from dataclasses import asdict
import argparse
import json
import shutil
import time
import traceback
from repository_timeseries_pilot import RUN,ROOT,read,save,hashes,digest
from autofix.autonomous.repository import RepositoryAgent,RepositoryTools
from repository_entrypoint_evaluation import RepositoryEvaluator
from autofix.autonomous.agent import AgentConfig


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--condition',default='ladim_repository_complete')
    args=parser.parse_args()
    if not args.condition.replace('_','').isalnum():raise ValueError('Invalid condition name')
    folder=RUN/'conditions'/args.condition
    folder.mkdir(parents=True,exist_ok=False)
    ws=folder/'workspace';ws.mkdir()
    shutil.copytree(RUN/'source',ws/'source')
    shutil.copytree(RUN/'translation/target',ws/'target')
    shutil.copy2(RUN/'task.json',ws/'task.json');(ws/'scratch_tests').mkdir()
    ev=RepositoryEvaluator(ws,folder/'evidence')
    initial=ev.complete_repository()
    config=AgentConfig(method='layered',model='deepseek-v4-flash',max_calls=40,max_output_tokens=120000,
        max_seconds=1800,per_call_output_tokens=16384,memory_policy='evidence',workflow_policy='progress_loop',diagnosis_policy='evidence',
        diagnosis_calls_per_stage=6,repair_calls_per_stage=32)
    tools=RepositoryTools(ws,ev.tool,named_tests=('paired','workflow','public','entrypoints'),validate_syntax=True,
        state_path=folder/'evidence/repository_state.json')
    agent=RepositoryAgent(tools,folder/'evidence/agent',config=config)
    save(folder/'protocol.json',{'method':'LaDiM with repository coordination','config':asdict(config),
        'initial_target_hashes':hashes(ws/'target'),'contract_sha256':digest(ws/'task.json'),
        'mechanism_sha256':digest(ROOT/'autofix/autonomous/repository.py'),
        'distinctions':['Public symbol/import inventory','Agent-defined dependency work units',
                        'Notebook cell edits','Transitive checkpoint invalidation','Unit-local context with measured checkpoint evidence'],
        'baseline_changes':None,'initial_shared_with':['ladim','swe','matchfix']})
    result={'method':args.condition,'status':'running','accepted':False,'attempts':[], 'initial':initial}
    save(folder/'result.json',result)
    started=time.monotonic()
    try:
        if initial['accepted']:
            result.update(accepted=True,status='completed',confirmation=initial['confirmations'])
        else:
            diagnosis=agent.diagnose(initial['observation']);result['diagnosis']=asdict(diagnosis)
            current=initial
            for attempt in range(1,5):
                stage=agent.repair(current['observation'],attempt)
                current=ev.complete_repository()
                passed=current['accepted']
                result['attempts'].append({'attempt':attempt,'stage':asdict(stage),'evaluation':current,'accepted':passed})
                result.update(accepted=passed,calls=agent.calls,usage=agent.usage());save(folder/'result.json',result)
                if passed:break
                if agent._budget_status() or stage.status in ('api_error','infrastructure_error','error'):break
            result.update(status='completed',final=current)
    except Exception as exc:
        result.update(status='infrastructure_error',error=str(exc),traceback=traceback.format_exc())
    finally:
        result.update(seconds=time.monotonic()-started,calls=agent.calls,usage=agent.usage(),final_target_hashes=hashes(ws/'target'),
                      repository_state=read(folder/'evidence/repository_state.json'))
        save(folder/'result.json',result)
    print(json.dumps({k:result.get(k) for k in ('method','status','accepted','calls','usage','error')}))


if __name__=='__main__':main()
