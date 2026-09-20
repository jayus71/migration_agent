"""Independent source/target observations for the small MoE repository pilot."""
from __future__ import annotations
import argparse
import builtins
import importlib
import json
from pathlib import Path
import sys
import traceback
import os
import numpy as np


def plain(value):
    if hasattr(value, 'detach'): return value.detach().cpu().numpy().tolist()
    if hasattr(value, 'asnumpy'): return value.asnumpy().tolist()
    if isinstance(value, dict): return {k: plain(v) for k,v in value.items()}
    if isinstance(value, (list, tuple)): return [plain(v) for v in value]
    return value


def source_request(seed):
    rng=np.random.default_rng(seed)
    return {'seed':seed,'model_kwargs':{'input_dim':4,'output_dim':3,'num_experts':3,'k':3,
            'expert_kwargs':{'hidden_dim':6,'num_layers':2,'dropout':0.0},'router_noise_epsilon':0.0},
            'batches':[{'x':rng.normal(size=(8,4)).astype('float32').tolist(),
                        'y':rng.integers(0,3,size=8).tolist()} for _ in range(3)],
            'routing_scores':rng.normal(size=(8,3)).astype('float32').tolist()}


def run(repository,source,request,work):
    sys.path.insert(0,str(repository))
    work.mkdir(parents=True,exist_ok=True)
    native_events=[]
    if source:
        import torch as framework
        framework.set_num_threads(1);framework.manual_seed(request['seed'])
        tensor=lambda v,integer=False:framework.tensor(v,dtype=framework.int64 if integer else framework.float32)
        loss_fn=framework.nn.CrossEntropyLoss()
    else:
        original_import=builtins.__import__
        def restricted(name,*args,**kwargs):
            if name.split('.')[0] in ('torch','torch4ms','torchax','jax','flax'):
                raise ImportError('Native MindSpore target cannot import '+name)
            return original_import(name,*args,**kwargs)
        builtins.__import__=restricted
        import mindspore as framework
        framework.set_context(mode=framework.PYNATIVE_MODE,device_target='CPU');framework.set_seed(request['seed'])
        tensor=lambda v,integer=False:framework.Tensor(np.asarray(v,dtype='int32' if integer else 'float32'))
        loss_fn=framework.nn.CrossEntropyLoss()
        original_vag=framework.value_and_grad
        def observed(*args,**kwargs):
            fn=original_vag(*args,**kwargs)
            weights=args[2] if len(args)>2 else kwargs.get('weights')
            def call(*xs,**kw):
                value,gradients=fn(*xs,**kw)
                native_events.append({'weights':weights,'gradients':[g.asnumpy().copy() for g in gradients]})
                return value,gradients
            return call
        framework.value_and_grad=observed;framework.ops.value_and_grad=observed
    from src.models.moe import MixtureOfExperts
    from src.training.trainer import MoETrainer
    from src.models import _model_stack
    from src.evaluation import metrics
    model=MixtureOfExperts(**request['model_kwargs'])
    if source:
        params=dict(model.named_parameters())
        request['initial_state']=plain(params)
        mapping={k:k for k in params}
        optimizer=framework.optim.Adam(model.parameters(),lr=.001,betas=(.9,.999),eps=1e-8)
    else:
        if not isinstance(model,framework.nn.Cell):raise TypeError('Model must be native nn.Cell')
        params=dict(model.parameters_and_names())
        mapping=json.loads((repository/'parameter_map.json').read_text())
        if set(mapping)!=set(request['initial_state']) or set(mapping.values())!=set(params) or len(set(mapping.values()))!=len(mapping):
            raise ValueError('parameter_map.json must bijectively cover source and target parameters')
        for s,t in mapping.items():
            value=np.asarray(request['initial_state'][s],dtype='float32')
            if tuple(value.shape)!=tuple(params[t].shape):raise ValueError('Parameter shape mismatch for '+s)
            params[t].set_data(tensor(value))
        optimizer=framework.nn.Adam(model.trainable_params(),learning_rate=.001,beta1=.9,beta2=.999,eps=1e-8)
    trainer=MoETrainer(model,loss_fn,optimizer,framework.device('cpu') if source else 'CPU',
                       aux_loss_weight=.1,gradient_clip_val=None)
    state=lambda:{s:plain(params[t]) for s,t in mapping.items()}
    mode=lambda training:model.train(training) if source else model.set_train(training)
    class Loader:
        def __init__(self,batches):
            self.batches=[(tensor(b['x']),tensor(b['y'],True)) for b in batches]
            self.dataset=list(range(sum(len(b['x']) for b in batches)))
        def __iter__(self):return iter(self.batches)
        def __len__(self):return len(self.batches)
    steps=[]
    for index,batch in enumerate(request['batches']):
        mode(True)
        pred,aux=model(tensor(batch['x']))
        loss=loss_fn(pred,tensor(batch['y'],True))+.1*aux
        event_start=len(native_events)
        report=trainer.train_epoch(Loader([batch]),index)
        if source:
            gradients={s:plain(params[t].grad) if params[t].grad is not None else np.zeros(tuple(params[t].shape)).tolist() for s,t in mapping.items()}
        else:
            if len(native_events)!=event_start+1:raise ValueError('Each trainer batch must use one observed native value_and_grad operation')
            event=native_events[-1];by_id={id(p):g for p,g in zip(event['weights'],event['gradients'])}
            if set(by_id)!=set(id(p) for p in params.values()):raise ValueError('Autodiff must cover every trainable parameter')
            gradients={s:by_id[id(params[t])].tolist() for s,t in mapping.items()}
        steps.append({'prediction':plain(pred),'loss':plain(loss),'gradients':gradients,'state':state(),'report':plain(report)})
    training_variants=[]
    mode(True)
    for k in (1,2,3):
        model.k=k;model.router.k=k
        training_variants.append(plain(model(tensor(request['batches'][0]['x']))))
    mode(False)
    outputs=[]
    for k in (1,2,3):
        model.k=k;model.router.k=k
        value,aux=model(tensor(np.asarray(request['batches'][0]['x']).reshape(2,4,4)))
        if aux is not None:raise ValueError('Evaluation auxiliary loss must be None')
        outputs.append(plain(value))
    model.k=3;model.router.k=3
    train_report=plain(trainer.train_epoch(Loader(request['batches']),3))
    eval_report=plain(trainer.evaluate(Loader(request['batches'])))
    mode(False);before=plain(model(tensor(request['batches'][0]['x']))[0])
    checkpoint=work/'checkpoint.ckpt'
    trainer.save_checkpoint(str(checkpoint),epoch=3,probe_marker='roundtrip')
    # Check that restore reloads weights, rather than simply retaining the object.
    if source:
        with framework.no_grad():next(iter(params.values())).add_(.25)
    else:
        p=next(iter(params.values()));p.set_data(p+tensor(.25))
    loaded=trainer.load_checkpoint(str(checkpoint));mode(False)
    after=plain(model(tensor(request['batches'][0]['x']))[0])
    if not np.allclose(before,after,atol=1e-7,rtol=1e-7):raise ValueError('Checkpoint did not restore predictions')
    if loaded['epoch']!=3 or loaded.get('probe_marker')!='roundtrip':raise ValueError('Checkpoint metadata lost')
    resume_report=plain(trainer.train_epoch(Loader([request['batches'][0]]),4))
    # Exercise native random training separately from deterministic equivalence.
    random_kwargs=dict(request['model_kwargs']);random_kwargs['router_noise_epsilon']=.01
    random_kwargs['expert_kwargs']={'hidden_dim':6,'num_layers':2,'dropout':.1}
    noisy=MixtureOfExperts(**random_kwargs)
    noisy_opt=framework.optim.Adam(noisy.parameters(),lr=.001) if source else framework.nn.Adam(noisy.trainable_params(),learning_rate=.001)
    noisy_trainer=MoETrainer(noisy,loss_fn,noisy_opt,framework.device('cpu') if source else 'CPU')
    stochastic_report=plain(noisy_trainer.train_epoch(Loader([request['batches'][0]]),0))
    scores=tensor(request['routing_scores'])
    routing=[]
    for k in (1,2,3):routing.append(plain(_model_stack.topk_route(scores,k=k)))
    weights=np.exp(np.asarray(request['routing_scores']));weights/=weights.sum(axis=1,keepdims=True)
    metric_values={'utilization':plain(metrics.expert_utilization(tensor(weights))),
        'capacity':plain(metrics.expert_capacity_utilization(tensor(weights),4)),
        'entropy':plain(metrics.routing_entropy(tensor(weights))),
        'correlation':plain(metrics.expert_correlation([tensor(np.asarray(request['batches'][i]['x'])[:,:3]) for i in range(3)]))}
    try:
        metric_values['collection']=plain(metrics.MoEMetrics(3,4).compute_metrics(tensor(weights)))
        metric_values['collection_status']='returned'
    except Exception as exc:
        metric_values['collection_status']='raises'
        metric_values['collection_error_type']=type(exc).__name__
    return {'request':request,'measurements':{'steps':steps,'forward_variants':outputs,'training_variants':training_variants,'routing':routing,
        'metrics':metric_values,'train_report':train_report,'eval_report':eval_report,
        'checkpoint_prediction':after,'resume_report':resume_report,'resume_state':state(),
        'checkpoint_metadata':{'epoch':loaded['epoch'],'probe_marker':loaded['probe_marker']},
        'stochastic_execution_finite':bool(np.isfinite(float(stochastic_report['loss']))),
        'native_autodiff_calls':len(native_events) if not source else None,
        'external_runtime_active':{'linear':getattr(_model_stack,'_runtime_linear_module',None) is not None,
                                   'router':getattr(_model_stack,'_runtime_topk_router',None) is not None},
        'model_config':plain(model.get_config())}}


def main():
    p=argparse.ArgumentParser();p.add_argument('--repository',type=Path,required=True)
    p.add_argument('--source',action='store_true');p.add_argument('--seed',type=int,default=101)
    p.add_argument('--tests',action='store_true')
    p.add_argument('--input',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    try:
        if a.tests:
            sys.path.insert(0,str(a.repository));os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
            if not a.source:
                original_import=builtins.__import__
                def restricted(name,*args,**kwargs):
                    if name.split('.')[0] in ('torch','torch4ms','torchax','jax','flax'):raise ImportError('Native target cannot import '+name)
                    return original_import(name,*args,**kwargs)
                builtins.__import__=restricted
            import pytest
            class Capture:
                def __init__(self):self.results=[]
                def pytest_runtest_logreport(self,report):
                    if report.when=='call':self.results.append({'nodeid':report.nodeid,'outcome':report.outcome})
            capture=Capture()
            code=pytest.main(['-q','-p','no:cacheprovider',str(a.repository/'tests')],plugins=[capture])
            result={'status':'ok' if code==0 and len(capture.results)>=3 and all(r['outcome']=='passed' for r in capture.results) else 'error',
                    'exit_code':int(code),'tests':capture.results}
        else:
            request=source_request(a.seed) if a.source else json.loads(a.input.read_text())
            result={'status':'ok',**run(a.repository,a.source,request,a.output.parent/'worker_files')}
    except Exception as exc:result={'status':'error','error':str(exc),'traceback':traceback.format_exc()}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2,allow_nan=False))
    print(json.dumps({'status':result['status'],'error':result.get('error')}))


if __name__=='__main__':main()
