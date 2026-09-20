"""Archive completed native baselines and compare fixed acceptance outcomes."""
from __future__ import annotations
import ast
import json
from pathlib import Path
import tarfile
from run_twotower_baselines import ROOT,RUN,BASELINE,RUNTIME,WORKER,read,save,hashes,digest,assert_frozen
from collect_repository_twotower import summarize_evaluation,test_structure


def compact_evaluation(evaluation):
    value=summarize_evaluation(evaluation)
    for key in ('tests','workflow'):
        item=value.get(key)
        if isinstance(item,dict):
            value[key]={k:v for k,v in item.items() if k not in ('stdout','traceback')}
    return value


def main():
    assert_frozen();manifest=read(RUN/'manifest.json');preparation=read(BASELINE/'preparation.json')
    rows=[];ledgers={};case_checks={};test_audits={};prefix_audits={}
    for method in ('swe','matchfix'):
        folder=BASELINE/method;r=read(folder/'result.json');assert r['status']!='running'
        protocol=read(folder/'protocol.json');log=folder/'evidence/agent';responses=[];requests=[]
        for p in sorted(log.glob('*_request.json')):
            request=read(p);requests.append((p,request))
        for p in sorted(log.glob('*_response.json')):
            v=read(p);meta=read(p.with_name(p.name.replace('_response','_metadata')))
            responses.append({'path':str(p.relative_to(BASELINE)),'sha256':digest(p),'usage':v.get('usage',{}),
                'stage':meta['stage'],'attempt':meta['attempt'],'actual_model':v.get('model'),
                'finish_reason':v.get('choices',[{}])[0].get('finish_reason')})
        keys=('prompt_tokens','completion_tokens','total_tokens','prompt_cache_hit_tokens','prompt_cache_miss_tokens')
        usage={k:sum(x['usage'].get(k,0) for x in responses) for k in keys}
        usage['reasoning_tokens']=sum(x['usage'].get('completion_tokens_details',{}).get('reasoning_tokens',0) for x in responses)
        integrity={
            'source_unchanged':hashes(folder/'workspace/source')==manifest['source_hashes'],
            'initial_target_matches_source':protocol['initial_target_hashes']==manifest['source_hashes'],
            'task_unchanged':digest(folder/'workspace/task.json')==preparation['baseline_task_sha256'],
            'final_target_matches':hashes(folder/'workspace/target')==r['final_target_hashes'],
            'calls_have_responses':len(responses)==r['calls'],
            'usage_matches':all(usage[k]==r['usage'][k] for k in keys[:3]),
            'fixed_backend':set(x['actual_model'] for x in responses)=={'deepseek-flash'},
            'fixed_requested_model':all(x.get('model')=='deepseek-v4-flash' for _,x in requests),
            'thinking_unchanged':all(x.get('thinking')=={'type':'enabled'} and x.get('reasoning_effort')=='high' for _,x in requests),
            'per_call_output_limit':all(x.get('max_tokens',0)<=32768 for _,x in requests),
            'calls_within_budget':r['calls']<=40,'outputs_within_budget':usage['completion_tokens']<=240000,
            'no_untracked_api_failures':r['usage']['unknown_usage_calls']==0,
        }
        final=r.get('final',{});numeric=final.get('public',{}).get('numeric',{})
        test_audits[method]={}
        for source in sorted((RUN/'source/tests').glob('test_*.py')):
            target=folder/'workspace/target/tests'/source.name
            try:test_audits[method][source.name]={'source':test_structure(source),'target':test_structure(target)}
            except (SyntaxError,FileNotFoundError) as exc:test_audits[method][source.name]={'error':str(exc)}
        prefix_rows=[]
        for (prior_path,prior),(path,current) in zip(requests,requests[1:]):
            a,b=prior['messages'],current['messages'];equal=0
            for x,y in zip(a,b):
                if x!=y:break
                equal+=1
            prefix_rows.append({'request':path.name,'previous_request':prior_path.name,'unchanged_prefix_messages':equal,
                'previous_messages':len(a),'system_prompt_unchanged':bool(a and b and a[0]==b[0])})
        prefix_audits[method]=prefix_rows
        changed=[k for k,v in r['final_target_hashes'].items() if manifest['source_hashes'].get(k)!=v]
        row={'method':method,'status':r['status'],'accepted':r.get('accepted'),'error':r.get('error'),
            'calls':r['calls'],'usage':usage,'seconds':r['seconds'],
            'cache_hit_fraction':usage['prompt_cache_hit_tokens']/usage['prompt_tokens'] if usage['prompt_tokens'] else None,
            'truncated_responses':sum(x['finish_reason']=='length' for x in responses),
            'initial_target':'unchanged source copy','final':compact_evaluation(final),'changed_files':changed,
            'attempts':[{'attempt':a['attempt'],'stage_status':a['stage']['status'],'accepted':a['evaluation']['accepted']} for a in r.get('attempts',[])],
            'integrity':integrity,'integrity_passed':all(integrity.values()),
            'upstream_manifest':str((log/'baseline_manifest.json').relative_to(BASELINE)),
        }
        if numeric.get('case_status'):
            row['cases']={}
            for case,status in numeric['case_status'].items():
                checks={k:v for k,v in numeric.get('checks',{}).items() if k.startswith(case+'_')}
                row['cases'][case]={'status':status,'failed_checks':[k for k,v in checks.items() if not v]}
        rows.append(row);ledgers[method]=responses;case_checks[method]=numeric.get('checks')
    runtime_integrity={name:digest(RUNTIME/'autofix/autonomous'/name)==value for name,value in preparation['baseline_runtime_hashes'].items()}
    original_integrity={name:digest(ROOT/'autofix/autonomous'/name)==value for name,value in preparation['original_runtime_hashes'].items()}
    ours=read(RUN/'continuation_summary.json')
    summary={'repository':manifest['repository'],'source_commit':manifest['commit'],
        'source_hashes':manifest['source_hashes'],'source_cases':manifest['source_cases'],
        'baseline_budget':preparation['budget'],'baselines':rows,
        'our_existing_result':{k:ours[k] for k in ('accepted','calls','usage','final','protocol_note')},
        'comparison_note':'Same raw source starting tree and final acceptance. LaDiM uses its own staged generation and was continued after a user-authorized budget increase; baselines receive the full 32768 per call / 240000 total allowance from launch. This is a single-repository development comparison, not a uniformly frozen repeated benchmark.',
        'runtime_integrity':runtime_integrity,'original_runtime_integrity':original_integrity,
        'integrity_passed':all(runtime_integrity.values()) and all(original_integrity.values()) and all(x['integrity_passed'] for x in rows),
        'baseline_physical_calls':sum(x['calls'] for x in rows),
        'baseline_physical_total_tokens':sum(x['usage']['total_tokens'] for x in rows),
    }
    save(BASELINE/'summary.json',summary);save(BASELINE/'provider_ledger.json',ledgers)
    save(BASELINE/'test_assertion_audit.json',test_audits);save(BASELINE/'prefix_audit.json',prefix_audits)
    def include(info):
        return None if any(x in ('__pycache__','.pytest_cache','.runtime','.git') for x in Path(info.name).parts) else info
    with tarfile.open(BASELINE/'twotower-baseline-evidence.tar.gz','w:gz') as tar:
        for name in ('summary.json','provider_ledger.json','prefix_audit.json','test_assertion_audit.json','preparation.json',
                     'task.json','preflight.json','preflight.log','launch_freeze.json','swe.log','matchfix.log'):
            p=BASELINE/name
            if p.exists():tar.add(p,arcname=name,filter=include)
        for method in ('swe','matchfix'):
            for name in ('result.json','protocol.json','evidence/agent/baseline_manifest.json'):
                p=BASELINE/method/name
                if p.exists():tar.add(p,arcname=method+'/'+name,filter=include)
            tar.add(BASELINE/method/'workspace/target',arcname=method+'/target',filter=include)
            for p in (BASELINE/method/'evidence').glob('measurement_*'):
                tar.add(p,arcname=str(p.relative_to(BASELINE)),filter=include)
        tar.add(RUNTIME/'autofix/autonomous',arcname='implementation/autofix/autonomous',filter=include)
        for name in ('prepare_twotower_baselines.py','run_twotower_baselines.py','collect_twotower_baselines.py'):
            tar.add(ROOT/'scripts'/name,arcname='implementation/'+name)
    print(json.dumps({'integrity_passed':summary['integrity_passed'],
        'results':[{k:x[k] for k in ('method','status','accepted','calls','usage','changed_files','attempts')} for x in rows]},indent=2))


if __name__=='__main__':main()
