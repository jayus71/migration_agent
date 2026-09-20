"""Compact baseline status based on actual response and artifact records."""
import hashlib
import json
from pathlib import Path
import time

ROOT=Path('/media/main/whj/projects/torch4ms/ascend-torch4ms-repository-pilot-20260920')
RUN=ROOT/'experiments/repository_twotower_20260920'
BASELINE=RUN/'baseline_comparison'
read=lambda p:json.loads(p.read_text())
manifest=read(RUN/'manifest.json');rows=[]
for method in ('swe','matchfix'):
    folder=BASELINE/method;log=folder/'evidence/agent'
    responses=sorted(log.glob('*_response.json'));requests=sorted(log.glob('*_request.json'))
    usage={k:0 for k in ('prompt_tokens','completion_tokens','total_tokens','prompt_cache_hit_tokens','prompt_cache_miss_tokens','reasoning_tokens')}
    last={};stages={}
    for path in responses:
        last=read(path);u=last.get('usage',{})
        for key in usage:
            usage[key]+=u.get(key,0) if key!='reasoning_tokens' else u.get('completion_tokens_details',{}).get('reasoning_tokens',0)
        meta=read(path.with_name(path.name.replace('_response','_metadata')))
        stage=meta['stage'];stages[stage]=stages.get(stage,0)+1
    result=read(folder/'result.json') if (folder/'result.json').exists() else {}
    message=last.get('choices',[{}])[0].get('message',{})
    target=folder/'workspace/target'
    changes=[str(p.relative_to(target)) for p in target.rglob('*') if p.is_file()
             and not any(x.startswith('.') or x=='__pycache__' for x in p.relative_to(target).parts)
             and manifest['source_hashes'].get(p.relative_to(target).as_posix())!=hashlib.sha256(p.read_bytes()).hexdigest()]
    rows.append({'method':method,'status':result.get('status','not_started'),'accepted':result.get('accepted'),
        'requests':len(requests),'responses':len(responses),'usage':usage,'stages':stages,
        'last_response_age_seconds':round(time.time()-responses[-1].stat().st_mtime,1) if responses else None,
        'last_finish_reason':last.get('choices',[{}])[0].get('finish_reason'),
        'last_tools':[x.get('function',{}).get('name') for x in message.get('tool_calls',[])],
        'changed_files':changes,'attempts':[{'attempt':x['attempt'],'stage_status':x['stage']['status'],
            'accepted':x['evaluation']['accepted']} for x in result.get('attempts',[])],
        'error':result.get('error')})
print(json.dumps(rows,indent=2))
