"""Isolated two-task JAX development protocol; never overwrites prior runs."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys

SEEDS = (7101, 7102, 7103)
METHODS = ('autonomous_layered', 'direct_shared_tools')
TASKS = ('task_001', 'task_002')
HERE = Path(__file__).resolve().parent


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reference(task, seed, source):
    import torch
    import numpy as np
    torch.set_num_threads(1)
    torch.manual_seed(seed)
    spec = importlib.util.spec_from_file_location('public_source', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    model = module.build_model(task)
    optimizer = module.build_optimizer(task, model.parameters())
    tree = lambda: {k: v.detach().numpy().reshape(-1).tolist() for k,v in model.named_parameters()}
    initial = tree()
    arrays = {'p:' + k: v.detach().numpy().copy() for k,v in model.named_parameters()}
    steps = []
    for i, (x, y) in enumerate(module.make_batches(task, seed)):
        arrays[f'x:{i}'], arrays[f'y:{i}'] = x.numpy(), y.numpy()
        optimizer.zero_grad()
        logits = model(x)
        loss = torch.nn.functional.cross_entropy(logits, y)
        loss.backward()
        gradients = {k: v.grad.detach().numpy().reshape(-1).tolist() for k,v in model.named_parameters()}
        before = {k: v.detach().clone() for k,v in model.named_parameters()}
        optimizer.step()
        updates = {k: (v.detach()-before[k]).numpy().reshape(-1).tolist() for k,v in model.named_parameters()}
        steps.append({'loss': float(loss.detach()), 'logits': logits.detach().numpy().reshape(-1).tolist(),
                      'gradients': gradients, 'updates': updates, 'parameters': tree()})
    return {'status': 'ok', 'initial': initial, 'steps': steps}, arrays


def prepare(run, snapshot):
    import numpy as np
    if run.exists():
        raise RuntimeError('Refusing to overwrite a run')
    run.mkdir(parents=True)
    shutil.copytree(snapshot / 'autofix', run / 'code_snapshot/autofix', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    (run / 'public_backend').mkdir(exist_ok=True)
    shutil.copy2(HERE / 'worker.py', run / 'public_backend/worker.py')
    shutil.copy2(__file__, run / 'runner.py')
    private = run / 'private_healthy'
    private.mkdir()
    healthy = (HERE / 'target_template.py').read_text()
    for task in TASKS:
        target = run / 'private_inputs' / task
        (target / 'inputs').mkdir(parents=True)
        shutil.copy2(HERE / 'source.py', target / 'source.py')
        candidate = healthy
        if task == 'task_001':
            candidate = candidate.replace('updates, state = optimizer(task).update(gradients, state, p)',
                                          'updates, state = optimizer(task).update(gradients, init_optimizer(p, task), p)')
        else:
            candidate = candidate.replace("q = linear(p, 'query', x)", "q = jax.lax.stop_gradient(linear(p, 'query', x))")
        (target / 'candidate.py').write_text(candidate)
        (private / f'{task}.py').write_text(healthy)
        dump(target / 'task.json', {'task': task, 'target_backend': 'native JAX and Optax',
             'evaluation': 'Three consecutive training steps on different batches; preserve optimizer state across steps. Source model and optimizer are defined in source.py.',
             'interface': 'forward(parameters, x, task), init_optimizer(parameters, task), train_step(parameters, state, x, y, task) returning parameters, state, scalar loss, gradients. Parameter keys/shapes match PyTorch state exactly.',
             'inputs': 'inputs/<seed>.npz contains initial parameters p:<name> and three x:<step>/y:<step> batches. No reference outputs are supplied.',
             'repair_scope': 'Only candidate.py is editable; scratch_tests/*.py may be created. Source, task contract, and input arrays are immutable.',
             'seeds': list(SEEDS), 'thresholds': {'loss_abs': 2e-5, 'logits_rel_l2': 2e-4, 'gradients_rel_l2': 2e-4, 'updates_rel_l2': 2e-4, 'parameters_rel_l2': 2e-4},
             'acceptance': 'All steps and all seeds must pass every per-parameter check. Missing, nonfinite, wrong-name or wrong-shape vectors fail. Initial values must match exactly. Actual JAX arrays required.'})
        for seed in SEEDS:
            ref, arrays = reference(task, seed, target / 'source.py')
            dump(run / 'private_reference' / task / f'{seed}.json', ref)
            np.savez(target / 'inputs' / f'{seed}.npz', **arrays)
    manifest = {'study': 'Two-task controlled multistep JAX development; never merge denominator with historical six',
       'tasks': [{'anonymous_id': task, 'original_id': task} for task in TASKS], 'methods': list(METHODS),
       'model': 'deepseek-v4-flash', 'max_calls': 40, 'max_output_tokens': 120000, 'max_seconds': 1800,
       'max_repair_attempts': 4, 'per_call_output_tokens': 16384, 'thinking_mode': 'enabled', 'reasoning_effort': 'high',
       'max_context_chars': 1000000, 'diagnosis_calls_per_stage': 8, 'repair_calls_per_stage': 8,
       'memory_policy': {'autonomous_layered': 'evidence', 'direct_shared_tools': 'native'},
       'workflow_policy': {'autonomous_layered': 'progress_loop', 'direct_shared_tools': 'standard'},
       'diagnosis_policy': {m: 'evidence' for m in METHODS}, 'syntax_guard': {'autonomous_layered': False, 'direct_shared_tools': False},
       'source_snapshot': str(snapshot), 'source_git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=snapshot, text=True).strip(),
       'method_version': 'slim-v4', 'api_workers': 1,
       'development_faults_private': {'task_001': 'optimizer state reset each step', 'task_002': 'query projection detached'},
       'selection': 'Two predetermined mechanisms, no outcome selection; hand-authored controlled targets, not natural migrations.'}
    dump(run / 'manifest.json', manifest)
    dump(run / 'frozen_hashes.json', {str(p.relative_to(run)): sha(p) for p in run.rglob('*') if p.is_file()})


def relative(left, right):
    if not isinstance(left, list) or not isinstance(right, list) or len(left) != len(right) or not left:
        return None
    if not all(isinstance(v, (int,float)) and math.isfinite(v) for v in left + right):
        return None
    return math.sqrt(sum((a-b)**2 for a,b in zip(left,right))) / max(math.sqrt(sum(a*a for a in left)), 1e-7)


def compare(ref, target, thresholds):
    if target.get('status') != 'ok' or len(target.get('steps', [])) != 3:
        return False, []
    checks = [{'step': 0, 'quantity': 'initial', 'accepted': ref['initial'] == target.get('initial')}]
    for i, (left, right) in enumerate(zip(ref['steps'], target['steps']), 1):
        checks.append({'step': i, 'quantity': 'jax_arrays', 'accepted': right.get('jax_arrays') is True})
        loss = right.get('loss')
        value = abs(left['loss'] - loss) if isinstance(loss, (float,int)) and math.isfinite(loss) else None
        checks.append({'step': i, 'quantity': 'loss', 'value': value, 'accepted': value is not None and value <= thresholds['loss_abs']})
        for quantity in ('logits','gradients','updates','parameters'):
            a, b = left[quantity], right.get(quantity)
            entries = [('all', a, b)] if quantity == 'logits' else [(k,a[k],b.get(k)) for k in a] if isinstance(b,dict) and a.keys() == b.keys() else [('mismatched_keys', [], [])]
            for name, av, bv in entries:
                value = relative(av,bv)
                checks.append({'step': i, 'quantity': quantity, 'parameter': name, 'value': value,
                               'accepted': value is not None and value <= thresholds[quantity+'_rel_l2']})
    return all(x['accepted'] for x in checks), checks


class Evaluator:
    def __init__(self, run, task, workspace, evidence, python):
        self.run, self.task, self.workspace, self.evidence, self.python = run,task,workspace,evidence,python
        self.calls = 0
        self.contract = json.loads((workspace/'task.json').read_text())
        self.immutable = {p:sha(p) for p in [workspace/'source.py',workspace/'task.json',*sorted((workspace/'inputs').glob('*.npz'))]}

    def paired(self, seed=SEEDS[0], timeout=180):
        from autofix.autonomous.sandbox import run_isolated
        self.calls += 1
        folder = self.evidence/f'measurement_{self.calls:04d}'
        proc = run_isolated(self.workspace,self.python,self.run/'public_backend/worker.py',timeout=timeout,
                            extra_reads=[str(self.run/'public_backend'),str(self.python.resolve().parent.parent)],
                            args=[str(self.workspace),str(seed)])
        try:
            target = json.loads(proc['stdout'].strip().splitlines()[-1])
        except (ValueError,IndexError):
            target = {'status':'failed','error_type':'WorkerProcessError','error':proc.get('stderr','')[-8000:]+proc.get('stdout','')[-8000:]}
        ref = json.loads((self.run/'private_reference'/self.task/f'{seed}.json').read_text())
        accepted, checks = compare(ref,target,self.contract['thresholds'])
        unchanged = all(p.exists() and sha(p)==h for p,h in self.immutable.items())
        accepted = accepted and unchanged and proc['returncode']==0
        observation = {'execution':{'status':target['status'],'error_type':target.get('error_type'),'message':target.get('error','')},
                       'source_immutable':unchanged,'scope':'three continuous training steps, every parameter vector',
                       'measurements': checks,'acceptance':{'accepted':accepted},
                       'target_backend_observed':target.get('status')=='ok' and all(s.get('jax_arrays') for s in target.get('steps',[]))}
        result={'accepted':accepted,'observation':observation,'seed':seed,'measurement':str(folder)}
        dump(folder/'process.json',proc); dump(folder/'raw_target.json',target); dump(folder/'observation.json',result)
        return result

    def confirm(self):
        return [self.paired(seed) for seed in SEEDS[1:]]

    def tool(self, request):
        if request['test'] in ('paired','public'):
            return self.paired(timeout=min(180,request.get('timeout_seconds',180)))['observation']
        from autofix.autonomous.sandbox import run_isolated
        path=(self.workspace/request['test']).resolve()
        if not path.is_relative_to(self.workspace/'scratch_tests') or path.suffix!='.py':
            raise ValueError('Only scratch tests may execute')
        proc=run_isolated(self.workspace,self.python,path,timeout=min(120,request.get('timeout_seconds',120)))
        self.calls+=1; dump(self.evidence/f'scratch_{self.calls:04d}.json',proc)
        return {**proc,'stdout':proc['stdout'][:16000]}


def runtime(run):
    sys.path.insert(0,str(run/'code_snapshot'))
    from autofix.autonomous import agent, experiment
    for name in ('SYSTEM_PROMPT','FIXER_PROMPT','EVIDENCE_SYSTEM_PROMPT','EVIDENCE_FIXER_PROMPT'):
        setattr(agent,name,getattr(agent,name).replace('torch4ms/MindSpore','native JAX/Optax'))
    experiment.evaluator_for=lambda output,task,workspace,evidence,python,manifest: Evaluator(output,task,workspace,evidence,python)
    return experiment


def preflight(run, python):
    experiment=runtime(run)
    results=[]
    for task in TASKS:
        for kind in ('initial','healthy'):
            workspace,evidence=experiment.workspace_for(run,task,'offline_'+kind)
            if kind=='healthy': shutil.copy2(run/'private_healthy'/f'{task}.py',workspace/'candidate.py')
            evaluator=Evaluator(run,task,workspace,evidence,python)
            for seed in SEEDS:
                row={'task':task,'kind':kind,**evaluator.paired(seed)}
                results.append(row); dump(run/'preflight.json',results)
                print(json.dumps({'task':task,'kind':kind,'seed':seed,'accepted':row['accepted'],'execution':row['observation']['execution']}),flush=True)
    if any(r['accepted'] != (r['kind']=='healthy') for r in results):
        raise RuntimeError('Offline gate failed; inspect preserved evidence')
    dump(run/'preflight_passed.json',{'checks':len(results),'passed':True})


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('command',choices=['prepare','preflight','run'])
    parser.add_argument('--run',type=Path,required=True); parser.add_argument('--snapshot',type=Path)
    parser.add_argument('--python',type=Path,default=Path(sys.executable))
    args=parser.parse_args()
    if args.command=='prepare': prepare(args.run,args.snapshot); return
    hashes=json.loads((args.run/'frozen_hashes.json').read_text())
    for p,h in hashes.items():
        if sha(args.run/p)!=h: raise RuntimeError('Frozen file changed: '+p)
    if args.command=='preflight': preflight(args.run,args.python); return
    if not (args.run/'preflight_passed.json').exists(): raise RuntimeError('Preflight required')
    experiment=runtime(args.run)
    for task in TASKS:
        for method in METHODS:
            if (args.run/'conditions'/task/method).exists():
                raise RuntimeError('Condition exists; explicit audited resume required')
            result=experiment.run_condition(args.run,task,method,args.python)
            print(json.dumps({'task':task,'method':method,'status':result['status'],'accepted':result['accepted'],'budget':result['budget']}),flush=True)


if __name__=='__main__': main()
