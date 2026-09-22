"""Offline audit of completed candidate paths; no changes to frozen decisions."""
import json
from pathlib import Path
import sys

BASE=Path(__file__).resolve().parent
RUN=BASE/'development_v2'
PYTHON=Path('/media/main/whj/miniconda3/envs/torchax311/bin/python')


def main():
    sys.path.insert(0,str(RUN/'code_snapshot'))
    from autofix.autonomous.sandbox import run_isolated
    rows=[]
    for task in ('task_001','task_002'):
        for method in ('autonomous_layered','direct_shared_tools'):
            folder=RUN/'conditions'/task/method
            if not (folder/'result.json').exists():continue
            result=json.loads((folder/'result.json').read_text())
            if result['status']=='running':continue
            for seed in (7101,7102,7103):
                proc=run_isolated(folder/'workspace',PYTHON,BASE/'audit_worker.py',timeout=180,
                                  extra_reads=[str(PYTHON.resolve().parent.parent)],args=[str(folder/'workspace'),str(seed)])
                try: observation=json.loads(proc['stdout'].strip().splitlines()[-1])
                except Exception:observation={'status':'failed','accepted':False}
                rows.append({'task':task,'method':method,'seed':seed,'process':proc,'audit':observation})
                (RUN/'additional_backend_audit.json').write_text(json.dumps(rows,indent=2)+'\n')
                print(json.dumps({'task':task,'method':method,'seed':seed,'accepted':observation['accepted']}),flush=True)


if __name__=='__main__':main()
