from pathlib import Path
import json
import time

root=Path('/media/main/whj/projects/torch4ms/ascend-torch4ms-repository-pilot-20260920/experiments/repository_timeseries_20260920')
for folder in sorted((root/'conditions').iterdir()):
    p=folder/'result.json'
    if not p.exists():continue
    r=json.loads(p.read_text())
    responses=list((folder/'evidence/agent').rglob('*response*.json'))
    latest=max((f.stat().st_mtime for f in responses),default=None)
    print(json.dumps({'method':folder.name,'status':r.get('status','evaluated'),'accepted':r.get('accepted'),
        'calls':r.get('calls'),'response_files':len(responses),'latest_response_age_seconds':round(time.time()-latest,1) if latest else None,
        'attempts':len(r.get('attempts',[])),'error':r.get('error')},ensure_ascii=False))
