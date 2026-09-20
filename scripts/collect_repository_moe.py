"""Archive one repository trial and all model costs, including unsuccessful calls."""
import ast
import hashlib
import json
from pathlib import Path
import tarfile
from run_repository_moe import RUN,ROOT,WORKER,read,save,hashes,digest,coverage


def main():
    folder=RUN/'condition';result=read(folder/'result.json');manifest=read(RUN/'manifest.json')
    if result['status']=='running':raise RuntimeError('Trial is still running')
    responses=[]
    for p in sorted((folder/'evidence/agent').glob('*_response.json')):
        value=read(p)
        responses.append({'path':str(p.relative_to(RUN)),'sha256':digest(p),'usage':value.get('usage',{}),
                          'actual_model':value.get('model'),'finish_reason':value.get('choices',[{}])[0].get('finish_reason')})
    keys=('prompt_tokens','completion_tokens','total_tokens','prompt_cache_hit_tokens','prompt_cache_miss_tokens')
    usage={k:sum(r['usage'].get(k,0) for r in responses) for k in keys}
    edits=[];tool_counts={};error_count=0;scratch_calls=set();production_edit_calls=set();focus_calls=[]
    for p in sorted((folder/'evidence/agent').glob('*_tool.json')):
        e=read(p);payload=e.get('payload',e.get('data',e))
        name=payload.get('name',payload.get('tool','unknown'));tool_counts[name]=tool_counts.get(name,0)+1
        outcome=payload.get('result',{})
        if payload.get('error') or (isinstance(outcome,dict) and (outcome.get('error') or outcome.get('returncode',0))):error_count+=1
        args=payload.get('arguments',{})
        if name=='focus_unit':focus_calls.append({'call':payload.get('call'),'id':args.get('id')})
        if name=='run_test' and args.get('test','').startswith('scratch_tests/'):scratch_calls.add(payload.get('call'))
        if name=='edit':
            edits.append(str(p.relative_to(RUN)))
            if isinstance(outcome,dict) and any(f.get('path','').startswith('target/') for f in outcome.get('files',[])):production_edit_calls.add(payload.get('call'))
    integrity={
        'frozen_source_unchanged':hashes(RUN/'source')==manifest['source_hashes'],
        'workspace_source_unchanged':hashes(folder/'workspace/source')==manifest['source_hashes'],
        'public_contract_unchanged':digest(folder/'workspace/task.json')==manifest['task_sha256'],
        'worker_unchanged':digest(WORKER)==manifest['worker_sha256'],
        'controller_unchanged':digest(ROOT/'scripts/run_repository_moe.py')==manifest['controller_sha256'],
        'repository_mechanism_unchanged':digest(ROOT/'autofix/autonomous/repository.py')==manifest['mechanism_sha256'],
        'final_target_matches':hashes(folder/'workspace/target')==result['final_target_hashes'],
        'usage_matches':all(usage[k]==result['usage'].get(k) for k in keys[:3]),
        'calls_have_responses':len(responses)==result['calls'],
        'fixed_model':set(r['actual_model'] for r in responses)=={'deepseek-flash'},
        'call_budget':result['calls']<=40,'output_budget':usage['completion_tokens']<=120000}
    summary={'repository':manifest['repository'],'source_commit':manifest['commit'],'status':result['status'],
        'accepted':result['accepted'],'calls':result['calls'],'usage':usage,'seconds':result['seconds'],
        'generation_cost_policy':'All translation and repair inside one lifetime from unmodified source copy; no separate initial translation.',
        'integrity':integrity,'integrity_passed':all(integrity.values()),
        'attempts':[{'attempt':a['attempt'],'stage_status':a['stage']['status'],'accepted':a['evaluation']['accepted'],
                    'evaluation':a['evaluation']} for a in result.get('attempts',[])],
        'error':result.get('error'),'provider_responses':responses,'tool_counts':tool_counts,'tool_error_count':error_count,
        'scratch_execution_calls':sorted(scratch_calls),'production_edit_calls':sorted(production_edit_calls),'focus_calls':focus_calls,
        'truncated_responses':sum(r['finish_reason']=='length' for r in responses),
        'production_files_changed':[name for name,value in result['final_target_hashes'].items() if manifest['source_hashes'].get(name)!=value],
        'source_tests':read(RUN/'source_tests.json'),'controls':manifest['controls']}
    save(RUN/'summary.json',summary)
    archive=RUN/'repository-moe-evidence.tar.gz'
    with tarfile.open(archive,'w:gz') as tar:
        for name in ('summary.json','manifest.json','task.json','source_tests.json','source_tests.log','condition/result.json','condition/protocol.json','condition/evidence/repository_state.json'):
            path=RUN/name
            if path.exists():tar.add(path,arcname=name)
        tar.add(folder/'workspace/target',arcname='target',filter=lambda item:None if '__pycache__' in Path(item.name).parts else item)
        for name in ('repository_moe_worker.py','run_repository_moe.py','collect_repository_moe.py'):
            tar.add(ROOT/'scripts'/name,arcname='implementation/'+name)
        tar.add(ROOT/'autofix/autonomous/repository.py',arcname='implementation/repository.py')
    print(json.dumps({k:summary[k] for k in ('status','accepted','calls','usage','seconds','integrity_passed','production_files_changed','error')},indent=2))


if __name__=='__main__':main()
