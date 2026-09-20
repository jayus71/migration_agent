"""One bounded end-to-end repository-mode trial; no baseline or historical reruns."""
from __future__ import annotations
import argparse
import ast
import copy
from dataclasses import asdict
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
import traceback
import numpy as np
from repository_timeseries_pilot import ROOT,BASE,SOURCE_PY,TARGET_PY,save,read,hashes,digest
from autofix.autonomous.repository import RepositoryAgent,RepositoryTools
from autofix.autonomous.agent import AgentConfig
from autofix.autonomous.sandbox import run_isolated

RUN=ROOT/'experiments/repository_simple_moe_20260920'
SOURCE=BASE/'repository-pilot-assessment-20260920/simple-moe'
WORKER=ROOT/'scripts/repository_moe_worker.py'
THRESHOLDS={'forward_max_abs':1e-4,'loss_abs':1e-4,'gradient_l2':.005,'update_relative_l2':.03,
            'auxiliary_values_max_abs':1e-4,'post_training_max_abs':.002}


def contract():
    return {'task_kind':'framework_migration','target_framework':'native MindSpore 2.7.2, CPU, PyNative',
      'task':'Migrate every implemented module, existing test, requirements and README of source/ to target/. target/ initially contains an unchanged source copy. All generation, investigation and repair must use the shared lifetime budget.',
      'source_read_only':True,'editable_roots':['target/','scratch_tests/'],
      'scope':'Native fallback implementation of this repository; the optional model-stack external runtime is not installed. Preserve its public native routing and linear helpers. Preserve existing public classes and implemented behavior, including existing source exception behavior. Do not add missing source algorithms.',
      'interfaces':{
        'model':'src.models.moe.MixtureOfExperts retains constructor parameters and tuple output. Use native nn.Cell and set_train(). Keep expert/router and get_config APIs.',
        'trainer':'MoETrainer retains constructor and train_epoch, evaluate, save_checkpoint and load_checkpoint signatures. Accept CPU device as a string, native nn.CrossEntropyLoss and native nn.Adam. A loader is an iterable of native tensor (x,y) batches with .dataset and __len__. Preserve reported source metric semantics. Use native value_and_grad for every training batch. Preserve checkpoint optimizer state and user metadata.',
        'parameter_map.json':'Map every source named parameter to exactly one target parameters_and_names() key with the same shape. Source initialization is loaded externally for equivalence tests.',
        'documentation':'Update installation and executable README examples for native MindSpore; preserve explanatory content. Convert all existing tests while preserving their test names and behaviors.'},
      'evaluation':{'numeric':'Three sequential trainer batches, identical source initialization; Adam lr=.001, betas=(.9,.999), epsilon=1e-8. Deterministic noise=0/dropout=0 with k=3. Also evaluate k=1,2,3 and extra leading dimensions. Three seeds verify the same candidate.',
         'workflow':'Original train/evaluate methods, multiple batches, checkpoint save/restore plus a resumed optimizer update, standalone metrics and routing helper APIs. Separate native stochastic training check uses dropout=.1/noise=.01/default clipping.',
         'source_behavior':'Compare source and target observables and original exception behavior. Source bugs are not a migration repair target.',
         'tests':'Run all converted repository tests with source framework imports prohibited.',
         'thresholds':THRESHOLDS},
      'available_dependencies':['mindspore 2.7.2','numpy 2.0.2','pytest','tqdm','tensorboard','tensorboardX','matplotlib','scikit-learn'],
      'tools':{'paired':'Deterministic numerical and public workflow observations.','workflow':'Same measured public workflow.','tests':'Execute migrated original test suite.','coverage':'File, import, original public symbol/test-name and documentation checks.','public':'All public checks.'},
      'integrity':'Do not change source, task, evaluator instrumentation or hard-code outputs. No healthy target, fault class, or repair location is supplied.'}


def compare(reference,target,request):
    checks={};measures={}
    def diff(label,left,right,threshold):
        a,b=np.asarray(left,dtype=float),np.asarray(right,dtype=float)
        value=float(np.max(np.abs(a-b))) if a.shape==b.shape and a.size else (0. if a.shape==b.shape else 1e100)
        checks[label]=bool(np.isfinite(value) and value<=threshold);measures[label]=value
    def vector(row,key):return np.concatenate([np.asarray(row[key][k],dtype=float).ravel() for k in sorted(request['initial_state'])])
    source_prev=np.concatenate([np.asarray(request['initial_state'][k]).ravel() for k in sorted(request['initial_state'])]);target_prev=source_prev.copy()
    checks['three_training_steps']=len(target['steps'])==3
    for i,(s,t) in enumerate(zip(reference['steps'],target['steps']),1):
        diff(f'step_{i}_forward',s['prediction'],t['prediction'],THRESHOLDS['forward_max_abs'])
        diff(f'step_{i}_loss',s['loss'],t['loss'],THRESHOLDS['loss_abs'])
        g=float(np.linalg.norm(vector(s,'gradients')-vector(t,'gradients')))
        checks[f'step_{i}_gradient']=bool(np.isfinite(g) and g<=THRESHOLDS['gradient_l2']);measures[f'step_{i}_gradient_l2']=g
        source_now,target_now=vector(s,'state'),vector(t,'state')
        u=float(np.linalg.norm((source_now-source_prev)-(target_now-target_prev))/max(np.linalg.norm(source_now-source_prev),1e-12))
        checks[f'step_{i}_update']=bool(np.isfinite(u) and u<=THRESHOLDS['update_relative_l2']);measures[f'step_{i}_update_relative_l2']=u
        source_prev,target_prev=source_now,target_now
        for name,value in s['report'].items():diff(f'step_{i}_report_{name}',value,t['report'][name],THRESHOLDS['auxiliary_values_max_abs'])
    for i,(s,t) in enumerate(zip(reference['forward_variants'],target['forward_variants']),1):diff(f'forward_k{i}',s,t,THRESHOLDS['post_training_max_abs'])
    checks['three_forward_variants']=len(target['forward_variants'])==3
    for i,(s,t) in enumerate(zip(reference['training_variants'],target['training_variants']),1):
        diff(f'training_forward_k{i}',s[0],t[0],THRESHOLDS['post_training_max_abs'])
        diff(f'training_auxiliary_k{i}',s[1],t[1],THRESHOLDS['auxiliary_values_max_abs'])
    checks['three_training_variants']=len(target['training_variants'])==3
    for i,(s,t) in enumerate(zip(reference['routing'],target['routing']),1):
        diff(f'route_weights_k{i}',s[0],t[0],1e-6);diff(f'route_indices_k{i}',s[1],t[1],0.)
    checks['three_routing_variants']=len(target['routing'])==3
    for name in ('utilization','capacity','entropy','correlation'):
        diff('metrics_'+name,reference['metrics'][name],target['metrics'][name],THRESHOLDS['auxiliary_values_max_abs'])
    checks['metric_collection_behavior']=reference['metrics']['collection_status']==target['metrics']['collection_status']
    for group in ('train_report','eval_report','resume_report'):
        for name,value in reference[group].items():diff(group+'_'+name,value,target[group][name],THRESHOLDS['post_training_max_abs'])
    diff('checkpoint_prediction',reference['checkpoint_prediction'],target['checkpoint_prediction'],THRESHOLDS['post_training_max_abs'])
    for name,value in reference['resume_state'].items():diff('resumed_state_'+name,value,target['resume_state'][name],1e-4)
    checks['checkpoint_metadata']=reference['checkpoint_metadata']==target['checkpoint_metadata']
    checks['model_config']=reference['model_config']==target['model_config']
    checks['stochastic_execution_finite']=target['stochastic_execution_finite']
    checks['native_autodiff']=target.get('native_autodiff_calls',0)>=8
    return {'accepted':all(checks.values()),'checks':checks,'measurements':measures}


def coverage(source,target):
    errors=[]
    def imports(text,path):
        try:
            tree=ast.parse(text,filename=path)
            for node in ast.walk(tree):
                names=[x.name for x in node.names] if isinstance(node,ast.Import) else [node.module or ''] if isinstance(node,ast.ImportFrom) else []
                if any(n.split('.')[0] in ('torch','torch4ms','torchax','jax','flax') for n in names):errors.append(path+': forbidden framework import')
            return tree
        except SyntaxError as exc:errors.append(path+': '+str(exc))
    def public_symbols(tree):
        return {n.name for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and not n.name.startswith('_')}
    for p in source.rglob('*.py'):
        rel=p.relative_to(source);q=target/rel
        if not q.exists():errors.append(str(rel)+': missing');continue
        tree=imports(q.read_text(),str(rel))
        if tree:
            missing=public_symbols(ast.parse(p.read_text()))-public_symbols(tree)
            if missing:errors.append(str(rel)+': missing public definitions '+','.join(sorted(missing)))
    for p in target.rglob('*.py'):
        if not (source/p.relative_to(target)).exists():imports(p.read_text(),str(p.relative_to(target)))
    readme=target/'README.md';requirements=target/'requirements.txt'
    if not readme.exists():errors.append('README.md missing')
    else:
        text=readme.read_text()
        if 'mindspore' not in text.lower():errors.append('README does not describe MindSpore target')
        for i,block in enumerate(re.findall(r'```python\s*\n(.*?)```',text,re.S)):imports(block,'README python block '+str(i))
        if re.search(r'pip\s+install\s+(?:[^\n]*\s)?torch(?:\s|[>=<]|$)',text):errors.append('README installs source framework')
    if not requirements.exists():errors.append('requirements.txt missing')
    else:
        lines=[x.strip().lower() for x in requirements.read_text().splitlines() if x.strip() and not x.lstrip().startswith('#')]
        if not any(x.startswith('mindspore') for x in lines):errors.append('requirements missing native target')
        if any(re.match(r'^(torch|torch4ms|torchax|model-stack)(\W|$)',x) for x in lines):errors.append('requirements retain mandatory source backend')
    return {'accepted':not errors,'errors':errors}


class Evaluator:
    def __init__(self,workspace,evidence):
        self.workspace=workspace;self.evidence=evidence;self.count=0;self.cache={}
        self.source_hashes=hashes(workspace/'source');self.task_hash=digest(workspace/'task.json')
    def worker(self,seed=101,tests=False):
        self.count+=1;folder=self.evidence/('measurement_%04d'%self.count);folder.mkdir(parents=True)
        runtime=self.workspace/'.runtime'/('measurement_%04d'%self.count);runtime.mkdir(parents=True)
        out=runtime/'result.json';args=['--repository',str(self.workspace/'target'),'--output',str(out)]
        if tests:args.append('--tests')
        else:
            reference=read(RUN/'references'/f'{seed}.json');save(runtime/'input.json',reference['request'])
            args+=['--input',str(runtime/'input.json')]
        proc=run_isolated(self.workspace,TARGET_PY,WORKER,timeout=180,args=args)
        save(folder/'execution.json',proc)
        result=read(out) if out.exists() else {'status':'error','error':'Worker did not return','traceback':proc['stdout'][-4000:]}
        save(folder/'result.json',result)
        if result['status']!='ok' or proc['returncode']:
            return {'accepted':False,'execution':'failed','error':result.get('error'),'traceback':result.get('traceback',proc['stdout'][-5000:])}
        if tests:return {'accepted':True,'execution':'ok','tests':result['tests']}
        try:return {'execution':'ok',**compare(reference['measurements'],result['measurements'],reference['request'])}
        except Exception as exc:return {'accepted':False,'execution':'failed','error':'Measurement contract mismatch: '+str(exc)}
    def evaluate(self,seed=101,full=True):
        if self.source_hashes!=hashes(self.workspace/'source') or self.task_hash!=digest(self.workspace/'task.json'):raise RuntimeError('Immutable source/task changed')
        key=(json.dumps(hashes(self.workspace/'target'),sort_keys=True),seed,full)
        if key in self.cache:return self.cache[key]
        cov=coverage(self.workspace/'source',self.workspace/'target')
        numeric=self.worker(seed);tests=self.worker(tests=True) if full else None
        accepted=numeric['accepted'] and (not full or (cov['accepted'] and tests['accepted']))
        result={'accepted':accepted,'numeric':numeric,'coverage':cov,'tests':tests}
        self.cache[key]=result;return result
    def tool(self,args):
        name=args['test']
        if name=='coverage':return coverage(self.workspace/'source',self.workspace/'target')
        if name=='tests':return self.worker(tests=True)
        if name in ('paired','workflow'):return self.evaluate(full=False)
        if name=='public':return self.evaluate()
        if name.startswith('scratch_tests/'):
            return run_isolated(self.workspace,TARGET_PY,self.workspace/name,timeout=min(args.get('timeout_seconds',120),180))
        raise ValueError('Unknown test')
    def final(self):
        public=self.evaluate();confirmations=[self.evaluate(s,False) for s in (202,303)] if public['accepted'] else []
        return {'accepted':public['accepted'] and all(c['accepted'] for c in confirmations),'public':public,'confirmations':confirmations,
                'observation':public if not public['accepted'] or all(c['accepted'] for c in confirmations) else next(c for c in confirmations if not c['accepted'])}


def prepare():
    if (RUN/'manifest.json').exists():raise FileExistsError('Preparation already frozen')
    RUN.mkdir(parents=True,exist_ok=True)
    shutil.copytree(SOURCE,RUN/'source',ignore=shutil.ignore_patterns('.git','__pycache__','.pytest_cache'))
    save(RUN/'task.json',contract());(RUN/'references').mkdir()
    for seed in (101,202,303):
        out=RUN/'references'/f'{seed}.json'
        proc=subprocess.run([str(SOURCE_PY),str(WORKER),'--source','--repository',str(RUN/'source'),'--seed',str(seed),'--output',str(out)],capture_output=True,text=True,timeout=180)
        (out.with_suffix('.log')).write_text(proc.stdout+proc.stderr)
        result=read(out)
        if proc.returncode or result['status']!='ok':raise RuntimeError('Source preflight failed: '+str(result.get('error')))
        identity=copy.deepcopy(result['measurements']);identity['native_autodiff_calls']=8
        assert compare(result['measurements'],identity,result['request'])['accepted']
        bad=copy.deepcopy(identity);bad['steps'][0]['prediction'][0][0]+=1
        assert not compare(result['measurements'],bad,result['request'])['accepted']
        bad=copy.deepcopy(identity);bad['steps'][0]['state']=result['request']['initial_state']
        assert not compare(result['measurements'],bad,result['request'])['accepted']
    proc=subprocess.run([str(SOURCE_PY),str(WORKER),'--source','--tests','--repository',str(RUN/'source'),'--output',str(RUN/'source_tests.json')],capture_output=True,text=True,timeout=180)
    (RUN/'source_tests.log').write_text(proc.stdout+proc.stderr)
    if read(RUN/'source_tests.json')['status']!='ok':raise RuntimeError('Source tests failed')
    save(RUN/'manifest.json',{'repository':'peytontolbert/simple-moe','commit':'eae129393941b3d6017ae6f4861d8e5f31c5466b',
        'source_hashes':hashes(RUN/'source'),'task_sha256':digest(RUN/'task.json'),'worker_sha256':digest(WORKER),
        'controller_sha256':digest(Path(__file__)),'mechanism_sha256':digest(ROOT/'autofix/autonomous/repository.py'),
        'backend':'deepseek-v4-flash','starting_state':'Unmodified copy of complete source repository; no external initial translation call.',
        'controls':{'identity':'passed','forward_corruption':'rejected','missing_update':'rejected'},
        'scope':'One development trial using our repository mode, native fallback runtime; no baseline runs or historical reruns.'})
    print(json.dumps({'prepared':True,'source_seeds':3,'source_tests':read(RUN/'source_tests.json')}))


def execute():
    manifest=read(RUN/'manifest.json')
    if manifest['worker_sha256']!=digest(WORKER) or manifest['controller_sha256']!=digest(Path(__file__)):raise ValueError('Code changed since preparation')
    folder=RUN/'condition';folder.mkdir(exist_ok=False);ws=folder/'workspace';ws.mkdir()
    shutil.copytree(RUN/'source',ws/'source');shutil.copytree(RUN/'source',ws/'target')
    shutil.copy2(RUN/'task.json',ws/'task.json');(ws/'scratch_tests').mkdir()
    ev=Evaluator(ws,folder/'evidence');initial=ev.final()
    config=AgentConfig(method='layered',model='deepseek-v4-flash',max_calls=40,max_output_tokens=120000,max_seconds=1800,
        per_call_output_tokens=16384,memory_policy='evidence',workflow_policy='progress_loop',diagnosis_policy='evidence',
        diagnosis_calls_per_stage=6,repair_calls_per_stage=32)
    tools=RepositoryTools(ws,ev.tool,named_tests=('paired','workflow','tests','coverage','public'),validate_syntax=True,state_path=folder/'evidence/repository_state.json')
    agent=RepositoryAgent(tools,folder/'evidence/agent',config=config)
    save(folder/'protocol.json',{'config':asdict(config),'manifest_sha256':digest(RUN/'manifest.json'),'initial_target_hashes':hashes(ws/'target')})
    result={'status':'running','accepted':False,'initial':initial,'attempts':[]};save(folder/'result.json',result);started=time.monotonic()
    try:
        result['diagnosis']=asdict(agent.diagnose(initial['observation']));current=initial
        for attempt in range(1,5):
            stage=agent.repair(current['observation'],attempt);current=ev.final()
            result['attempts'].append({'attempt':attempt,'stage':asdict(stage),'evaluation':current})
            result.update(accepted=current['accepted'],calls=agent.calls,usage=agent.usage());save(folder/'result.json',result)
            if current['accepted'] or agent._budget_status() or stage.status in ('api_error','infrastructure_error','error'):break
        result.update(status='completed',final=current)
    except Exception as exc:result.update(status='infrastructure_error',error=str(exc),traceback=traceback.format_exc())
    finally:
        result.update(seconds=time.monotonic()-started,calls=agent.calls,usage=agent.usage(),final_target_hashes=hashes(ws/'target'),
            source_unchanged=hashes(ws/'source')==manifest['source_hashes'],mechanism_unchanged=digest(ROOT/'autofix/autonomous/repository.py')==manifest['mechanism_sha256'])
        save(folder/'result.json',result)
    print(json.dumps({k:result.get(k) for k in ('status','accepted','calls','usage','seconds','error')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','run']);args=parser.parse_args()
    prepare() if args.command=='prepare' else execute()
