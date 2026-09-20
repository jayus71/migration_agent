"""Archive the completed two-tower trial, preserving generation and repair costs."""
import ast
import json
from pathlib import Path
import tarfile
from run_repository_twotower import RUN, ROOT, WORKER, read, save, hashes, digest


def test_structure(path):
    tree=ast.parse(path.read_text())
    result={}
    for n in ast.walk(tree):
        if isinstance(n,ast.FunctionDef) and n.name.startswith('test_'):
            result[n.name]={
                'assertions':[ast.unparse(x) for x in ast.walk(n)
                              if isinstance(x,ast.Assert) or (isinstance(x,ast.Call)
                              and isinstance(x.func,ast.Attribute) and x.func.attr.startswith('assert'))],
                'numeric_constants':[x.value for x in ast.walk(n) if isinstance(x,ast.Constant)
                                     and isinstance(x.value,(int,float)) and not isinstance(x.value,bool)],
            }
    return result


def summarize_evaluation(evaluation):
    public=evaluation.get('public',{})
    numeric=public.get('numeric',{})
    return {
        'accepted':evaluation.get('accepted'),
        'numeric_accepted':numeric.get('accepted'),
        'numeric_execution':numeric.get('execution'),
        'numeric_error':numeric.get('error'),
        'failed_numeric_checks':[k for k,v in numeric.get('checks',{}).items() if not v],
        'case_status':numeric.get('case_status'),
        'tests':public.get('tests'),
        'workflow':public.get('workflow'),
        'coverage':public.get('coverage'),
        'confirmation_seeds_executed':len(evaluation.get('confirmations',[])),
        'confirmation_results':[x.get('accepted') for x in evaluation.get('confirmations',[])],
    }


def main():
    folder=RUN/'condition';r=read(folder/'result.json');m=read(RUN/'manifest.json')
    assert r['status']!='running'
    responses=[]
    for p in sorted((folder/'evidence/agent').glob('*_response.json')):
        v=read(p);responses.append({'path':str(p.relative_to(RUN)),'sha256':digest(p),
            'usage':v.get('usage',{}),'actual_model':v.get('model'),
            'finish_reason':v.get('choices',[{}])[0].get('finish_reason')})
    keys=('prompt_tokens','completion_tokens','total_tokens','prompt_cache_hit_tokens','prompt_cache_miss_tokens')
    usage={k:sum(x['usage'].get(k,0) for x in responses) for k in keys}
    usage['reasoning_tokens']=sum(x['usage'].get('completion_tokens_details',{}).get('reasoning_tokens',0) for x in responses)
    integrity={
        'source_snapshot_unchanged':hashes(RUN/'source')==m['source_hashes'],
        'workspace_source_unchanged':hashes(folder/'workspace/source')==m['source_hashes'],
        'frozen_public_task_unchanged':digest(RUN/'task.json')==m['task_sha256'],
        'workspace_public_task_unchanged':digest(folder/'workspace/task.json')==m['task_sha256'],
        'worker_unchanged':digest(WORKER)==m['worker_sha256'],
        'controller_unchanged':digest(ROOT/'scripts/run_repository_twotower.py')==m['controller_sha256'],
        'bootstrap_unchanged':digest(ROOT/'scripts/repository_bootstrap.py')==m['bootstrap_sha256'],
        'repository_mechanism_unchanged':digest(ROOT/'autofix/autonomous/repository.py')==m['mechanism_sha256'],
        'final_target_matches':hashes(folder/'workspace/target')==r['final_target_hashes'],
        'usage_matches':all(usage[k]==r['usage'][k] for k in keys[:3]),
        'calls_have_responses':len(responses)==r['calls'],
        'fixed_model':set(x['actual_model'] for x in responses)=={'deepseek-flash'},
        'call_budget':r['calls']<=40,
        'output_budget':usage['completion_tokens']<=120000,
    }
    tests={}
    for source in sorted((RUN/'source/tests').glob('test_*.py')):
        target=folder/'workspace/target/tests'/source.name
        try:tests[source.name]={'source':test_structure(source),'target':test_structure(target)}
        except (SyntaxError,FileNotFoundError) as exc:tests[source.name]={'error':str(exc)}
    save(RUN/'test_assertion_audit.json',tests)
    summary={
        'repository':m['repository'],'source_commit':m['commit'],
        'status':r['status'],'accepted':r.get('accepted'),'error':r.get('error'),
        'calls':r['calls'],'usage':usage,'seconds':r['seconds'],
        'generation_cost_policy':'File generation, diagnosis and repair share one lifetime budget; generation is included in the reported totals.',
        'translation':r.get('translation'),
        'initial_after_translation':summarize_evaluation(r.get('initial_after_translation',{})),
        'attempts':[{'attempt':a['attempt'],'stage_status':a['stage']['status'],
                     **summarize_evaluation(a['evaluation'])} for a in r.get('attempts',[])],
        'final':summarize_evaluation(r.get('final',{})),
        'source_cases':m['source_cases'],
        'source_tests':m['source_tests'],'source_cli':m['source_cli'],
        'integrity':integrity,'integrity_passed':all(integrity.values()),
        'truncated_responses':sum(x['finish_reason']=='length' for x in responses),
        'provider_responses':responses,
        'changed_files':[k for k,v in r['final_target_hashes'].items() if m['source_hashes'].get(k)!=v],
        'zero_call_startup_failure':m.get('pre_api_setup_correction'),
        'test_assertion_review':'test_assertion_audit.json retains source and migrated assertions for separate review; test execution alone is not assertion-preservation evidence.',
    }
    save(RUN/'summary.json',summary)
    def include(info):
        return None if any(x in ('__pycache__','.pytest_cache','.runtime') for x in Path(info.name).parts) else info
    with tarfile.open(RUN/'repository-twotower-evidence.tar.gz','w:gz') as tar:
        for name in ('summary.json','manifest.json','task.json','test_assertion_audit.json',
                     'source_tests.json','source_tests.log','source_cli.json','source_cli.log',
                     'source_cli_pre_cpu_fix.json','source_fixtures.json','references',
                     'mechanism_tests.log','bootstrap_config_tests.log','run.log',
                     'condition/result.json','condition/protocol.json','condition/translation',
                     'condition/evidence/repository_state.json','zero_call_config_error'):
            p=RUN/name
            if p.exists():tar.add(p,arcname=name,filter=include)
        for p in sorted((folder/'evidence').glob('measurement_*')):
            tar.add(p,arcname=str(p.relative_to(RUN)),filter=include)
        tar.add(folder/'workspace/target',arcname='target',filter=include)
        for name in ('repository_twotower_worker.py','run_repository_twotower.py','repository_bootstrap.py',
                     'collect_repository_twotower.py','test_repository_bootstrap.py','recover_twotower_zero_call_start.py'):
            tar.add(ROOT/'scripts'/name,arcname='implementation/'+name)
        for name in ('repository','agent','tools','sandbox'):
            tar.add(ROOT/'autofix/autonomous'/(name+'.py'),arcname='implementation/'+name+'.py')
    print(json.dumps({k:summary[k] for k in ('status','accepted','calls','usage','seconds','integrity_passed','error','final')},indent=2))


if __name__=='__main__':main()
