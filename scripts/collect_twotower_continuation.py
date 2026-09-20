"""Collect cumulative spending, prefix equality and the continued candidate."""
import json
from pathlib import Path
import tarfile
from collect_repository_twotower import summarize_evaluation, test_structure
from run_repository_twotower import RUN, ROOT, WORKER, read, save, hashes, digest


def main():
    folder=RUN/'continuation';r=read(folder/'result.json');m=read(RUN/'manifest.json');p=read(folder/'protocol.json')
    assert r['status']!='running'
    original=read(RUN/'condition/result.json');base_summary=read(RUN/'summary.json')
    responses=[];stages={}
    for phase in ('condition','continuation'):
        for path in sorted((RUN/phase/'evidence/agent').glob('*_response.json')):
            v=read(path);metadata=read(path.with_name(path.name.replace('_response','_metadata')))
            row={'phase':phase,'stage':metadata['stage'],'path':str(path.relative_to(RUN)),'sha256':digest(path),
                 'usage':v.get('usage',{}),'actual_model':v.get('model'),'finish_reason':v.get('choices',[{}])[0].get('finish_reason')}
            responses.append(row)
            label=phase+'/'+row['stage'];stages.setdefault(label,{'calls':0,'prompt_tokens':0,'completion_tokens':0,'total_tokens':0,'reasoning_tokens':0})
            stages[label]['calls']+=1
            for key in ('prompt_tokens','completion_tokens','total_tokens'):stages[label][key]+=row['usage'].get(key,0)
            stages[label]['reasoning_tokens']+=row['usage'].get('completion_tokens_details',{}).get('reasoning_tokens',0)
    keys=('prompt_tokens','completion_tokens','total_tokens','prompt_cache_hit_tokens','prompt_cache_miss_tokens')
    usage={k:sum(x['usage'].get(k,0) for x in responses) for k in keys}
    usage['reasoning_tokens']=sum(x['usage'].get('completion_tokens_details',{}).get('reasoning_tokens',0) for x in responses)
    requests=sorted((folder/'evidence/agent').glob('*_request.json'))
    first=read(requests[0]);previous=read(RUN/'condition/evidence/agent/call_0020_request.json')
    changes=[key for key in set(first)|set(previous) if first.get(key)!=previous.get(key)]
    prefixes=[];sent=first['messages']
    for request_path in requests[1:]:
        current=read(request_path)['messages']
        prefixes.append({'request':request_path.name,'prior_messages_unchanged':current[:len(sent)]==sent,
                         'prior_message_count':len(sent),'current_message_count':len(current)})
        sent=current
    integrity={
        'original_completed_record_integrity':base_summary['integrity_passed'],
        'original_target_unchanged':hashes(RUN/'condition/workspace/target')==original['final_target_hashes'],
        'source_unchanged':hashes(folder/'workspace/source')==m['source_hashes'],
        'task_unchanged':digest(folder/'workspace/task.json')==m['task_sha256'],
        'worker_unchanged':digest(WORKER)==m['worker_sha256'],
        'controller_unchanged':digest(ROOT/'scripts/run_repository_twotower.py')==m['controller_sha256'],
        'bootstrap_unchanged':digest(ROOT/'scripts/repository_bootstrap.py')==m['bootstrap_sha256'],
        'repository_mechanism_unchanged':digest(ROOT/'autofix/autonomous/repository.py')==m['mechanism_sha256'],
        'continuation_code_unchanged':digest(ROOT/'scripts/continue_repository_twotower.py')==p['continuation_code_sha256'],
        'same_checkpoint_target':p['initial_target_hashes']==original['final_target_hashes'],
        'final_target_matches':hashes(folder/'workspace/target')==r['final_target_hashes'],
        'replay_only_max_tokens_changed':changes==['max_tokens'],
        'later_prefixes_unchanged':all(x['prior_messages_unchanged'] for x in prefixes),
        'usage_matches':all(usage[k]==r['usage'][k] for k in keys[:3]),
        'calls_have_responses':len(responses)==r['calls'],
        'fixed_model':set(x['actual_model'] for x in responses)=={'deepseek-flash'},
        'cumulative_call_budget':r['calls']<=40,
        'cumulative_output_budget':usage['completion_tokens']<=240000,
    }
    tests={}
    for source in sorted((RUN/'source/tests').glob('test_*.py')):
        target=folder/'workspace/target/tests'/source.name
        try:tests[source.name]={'source':test_structure(source),'target':test_structure(target)}
        except (SyntaxError,FileNotFoundError) as exc:tests[source.name]={'error':str(exc)}
    save(folder/'test_assertion_audit.json',tests)
    summary={
        'repository':m['repository'],'source_commit':m['commit'],'status':r['status'],'accepted':r.get('accepted'),'error':r.get('error'),
        'calls':r['calls'],'new_calls':r['calls']-original['calls'],'usage':usage,
        'new_usage':{k:usage[k]-base_summary['usage'][k] for k in usage},
        'cumulative_active_seconds':original['seconds']+r['seconds'],'continuation_seconds':r['seconds'],
        'cost_by_stage':stages,'first_replay_changed_request_fields':changes,
        'first_replay_original_max_tokens':previous['max_tokens'],'first_replay_new_max_tokens':first['max_tokens'],
        'first_replay_usage':next(x['usage'] for x in responses if x['phase']=='continuation'),
        'prefix_audit':prefixes,'final':summarize_evaluation(r.get('final',{})),
        'attempts':[{'attempt':x['attempt'],'stage_status':x['stage']['status'],**summarize_evaluation(x['evaluation'])} for x in r.get('attempts',[])],
        'integrity':integrity,'integrity_passed':all(integrity.values()),
        'source_cases':m['source_cases'],'truncated_responses':sum(x['finish_reason']=='length' for x in responses),
        'changed_files':[name for name,value in r['final_target_hashes'].items() if m['source_hashes'].get(name)!=value],
        'provider_responses':responses,
        'protocol_note':'User-authorized continuation with increased output allowance and append-only message prefix; cumulative costs retain all initial truncated generations. Separate from the original 120000-output result.',
    }
    save(RUN/'continuation_summary.json',summary)
    def include(info):return None if any(x in ('__pycache__','.pytest_cache','.runtime') for x in Path(info.name).parts) else info
    with tarfile.open(RUN/'repository-twotower-continuation-evidence.tar.gz','w:gz') as tar:
        for name in ('continuation_summary.json','manifest.json','task.json','continuation/result.json','continuation/protocol.json',
                     'continuation/test_assertion_audit.json','continuation/evidence/repository_state.json','continuation_offline_tests.log','continuation.log'):
            path=RUN/name
            if path.exists():tar.add(path,arcname=name,filter=include)
        for path in sorted((folder/'evidence').glob('measurement_*')):
            tar.add(path,arcname=str(path.relative_to(RUN)),filter=include)
        for path in (folder/'evidence/agent').glob('*_cache_prefix_replay.json'):
            tar.add(path,arcname=str(path.relative_to(RUN)))
        tar.add(folder/'workspace/target',arcname='target',filter=include)
        for name in ('continue_repository_twotower.py','collect_twotower_continuation.py','test_repository_budget_continuation.py'):
            tar.add(ROOT/'scripts'/name,arcname='implementation/'+name)
    print(json.dumps({key:summary[key] for key in ('status','accepted','calls','new_calls','usage','new_usage','integrity_passed','error')},indent=2))


if __name__=='__main__':main()
