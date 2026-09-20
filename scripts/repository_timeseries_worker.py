"""Source-derived measurements and isolated native MindSpore checks for one repository."""
from __future__ import annotations
import argparse
import ast
import builtins
from datetime import date, timedelta
import importlib.util
import json
import os
from pathlib import Path
import runpy
import sys
import traceback
import numpy as np


def source_namespace(path):
    tree = ast.parse(path.read_text())
    keep = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom, ast.ClassDef, ast.FunctionDef))]
    ns = {'__name__': 'source_reference'}
    exec(compile(ast.Module(body=keep, type_ignores=[]), str(path), 'exec'), ns)
    return ns


def prices(seed, count=180):
    rng = np.random.RandomState(seed)
    i = np.arange(count)
    return (100 + .1*i + np.sin(i/11) + rng.normal(0, .01, count)).tolist()


def source_probe(source, seed):
    import torch
    torch.set_num_threads(1)
    torch.manual_seed(seed)
    ns = source_namespace(source / 'project.py')
    model = ns['LSTMModel'](dropout=0)
    model.train()
    initial = {k: p.detach().numpy().tolist() for k,p in model.named_parameters()}
    rng = np.random.RandomState(seed + 47)
    batches = [{'x': rng.normal(size=(4,20,1)).astype('float32').tolist(),
                'y': rng.normal(size=4).astype('float32').tolist()} for _ in range(3)]
    opt = torch.optim.Adam(model.parameters(), lr=.01, betas=(.9,.98), eps=1e-9)
    steps = []
    for batch in batches:
        x, y = torch.tensor(batch['x']), torch.tensor(batch['y'])
        opt.zero_grad()
        pred = model(x)
        loss = torch.nn.functional.mse_loss(pred, y)
        loss.backward()
        gradients = {k:p.grad.detach().numpy().tolist() for k,p in model.named_parameters()}
        opt.step()
        steps.append({'prediction': pred.detach().numpy().tolist(), 'loss': float(loss.detach()),
                      'gradients': gradients, 'state': {k:p.detach().numpy().tolist() for k,p in model.named_parameters()}})
    p = np.array(prices(seed))
    norm = ns['Normalizer']()
    normalized = norm.fit_transform(p)
    windows, unseen = ns['prepare_data_x'](normalized,20)
    labels = ns['prepare_data_y'](normalized,20)
    request = {'seed': seed, 'initial_state': initial, 'batches': batches, 'prices': p.tolist()}
    reference = {'steps': steps, 'preprocessing': {'normalized':normalized.tolist(), 'windows':windows.tolist(),
                       'unseen':unseen.tolist(), 'labels':labels.tolist(), 'inverse':norm.inverse_transform(normalized).tolist()}}
    return request, reference


def block_torch():
    original = builtins.__import__
    def restricted(name, *args, **kwargs):
        if name.split('.')[0] in ('torch','torch4ms','torchax','jax','flax'):
            raise ImportError('Target execution must use native MindSpore; prohibited import: '+name)
        return original(name, *args, **kwargs)
    builtins.__import__ = restricted


def target_module(target):
    sys.path.insert(0,str(target))
    spec = importlib.util.spec_from_file_location('project', target/'project.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules['project'] = module
    spec.loader.exec_module(module)
    return module


def target_probe(target, request):
    block_torch()
    import mindspore as ms
    ms.set_context(mode=ms.PYNATIVE_MODE, device_target='CPU')
    ms.set_seed(request['seed'])
    module = target_module(target)
    model = module.LSTMModel(dropout=0)
    if not isinstance(model, ms.nn.Cell):
        raise TypeError('LSTMModel must be a native mindspore.nn.Cell')
    mapping = json.loads((target/'parameter_map.json').read_text())
    params = dict(model.parameters_and_names())
    if set(mapping) != set(request['initial_state']) or set(mapping.values()) != set(params):
        raise ValueError('parameter_map.json must bijectively cover all source and native target parameters')
    for source_name,target_name in mapping.items():
        value = np.array(request['initial_state'][source_name],dtype='float32')
        if tuple(value.shape) != tuple(params[target_name].shape):
            raise ValueError('Parameter shape mismatch: '+source_name)
        params[target_name].set_data(ms.Tensor(value))
    model.set_train(True)
    optimizer = module.make_optimizer(model)
    events = []
    # The observation is captured from native autodiff, not a candidate result flag.
    original_vag = ms.value_and_grad
    def observed_vag(*args, **kwargs):
        fn = original_vag(*args, **kwargs)
        def run(*inputs, **kw):
            value, gradients = fn(*inputs, **kw)
            events.append({'gradient_tensors':len(gradients),
                           'gradients':[g.asnumpy().copy() for g in gradients],
                           'weights':args[2] if len(args)>2 else kwargs.get('weights')})
            return value, gradients
        return run
    ms.value_and_grad = observed_vag
    # Also cover the documented ops alias and imports performed at module load.
    ms.ops.value_and_grad = observed_vag
    for name, value in vars(module).copy().items():
        if value is original_vag:
            setattr(module,name,observed_vag)
    steps=[]
    for batch in request['batches']:
        x,y=ms.Tensor(np.array(batch['x'],dtype='float32')),ms.Tensor(np.array(batch['y'],dtype='float32'))
        pred=model(x).asnumpy().copy()
        loss=float(np.mean((pred-y.asnumpy())**2))
        before=len(events)
        module.train_batch(model,optimizer,x,y)
        if len(events)!=before+1:
            raise RuntimeError('Expected one observed native value_and_grad operation per train_batch')
        event=events[-1]
        names_by_id={id(p):k for k,p in params.items()}
        grads={names_by_id[id(p)]:g for p,g in zip(event['weights'],event['gradients'])}
        steps.append({'prediction':pred.tolist(),'loss':loss,
                      'gradients':{k:grads[v].tolist() for k,v in mapping.items()},
                      'state':{k:params[v].asnumpy().tolist() for k,v in mapping.items()},
                      'native_gradient_tensors':event['gradient_tensors']})
    norm=module.Normalizer()
    p=np.array(request['prices'])
    normalized=norm.fit_transform(p)
    windows,unseen=module.prepare_data_x(normalized,20)
    labels=module.prepare_data_y(normalized,20)
    rates=[float(module.learning_rate_for_epoch(e)) for e in (0,39,40,79,80)]
    return {'steps':steps,'preprocessing':{'normalized':np.asarray(normalized).tolist(),
            'windows':np.asarray(windows).tolist(),'unseen':np.asarray(unseen).tolist(),
            'labels':np.asarray(labels).tolist(),'inverse':np.asarray(norm.inverse_transform(normalized)).tolist()},
            'learning_rates':rates,'backend':'native MindSpore','parameter_count':sum(p.size for p in params.values())}


def workflow(target,request,output):
    block_torch()
    import mindspore as ms
    ms.set_context(mode=ms.PYNATIVE_MODE,device_target='CPU')
    ms.set_seed(request['seed'])
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import alpha_vantage.timeseries
    data={(date(2020,1,1)+timedelta(days=i)).isoformat():{'5. adjusted close':str(v)}
          for i,v in reversed(list(enumerate(request['prices'])))}
    class Fixture:
        def __init__(self,*args,**kwargs): pass
        def get_daily_adjusted(self,*args,**kwargs): return data,{'fixture':'frozen synthetic prices'}
    alpha_vantage.timeseries.TimeSeries=Fixture
    grid=plt.grid
    def legacy_grid(*args,**kwargs):
        if 'b' in kwargs: kwargs['visible']=kwargs.pop('b')
        return grid(*args,**kwargs)
    plt.grid=legacy_grid
    events={'autodiff':0,'gradient_tensors':0}
    vag=ms.value_and_grad
    def observed(*args,**kwargs):
        fn=vag(*args,**kwargs)
        def call(*xs,**kw):
            value,grad=fn(*xs,**kw)
            events['autodiff']+=1
            events['gradient_tensors']+=len(grad)
            if not all(np.isfinite(g.asnumpy()).all() for g in grad): raise ValueError('Nonfinite native gradients')
            return value,grad
        return call
    ms.value_and_grad=observed
    ms.ops.value_and_grad=observed
    module=target_module(target)
    state=module.main()
    # main returns its final locals for external observation, without replacing the workflow.
    if not isinstance(state,dict): raise TypeError('main() must return final workflow state')
    config=state['config']
    if config['training']['num_epoch']!=100 or config['model']['dropout']!=.2:
        raise ValueError('The default workflow must retain 100 epochs and dropout=0.2')
    prediction=np.asarray(state['prediction'])
    if prediction.size!=1 or not np.isfinite(prediction).all(): raise ValueError('Invalid next-day forecast')
    if len(state['predicted_train'])!=128 or len(state['predicted_val'])!=32:
        raise ValueError('Expected complete predictions for the 180-price fixture and original split')
    if events['autodiff'] < 200: raise ValueError('Fewer than 200 observed training batches in the default workflow')
    numbers=plt.get_fignums()
    if len(numbers)!=5: raise ValueError('Expected five original plots, got '+str(len(numbers)))
    for i,n in enumerate(numbers,1): plt.figure(n).savefig(output.parent/('plot_%d.png'%i),dpi=80)
    if not isinstance(state['model'],ms.nn.Cell): raise TypeError('Workflow model is not native MindSpore')
    return {'epochs':100,'plot_count':len(numbers),'forecast':prediction.tolist(),'backend':events,
            'train_predictions':len(state['predicted_train']),'validation_predictions':len(state['predicted_val'])}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('mode',choices=['source','numeric','workflow'])
    p.add_argument('--repository',type=Path,required=True)
    p.add_argument('--input',type=Path)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--seed',type=int,default=101)
    a=p.parse_args()
    try:
        if a.mode=='source':
            request,reference=source_probe(a.repository,a.seed)
            result={'status':'ok','request':request,'reference':reference}
        else:
            request=json.loads(a.input.read_text())
            value=target_probe(a.repository,request) if a.mode=='numeric' else workflow(a.repository,request,a.output)
            result={'status':'ok','measurements':value}
    except Exception as exc:
        result={'status':'error','error':str(exc),'traceback':traceback.format_exc()}
    a.output.write_text(json.dumps(result,allow_nan=False,indent=2))
    print(json.dumps({'status':result['status'],'error':result.get('error')}))


if __name__=='__main__': main()
