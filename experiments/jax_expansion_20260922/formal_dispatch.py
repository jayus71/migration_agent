"""Persistent formal dispatcher; prepare a reviewable plan before launching.

Each condition runs once in its own process/workspace. No automatic retries or
budget extensions. Initial-translation costs are recorded separately and added
once per selected task to each method's end-to-end total.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time
BASE=Path(__file__).resolve().parent
RUN=BASE/'natural12_v2'
PYTHON='/media/main/whj/miniconda3/envs/torchax311/bin/python'
sys.path.insert(0,str(RUN))
from formal_runner import METHODS,check_hashes,dump,runtime,sha


def prepare_launch(workers):
    check_hashes(RUN,'pretranslation_hashes.json');check_hashes(RUN,'translated_hashes.json')
    if (RUN/'formal_launch_manifest.json').exists():raise RuntimeError('Launch plan already frozen')
    selection=json.loads((RUN/'repair_selection.json').read_text())
    cpus=sorted(os.sched_getaffinity(0))
    if len(cpus)<2*workers:raise RuntimeError('Insufficient CPU affinity groups')
    conditions=[{'task':task,'method':method} for task in selection['repair_tasks'] for method in METHODS]
    source=json.loads((RUN/'manifest.json').read_text())
    plan={'api_workers':workers,'cpu_groups':[cpus[i*2:i*2+2] for i in range(workers)],
          'conditions':conditions,'selection':selection,'dispatcher_sha256':sha(Path(__file__)),
          'manifest_sha256':sha(RUN/'manifest.json'),'selection_sha256':sha(RUN/'repair_selection.json'),
          'translated_hashes_sha256':sha(RUN/'translated_hashes.json'),
          'method_snapshot_hashes':{str(p.relative_to(RUN)):sha(p) for p in (RUN/'code_snapshot').rglob('*.py')},
          'budgets':{k:source[k] for k in ('max_calls','max_output_tokens','max_seconds','max_repair_attempts','per_call_output_tokens')},
          'max_total_repair_calls':len(conditions)*source['max_calls'],
          'max_total_repair_output_tokens':len(conditions)*source['max_output_tokens'],
          'retry_policy':'No dispatcher retry; each native method keeps its own frozen retry behavior within existing budgets.'}
    dump(RUN/'formal_launch_manifest.json',plan);print(json.dumps(plan))


def environment():
    env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',JAX_PLATFORMS='cpu',JAX_ENABLE_X64='true')
    for line in (Path.home()/'.autofix_llm_env').read_text().splitlines():
        text=line.strip()
        if text.startswith('export '):text=text[7:]
        if text.startswith('AUTOFIX_LLM_') and '=' in text:
            key,value=text.split('=',1);tokens=shlex.split(value)
            if len(tokens)==1:env[key]=tokens[0]
    if not env.get('AUTOFIX_LLM_API_KEY'):raise RuntimeError('Credential unavailable')
    return env


def check_plan(plan):
    check_hashes(RUN,'pretranslation_hashes.json');check_hashes(RUN,'translated_hashes.json')
    if sha(Path(__file__))!=plan['dispatcher_sha256']:raise RuntimeError('Dispatcher changed after plan freeze')
    for p,h in plan['method_snapshot_hashes'].items():
        if sha(RUN/p)!=h:raise RuntimeError('Method snapshot changed')
    if sha(RUN/'repair_selection.json')!=plan['selection_sha256']:raise RuntimeError('Selection changed')


def launch():
    plan=json.loads((RUN/'formal_launch_manifest.json').read_text());check_plan(plan)
    if (RUN/'formal_launch.json').exists():raise RuntimeError('Refusing duplicate launch')
    for c in plan['conditions']:
        if (RUN/'conditions'/c['task']/c['method']).exists():raise RuntimeError('Condition already exists')
    process=subprocess.Popen([PYTHON,str(Path(__file__).resolve()),'worker'],env=environment(),
          stdout=open(RUN/'formal_dispatch.log','x'),stderr=subprocess.STDOUT,start_new_session=True)
    record={'pid':process.pid,'api_workers':plan['api_workers'],'conditions':len(plan['conditions']),
            'launch_manifest_sha256':sha(RUN/'formal_launch_manifest.json'),'started_unix':time.time(),
            'log':str(RUN/'formal_dispatch.log')}
    dump(RUN/'formal_launch.json',record);print(json.dumps(record))


def summary():
    plan=json.loads((RUN/'formal_launch_manifest.json').read_text());rows=[]
    for c in plan['conditions']:
        path=RUN/'conditions'/c['task']/c['method']/'result.json'
        if not path.exists():rows.append({**c,'status':'not_started','accepted':None});continue
        result=json.loads(path.read_text());translation=json.loads((RUN/'translations'/c['task']/'result.json').read_text())
        shared=translation.get('usage') or {};repair=result.get('budget',{}).get('usage',{})
        row={**c,'status':result['status'],'accepted':result['accepted'],
             'repair_calls':result.get('budget',{}).get('calls'),'translation_usage':shared,'repair_usage':repair,
             'accepted_at_submissions':{str(a['attempt']):a['accepted'] for a in result.get('attempts',[])},
             'end_to_end_total_tokens':shared.get('total_tokens',0)+repair.get('total_tokens',0) if shared and repair and not repair.get('unknown_usage_calls',0) else None}
        rows.append(row)
    generation_rows=[json.loads(p.read_text()) for p in (RUN/'translations').glob('*/result.json')]
    generation_known=all(r.get('usage') and all(k in r['usage'] for k in ('prompt_tokens','completion_tokens','total_tokens')) for r in generation_rows)
    generation_usage={k:sum(r.get('usage',{}).get(k,0) for r in generation_rows) for k in ('prompt_tokens','completion_tokens','total_tokens')}
    totals={}
    for method in METHODS:
        method_rows=[r for r in rows if r['method']==method]
        repair_tokens=sum(r.get('repair_usage',{}).get('total_tokens',0) for r in method_rows)
        costs_known=all(r.get('repair_usage') and not r['repair_usage'].get('unknown_usage_calls',0) for r in method_rows)
        accepted=sum(r.get('accepted') is True for r in method_rows)
        totals[method]={'repair_accepted':accepted,'repair_denominator':len(plan['selection']['repair_tasks']),
                        'repair_total_tokens':repair_tokens if costs_known else None,
                        'selected_task_end_to_end_tokens':sum(r['end_to_end_total_tokens'] for r in method_rows) if all(r.get('end_to_end_total_tokens') is not None for r in method_rows) else None,
                        'shared_translation_then_repair_accepted':len(plan['selection']['initial_passes'])+accepted,
                        'source_pool_denominator':12,
                        'shared_translation_then_repair_total_tokens':generation_usage['total_tokens']+repair_tokens if costs_known and generation_known else None}
    dump(RUN/'formal_summary.json',{'source_pool_tasks':12,'selection':plan['selection'],'conditions':rows,
       'source_pool_translation_usage':generation_usage,'source_pool_translation_usage_complete':generation_known,'method_totals':totals,
       'cost_accounting':'Each selected task includes its one actual shared initial translation in each method end-to-end total; all attempted repair calls retained. Generation failures and initial passes remain in the separate full source-pool ledger.'})


def worker():
    plan=json.loads((RUN/'formal_launch_manifest.json').read_text());check_plan(plan)
    # Each thread owns one fixed CPU group and executes its queue sequentially.
    queues=[plan['conditions'][i::plan['api_workers']] for i in range(plan['api_workers'])]
    logs=RUN/'dispatch_logs';logs.mkdir(exist_ok=False)
    def run_queue(index):
        completed=[]
        for c in queues[index]:
            log=logs/f"{c['task']}__{c['method']}.log"
            command=[PYTHON,str(Path(__file__).resolve()),'condition','--task',c['task'],'--method',c['method'],'--cpu-group',','.join(map(str,plan['cpu_groups'][index]))]
            with log.open('x') as handle:result=subprocess.run(command,stdout=handle,stderr=subprocess.STDOUT)
            record={**c,'returncode':result.returncode,'log':str(log),'worker':index,'finished_unix':time.time()}
            completed.append(record);dump(RUN/f'dispatch_worker_{index}.json',completed)
            print(json.dumps(record),flush=True)
        return completed
    with ThreadPoolExecutor(max_workers=plan['api_workers']) as pool:
        for future in as_completed([pool.submit(run_queue,i) for i in range(plan['api_workers'])]):future.result()
    summary();dump(RUN/'formal_dispatch_complete.json',{'completed_unix':time.time(),'conditions':len(plan['conditions'])})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','launch','worker','condition','summary'])
    parser.add_argument('--workers',type=int,choices=[1,2],default=2);parser.add_argument('--task');parser.add_argument('--method');parser.add_argument('--cpu-group')
    args=parser.parse_args()
    if args.command=='prepare':prepare_launch(args.workers)
    elif args.command=='launch':launch()
    elif args.command=='worker':worker()
    elif args.command=='summary':summary()
    else:
        os.sched_setaffinity(0,[int(v) for v in args.cpu_group.split(',')]);experiment=runtime(RUN)
        result=experiment.run_condition(RUN,args.task,args.method,Path(PYTHON))
        print(json.dumps({'task':args.task,'method':args.method,'status':result['status'],'accepted':result['accepted'],'budget':result['budget']}),flush=True)


if __name__=='__main__':main()
