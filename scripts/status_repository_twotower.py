"""Read two-tower progress and actual billed usage without request payloads."""
import json
import time
from run_repository_twotower import RUN, read

folder=RUN/('continuation' if (RUN/'continuation/result.json').exists() else 'condition')
responses=sorted((RUN/'condition/evidence/agent').glob('*_response.json'))
if folder.name=='continuation':responses+=sorted((folder/'evidence/agent').glob('*_response.json'))
keys=('prompt_tokens','completion_tokens','total_tokens','prompt_cache_hit_tokens','prompt_cache_miss_tokens')
usage={key:0 for key in keys};last={}
for path in responses:
    last=read(path)
    for key in keys:usage[key]+=last.get('usage',{}).get(key,0)
result=read(folder/'result.json') if (folder/'result.json').exists() else {}
translation=read(RUN/'condition/translation/result.json') if (RUN/'condition/translation/result.json').exists() else {}
tools=sorted((folder/'evidence/agent').glob('*_tool.json'))
last_tool=read(tools[-1]).get('data',{}) if tools else {}
recent_tests={}
for path in tools:
    row=read(path).get('data',{})
    if row.get('name')!='run_test':continue
    outcome=row.get('result',{});numeric=outcome.get('numeric',outcome)
    recent_tests[row.get('arguments',{}).get('test')]=dict(
        call=row.get('call'),accepted=outcome.get('accepted'),error=numeric.get('error'),
        failed_checks=[k for k,v in numeric.get('checks',{}).items() if not v],
        case_status=numeric.get('case_status'),coverage_errors=outcome.get('errors'),
        tests=outcome.get('tests',{}).get('tests') if isinstance(outcome.get('tests'),dict) else None)
print(json.dumps({
    'phase':folder.name,'status':result.get('status','not_started'),'accepted':result.get('accepted'),
    'responses':len(responses),'usage':usage,
    'response_age_seconds':round(time.time()-responses[-1].stat().st_mtime,1) if responses else None,
    'last_finish_reason':last.get('choices',[{}])[0].get('finish_reason'),
    'last_tools':[x['function']['name'] for x in last.get('choices',[{}])[0].get('message',{}).get('tool_calls',[])],
    'translation':{k:translation.get(k) for k in ('status','calls','output_tokens','planned_units','unattempted_units','written_units')},
    'attempts':[{'attempt':a['attempt'],'stage_status':a['stage']['status'],'accepted':a['evaluation']['accepted']} for a in result.get('attempts',[])],
    'recent_tests':recent_tests,
    'last_tool':{'call':last_tool.get('call'),'name':last_tool.get('name'),'error':last_tool.get('result',{}).get('error'),
                 'arguments':{k:v for k,v in last_tool.get('arguments',{}).items() if k in ('path','id','test')},
                 'edited_files':[x.get('path') for x in last_tool.get('result',{}).get('files',[]) if isinstance(x,dict)]},
    'error':result.get('error'),
},indent=2))
