"""Read status and physical usage without printing requests or credentials."""
import json
from pathlib import Path
import time
from run_repository_moe import RUN

folder=RUN/'condition'
responses=sorted((folder/'evidence/agent').glob('*_response.json'))
usage={k:0 for k in ('prompt_tokens','completion_tokens','total_tokens','prompt_cache_hit_tokens','prompt_cache_miss_tokens')}
last=None
for p in responses:
    response=json.loads(p.read_text());last=response
    for key in usage:usage[key]+=response.get('usage',{}).get(key,0)
r=json.loads((folder/'result.json').read_text()) if (folder/'result.json').exists() else {}
session=json.loads((folder/'evidence/agent/session.json').read_text()) if (folder/'evidence/agent/session.json').exists() else {}
print(json.dumps({'status':r.get('status','not_started'),'accepted':r.get('accepted'),'calls':len(responses),
    'usage':usage,'response_age_seconds':round(time.time()-responses[-1].stat().st_mtime,1) if responses else None,
    'last_tools':[c['function']['name'] for c in (last or {}).get('choices',[{}])[0].get('message',{}).get('tool_calls',[])],
    'attempts':[{'attempt':a['attempt'],'stage_status':a['stage']['status'],'accepted':a['evaluation']['accepted'],
                 'numeric':a['evaluation']['public']['numeric'],'coverage':a['evaluation']['public']['coverage'],
                 'tests':a['evaluation']['public']['tests']} for a in r.get('attempts',[])],
    'error':r.get('error')},indent=2))
