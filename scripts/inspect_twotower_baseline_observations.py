"""Inspect delivered actions and tool outcomes without model reasoning text."""
import json
from pathlib import Path
ROOT=Path('/media/main/whj/projects/torch4ms/ascend-torch4ms-repository-pilot-20260920')
RUN=ROOT/'experiments/repository_twotower_20260920/baseline_comparison'
read=lambda p:json.loads(p.read_text())
for method in ('swe','matchfix'):
    folder=RUN/method/'evidence/agent'
    requests=sorted(folder.glob('*_request.json'))
    if not requests:continue
    request=read(requests[-1]);records=[]
    for message in request.get('messages',[])[-9:]:
        if message.get('role')=='tool':
            records.append({'role':'tool','content':str(message.get('content'))[-1800:]})
        elif message.get('role')=='assistant':
            records.append({'role':'assistant','tools':[{'name':x['function']['name'],'arguments':x['function']['arguments'][:450]}
                for x in message.get('tool_calls',[])]})
    print(json.dumps({'method':method,'request':requests[-1].name,'max_tokens':request.get('max_tokens'),'recent_actions':records},indent=2))
