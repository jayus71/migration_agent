"""Resume the existing two-tower trial with the user's larger output allowance.

The first request replays the truncated request with only max_tokens changed.
Later requests append observations without rewriting the cached message prefix.
"""
from __future__ import annotations
import copy
from dataclasses import asdict, replace
import hashlib
import json
import shutil
import time
import traceback
from run_repository_twotower import RUN, ROOT, WORKER, Evaluator, RepositoryAgent, RepositoryTools, AgentConfig, read, save, hashes, digest
from autofix.autonomous.agent import AutonomousAgent, BudgetExhausted


def normalized(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,allow_nan=False)


class CachedContinuationAgent(RepositoryAgent):
    replay_request=None
    previous_prefix=None

    def complete(self,messages,**kwargs):
        if self.replay_request is not None:
            # The interrupted response executed no tools. Reuse the exact request
            # preceding it; its failed response and cost remain in the old log.
            expected=copy.deepcopy(self.replay_request)
            self.history=copy.deepcopy(expected['messages']);messages=self.history
            kwargs['tool_schemas']=copy.deepcopy(expected.get('tools'))
            proposed=self._request(False,min(self.config.per_call_output_tokens,self.config.max_output_tokens-self.output_tokens))
            proposed['messages']=copy.deepcopy(messages)
            if kwargs['tool_schemas']:proposed['tools']=copy.deepcopy(kwargs['tool_schemas'])
            else:proposed.pop('tools',None);proposed.pop('tool_choice',None)
            changes=[k for k in set(expected)|set(proposed) if expected.get(k)!=proposed.get(k)]
            if changes!=['max_tokens']:raise ValueError('Replay must change only max_tokens: '+str(changes))
            self._event('cache_prefix_replay',{
                'changed_request_fields':changes,'original_max_tokens':expected['max_tokens'],
                'new_max_tokens':proposed['max_tokens'],
                'messages_sha256':hashlib.sha256(normalized(messages).encode()).hexdigest(),
                'message_count':len(messages)})
            self.replay_request=None
        if self.previous_prefix is not None and messages[:len(self.previous_prefix)]!=self.previous_prefix:
            raise ValueError('Continuation altered previously sent messages')
        # Stop explicitly at the context limit instead of rewriting the prefix.
        if len(normalized(messages))>self.config.max_context_chars:
            raise BudgetExhausted('context_budget_exhausted')
        self.previous_prefix=copy.deepcopy(messages)
        # Retain unit planning and tools while honoring the requested stable prefix.
        return AutonomousAgent.complete(self,messages,**kwargs)


def main():
    original_folder=RUN/'condition';original=read(original_folder/'result.json')
    session=read(original_folder/'evidence/agent/session.json');manifest=read(RUN/'manifest.json')
    assert original['status']=='completed' and not original['accepted']
    assert original['calls']==session['calls']==20
    assert original['usage']['completion_tokens']==120000
    assert original['final_target_hashes']==hashes(original_folder/'workspace/target')
    for key,path in [('worker_sha256',WORKER),('controller_sha256',ROOT/'scripts/run_repository_twotower.py'),
                     ('bootstrap_sha256',ROOT/'scripts/repository_bootstrap.py'),('mechanism_sha256',ROOT/'autofix/autonomous/repository.py')]:
        assert digest(path)==manifest[key]
    request=read(original_folder/'evidence/agent/call_0020_request.json')
    response=read(original_folder/'evidence/agent/call_0020_response.json')
    assert response['choices'][0]['finish_reason']=='length'
    for p in (original_folder/'evidence/agent').glob('*_tool.json'):
        assert read(p)['data']['call']!=20,'A replay must not repeat already executed tools'
    folder=RUN/'continuation';folder.mkdir(exist_ok=False);ws=folder/'workspace';ws.mkdir()
    for name in ('source','target'):
        shutil.copytree(original_folder/'workspace'/name,ws/name,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache'))
    shutil.copy2(original_folder/'workspace/task.json',ws/'task.json')
    shutil.copytree(original_folder/'workspace/scratch_tests',ws/'scratch_tests')
    ev=Evaluator(ws,folder/'evidence')
    tools=RepositoryTools(ws,ev.tool,named_tests=('base','paired','tests','workflow','coverage','public'),
                          validate_syntax=True,state_path=folder/'evidence/repository_state.json')
    state=read(original_folder/'evidence/repository_state.json')
    tools.units=copy.deepcopy(state['units']);tools.active=state['active']
    tools.checkpoints=copy.deepcopy(state['checkpoints']);tools.revision=state['revision'];tools._persist()
    config=replace(AgentConfig(**session['config']),per_call_output_tokens=32768,max_output_tokens=240000)
    agent=CachedContinuationAgent(tools,folder/'evidence/agent',config=config)
    agent.calls=session['calls'];usage=session['usage']
    for attr,key in [('prompt_tokens','prompt_tokens'),('output_tokens','budget_output_tokens'),('measured_output_tokens','completion_tokens'),
                     ('unknown_usage_calls','unknown_usage_calls'),('unknown_prompt_usage_calls','unknown_prompt_usage_calls'),
                     ('unknown_completion_usage_calls','unknown_completion_usage_calls'),('reasoning_tokens','reasoning_tokens'),('truncated_calls','truncated_calls')]:
        setattr(agent,attr,usage[key])
    agent.actual_models=copy.deepcopy(usage['actual_models']);agent.started=time.monotonic()-usage['elapsed_seconds']
    agent.history=copy.deepcopy(session['history']);agent.last_diagnosis=copy.deepcopy(session['diagnosis'])
    agent.verifier_history=copy.deepcopy(session['verifier_history']);agent.active_role=session['active_role']
    agent.tools.edit_records=copy.deepcopy(session['edit_records'])
    agent.verifier_findings=copy.deepcopy(original['diagnosis']['diagnosis'])
    agent.initial_observation=copy.deepcopy(original['initial_after_translation']['observation'])
    for p in sorted((original_folder/'evidence/agent').glob('*_tool.json')):
        row=read(p)['data'];agent.tool_records[row['tool_call_id']]={'name':row['name'],'event':str(p),'compacted':False}
    agent.replay_request=request;agent._snapshot()
    save(folder/'protocol.json',{
        'config':asdict(config),'original_config':session['config'],'calls_before':agent.calls,'usage_before':usage,
        'authorization':'User requested a longer inference allowance and unchanged prompt prefix before the next request.',
        'budget_scope':'Cumulative: the initial 20 calls and 120000 output tokens remain charged. 40 calls and 240000 output tokens total.',
        'cache_policy':'First request differs from call 20 only in max_tokens. Later messages append to the same prefix; unit context replacement is disabled during this continuation.',
        'original_request_sha256':digest(original_folder/'evidence/agent/call_0020_request.json'),
        'initial_target_hashes':hashes(ws/'target'),'manifest_sha256':digest(RUN/'manifest.json'),
        'continuation_code_sha256':digest(ROOT/'scripts/continue_repository_twotower.py'),
        'acceptance_protocol_changed':False,
    })
    result={'status':'running','accepted':False,'calls_before':agent.calls,'attempts':[]};save(folder/'result.json',result)
    started=time.monotonic();current=original['final']
    try:
        for attempt in range(2,5):
            if agent._budget_status():break
            stage=agent.repair(current['observation'],attempt=attempt);current=ev.final()
            result['attempts'].append({'attempt':attempt,'stage':asdict(stage),'evaluation':current})
            result.update(calls=agent.calls,usage=agent.usage(),accepted=current['accepted']);save(folder/'result.json',result)
            if current['accepted'] or agent._budget_status() or stage.status in ('api_error','infrastructure_error','error'):break
        result.update(status='completed',accepted=current['accepted'],final=current)
    except Exception as exc:
        result.update(status='infrastructure_error',error=str(exc),traceback=traceback.format_exc())
    finally:
        result.update(calls=agent.calls,usage=agent.usage(),seconds=time.monotonic()-started,
                      final_target_hashes=hashes(ws/'target'),source_unchanged=hashes(ws/'source')==manifest['source_hashes'])
        save(folder/'result.json',result)
    print(json.dumps({k:result.get(k) for k in ('status','accepted','calls','usage','seconds','error')}))


if __name__=='__main__':main()
