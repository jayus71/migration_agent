"""Natural initial translation and multistep JAX model-migration repair protocol.

Prepare and translation are independent of repair-method outcomes. All initial
failures, determined by the frozen common evaluator, enter the repair suite.
"""
import argparse
import ast
import hashlib
import inspect
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
import numpy as np
from formal_validation import compare_arrays

HERE=Path(__file__).resolve().parent
SEEDS=(8101,8102,8103)
METHODS=('autonomous_layered','direct_shared_tools','matchfix_full_orchestration','swe_native_isolated')


def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2)+'\n')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def source_module(task):
    import formal_workloads as work
    path,name,args,mode,opt=work.TASKS[task]
    prefix='"""Public PyTorch model workload extracted from pinned upstream; see task.json."""\nimport torch\nfrom torch import nn, Tensor\nfrom torch.nn import functional as F\nfrom torch.nn import init\nfrom unittest.mock import patch\nfrom typing import Callable, Optional, Union\nimport math\nnz,ngf,nc=8,4,1\ndef _log_api_usage_once(obj): pass  # instrumentation only\n'
    text=prefix+work.class_source(task)+'\n'
    text+=f'\nTASK = {task!r}\n\ndef build_model():\n    model = {work.constructor(task)}.double()\n    model.train({mode=="train"!r})\n    return model\n'
    cfg=work.contracts()['tasks'][task]['optimizer']
    expr="torch.optim.SGD(parameters, lr=0.01, momentum=0.9)" if cfg['type']=='SGD' else "torch.optim.Adam(parameters, lr=0.001, betas=(0.9,0.999), eps=1e-8)"
    text+=f'\ndef build_optimizer(parameters):\n    return {expr}\n\n'
    text+=inspect.getsource(work.loss_and_outputs)
    text+='\n\n# The evaluator provides initial parameters, buffers, and three fixed input batches.\n# Loss and output semantics are loss_and_outputs(TASK, model, batch).\n'
    return text


def reference(task,seed):
    import formal_workloads as work
    import torch
    torch.set_num_threads(1)
    model,opt=work.build(task,seed)
    arr=lambda v:v.detach().cpu().numpy().copy()
    public={'p:'+k:arr(v) for k,v in model.named_parameters()}
    public.update({'b:'+k:arr(v) for k,v in model.named_buffers()})
    arrays={'initial:'+k:v.copy() for k,v in public.items()}
    for step,batch in enumerate(work.batches(task,seed)):
        public.update({f'batch:{step}:'+k:arr(v) for k,v in batch.items()})
        opt.zero_grad();loss,outputs=work.loss_and_outputs(task,model,batch);loss.backward()
        before={k:arr(v) for k,v in model.named_parameters()}
        grad={k:np.zeros_like(before[k]) if v.grad is None else arr(v.grad) for k,v in model.named_parameters()}
        opt.step()
        arrays[f'{step}:loss']=arr(loss)
        outputs={str(i):v for i,v in enumerate(outputs)} if isinstance(outputs,(tuple,list)) else {'0':outputs}
        groups={'outputs':{k:arr(v) for k,v in outputs.items()},'gradients':grad,
                'updates':{k:arr(v)-before[k] for k,v in model.named_parameters()},
                'parameters':{k:arr(v) for k,v in model.named_parameters()},
                'buffers':{k:arr(v) for k,v in model.named_buffers()}}
        for kind,values in groups.items():arrays.update({f'{step}:{kind}:'+k:v for k,v in values.items()})
    return public,arrays


def prepare(run,snapshot):
    import formal_workloads as work
    if run.exists():raise RuntimeError('Run already exists')
    run.mkdir(parents=True)
    shutil.copytree(snapshot/'autofix',run/'code_snapshot/autofix',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    # Native SWE sees public input files in its anonymous Git snapshot. No change
    # to its model, prompts, parsing, algorithm, retry policy, or upstream source.
    swe=run/'code_snapshot/autofix/autonomous/swe_upstream.py'
    old=swe.read_text();new=old.replace('("torch4ms", "scratch_tests", "source", "target")','("torch4ms", "scratch_tests", "source", "target", "inputs")')
    new=new.replace('("source.py", "candidate.py", "task.json", "torch4ms", "scratch_tests", "source", "target")','("source.py", "candidate.py", "task.json", "torch4ms", "scratch_tests", "source", "target", "inputs")')
    swe.write_text(new)
    dump(run/'integration_changes.json',{'file':'autofix/autonomous/swe_upstream.py','before_sha256':hashlib.sha256(old.encode()).hexdigest(),'after_sha256':sha(swe),'change':'Validate shared public inputs as regular files and include them in anonymous public Git snapshot; input directory remains read-only.'})
    (run/'public_backend').mkdir()
    for name in ['formal_worker.py','formal_api.py']:
        shutil.copy2(HERE/name,run/'public_backend'/name)
    for name in ['formal_runner.py','formal_validation.py']:
        shutil.copy2(HERE/name,run/name)
    contracts=work.contracts();pool=json.loads((work.ROOT/'manifest_12_tasks.json').read_text())
    dump(run/'source_pool.json',pool)
    rows=[]
    for task in work.TASKS:
        target=run/'private_inputs'/task;(target/'inputs').mkdir(parents=True)
        (target/'source.py').write_text(source_module(task))
        row=contracts['tasks'][task]
        upstream_repository='pytorch/examples';upstream_revision=pool['revision']
        if row['source'].startswith('complex/'):
            upstream_repository={'karpathy_minGPT':'karpathy/minGPT','pytorch_vision':'pytorch/vision','pytorch_examples':'pytorch/examples'}[row['source'].split('/')[1]]
            upstream_revision=next(s['revision'] for s in pool['extension_sources'] if s['repository']==upstream_repository)
        contract={**row,'task':task,'task_kind':'framework_migration','source_framework':'pytorch','target_framework':'native JAX/Optax',
          'source_entry':'source.py','target_entry':'candidate.py','seeds':list(SEEDS),
          'scope':contracts['scope'],'precision':contracts['precision'],'state_contract':contracts['state_contract'],'randomness':contracts['randomness'],
          'interface':'Implement forward(parameters, buffers, batch, task) -> (outputs, new_buffers). Parameters/buffers retain source dotted names, tensor shapes and float64 dtype. Inputs come from inputs/<seed>.npz: p:<name>, b:<name>, batch:<step>:<name>. Do not implement optimization: the trusted runtime differentiates loss_from_outputs and runs the declared Optax optimizer continuously for three steps.',
          'outputs':'CNN/GAT: log probabilities; ResNet/GPT: raw logits; super-resolution/GAN/time-series: model tensor; VAE: tuple(reconstruction, mu, logvar); RNN: tuple(log_probs, h_n, c_n), zero hidden state each batch; Transformer: log_probs; actor-critic: tuple(probabilities, values); REINFORCE: probabilities. Return unchanged buffers when there is no model-state update.',
          'repair_scope':'Only candidate.py is editable. source.py, task.json and inputs are immutable; scratch_tests/*.py may be created.',
          'public_test_aliases':'public and paired invoke exactly the same numerical check for the first public seed. Both names are available for compatibility; invoking both on unchanged code repeats the same check. Final acceptance separately checks all three seeds.',
          'thresholds':{'atol':1e-7,'rtol':1e-5},
          'acceptance':'All three steps on all three seeds must pass elementwise abs(target-reference)<=atol+rtol*abs(reference) for loss, outputs, gradients, updates, parameters and buffers. Tensor names and shapes must match. Initial arrays must match exactly. JAX x64 and independent jax.value_and_grad are required.',
          'upstream_repository':upstream_repository,'upstream_revision':upstream_revision}
        dump(target/'task.json',contract)
        for seed in SEEDS:
            inputs,ref=reference(task,seed)
            np.savez_compressed(target/'inputs'/f'{seed}.npz',**inputs)
            path=run/'private_reference'/task;path.mkdir(parents=True,exist_ok=True)
            np.savez_compressed(path/f'{seed}.npz',**ref)
        rows.append({'anonymous_id':task,'original_id':task,'source_sha256':sha(target/'source.py'),'contract_sha256':sha(target/'task.json')})
    base=json.loads((HERE/'development_v2/manifest.json').read_text())
    base.update({'study':'Natural initial JAX model translations, repaired on all initial failures','tasks':rows,'methods':list(METHODS),
      'selection':'All nonempty naturally generated candidate programs failing initial common acceptance, determined before any repair method. Syntax, import, execution, numerical and state errors all enter the repair group. API failures and empty or unavailable candidate outputs remain generation failures in source-pool flow/cost, with no fabricated candidate and no repair denominator entry. Initial passes remain in source-pool flow but are excluded from repair denominator.',
      'task_kind':'framework_migration','translation':{'calls_per_task':1,'max_output_tokens':16384,'shared_across_methods':True},
      'source_pool_revision':pool['revision'],'no_fault_injection':True})
    base.pop('development_faults_private',None)
    dump(run/'manifest.json',base)
    dump(run/'pretranslation_hashes.json',{str(p.relative_to(run)):sha(p) for p in run.rglob('*') if p.is_file()})


def check_hashes(run,name):
    for p,h in json.loads((run/name).read_text()).items():
        if sha(run/p)!=h:raise RuntimeError('Frozen input changed: '+p)


def runtime(run):
    sys.path.insert(0,str(run/'code_snapshot'))
    from autofix.autonomous import agent,experiment
    for name in ('SYSTEM_PROMPT','FIXER_PROMPT','EVIDENCE_SYSTEM_PROMPT','EVIDENCE_FIXER_PROMPT'):
        setattr(agent,name,getattr(agent,name).replace('torch4ms/MindSpore','native JAX/Optax'))
    experiment.evaluator_for=lambda output,task,workspace,evidence,python,manifest:Evaluator(output,task,workspace,evidence,python)
    return experiment


def translate(run):
    check_hashes(run,'pretranslation_hashes.json');runtime(run)
    from autofix.autonomous.agent import OpenAICompatibleClient
    client=OpenAICompatibleClient();manifest=json.loads((run/'manifest.json').read_text())
    for row in manifest['tasks']:
        task=row['anonymous_id'];folder=run/'translations'/task
        if folder.exists():raise RuntimeError('Translation exists; no silent retry')
        folder.mkdir(parents=True)
        public=run/'private_inputs'/task
        prompt='Translate the supplied independent PyTorch model workload into native JAX. Implement only the public forward interface. Preserve parameter names, shapes, buffers, dtype and model semantics. Use JAX operations; the trusted evaluator will differentiate your function and apply the specified optimizer. Do not use PyTorch, TorchAX, callbacks, external files, or a source interpreter in the target. Return only complete Python code for candidate.py, with no Markdown.\n\nSOURCE\n'+(public/'source.py').read_text()+'\n\nCONTRACT\n'+(public/'task.json').read_text()
        request={'model':manifest['model'],'messages':[{'role':'user','content':prompt}],'max_tokens':16384,'thinking':{'type':'enabled'},'reasoning_effort':'high'}
        dump(folder/'request.json',request)
        try:
            response=client(request,timeout_seconds=1800);dump(folder/'response.json',response)
            content=response['choices'][0]['message'].get('content') or ''
            match=re.fullmatch(r'\s*```(?:python)?\s*\n(.*?)\n```\s*',content,re.S)
            if match:content=match.group(1)
            (folder/'generated_text.txt').write_text(content)
            record={'status':'generated','usage':response.get('usage'),'actual_model':response.get('model'),'usable_candidate':False}
            if not content.strip():record['status']='empty_output'
            else:
                try:ast.parse(content)
                except SyntaxError as exc:
                    record.update({'syntax_status':'failed','syntax_error':str(exc)})
                else:record['syntax_status']='ok'
                (public/'candidate.py').write_text(content+'\n')
                record.update({'usable_candidate':True,'candidate_sha256':sha(public/'candidate.py')})
        except Exception as exc:
            # One predetermined call only. Keep failure in the source pool.
            record={'status':'generation_failed','usable_candidate':False,'error_type':type(exc).__name__,'error':str(exc)}
        dump(folder/'result.json',record);print(json.dumps({'task':task,**record}),flush=True)
    dump(run/'translated_hashes.json',{str(p.relative_to(run)):sha(p) for p in (run/'private_inputs').rglob('*') if p.is_file()})


class Evaluator:
    def __init__(self,run,task,workspace,evidence,python):
        self.run,self.task,self.workspace,self.evidence,self.python=run,task,workspace,evidence,python;self.calls=0
        self.contract=json.loads((workspace/'task.json').read_text())
        self.immutable={p:sha(p) for p in [workspace/'source.py',workspace/'task.json',*sorted((workspace/'inputs').glob('*.npz'))]}

    def paired(self,seed=SEEDS[0],timeout=300):
        from autofix.autonomous.sandbox import run_isolated
        self.calls+=1;folder=self.evidence/f'measurement_{self.calls:04d}';folder.mkdir(parents=True)
        temp=self.workspace/'.runtime';temp.mkdir(exist_ok=True)
        artifact=temp/f'target_{self.calls:04d}_{seed}.npz'
        proc=run_isolated(self.workspace,self.python,self.run/'public_backend/formal_worker.py',timeout=timeout,
                          extra_reads=[str(self.run/'public_backend'),str(self.python.resolve().parent.parent)],
                          args=[str(self.workspace),str(seed),str(artifact)])
        try:target=json.loads(proc['stdout'].strip().splitlines()[-1])
        except Exception:target={'status':'failed','error_type':'WorkerProcessError','error':proc['stdout'][-8000:]}
        checks=[]
        if proc['returncode']==0 and target.get('status')=='ok' and artifact.exists():
            shutil.move(artifact,folder/'target.npz')
            with np.load(self.run/'private_reference'/self.task/f'{seed}.npz') as ref,np.load(folder/'target.npz') as got:
                if set(ref.files)!=set(got.files):checks.append({'quantity':'array_keys','accepted':False,'missing':sorted(set(ref.files)-set(got.files)),'extra':sorted(set(got.files)-set(ref.files))})
                else:
                    for key in sorted(ref.files):
                        result=compare_arrays(ref[key],got[key],**({'atol':0,'rtol':0} if key.startswith('initial:') else self.contract['thresholds']))
                        checks.append({'quantity':key,**result})
        unchanged=all(p.exists() and sha(p)==h for p,h in self.immutable.items())
        accepted=bool(checks) and all(c['accepted'] for c in checks) and unchanged and target.get('jax_x64') is True
        failures=[c for c in checks if not c['accepted']]
        # Full numerical evidence is retained outside the agent prompt. All
        # failed quantities remain available in summary, with no threshold loss.
        observation={'execution':{'status':target.get('status'),'error_type':target.get('error_type'),'message':target.get('error','')},
                     'acceptance':{'accepted':accepted,'checked_arrays':len(checks),'failed_arrays':len(failures)},
                     'measurements':failures,'source_immutable':unchanged,'backend':target.get('backend'),
                     'scope':'three consecutive optimization steps; all parameter vectors and buffers; fixed float64 contract'}
        result={'accepted':accepted,'observation':observation,'seed':seed,'measurement':str(folder)}
        dump(folder/'process.json',proc);dump(folder/'checks.json',checks);dump(folder/'observation.json',result)
        return result

    def confirm(self):return [self.paired(seed) for seed in SEEDS[1:]]

    def tool(self,request):
        if request['test'] in ('paired','public'):return self.paired(timeout=min(300,request.get('timeout_seconds',300)))['observation']
        from autofix.autonomous.sandbox import run_isolated
        path=(self.workspace/request['test']).resolve()
        if not path.is_relative_to(self.workspace/'scratch_tests') or path.suffix!='.py':raise ValueError('Only scratch tests may execute')
        proc=run_isolated(self.workspace,self.python,path,timeout=min(120,request.get('timeout_seconds',120)))
        self.calls+=1;dump(self.evidence/f'scratch_{self.calls:04d}.json',proc)
        return {**proc,'stdout':proc['stdout'][:16000]}


def initial_check(run,python):
    check_hashes(run,'pretranslation_hashes.json');check_hashes(run,'translated_hashes.json')
    experiment=runtime(run);manifest=json.loads((run/'manifest.json').read_text());rows=[]
    for task in [r['anonymous_id'] for r in manifest['tasks']]:
        generated=json.loads((run/'translations'/task/'result.json').read_text())
        if not generated.get('usable_candidate'):
            rows.append({'task':task,'accepted':None,'generation_status':generated['status'],'checks':[]})
            dump(run/'initial_checks.json',rows)
            continue
        workspace,evidence=experiment.workspace_for(run,task,'initial_check')
        evaluator=Evaluator(run,task,workspace,evidence,python)
        checks=[evaluator.paired(seed) for seed in SEEDS]
        row={'task':task,'accepted':all(c['accepted'] for c in checks),'checks':checks}
        rows.append(row);dump(run/'initial_checks.json',rows)
        print(json.dumps({'task':task,'initially_accepted':row['accepted']}),flush=True)
    dump(run/'repair_selection.json',{'rule':'All source-pool tasks failing initial common acceptance, before repair outcomes',
       'repair_tasks':[r['task'] for r in rows if r['accepted'] is False],'initial_passes':[r['task'] for r in rows if r['accepted'] is True],
       'generation_failures':[r['task'] for r in rows if r['accepted'] is None]})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','translate','initial-check','run'])
    parser.add_argument('--run',type=Path,required=True);parser.add_argument('--snapshot',type=Path)
    parser.add_argument('--python',type=Path,default=Path(sys.executable));args=parser.parse_args()
    if args.command=='prepare':prepare(args.run,args.snapshot)
    elif args.command=='translate':translate(args.run)
    elif args.command=='initial-check':initial_check(args.run,args.python)
    else:
        raise RuntimeError('Formal repair dispatcher deliberately not enabled until parent review of fixed inputs and gates')


if __name__=='__main__':main()
