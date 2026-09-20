import json,time,sys
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,'.')
from scripts.status_unified_formal_20260918 import summarize
root=Path('experiments/unified_migration50_20260918/final_review').resolve()
c=root.parent/'formal_control'
s=summarize(root)
now=time.time()
s['checked_at']=datetime.now(timezone.utc).isoformat()
s['status_file_age_seconds']=now-(c/'status.json').stat().st_mtime
jobs={j['id']:j for j in json.loads((c/'plan.json').read_text())}
adapters={'ladim':'autonomous_layered','swe':'swe_native_isolated','matchfix':'matchfix_full_orchestration','test_repair':'ordinary_test_repair'}
for a in s['active']:
 j=jobs[a['job']]
 if j['method'] in adapters: p=Path(j['review'])/'conditions'/j['task']/adapters[j['method']]
 elif j['method']=='msadapter': p=Path(j['review'])/'nonagent_conditions'/j['group']/j['method']
 else: p=root.parent/'formal_generations'/j['group']/j['method']
 files=[x for x in p.rglob('*') if x.is_file()] if p.exists() else []
 log=c/'logs'/(a['job']+'.log')
 if log.exists(): files.append(log)
 latest=max(files,key=lambda x:x.stat().st_mtime) if files else None
 responses=[x for x in files if 'response' in x.name]
 r=max(responses,key=lambda x:x.stat().st_mtime) if responses else None
 a.update(directory=str(p),latest_file=str(latest) if latest else None,latest_file_age_seconds=now-latest.stat().st_mtime if latest else None,latest_response_age_seconds=now-r.stat().st_mtime if r else None)
 start=c/'started'/(a['job']+'.json')
 a['started']=json.loads(start.read_text()) if start.exists() else None
s['scheduler_log_tail']=(c/'scheduler.log').read_text().splitlines()[-8:]
print(json.dumps(s))
