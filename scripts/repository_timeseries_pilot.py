"""Reproducible whole-repository pilot with shared initial translation and native controllers."""
from __future__ import annotations
import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import time
import traceback
import numpy as np

BASE=Path('/media/main/whj/projects/torch4ms')
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'experiments/repository_timeseries_20260920'
SOURCE=BASE/'repository-pilot-assessment-20260920/time-series-forecasting-pytorch'
SOURCE_PY=BASE/'repository-pilot-assessment-20260920/assessment_env/bin/python'
TARGET_PY=BASE/'repository-pilot-assessment-20260920/mindspore_env/bin/python'
WORKER=ROOT/'scripts/repository_timeseries_worker.py'
sys.path.insert(0,str(ROOT))


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')


def read(path):return json.loads(path.read_text())
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def hashes(root):
    return {p.relative_to(root).as_posix():digest(p) for p in sorted(root.rglob('*'))
            if p.is_file() and not any(x.startswith('.') or x=='__pycache__' for x in p.relative_to(root).parts)}


def protocol():
    return {
      'task_kind':'framework_migration','source_framework':'PyTorch','target_framework':'native MindSpore 2.7.2 (CPU, PyNative)',
      'source_entry':'source/project.py','target_entry':'target/project.py','source_commit':'749689e352290616e69d9b3e243af36936328964',
      'scope':'Complete repository: project.py, every step_by_step_code_blocks Python file, executable notebook code, requirements and README. Preserve original file paths and all implemented behavior; shared helpers may replace duplicated code.',
      'inputs':'The evaluator replaces the external Alpha Vantage response with 180 fixed synthetic prices. No external API key is needed for tests. Preserve download_data parsing, normalization, window size, chronological split, model architecture, optimizer, learning-rate schedule, training/validation, forecasts and five plots.',
      'source_roots':['source/'],'editable_roots':['target/','scratch_tests/'],
      'runtime':'Use native MindSpore for forward, autodiff and parameter updates. NumPy is allowed for preprocessing and visualization only. Do not import PyTorch, torch4ms, torchax or JAX in target code. Importing project must not train or fetch data; executing it must call main().',
      'public_interfaces':{
        'LSTMModel':'Retain original constructor signature and architecture as mindspore.nn.Cell. Source parameter shapes are preserved. parameter_map.json maps every original named parameter to exactly one target parameters_and_names() key.',
        'Normalizer, prepare_data_x, prepare_data_y, TimeSeriesDataset, download_data':'Preserve source behavior and public signatures.',
        'make_optimizer(model)':'Return the native target optimizer configured according to the source, initialized with the source initial learning rate. Used by both main training and the probe.',
        'train_batch(model, optimizer, x, y)':'Execute one real training batch using mindspore.value_and_grad and the supplied optimizer. Inputs are MindSpore float32 tensors. The evaluator independently observes native autodiff, parameters, predictions and gradients. This same helper must be used by run_epoch/main.',
        'learning_rate_for_epoch(epoch)':'Return the source learning rate for zero-based epoch. This schedule must be used by the real workflow.',
        'main()':'Run the original complete workflow with default config (100 epochs, dropout 0.2), print progress and generate all five figures. Return final locals as a dict including config, model, prediction (NumPy array), predicted_train and predicted_val. CLI calls main().',
        'parameter_map.json':'Object mapping source named parameter strings to native target parameter names. No omitted, extra, merged, or duplicated parameters.',
        'notebook':'Preserve the instructional progression and runnable functionality using MindSpore. Clear old execution outputs. Shared project helpers may be imported; do not leave PyTorch code in cells.'},
      'acceptance':{'preprocessing_max_abs':1e-9,'prediction_max_abs':1e-4,'loss_abs':.02,'gradient_vector_l2':.05,'parameter_update_relative_l2':.03,
        'numeric_probe':'Three sequential Adam steps from identical source-derived parameters, dropout=0, batch [4,20,1], three validation seeds. All steps must pass. Learning-rate boundaries at epochs 0,39,40,79,80.',
        'workflow':'Default 100 epochs, 128 training and 32 validation predictions, one finite next-day forecast, five plots, observed native gradients during at least 200 training batches. This is stochastic execution coverage, not cross-framework identical Dropout-mask equivalence.',
        'coverage':'All original code-bearing files present and syntactically valid; no forbidden target framework imports or unconverted notebook cells. Instructional snippets remain part of the repository; their standalone execution is not assumed by the original repo.'},
      'tools':{'paired':'Preprocessing and training-equivalence probe on the public seed.','workflow':'Full default 100-epoch workflow with local market-data fixture.','public':'Both paired and workflow tests.'},
      'integrity':'Do not modify source/, task.json, evaluator instrumentation or hard-code test outputs. Investigate and repair autonomously from source code, public contract and observed tests. No known faults or repair locations are supplied.'}


def prepare():
    if (RUN/'manifest.json').exists():raise FileExistsError('Prepared run exists; not overwriting')
    RUN.mkdir(parents=True,exist_ok=True)
    shutil.copytree(SOURCE,RUN/'source',ignore=shutil.ignore_patterns('.git','__pycache__'))
    contract=protocol();save(RUN/'task.json',contract)
    for seed in (101,202,303):
        out=RUN/'private_reference'/('%d.json'%seed);out.parent.mkdir(exist_ok=True)
        proc=subprocess.run([str(SOURCE_PY),str(WORKER),'source','--repository',str(RUN/'source'),'--seed',str(seed),'--output',str(out)],capture_output=True,text=True,timeout=120)
        (out.with_suffix('.log')).write_text(proc.stdout+proc.stderr)
        if proc.returncode or read(out)['status']!='ok':raise RuntimeError('Source reference failed: '+str(out))
        reference=read(out)
        for step in reference['reference']['steps']:
            if not np.isfinite(step['loss']):raise ValueError('Invalid source measurement')
    manifest={'source_hashes':hashes(RUN/'source'),'contract_sha256':digest(RUN/'task.json'),
              'model':'deepseek-v4-flash','thinking':'enabled','reasoning_effort':'high',
              'methods':['ladim','swe','matchfix'],'max_calls':40,'max_output_tokens':120000,'per_call_output_tokens':16384,
              'max_seconds':1800,'max_repair_attempts':4,'translation_max_tokens':32768,
              'target_python':str(TARGET_PY),'source_python':str(SOURCE_PY),'validation_seeds':[101,202,303],
              'translation_policy':'One complete initial target shared across methods; same cost attributed to each end-to-end condition.',
              'user_authorization':'目标你觉得统一为jax还是统一为mindspore更好？就先转换时间序列预测这个吧',
              'target_decision':'MindSpore matches the primary experiment; JAX reserved for separate generalization work.',
              'source_original_python_files':12,'source_notebooks':1}
    save(RUN/'manifest.json',manifest)
    payload={}
    for p in sorted((RUN/'source').rglob('*')):
        if p.suffix in ('.py','.md','.txt'):
            payload[p.relative_to(RUN/'source').as_posix()]=p.read_text()
        elif p.suffix=='.ipynb':
            nb=read(p)
            payload[p.name]={'cells':[{'cell_type':c['cell_type'],'source':''.join(c['source'])} for c in nb['cells']]}
    request={'model':manifest['model'],'thinking':{'type':'enabled'},'reasoning_effort':'high','max_tokens':32768,'stream':False,
             'messages':[{'role':'system','content':'Translate the complete supplied source repository to its designated framework, preserving its implemented behavior and public contract. Return a single JSON object {"files": {"relative/path": "complete UTF-8 file contents", ...}}. Include all translated Python files, the complete notebook JSON as a string, requirements.txt, README.md, and parameter_map.json. Assets and license are copied separately. Do not return explanations or Markdown fences.'},
                         {'role':'user','content':json.dumps({'public_contract':contract,'source_repository':payload},ensure_ascii=False)}]}
    save(RUN/'translation_request.json',request)
    print(json.dumps({'prepared':str(RUN),'source_files':len(manifest['source_hashes']),'source_probes':3}))


def coverage(target):
    import ast
    required={k for k in read(RUN/'manifest.json')['source_hashes'] if k.endswith(('.py','.ipynb'))}
    missing=sorted(k for k in required if not (target/k).is_file())
    errors=[]
    for p in sorted(target.rglob('*')):
        if not p.is_file() or '__pycache__' in p.parts:continue
        if p.is_symlink():errors.append(str(p)+' is a symlink');continue
        snippets=[]
        if p.suffix=='.py':snippets=[p.read_text()]
        elif p.suffix=='.ipynb':
            try:snippets=[''.join(c['source']) for c in read(p)['cells'] if c['cell_type']=='code']
            except Exception as exc:errors.append(p.name+': '+str(exc))
        for i,code in enumerate(snippets):
            # Notebook shell installation lines are syntax-checked separately from Python.
            code='\n'.join(line for line in code.splitlines() if not line.lstrip().startswith(('!','%')))
            try:
                tree=ast.parse(code)
                for n in ast.walk(tree):
                    names=[a.name for a in n.names] if isinstance(n,ast.Import) else [n.module or ''] if isinstance(n,ast.ImportFrom) else []
                    if any(v.split('.')[0] in ('torch','torch4ms','torchax','jax','flax') for v in names):
                        errors.append(p.relative_to(target).as_posix()+': forbidden target import')
            except SyntaxError as exc:errors.append(p.relative_to(target).as_posix()+f':{exc.lineno}: '+str(exc))
    return {'passed':not missing and not errors,'missing_code_files':missing,'errors':errors}


def compare(reference,target,request):
    def arr(x):return np.asarray(x,dtype=float)
    measures={};checks={}
    for name,value in reference['preprocessing'].items():
        a,b=arr(value),arr(target['preprocessing'][name])
        diff=float(np.max(np.abs(a-b))) if a.shape==b.shape else 1e100
        measures['preprocessing_'+name]=diff;checks['preprocessing_'+name]=diff<=1e-9
    initial=np.concatenate([arr(request['initial_state'][k]).ravel() for k in sorted(request['initial_state'])])
    for i,(source,dest) in enumerate(zip(reference['steps'],target['steps']),1):
        pred=float(np.max(np.abs(arr(source['prediction'])-arr(dest['prediction']))))
        loss=abs(source['loss']-dest['loss'])
        grad=np.concatenate([(arr(source['gradients'][k])-arr(dest['gradients'][k])).ravel() for k in sorted(source['gradients'])])
        state=lambda row:np.concatenate([arr(row['state'][k]).ravel() for k in sorted(row['state'])])
        source_state,target_state=state(source),state(dest)
        update=float(np.linalg.norm(source_state-target_state)/max(float(np.linalg.norm(source_state-initial)),1e-12))
        values={'prediction_max_abs':pred,'loss_abs':loss,'gradient_vector_l2':float(np.linalg.norm(grad)),'parameter_update_relative_l2':update}
        for k,v in values.items():
            measures[f'step_{i}_{k}']=v;checks[f'step_{i}_{k}']=bool(np.isfinite(v) and v<=protocol()['acceptance'][k])
        checks[f'step_{i}_native_autodiff']=dest.get('native_gradient_tensors',0)==len(request['initial_state'])
    checks['three_steps']=len(target['steps'])==3
    checks['learning_rate_boundaries']=bool(np.allclose(target['learning_rates'],[.01,.01,.001,.001,.0001],rtol=1e-6,atol=1e-10))
    checks['parameter_count']=target['parameter_count']==17025
    return {'accepted':all(checks.values()),'checks':checks,'measurements':measures}


class Evaluator:
    def __init__(self,workspace,evidence):
        self.workspace=workspace;self.evidence=evidence;self.calls=0;self.cache={}
        self.immutable=hashes(workspace/'source');self.contract=digest(workspace/'task.json')
    def _run(self,mode,seed):
        from autofix.autonomous.sandbox import run_isolated
        reference=read(RUN/'private_reference'/('%d.json'%seed))
        self.calls+=1
        folder=self.evidence/('measurement_%04d'%self.calls);folder.mkdir(parents=True)
        runtime=self.workspace/'.runtime';runtime.mkdir(exist_ok=True)
        inp=runtime/('input_%04d.json'%self.calls);out=runtime/('output_%04d.json'%self.calls)
        save(inp,reference['request'])
        proc=run_isolated(self.workspace,TARGET_PY,WORKER,timeout=240 if mode=='workflow' else 120,
                          args=[mode,'--repository',str(self.workspace/'target'),'--input',str(inp),'--output',str(out)],
                          extra_writes=[str(runtime)])
        save(folder/'execution.json',proc)
        result=read(out) if out.exists() else {'status':'error','error':'Worker did not return a measurement','stdout':proc['stdout'][-6000:]}
        save(folder/'worker.json',result)
        if proc['returncode'] or result['status']!='ok':
            return {'accepted':False,'execution':'failed','error':result.get('error'),'traceback':result.get('traceback',result.get('stdout',proc['stdout'][-4000:]))}
        if mode=='numeric':return {'execution':'ok',**compare(reference['reference'],result['measurements'],reference['request'])}
        return {'accepted':True,'execution':'ok','measurements':result['measurements']}
    def evaluate(self,seed=101,full=True):
        immutable=hashes(self.workspace/'source')==self.immutable and digest(self.workspace/'task.json')==self.contract
        cov=coverage(self.workspace/'target')
        key=(json.dumps(hashes(self.workspace/'target'),sort_keys=True),seed,full)
        if key in self.cache and immutable:return self.cache[key]
        if not immutable:raise RuntimeError('Immutable source or task changed')
        numeric=self._run('numeric',seed)
        workflow=self._run('workflow',seed) if full else None
        accepted=cov['passed'] and numeric['accepted'] and (not full or workflow['accepted'])
        result={'accepted':accepted,'observation':{'coverage':cov,'numeric':numeric,'workflow':workflow,'accepted':accepted}}
        self.cache[key]=result
        return result
    def tool(self,args):
        name=args.get('test','paired')
        if name in ('paired','public'):return self.evaluate(full=name=='public')['observation']
        if name=='workflow':return self._run('workflow',101)
        if name.startswith('scratch_tests/'):
            from autofix.autonomous.sandbox import run_isolated
            return run_isolated(self.workspace,TARGET_PY,self.workspace/name,timeout=min(args.get('timeout_seconds',120),180))
        raise ValueError('Unknown public test')


def translate():
    from autofix.autonomous.agent import OpenAICompatibleClient
    manifest=read(RUN/'manifest.json')
    assert read(RUN/'integration_checks.json')['passed']
    assert (RUN/'offline_checks.json').is_file()
    assert manifest['source_hashes']==hashes(RUN/'source')
    assert manifest['contract_sha256']==digest(RUN/'task.json')
    save(RUN/'launch_freeze.json',{'manifest_sha256':digest(RUN/'manifest.json'),
        'request_sha256':digest(RUN/'translation_request.json'),'worker_sha256':digest(WORKER),
        'controller_sha256':digest(Path(__file__)),
        'runtime_hashes':hashes(ROOT/'autofix/autonomous'),'source_hashes':manifest['source_hashes']})
    folder=RUN/'translation';folder.mkdir(exist_ok=False)
    request=read(RUN/'translation_request.json');started=time.time()
    save(folder/'status.json',{'status':'running','model':request['model']})
    try:
        response=OpenAICompatibleClient()(request,1800)
        save(folder/'response.json',response)
        content=response['choices'][0]['message']['content']
        if content.strip().startswith('```'):content=content.strip().split('\n',1)[1].rsplit('```',1)[0]
        files=json.loads(content)['files']
        target=folder/'target';shutil.copytree(RUN/'source',target)
        for name,contents in files.items():
            path=PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts or any(x.startswith('.') for x in path.parts):raise ValueError('Invalid translation path')
            dest=target/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(contents)
        save(folder/'status.json',{'status':'generated','seconds':time.time()-started,'usage':response.get('usage'),
                                 'finish_reason':response['choices'][0].get('finish_reason'),'files':hashes(target),'coverage':coverage(target)})
    except Exception as exc:
        save(folder/'status.json',{'status':'error','seconds':time.time()-started,'error':str(exc)});raise
    print(json.dumps({'status':'generated','usage':response.get('usage'),'coverage':coverage(target)}))


def run_condition(method):
    from autofix.autonomous.agent import AgentConfig,AutonomousAgent
    from autofix.autonomous.tools import WorkspaceTools
    folder=RUN/'conditions'/method;folder.mkdir(parents=True,exist_ok=False)
    ws=folder/'workspace';ws.mkdir()
    shutil.copytree(RUN/'source',ws/'source');shutil.copytree(RUN/'translation/target',ws/'target')
    shutil.copy2(RUN/'task.json',ws/'task.json');(ws/'scratch_tests').mkdir()
    ev=Evaluator(ws,folder/'evidence')
    if method=='initial':
        result=ev.evaluate();result['confirmation']=[ev.evaluate(seed=s,full=False) for s in (202,303)] if result['accepted'] else []
        result['accepted']=result['accepted'] and all(x['accepted'] for x in result['confirmation'])
        save(folder/'result.json',result);print(json.dumps(result));return
    config=AgentConfig(method='layered' if method=='ladim' else 'single',model='deepseek-v4-flash',memory_policy='evidence' if method=='ladim' else 'native',
                       workflow_policy='progress_loop' if method=='ladim' else 'standard',max_calls=40,max_output_tokens=120000,max_seconds=1800,per_call_output_tokens=16384)
    agent=AutonomousAgent(WorkspaceTools(ws,ev.tool,named_tests=('paired','workflow','public'),validate_syntax=method=='ladim'),folder/'evidence/agent',config=config)
    adapter=None
    if method=='swe':
        from autofix.autonomous.swe_upstream import SWEAgentNative
        adapter=SWEAgentNative(agent,upstream_root=BASE/'external_baselines/SWE-agent-v1.1.0',python='/media/main/whj/miniconda3/envs/sweagent110/bin/python',target_python=TARGET_PY,vendor=BASE/'experiments/autonomous_verifier_20260917/swe_native_vendor')
    elif method=='matchfix':
        from autofix.autonomous.baselines import MatchFixFullOrchestration
        adapter=MatchFixFullOrchestration(agent,upstream_root=BASE/'external_baselines/MatchFixAgent-66a52a5',python='/media/main/whj/miniconda3/envs/matchfixagent/bin/python')
    result={'method':method,'status':'running','accepted':False,'attempts':[]};save(folder/'result.json',result)
    started=time.monotonic()
    try:
        initial=ev.evaluate();result['initial']=initial
        stage=adapter.initialize(initial['observation']) if adapter else agent.diagnose(initial['observation'])
        result['diagnosis']=asdict(stage)
        current=initial
        for attempt in range(1,5):
            if current['accepted'] and (not adapter or attempt>1):break
            stage=adapter.repair(current['observation'],attempt=attempt) if adapter else agent.repair(current['observation'],attempt=attempt)
            current=ev.evaluate()
            confirmations=[ev.evaluate(seed=s,full=False) for s in (202,303)] if current['accepted'] else []
            accepted=current['accepted'] and all(x['accepted'] for x in confirmations)
            result['attempts'].append({'attempt':attempt,'stage':asdict(stage),'evaluation':current,'confirmations':confirmations,'accepted':accepted})
            result['accepted']=accepted;save(folder/'result.json',result)
            if accepted:break
            if confirmations and not accepted:current=next(x for x in confirmations if not x['accepted'])
            if stage.status in ('budget_exhausted','api_error','infrastructure_error','error'):break
        if not result['attempts']:
            confirmations=[ev.evaluate(seed=s,full=False) for s in (202,303)] if current['accepted'] else []
            result['confirmation']=confirmations;result['accepted']=current['accepted'] and all(x['accepted'] for x in confirmations)
        result.update(status='completed',final=current)
    except Exception as exc:result.update(status='infrastructure_error',error=str(exc),traceback=traceback.format_exc())
    finally:
        if adapter and hasattr(adapter,'close'):adapter.close()
        result.update(seconds=time.monotonic()-started,calls=agent.calls,usage=agent.usage(),final_target_hashes=hashes(ws/'target'))
        save(folder/'result.json',result)
    print(json.dumps({k:result.get(k) for k in ('method','status','accepted','calls','usage','error')}))


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','translate','run','check']);p.add_argument('--method',choices=['initial','ladim','swe','matchfix'])
    a=p.parse_args()
    if a.command=='prepare':prepare()
    elif a.command=='translate':translate()
    elif a.command=='run':run_condition(a.method)
    else:
        reference=read(RUN/'private_reference/101.json');ref=reference['reference'];req=reference['request']
        target={**ref,'learning_rates':[.01,.01,.001,.001,.0001],'parameter_count':17025}
        for step in target['steps']:step['native_gradient_tensors']=len(req['initial_state'])
        assert compare(ref,target,req)['accepted']
        bad=json.loads(json.dumps(target));bad['steps'][0]['prediction'][0]+=1
        assert not compare(ref,bad,req)['accepted']
        bad=json.loads(json.dumps(target));bad['steps'][0]['state']=req['initial_state']
        assert not compare(ref,bad,req)['accepted']
        save(RUN/'offline_checks.json',{'source_identity_control':'passed','forward_error_control':'rejected','missing_update_control':'rejected','model_calls':0})
        print('Offline scoring checks passed')


if __name__=='__main__':main()
