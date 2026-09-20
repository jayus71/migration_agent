"""Complete two-tower source collection, bounded translation, repository repair."""
from __future__ import annotations
import argparse
import ast
import copy
from dataclasses import asdict
import json
from pathlib import Path
import shutil
import subprocess
import time
import traceback
import numpy as np
from repository_timeseries_pilot import ROOT,BASE,SOURCE_PY,TARGET_PY,save,read,hashes,digest
from autofix.autonomous.repository import RepositoryAgent,RepositoryTools
from autofix.autonomous.agent import AgentConfig
from autofix.autonomous.sandbox import run_isolated
from repository_bootstrap import bootstrap
from run_repository_moe import coverage

RUN=ROOT/'experiments/repository_twotower_20260920'
SOURCE=BASE/'repository-pilot-assessment-20260920/two_tower_models'
WORKER=ROOT/'scripts/repository_twotower_worker.py'
THRESHOLDS={'embedding_max_abs':1e-4,'loss_atol':.002,'loss_rtol':.0001,'gradient_atol':.0001,'gradient_rtol':.005,'update_relative_l2':.03}


def contract():
    return {'task_kind':'framework_migration','target_framework':'native MindSpore 2.7.2 CPU PyNative',
        'task':'Translate the full source repository, then investigate and repair observed failures. Preserve all original files, public class/function signatures, existing source behavior and limitations. Source and task are read-only; edit only target/ and scratch_tests/.',
        'scope':'All implemented retrieval, history encoding, debiasing, reward wrapper, ranking wrappers, original tests, training CLI, packaging and README. Preserve source exceptions and unimplemented returns; do not invent missing algorithms.',
        'native_contract':'Use native nn.Cell forward computation and value_and_grad in train.train.train_one_epoch. No torch, torch4ms, torchax, JAX or Flax execution in target. NumPy is permitted only for initialization, data handling and fixed constants.',
        'interfaces':{'train.train.train_one_epoch':'Keep (model,dataloader,optimizer,device), accept native nn.Adam and device string CPU. One native value_and_grad per training batch, preserve source training loss and averaging.',
            'models':'Preserve constructors, public methods and names of model attributes such as mips_module.corpus. Framework-specific forward/train dispatch can change to construct/set_train.',
            'parameter_map.json':'JSON {"shared": {source_parameter_name: target_parameter_name}, "cases": {case_name: {optional overrides}}}. Covers each source named parameter once, same shape; union of shared source names is supplied. Target parameters_and_names() must have a bijection for each case. Public case names: base,history,position,user,debias,reward,ranker,distillation.',
            'tests':'Preserve every original test name and its behavioral assertions. Exact-value source tests require the same source-derived initial parameters; the public initializations below supply them. Do not change expected outputs or tolerances to make tests pass.',
            'README':'Update framework and installation instructions. Preserve the descriptions and existing source limitations.',
            'requirements.txt':'List native target dependencies; do not require source framework.'},
        'acceptance':{'numeric':'For each source-executable model variant: retrieval indices, user/item embeddings, losses, gradients and three Adam updates from identical source-derived initial parameters and corpus. Adam lr=.001, beta1=.9,beta2=.999,eps=1e-8. Three seeds verify the same candidate. Labels are [4,2]; user/item feature widths 3; embedding width 4; history length 3.',
             'source_boundary':'Source exceptions and None returns are recorded separately from executable functionality. Preserve their behavior; they do not count as completed ranking or distillation algorithms.',
             'entrypoints':'Run all ten original migrated tests and the training CLI for one CPU epoch on 16 synthetic examples, batch size 8. Complete file/import/documentation checks.',
             'thresholds':THRESHOLDS},
        'available_dependencies':['mindspore 2.7.2','numpy 2.0.2','pytest','setuptools'],
        'tools':{'paired':'Public numeric and original train_one_epoch checks for source-executable variants.','base':'Base model numeric and trainer checks only.','tests':'All original migrated tests.','workflow':'Training CLI.','coverage':'File, symbol, test-name and framework checks.','public':'All public checks.'}}


def compare(reference,target,request):
    checks={};measurements={};case_status={}
    def arrays(label,left,right,atol,rtol=0.):
        a,b=np.asarray(left,dtype=float),np.asarray(right,dtype=float)
        ok=a.shape==b.shape and np.isfinite(b).all() and np.allclose(a,b,atol=atol,rtol=rtol)
        checks[label]=bool(ok)
        measurements[label]=float(np.max(np.abs(a-b))) if a.shape==b.shape and a.size else (0. if a.shape==b.shape else 1e100)
    for name,src in reference.items():
        dst=target.get(name,{})
        if dst.get('status')=='error' or 'inference' not in dst or 'training' not in dst:
            checks[name+'_execution']=False;case_status[name]=dst;continue
        case_status[name]={k:{'source':src[k]['status'],'target':dst[k]['status']} for k in ('inference','training')}
        for kind in ('inference','training'):
            s,t=src[kind],dst[kind]
            checks[name+'_'+kind+'_status']=s['status']==t['status']
            if s['status']=='raises':checks[name+'_'+kind+'_exception']=s.get('error_type')==t.get('error_type')
        if src['inference']['status']=='ok' and dst['inference']['status']=='ok':arrays(name+'_retrieval',src['inference']['recommendations'],dst['inference']['recommendations'],0.)
        if src['training']['status']!='ok' or dst['training']['status']!='ok':continue
        s_steps=src['training']['steps'];t_steps=dst['training']['steps'];checks[name+'_three_steps']=len(t_steps)==3
        keys=sorted(request['cases'][name]['initial_state'])
        vector=lambda values:np.concatenate([np.asarray(values[k],dtype=float).ravel() for k in keys])
        s_before=vector(request['cases'][name]['initial_state']);t_before=s_before.copy()
        for i,(s,t) in enumerate(zip(s_steps,t_steps),1):
            prefix=name+'_step'+str(i)
            for value in ('user_embedding','item_embedding'):arrays(prefix+'_'+value,s[value],t[value],THRESHOLDS['embedding_max_abs'])
            for value in ('loss','epoch_loss'):arrays(prefix+'_'+value,s[value],t[value],THRESHOLDS['loss_atol'],THRESHOLDS['loss_rtol'])
            sg,tg=vector(s['gradients']),vector(t['gradients'])
            arrays(prefix+'_gradient',sg,tg,THRESHOLDS['gradient_atol'],THRESHOLDS['gradient_rtol'])
            sn,tn=vector(s['state']),vector(t['state'])
            delta=float(np.linalg.norm((sn-s_before)-(tn-t_before))/max(np.linalg.norm(sn-s_before),1e-12))
            checks[prefix+'_update']=bool(np.isfinite(delta) and delta<=THRESHOLDS['update_relative_l2']);measurements[prefix+'_update_relative_l2']=delta
            s_before,t_before=sn,tn
        checks[name+'_native_autodiff']=dst['training'].get('native_autodiff_calls',0)>=3
    return {'accepted':all(checks.values()),'checks':checks,'measurements':measurements,'case_status':case_status}


def file_coverage(source,target):
    result=coverage(source,target)
    for p in source.rglob('test_*.py'):
        q=target/p.relative_to(source)
        if not q.exists():continue
        try:
            expected={n.name for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')}
            actual={n.name for n in ast.walk(ast.parse(q.read_text())) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')}
            if expected!=actual:result['errors'].append(str(p.relative_to(source))+': original test names changed')
        except SyntaxError:pass
    result['accepted']=not result['errors'];return result


class Evaluator:
    def __init__(self,workspace,evidence):
        self.workspace=workspace;self.evidence=evidence;self.count=0;self.cache={}
        self.source_hashes=hashes(workspace/'source');self.task_hash=digest(workspace/'task.json')
    def worker(self,mode='numeric',seed=101,case=None):
        self.count+=1;folder=self.evidence/('measurement_%04d'%self.count);folder.mkdir(parents=True)
        runtime=self.workspace/'.runtime'/('measurement_%04d'%self.count);runtime.mkdir(parents=True)
        out=runtime/'result.json';args=['--repository',str(self.workspace/'target'),'--mode',mode,'--output',str(out)]
        if mode=='numeric':
            reference=read(RUN/'references'/f'{seed}.json');save(runtime/'input.json',reference['request'])
            args+=['--input',str(runtime/'input.json')]
        if case:args+=['--case',case]
        proc=run_isolated(self.workspace,TARGET_PY,WORKER,timeout=180,args=args)
        save(folder/'execution.json',proc);result=read(out) if out.exists() else {'status':'error','error':'No measurement','traceback':proc['stdout'][-5000:]}
        save(folder/'result.json',result)
        if proc['returncode'] or result['status']!='ok':return {'accepted':False,'execution':'failed','error':result.get('error'),'traceback':result.get('traceback',proc['stdout'][-5000:])}
        if mode!='numeric':return {'accepted':result['accepted'],'execution':'ok',mode:result,'stdout':proc['stdout'][-6000:]}
        try:
            ref={case:reference['cases'][case]} if case else reference['cases']
            return {'execution':'ok',**compare(ref,result['cases'],reference['request'])}
        except Exception as exc:return {'accepted':False,'execution':'failed','error':'Measurement mismatch: '+str(exc)}
    def evaluate(self,seed=101,full=True):
        if self.source_hashes!=hashes(self.workspace/'source') or self.task_hash!=digest(self.workspace/'task.json'):raise RuntimeError('Immutable input modified')
        key=(json.dumps(hashes(self.workspace/'target'),sort_keys=True),seed,full)
        if key in self.cache:return self.cache[key]
        numeric=self.worker(seed=seed);cov=file_coverage(self.workspace/'source',self.workspace/'target')
        tests=self.worker('tests') if full else None;workflow=self.worker('cli') if full else None
        accepted=numeric['accepted'] and (not full or (cov['accepted'] and tests['accepted'] and workflow['accepted']))
        result={'accepted':accepted,'numeric':numeric,'coverage':cov,'tests':tests,'workflow':workflow}
        self.cache[key]=result;return result
    def tool(self,args):
        name=args['test']
        if name=='coverage':return file_coverage(self.workspace/'source',self.workspace/'target')
        if name=='base':return self.worker(case='base')
        if name=='tests':return self.worker('tests')
        if name=='workflow':return self.worker('cli')
        if name=='paired':return self.evaluate(full=False)
        if name=='public':return self.evaluate()
        if name.startswith('scratch_tests/'):return run_isolated(self.workspace,TARGET_PY,self.workspace/name,timeout=min(args.get('timeout_seconds',120),180))
        raise ValueError('Unknown public test')
    def final(self):
        current=self.evaluate();confirmations=[self.evaluate(s,False) for s in (202,303)] if current['accepted'] else []
        accepted=current['accepted'] and all(r['accepted'] for r in confirmations)
        observation=current if not current['accepted'] or all(r['accepted'] for r in confirmations) else next(r for r in confirmations if not r['accepted'])
        return {'accepted':accepted,'public':current,'confirmations':confirmations,'observation':observation}


def prepare():
    if (RUN/'manifest.json').exists():raise FileExistsError('Prepared experiment already exists')
    RUN.mkdir(parents=True,exist_ok=True)
    if not (RUN/'source').exists():shutil.copytree(SOURCE,RUN/'source',ignore=shutil.ignore_patterns('.git','__pycache__','.pytest_cache'))
    if hashes(SOURCE)!=hashes(RUN/'source'):raise ValueError('Source snapshot changed during preflight')
    (RUN/'references').mkdir(exist_ok=True);metadata={}
    for seed in (101,202,303):
        out=RUN/'references'/f'{seed}.json'
        if not out.exists():
            proc=subprocess.run([str(SOURCE_PY),str(WORKER),'--source','--repository',str(RUN/'source'),'--seed',str(seed),'--output',str(out)],capture_output=True,text=True,timeout=180)
            out.with_suffix('.log').write_text(proc.stdout+proc.stderr)
        r=read(out)
        if r['status']!='ok' or any(v.get('status')=='error' for v in r['cases'].values()):raise RuntimeError('Source model preflight failed')
        identity=copy.deepcopy(r['cases'])
        for name,case in identity.items():
            if case['training']['status']=='ok':case['training']['native_autodiff_calls']=3
        assert compare(r['cases'],identity,r['request'])['accepted']
        bad=copy.deepcopy(identity);bad['base']['training']['steps'][0]['loss']+=1
        assert not compare(r['cases'],bad,r['request'])['accepted']
        bad=copy.deepcopy(identity);bad['base']['training']['steps'][0]['state']=r['request']['cases']['base']['initial_state']
        assert not compare(r['cases'],bad,r['request'])['accepted']
        for case,values in r['request']['cases'].items():metadata[case]={k:list(np.asarray(v).shape) for k,v in values['initial_state'].items()}
    for mode in ('tests','cli','fixtures'):
        out=RUN/('source_'+mode+'.json')
        if out.exists() and read(out)['status']=='ok' and read(out).get('accepted',True):continue
        if out.exists():shutil.copy2(out,out.with_name(out.stem+'_pre_cpu_fix.json'))
        proc=subprocess.run([str(SOURCE_PY),str(WORKER),'--source','--mode',mode,'--repository',str(RUN/'source'),'--output',str(out)],capture_output=True,text=True,timeout=180)
        out.with_suffix('.log').write_text(proc.stdout+proc.stderr)
        if proc.returncode or read(out)['status']!='ok' or not read(out).get('accepted',True):raise RuntimeError('Source '+mode+' failed')
    task=contract();task['source_parameter_metadata']=metadata;task['public_test_initializations']=read(RUN/'source_fixtures.json')['source_test_initializations']
    save(RUN/'task.json',task)
    source_status={name:{key:value[key]['status'] for key in ('inference','training')} for name,value in read(RUN/'references/101.json')['cases'].items()}
    save(RUN/'manifest.json',{'repository':'gauravchak/two_tower_models','commit':'cf86221775efec3184e83b9417bf9daeddc4e057',
        'source_hashes':hashes(RUN/'source'),'task_sha256':digest(RUN/'task.json'),'worker_sha256':digest(WORKER),
        'controller_sha256':digest(Path(__file__)),'bootstrap_sha256':digest(ROOT/'scripts/repository_bootstrap.py'),
        'mechanism_sha256':digest(ROOT/'autofix/autonomous/repository.py'),'source_cases':source_status,
        'offline_controls':{'identity':'passed','loss_corruption':'rejected','missing_update':'rejected'},
        'source_tests':read(RUN/'source_tests.json'),'source_cli':read(RUN/'source_cli.json'),
        'trial':'One full-file migration with source-executable scope recorded, our method only. Shared generation/repair budget; no baseline changes.'})
    print(json.dumps({'prepared':True,'source_cases':source_status,'source_tests_passed':read(RUN/'source_tests.json')['accepted']}))


def execute():
    manifest=read(RUN/'manifest.json')
    for key,p in [('worker_sha256',WORKER),('controller_sha256',Path(__file__)),('bootstrap_sha256',ROOT/'scripts/repository_bootstrap.py'),('mechanism_sha256',ROOT/'autofix/autonomous/repository.py')]:
        if digest(p)!=manifest[key]:raise ValueError('Prepared code hash changed: '+key)
    folder=RUN/'condition';folder.mkdir(exist_ok=False);ws=folder/'workspace';ws.mkdir()
    shutil.copytree(RUN/'source',ws/'source');shutil.copytree(RUN/'source',ws/'target');shutil.copy2(RUN/'task.json',ws/'task.json');(ws/'scratch_tests').mkdir()
    ev=Evaluator(ws,folder/'evidence');config=AgentConfig(method='layered',model='deepseek-v4-flash',max_calls=40,max_output_tokens=120000,max_seconds=1800,
        per_call_output_tokens=16384,memory_policy='evidence',workflow_policy='progress_loop',diagnosis_policy='evidence',diagnosis_calls_per_stage=4,repair_calls_per_stage=24)
    tools=RepositoryTools(ws,ev.tool,named_tests=('base','paired','tests','workflow','coverage','public'),validate_syntax=True,state_path=folder/'evidence/repository_state.json')
    agent=RepositoryAgent(tools,folder/'evidence/agent',config=config)
    save(folder/'protocol.json',{'config':asdict(config),'manifest_sha256':digest(RUN/'manifest.json'),'generation_output_cap':80000,'generation_call_cap':20,
        'budget_scope':'All file generation, diagnosis and repair share the same 40 calls / 120000 output tokens; no extra paid initial generation.'})
    result={'status':'running','accepted':False,'attempts':[]};save(folder/'result.json',result);started=time.monotonic()
    try:
        result['translation']=bootstrap(agent,ws,read(ws/'task.json'),save,folder/'translation')
        current=ev.final();result['initial_after_translation']=current
        result.update(calls=agent.calls,usage=agent.usage());save(folder/'result.json',result)
        if not current['accepted'] and not agent._budget_status():
            result['diagnosis']=asdict(agent.diagnose(current['observation']))
            for attempt in range(1,5):
                if agent._budget_status():break
                stage=agent.repair(current['observation'],attempt);current=ev.final()
                result['attempts'].append({'attempt':attempt,'stage':asdict(stage),'evaluation':current})
                result.update(calls=agent.calls,usage=agent.usage(),accepted=current['accepted']);save(folder/'result.json',result)
                if current['accepted'] or agent._budget_status() or stage.status in ('api_error','infrastructure_error','error'):break
        result.update(status='completed',accepted=current['accepted'],final=current)
    except Exception as exc:result.update(status='infrastructure_error',error=str(exc),traceback=traceback.format_exc())
    finally:
        result.update(calls=agent.calls,usage=agent.usage(),seconds=time.monotonic()-started,final_target_hashes=hashes(ws/'target'),
            source_unchanged=hashes(ws/'source')==manifest['source_hashes'])
        save(folder/'result.json',result)
    print(json.dumps({k:result.get(k) for k in ('status','accepted','calls','usage','seconds','error')}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run']);args=p.parse_args()
    prepare() if args.command=='prepare' else execute()
