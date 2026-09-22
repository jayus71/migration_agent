"""Independent measurements of the original and migrated two-tower repository."""
from __future__ import annotations
import argparse
import builtins
import importlib
import inspect
import json
import os
from pathlib import Path
import sys
import traceback
import numpy as np

CASES={
 'base':('two_tower_base_retrieval','TwoTowerBaseRetrieval'),
 'history':('two_tower_with_user_history_encoder','TwoTowerWithUserHistoryEncoder'),
 'position':('two_tower_with_position_debiased_weights','TwoTowerWithPositionDebiasedWeights'),
 'user':('two_tower_with_user_debiased_weights','TwoTowerWithUserDebiasedWeights'),
 'debias':('two_tower_with_debiasing','TwoTowerWithDebiasing'),
 'reward':('two_tower_base_plus_main_ranker_reward_model','TwoTowerWithMainRankerReward'),
 'ranker':('two_tower_plus_light_ranker','TwoTowerPlusLightRanker'),
 'distillation':('two_tower_plus_light_ranker_plus_main_ranker_kd','TwoTowerPlusLightRankerWithKD')}

def plain(value):
    if hasattr(value,'detach'):return value.detach().cpu().numpy().tolist()
    if hasattr(value,'asnumpy'):return value.asnumpy().tolist()
    if isinstance(value,dict):return {k:plain(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [plain(v) for v in value]
    return value

def configure(source,seed):
    os.environ['CUDA_VISIBLE_DEVICES']=''
    if source:
        import torch as f
        f.set_num_threads(1);f.manual_seed(seed)
        tensor=lambda x,integer=False:f.tensor(x,dtype=f.int64 if integer else f.float32)
    else:
        original=builtins.__import__
        def restricted(name,*args,**kwargs):
            if name.split('.')[0] in ('torch','torch4ms','torchax','jax','flax'):raise ImportError('Native MindSpore target cannot import '+name)
            return original(name,*args,**kwargs)
        builtins.__import__=restricted
        import mindspore as f
        f.set_context(mode=f.PYNATIVE_MODE,device_target='CPU');f.set_seed(seed)
        tensor=lambda x,integer=False:f.Tensor(np.asarray(x,dtype='int32' if integer else 'float32'))
    return f,tensor

def make_request(seed):
    rng=np.random.default_rng(seed)
    batches=[]
    for _ in range(3):
        batches.append({'user_id':rng.integers(0,9,size=4).tolist(),'user_features':rng.normal(size=(4,3)).tolist(),
            'user_history':rng.integers(0,11,size=(4,3)).tolist(),'item_id':rng.integers(0,11,size=4).tolist(),
            'item_features':rng.normal(size=(4,3)).tolist(),'position':rng.integers(0,8,size=4).tolist(),
            'labels':rng.uniform(.1,1,size=(4,2)).tolist()})
    return {'seed':seed,'batches':batches,'cases':{}}

def models(repository,source,request,selected=None):
    sys.path.insert(0,str(repository));f,tensor=configure(source,request['seed'])
    from src.baseline_mips_module import BaselineMIPSModule
    from train.train import train_one_epoch
    outcomes={};maps=json.loads((repository/'parameter_map.json').read_text()) if not source else None
    args_order=('user_id','user_features','user_history','item_id','item_features','position','labels')
    def batch_tensors(row):return {k:tensor(v,k in ('user_id','user_history','item_id','position')) for k,v in row.items()}
    class Loader:
        def __init__(self,row):self.batch=tuple(batch_tensors(row)[k] for k in args_order);self.dataset=list(range(4))
        def __iter__(self):return iter([self.batch])
        def __len__(self):return 1
    for case,(module_name,class_name) in CASES.items():
        if selected and case!=selected:continue
        try:
            cls=getattr(importlib.import_module('src.'+module_name),class_name)
            kwargs={'num_items':2,'num_mips_items':4,'num_ranker_user_embeddings':2,
                'user_id_hash_size':9,'user_id_embedding_dim':4,'user_features_size':3,'user_history_seqlen':3,
                'item_id_hash_size':11,'item_id_embedding_dim':4,'item_features_size':3,
                'user_value_weights':[.3,.7],'mips_module':BaselineMIPSModule(13,4)}
            kwargs={k:v for k,v in kwargs.items() if k in inspect.signature(cls.__init__).parameters}
            model=cls(**kwargs)
            params=dict(model.named_parameters()) if source else dict(model.parameters_and_names())
            if source:
                request['cases'][case]={'initial_state':plain(params),'corpus':plain(model.mips_module.corpus)}
                mapping={k:k for k in params}
            else:
                available={**maps.get('shared',{}),**maps.get('cases',{}).get(case,{})}
                mapping={k:available[k] for k in request['cases'][case]['initial_state']}
                if set(mapping)!=set(request['cases'][case]['initial_state']) or set(mapping.values())!=set(params) or len(mapping)!=len(set(mapping.values())):
                    raise ValueError('Parameter mapping must bijectively cover '+case)
                for s,t in mapping.items():
                    value=np.asarray(request['cases'][case]['initial_state'][s],dtype='float32')
                    if tuple(value.shape)!=tuple(params[t].shape):raise ValueError('Parameter shape mismatch '+s)
                    params[t].set_data(tensor(value))
                model.mips_module.corpus=tensor(request['cases'][case]['corpus'])
            state=lambda:{s:plain(params[t]) for s,t in mapping.items()}
            mode=lambda flag:model.train(flag) if source else model.set_train(flag)
            first=batch_tensors(request['batches'][0]);mode(False)
            forward_args=tuple(first[k] for k in args_order[:3])
            observation={'inference':{},'training':{}}
            try:
                prediction=model(*forward_args)
                observation['inference']={'status':'ok','recommendations':plain(prediction)}
            except Exception as exc:observation['inference']={'status':'raises','error_type':type(exc).__name__,'error':str(exc)}
            train_keys=list(inspect.signature(model.train_forward).parameters)
            mode(True)
            try:
                loss=model.train_forward(**{k:first[k] for k in train_keys})
                if loss is None:
                    observation['training']={'status':'returns_none'};outcomes[case]=observation;continue
                if not np.isfinite(float(plain(loss))):raise ValueError('Nonfinite source/target loss')
            except Exception as exc:
                observation['training']={'status':'raises','error_type':type(exc).__name__,'error':str(exc)}
                outcomes[case]=observation;continue
            optimizer=f.optim.Adam(model.parameters(),lr=.001,eps=1e-8) if source else importlib.import_module("train.train").make_optimizer(model, learning_rate=.001)
            events=[]
            if not source:
                original=f.value_and_grad;original_ops=f.ops.value_and_grad
                def observed(*xs,**kw):
                    fn=original(*xs,**kw);weights=xs[2] if len(xs)>2 else kw.get('weights')
                    def call(*inputs,**kwargs):
                        value,grads=fn(*inputs,**kwargs);events.append({id(p):g.asnumpy().copy() for p,g in zip(weights,grads)})
                        return value,grads
                    return call
                f.value_and_grad=observed;f.ops.value_and_grad=observed
                trainer_module=sys.modules['train.train'];aliases=[]
                for key,value in vars(trainer_module).copy().items():
                    if value is original:aliases.append(key);setattr(trainer_module,key,observed)
            steps=[]
            try:
                for row in request['batches']:
                    xs=batch_tensors(row);mode(True)
                    emb=model.compute_user_embedding(*[xs[k] for k in args_order[:3]])
                    items=model.compute_item_embeddings(xs['item_id'],xs['item_features'])
                    loss=model.train_forward(**xs)
                    old=len(events)
                    epoch_loss=train_one_epoch(model,Loader(row),optimizer,f.device('cpu') if source else 'CPU')
                    if source:
                        grads={s:plain(params[t].grad) if params[t].grad is not None else np.zeros(tuple(params[t].shape)).tolist() for s,t in mapping.items()}
                    else:
                        if len(events)!=old+1:raise ValueError('train_one_epoch must execute one native value_and_grad per batch')
                        if set(events[-1])!=set(id(p) for p in params.values()):raise ValueError('Autodiff did not cover all trainable parameters')
                        grads={s:events[-1][id(params[t])].tolist() for s,t in mapping.items()}
                    steps.append({'user_embedding':plain(emb),'item_embedding':plain(items),'loss':plain(loss),
                        'epoch_loss':plain(epoch_loss),'gradients':grads,'state':state()})
                observation['training']={'status':'ok','steps':steps,'native_autodiff_calls':len(events) if not source else None}
            finally:
                if not source:
                    f.value_and_grad=original;f.ops.value_and_grad=original_ops
                    for key in aliases:setattr(trainer_module,key,original)
            outcomes[case]=observation
        except Exception as exc:outcomes[case]={'status':'error','error_type':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc()}
    return {'request':request,'cases':outcomes}

def tests(repository,source):
    sys.path.insert(0,str(repository));configure(source,42);os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
    import pytest
    class Capture:
        def __init__(self):self.results=[]
        def pytest_runtest_logreport(self,report):
            if report.when=='call':self.results.append({'nodeid':report.nodeid,'outcome':report.outcome})
    capture=Capture();code=pytest.main(['-q','-p','no:cacheprovider',str(repository/'tests')],plugins=[capture])
    return {'exit_code':int(code),'tests':capture.results,'accepted':code==0 and len(capture.results)==10 and all(r['outcome']=='passed' for r in capture.results)}

def cli(repository,source):
    sys.path.insert(0,str(repository));f,tensor=configure(source,101)
    import runpy
    events=[]
    if not source:
        original=f.value_and_grad
        def observed(*args,**kwargs):
            fn=original(*args,**kwargs)
            def call(*xs,**kw):
                value,grad=fn(*xs,**kw)
                if not all(np.isfinite(g.asnumpy()).all() for g in grad):raise ValueError('Nonfinite CLI gradients')
                events.append(len(grad));return value,grad
            return call
        f.value_and_grad=observed;f.ops.value_and_grad=observed
    sys.argv=['train.train','--num_epochs','1','--num_samples','16','--batch_size','8',
              '--num_users','8','--num_items','13','--num_items_to_return','2','--user_id_hash_size','9',
              '--item_id_hash_size','16','--embedding_dim','4','--feature_dim','3','--user_history_seqlen','3']
    optimizer_calls=[]
    def profile(frame,event,arg):
        if event=='call' and frame.f_code.co_name=='make_optimizer' and Path(frame.f_code.co_filename).resolve()==(repository/'train/train.py').resolve():
            optimizer_calls.append(frame.f_code.co_filename)
    previous=sys.getprofile()
    if not source:sys.setprofile(profile)
    try:runpy.run_module('train.train',run_name='__main__')
    finally:sys.setprofile(previous)
    return {'accepted':source or (len(events)==2 and bool(optimizer_calls)),
            'native_autodiff_calls':len(events) if not source else None,
            'candidate_optimizer_factory_calls':len(optimizer_calls) if not source else None}

def fixtures(repository):
    sys.path.insert(0,str(repository))
    import torch
    from src.user_history_encoder import UserHistoryEncoder
    rows=[]
    for position in (False,True):
        torch.manual_seed(42)
        kwargs={'item_id_embedding_dim':2,'history_len':3,'num_attention_heads':1,'num_attention_layers':1,'use_positional_encoding':position}
        model=UserHistoryEncoder(**kwargs)
        rows.append({'source_class':'src.user_history_encoder.UserHistoryEncoder','constructor':kwargs,
                     'seed':42,'source_initial_state':plain(dict(model.named_parameters()))})
    return {'source_test_initializations':rows,'meaning':'Source-derived initial parameters for existing exact-value tests; framework seeds alone do not align initialization. No reference outputs or healthy target implementation.'}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--repository',type=Path,required=True)
    parser.add_argument('--mode',choices=['numeric','tests','cli','fixtures'],default='numeric')
    parser.add_argument('--source',action='store_true');parser.add_argument('--seed',type=int,default=101)
    parser.add_argument('--input',type=Path);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--case',choices=list(CASES));args=parser.parse_args()
    try:
        if args.mode=='numeric':
            request=make_request(args.seed) if args.source else json.loads(args.input.read_text())
            result={'status':'ok',**models(args.repository,args.source,request,args.case)}
        elif args.mode=='fixtures':result={'status':'ok',**fixtures(args.repository)}
        elif args.mode=='tests':result={'status':'ok',**tests(args.repository,args.source)}
        else:result={'status':'ok',**cli(args.repository,args.source)}
    except Exception as exc:result={'status':'error','error':str(exc),'traceback':traceback.format_exc()}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2,allow_nan=False))
    print(json.dumps({'status':result['status'],'error':result.get('error'),'accepted':result.get('accepted'),
        'cases':{k:{p:v.get(p,{}).get('status') for p in ('inference','training')} for k,v in result.get('cases',{}).items()}}))

if __name__=='__main__':main()
