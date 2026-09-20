"""Read-only evidence aggregation. No generation or evaluation is performed."""
import json, hashlib
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timezone

root=Path('experiments/unified_migration50_20260918').resolve()
review=root/'final_review'
control=root/'formal_control'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
adapters={'ladim':'autonomous_layered','swe':'swe_native_isolated','matchfix':'matchfix_full_orchestration','test_repair':'ordinary_test_repair'}
plan=read(control/'plan.json')
manifest=read(review/'manifest.json')
groups={g['group']:g['tasks'] for g in manifest['translation_reuse']}
rows=[]
calls={}
def usage(paths,owner):
    keys=[]
    for p in sorted(set(paths)):
        v=read(p)
        if 'choices' not in v: continue
        key=v.get('id') or ('sha256:'+sha(p))
        u=v.get('usage') or {}
        record={'response_id':v.get('id'),'paths':[str(p)],'owners':[owner],'model':v.get('model'),'usage':u,'response_sha256':sha(p)}
        if key in calls:
            previous=calls[key]
            assert previous['usage']==u,('Conflicting provider usage',key)
            previous['paths']=sorted(set(previous['paths']+[str(p)]))
            previous['owners']=sorted(set(previous['owners']+[owner]))
        else:calls[key]=record
        keys.append(key)
    return sorted(set(keys))
for job in plan:
    receipt_path=control/'jobs'/(job['id']+'.json')
    receipt=read(receipt_path) if receipt_path.exists() else {}
    result_path=Path(receipt['result_file']) if receipt.get('result_file') else None
    result=read(result_path) if result_path and result_path.exists() else {}
    phase=job['lane'] if job['lane']!='analyses' else ('plugin' if '_investigation__' in job['id'] else 'ablation')
    variant=Path(job['review']).name if job['lane']=='analyses' else phase
    interrupted=receipt.get('reconciliation',{}).get('classification')=='interrupted_integration_failure'
    valid=receipt.get('state')=='finished' and result.get('status')!='infrastructure_error' and not interrupted
    accepted=result.get('accepted') if valid else None
    row={'id':job['id'],'phase':phase,'variant':variant,'method':job['method'],'task':job['task'],'group':job.get('group'),'aliases':groups.get(job.get('group'),[job['task']]),'dispatch_state':receipt.get('state','pending'),'result_status':result.get('status'),'accepted':accepted,'raw_result_accepted':result.get('accepted'),'valid_terminal_outcome':valid,'interrupted':interrupted,'initially_accepted':result.get('initially_accepted'),'result_path':str(result_path) if result_path else None,'result_sha256':sha(result_path) if result_path and result_path.exists() else None,'receipt_sha256':sha(receipt_path) if receipt_path.exists() else None,'attempts':[{'attempt':a.get('attempt'),'accepted':a.get('accepted')} for a in result.get('attempts',[])],'declared_usage':result.get('budget')}
    if job['method'] in adapters:
        case=Path(job['review'])/'conditions'/job['task']/adapters[job['method']]
        paths=list(case.rglob('call_*_response.json'))
        requests=list(case.rglob('call_*_request.json'))
        if job['method']=='test_repair': paths+=list(case.glob('repair_*/response.json'))
        if job['method']=='test_repair': requests+=list(case.glob('repair_*/request.json'))
    elif job['method'] in ('direct','cte'):
        case=root/'formal_generations'/job['group']/job['method']
        paths=list(case.glob('response.json')) if job['method']=='direct' else list(case.glob('provider/call_*/response.json'))
        requests=list(case.glob('request.json')) if job['method']=='direct' else list(case.glob('provider/call_*/request.json'))
    else: paths=[];requests=[]
    row['incremental_call_keys']=usage(paths,job['id'])
    row['request_files_without_response']=[str(p) for p in requests if not p.with_name(p.name.replace('request.json','response.json')).exists()]
    rows.append(row)
reuse=read(root/'extension_reuse.json')
historical=[]
for item in reuse['rows']:
    if item['action']!='reuse_existing':continue
    row=dict(item)
    if item['method']=='direct_llm':
        p=Path(item['candidate']).parent/'response.json'
        row['call_keys']=usage([p], 'historical/direct/'+item['task']) if p.exists() else []
        row['response_path']=str(p)
    else:
        p=Path(item['result']);row['result_hash_verified']=sha(p)==item['result_sha256']
    historical.append(row)
historical_direct={r['task']:r for r in historical if r['method']=='direct_llm'}
cross_tasks={t['anonymous_id']:t['original_id'] for t in read(review/'cross_language/manifest.json')['tasks']}
direct={r['group']:r['incremental_call_keys'] for r in rows if r['phase']=='main' and r['method']=='direct'}
for row in rows:
    initial=[]
    if row['phase']=='cross_language':initial=historical_direct[cross_tasks[row['task']]]['call_keys']
    elif row['method'] in adapters:initial=direct[row['group']]
    row['end_to_end_call_keys']=sorted(set(initial+row['incremental_call_keys']))
def total(keys):
    keys=set(keys);u=Counter();missing=Counter()
    for key in keys:
        value=calls[key]['usage']
        for field in ('prompt_tokens','completion_tokens','total_tokens','prompt_cache_hit_tokens','prompt_cache_miss_tokens'):
            if value.get(field) is None:missing[field]+=1
            else:u[field]+=value[field]
    return {'observed_calls':len(keys),'usage':dict(u),'missing_usage_fields':dict(missing),'usd_cost':None}
aggregates={}
for row in rows:
    key=row['variant']+'/'+row['method']
    a=aggregates.setdefault(key,{'phase':row['phase'],'variant':row['variant'],'method':row['method'],'denominator':0,'finished':0,'accepted':0,'not_accepted_valid':0,'unmeasured_or_interrupted':0,'incremental_keys':[],'end_to_end_keys':[]})
    a['denominator']+=1;a['finished']+=row['dispatch_state']=='finished';a['accepted']+=row['accepted'] is True;a['not_accepted_valid']+=row['accepted'] is False;a['unmeasured_or_interrupted']+=row['accepted'] is None
    a['incremental_keys']+=row['incremental_call_keys'];a['end_to_end_keys']+=row['end_to_end_call_keys']
for a in aggregates.values():
    a['incremental_observed_usage']=total(a.pop('incremental_keys'));a['end_to_end_observed_usage']=total(a.pop('end_to_end_keys'))
formal_keys={k for r in rows for k in r['incremental_call_keys']}
intertrans=read(Path('/media/main/whj/projects/torch4ms/intertrans-completion-20260918/paper_results.json'))
intertrans_ids={item['response_id'] for row in intertrans['rows'] for item in row.get('response_usage_evidence',[])}
assert not intertrans_ids.intersection(calls),'Historical InterTrans response was counted elsewhere'
out={'checked_at':datetime.now(timezone.utc).isoformat(),'plan_sha256':sha(control/'plan.json'),'status':read(control/'status.json'),'formal_unique_conditions':len(rows),'main_unique_groups':len(groups),'main_alias_ids':sum(map(len,groups.values())),'aggregates':aggregates,'rows':rows,'provider_calls':calls,'formal_physical_observed_usage':total(formal_keys),'formal_plus_reused_direct_observed_usage':total(calls),'historical_reused_conditions':historical,'historical_intertrans_summary':{k:intertrans[k] for k in ('expected','completed','accepted','current_usage','historical_incomplete_usage','cumulative_usage','usd_cost','usd_cost_note')},'accounting_notes':['Physical provider responses are deduplicated by provider response ID; shared Direct generation counted once physically.','End-to-end attribution adds shared initial translation once within each method condition; these method totals must not be summed as physical spend.','Interrupted integration outcome remains in the denominator with accepted=null; raw accepted=true is initial state, not final acceptance.','Observed response usage is evidence-backed; missing responses and unrecorded transport attempts are not assigned zero usage.','No verified invoice or billing tariff is available; monetary cost is n/a.','Historical InterTrans valid outcomes and historical incomplete call costs are separately preserved.']}
print(json.dumps(out,ensure_ascii=False,indent=2))
