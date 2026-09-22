"""Reconcile original provider usage and explain stage costs, without new calls."""
import json
from pathlib import Path

BASE=Path(__file__).resolve().parent
RUN=BASE/'development_v2'


def main():
    rows=[]
    for task in ('task_001','task_002'):
        for method in ('autonomous_layered','direct_shared_tools'):
            folder=RUN/'conditions'/task/method;result=json.loads((folder/'result.json').read_text());stages={};calls=[]
            for path in sorted((folder/'evidence/agent').glob('call_*_metadata.json')):
                meta=json.loads(path.read_text());response=json.loads(path.with_name(path.name.replace('_metadata','_response')).read_text())
                usage=response['usage'];stage=stages.setdefault(meta['stage'],{'calls':0,'prompt_tokens':0,'completion_tokens':0,'total_tokens':0})
                stage['calls']+=1
                for key in ('prompt_tokens','completion_tokens','total_tokens'):stage[key]+=usage[key]
                calls.append({'call':path.name,'stage':meta['stage'],'usage':usage,'input_characters':meta['prepared_chars']})
            aggregate={key:sum(s[key] for s in stages.values()) for key in ('calls','prompt_tokens','completion_tokens','total_tokens')}
            assert aggregate['calls']==result['budget']['calls']
            assert all(aggregate[k]==result['budget']['usage'][k] for k in ('prompt_tokens','completion_tokens','total_tokens'))
            rows.append({'task':task,'method':method,'accepted':result['accepted'],'first_submission_accepted':result['attempts'][0]['accepted'],
                         'stages':stages,'aggregate':aggregate,'calls':calls,'stage_status':result['attempts'][0]['stage']['status']})
    totals={method:{k:sum(r['aggregate'][k] for r in rows if r['method']==method) for k in ('calls','prompt_tokens','completion_tokens','total_tokens')} for method in ('autonomous_layered','direct_shared_tools')}
    (RUN/'development_summary.json').write_text(json.dumps({'rows':rows,'totals':totals,'all_usage_reconciled':True},indent=2)+'\n')
    print(json.dumps(totals))


if __name__=='__main__':main()
