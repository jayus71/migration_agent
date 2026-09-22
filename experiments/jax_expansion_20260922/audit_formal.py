"""Reconcile all raw usage, frozen inputs and final three-seed outcomes."""
import ast
from collections import Counter
import json
from pathlib import Path
import sys

BASE=Path(__file__).resolve().parent
RUN=BASE/'natural12_v2'
sys.path.insert(0,str(RUN))
from formal_runner import check_hashes,dump,runtime,Evaluator,sha
PYTHON=Path('/media/main/whj/miniconda3/envs/torchax311/bin/python')


def candidate_path_audit(path):
    text=path.read_text();imports=[];flags=[]
    try:tree=ast.parse(text)
    except SyntaxError as exc:return {'syntax':'failed','error':str(exc),'imports':[],'backend_flags':[]}
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):imports.extend(alias.name for alias in node.names)
        elif isinstance(node,ast.ImportFrom):imports.append(node.module or '')
    for name in imports:
        if name.startswith(('torch','tensorflow','source','scratch_tests')):flags.append('non-JAX production dependency: '+name)
    for term in ('pure_callback','io_callback','host_callback','ctypes','subprocess','__import__'):
        if term in text:flags.append('manual inspection required: '+term)
    return {'syntax':'ok','imports':sorted(set(imports)),'backend_flags':flags,'sha256':sha(path)}


def usage_audit(folder,result):
    totals={'prompt_tokens':0,'completion_tokens':0,'total_tokens':0};unknown=[];actual=Counter();response_count=0
    for metadata in sorted((folder/'evidence/agent').glob('call_*_metadata.json')):
        response=metadata.with_name(metadata.name.replace('_metadata','_response'))
        if not response.exists():unknown.append(response.name);continue
        raw=json.loads(response.read_text());response_count+=1;actual[raw.get('model','unknown')]+=1
        usage=raw.get('usage')
        if not usage or any(k not in usage for k in totals):unknown.append(response.name);continue
        for key in totals:totals[key]+=usage[key]
    ledger=result.get('budget',{}).get('usage',{})
    return {'raw_totals':totals,'raw_responses':response_count,'unknown_usage_files':unknown,'actual_models':dict(actual),
            'matches_reported_known_usage':all(totals[k]==ledger.get(k) for k in totals),'reported_calls':result.get('budget',{}).get('calls')}


def main():
    check_hashes(RUN,'pretranslation_hashes.json');check_hashes(RUN,'translated_hashes.json')
    runtime(RUN);plan=json.loads((RUN/'formal_launch_manifest.json').read_text())
    initial=json.loads((RUN/'initial_checks.json').read_text());selection=plan['selection']
    expected=[r['task'] for r in initial if r['accepted'] is False]
    if expected!=selection['repair_tasks']:raise RuntimeError('Repair selection differs from all initial failures')
    rows=[]
    for c in plan['conditions']:
        folder=RUN/'conditions'/c['task']/c['method'];result=json.loads((folder/'result.json').read_text());workspace=folder/'workspace'
        if result['status']=='running':raise RuntimeError('Condition still running')
        immutable=[]
        for source in (RUN/'private_inputs'/c['task']).rglob('*'):
            if not source.is_file() or source.name=='candidate.py':continue
            relative=source.relative_to(RUN/'private_inputs'/c['task']);target=workspace/relative
            immutable.append({'path':str(relative),'unchanged':target.is_file() and sha(target)==sha(source)})
        evidence=RUN/'final_audit'/c['task']/c['method']
        if evidence.exists():raise RuntimeError('Refusing to overwrite final audit')
        evaluator=Evaluator(RUN,c['task'],workspace,evidence,PYTHON)
        checks=[evaluator.paired(seed) for seed in (8101,8102,8103)]
        accepted=all(x['accepted'] for x in checks)
        row={**c,'original_accepted':result['accepted'],'audit_accepted':accepted,'acceptance_reproduced':accepted==result['accepted'],
             'immutable_files':immutable,'all_immutable':all(v['unchanged'] for v in immutable),
             'candidate_path':candidate_path_audit(workspace/'candidate.py'),'usage':usage_audit(folder,result),'checks':checks}
        rows.append(row);dump(RUN/'final_audit_summary.json',{'conditions':rows,'selection_verified':True,'complete':False})
        print(json.dumps({**c,'audit_accepted':accepted,'acceptance_reproduced':row['acceptance_reproduced'],'usage_matches':row['usage']['matches_reported_known_usage']}),flush=True)
    translations=[]
    for folder in sorted((RUN/'translations').iterdir()):
        outcome=json.loads((folder/'result.json').read_text());response=folder/'response.json'
        translations.append({'task':folder.name,**outcome,'raw_usage_matches':json.loads(response.read_text()).get('usage')==outcome.get('usage') if response.exists() else None})
    summary={'conditions':rows,'translations':translations,'selection_verified':True,'complete':True,
             'all_acceptances_reproduced':all(r['acceptance_reproduced'] for r in rows),
             'all_immutable':all(r['all_immutable'] for r in rows),
             'all_repair_usage_reconciled':all(r['usage']['matches_reported_known_usage'] for r in rows),
             'backend_flags':[{k:r[k] for k in ('task','method','candidate_path')} for r in rows if r['candidate_path']['backend_flags']]}
    dump(RUN/'final_audit_summary.json',summary)


if __name__=='__main__':main()
