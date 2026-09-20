"""Use our existing run's remaining budget for actual repository entrypoint coverage."""
import copy
from dataclasses import asdict
import json
import shutil
import time
import traceback
from repository_timeseries_pilot import RUN,ROOT,read,save,hashes,digest
from repository_agent_mode import RepositoryAgent,RepositoryTools
from repository_entrypoint_evaluation import RepositoryEvaluator
from autofix.autonomous.agent import AgentConfig


def main():
    folder=RUN/'conditions/ladim_repository'
    resultfile=folder/'completion_result.json'
    if resultfile.exists():raise FileExistsError('Continuation already attempted; preserve result')
    original=read(folder/'result.json')
    session=read(folder/'evidence/agent/session.json')
    state=read(folder/'evidence/repository_state.json')
    assert original['calls']==session['calls']==32
    assert len(original['attempts'])==3
    shutil.copytree(folder/'workspace/target',folder/'target_before_entrypoint_continuation')
    ev=RepositoryEvaluator(folder/'workspace',folder/'evidence/entrypoint_continuation')
    before=ev.complete_repository()
    tools=RepositoryTools(folder/'workspace',ev.tool,named_tests=('paired','workflow','public','entrypoints'),validate_syntax=True,
                           state_path=folder/'evidence/repository_state_continuation.json')
    tools.units=copy.deepcopy(state['units']);tools.active=state['active'];tools.checkpoints=copy.deepcopy(state['checkpoints']);tools.revision=state['revision'];tools._persist()
    config=AgentConfig(**session['config'])
    agent=RepositoryAgent(tools,folder/'evidence/agent_continuation',config=config)
    agent.calls=session['calls'];usage=session['usage']
    for attr,key in [('prompt_tokens','prompt_tokens'),('output_tokens','budget_output_tokens'),('measured_output_tokens','completion_tokens'),
                     ('unknown_usage_calls','unknown_usage_calls'),('unknown_prompt_usage_calls','unknown_prompt_usage_calls'),
                     ('unknown_completion_usage_calls','unknown_completion_usage_calls'),('reasoning_tokens','reasoning_tokens'),('truncated_calls','truncated_calls')]:
        setattr(agent,attr,usage[key])
    agent.actual_models=usage['actual_models'];agent.started=time.monotonic()-usage['elapsed_seconds']
    agent.history=copy.deepcopy(session['history']);agent.last_diagnosis=copy.deepcopy(session['diagnosis'])
    agent.verifier_history=copy.deepcopy(session['verifier_history']);agent.active_role=session['active_role']
    agent.tools.edit_records=copy.deepcopy(session['edit_records'])
    agent.verifier_findings=copy.deepcopy(original['diagnosis']['diagnosis'])
    agent.initial_observation=copy.deepcopy(original['initial']['observation'])
    agent.history.append({'role':'user','content':'The final repository audit now executes every notebook cell and the original sequence of instructional snippets with the same frozen data fixture. The public entrypoints test returns actual runtime observations for both. Complete this repository using the remaining lifetime budget and fourth external submission. Preserve the original core numerical and workflow acceptance. Update dependency units as needed; entrypoints may be declared as a unit test. No new initial candidate or budget reset is provided.'})
    result={'status':'running','calls_before':agent.calls,'original_acceptance':original['accepted'],'before':before,
            'remaining_calls':config.max_calls-agent.calls,'remaining_output_tokens':config.max_output_tokens-agent.output_tokens,
            'protocol_note':'Additional execution coverage within our remaining lifetime budget. Original frozen comparison results remain separate.',
            'mechanism_sha256':digest(ROOT/'scripts/repository_agent_mode.py')}
    save(resultfile,result)
    try:
        stage=agent.repair(before['observation'],attempt=4)
        final=ev.complete_repository()
        result.update(status='completed',stage=asdict(stage),final=final,accepted=final['accepted'])
    except Exception as exc:result.update(status='infrastructure_error',accepted=False,error=str(exc),traceback=traceback.format_exc())
    finally:
        result.update(calls=agent.calls,usage=agent.usage(),final_target_hashes=hashes(folder/'workspace/target'),repository_state=read(folder/'evidence/repository_state_continuation.json'))
        save(resultfile,result)
    print(json.dumps({k:result.get(k) for k in ('status','accepted','calls','usage','error')}))


if __name__=='__main__':main()
