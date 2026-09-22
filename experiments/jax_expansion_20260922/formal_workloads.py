"""Public model-workload adapters, not whole-application migration tasks.

Original model class bodies are loaded without executing dataset downloads,
argument parsing, or application loops. Runtime dimensions, losses and model
modes below are part of the common public migration contract.
"""
import ast
from contextlib import nullcontext
import math
from pathlib import Path
from unittest.mock import patch
import torch
from typing import Callable, Optional, Union
from torch import nn
from torch.nn import functional as F
from torch.nn import init

ROOT = Path(__file__).resolve().parent / 'formal_source_pool'
TASKS = {
 'cnn_classifier': ('mnist/main.py','Net', [], 'eval', 'sgd'),
 'super_resolution': ('super_resolution/model.py','Net',[2], 'train','adam'),
 'variational_autoencoder': ('vae/main.py','VAE',[],'train','adam'),
 'gan_generator': ('dcgan/main.py','Generator',[0],'train','adam'),
 'recurrent_language_model': ('word_language_model/model.py','RNNModel',['LSTM',17,8,8,1,0.0,False],'eval','sgd'),
 'transformer_language_model': ('word_language_model/model.py','TransformerModel',[17,8,2,16,1,0.0],'eval','sgd'),
 'time_sequence': ('time_sequence_prediction/train.py','Sequence',[],'train','adam'),
 'actor_critic': ('reinforcement_learning/actor_critic.py','Policy',[],'train','adam'),
 'reinforce': ('reinforcement_learning/reinforce.py','Policy',[],'eval','sgd'),
 'graph_attention': ('complex/pytorch_examples/gat/main.py','GAT',[8,16,4,3,True,0.0],'train','adam'),
 'gpt_nano': ('complex/karpathy_minGPT/mingpt/model.py','GPT',[],'eval','sgd'),
 'residual_cnn': ('complex/pytorch_vision/torchvision/models/resnet.py','ResNet',[],'train','sgd'),
}


def class_source(task):
    path,name,*_=TASKS[task]
    tree=ast.parse((ROOT/path).read_text())
    names={name}
    if name=='TransformerModel':names.add('PositionalEncoding')
    if name=='GAT':names.add('GraphAttentionLayer')
    if name=='GPT':names.update(('NewGELU','CausalSelfAttention','Block'))
    if name=='ResNet':names.update(('BasicBlock','Bottleneck','conv1x1','conv3x3'))
    nodes=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names]
    prefix=''
    if name=='GPT':
        utils=ast.parse((ROOT/'complex/karpathy_minGPT/mingpt/utils.py').read_text())
        prefix=ast.unparse(next(n for n in utils.body if isinstance(n,ast.ClassDef) and n.name=='CfgNode'))+'\nCN=CfgNode\n'
    return prefix+'\n\n'.join(ast.unparse(n) for n in nodes)


def constructor(task):
    _,name,args,*_=TASKS[task]
    if task=='gpt_nano':
        return "GPT(CN(model_type='gpt-nano', n_layer=None, n_head=None, n_embd=None, vocab_size=17, block_size=8, embd_pdrop=0.0, resid_pdrop=0.0, attn_pdrop=0.0))"
    if task=='residual_cnn':return 'ResNet(BasicBlock, [1,1,1,1], num_classes=5)'
    return f'{name}(*{args!r})'


def build(task, seed):
    path, name, args, mode, optimizer = TASKS[task]
    namespace = dict(torch=torch,nn=nn,F=F,init=init,math=math,nz=8,ngf=4,nc=1,
                     Callable=Callable,Optional=Optional,Union=Union,Tensor=torch.Tensor,
                     _log_api_usage_once=lambda obj:None)
    exec(compile(class_source(task),str(ROOT/path),'exec'),namespace)
    torch.manual_seed(seed)
    model=eval(constructor(task),namespace).double()
    model.train(mode=='train')
    if optimizer=='sgd':
        opt=torch.optim.SGD(model.parameters(),lr=0.01,momentum=0.9)
    else:
        opt=torch.optim.Adam(model.parameters(),lr=0.001,eps=1e-8)
    return model,opt


def batches(task, seed):
    g=torch.Generator().manual_seed(seed+20000)
    randn=lambda *shape:torch.randn(shape,generator=g,dtype=torch.float64)
    rand=lambda *shape:torch.rand(shape,generator=g,dtype=torch.float64)
    randint=lambda high,*shape:torch.randint(high,shape,generator=g)
    result=[]
    for _ in range(3):
        if task=='cnn_classifier': item={'x':randn(2,1,28,28),'y':randint(10,2)}
        elif task=='super_resolution': item={'x':randn(2,1,8,8),'y':randn(2,1,16,16)}
        elif task=='variational_autoencoder': item={'x':rand(2,1,28,28),'epsilon':randn(2,20)}
        elif task=='gan_generator': item={'x':randn(2,8,1,1),'y':randn(2,1,64,64)}
        elif task in ('recurrent_language_model','transformer_language_model'):
            item={'x':randint(17,5,2),'y':randint(17,10)}
        elif task=='time_sequence': item={'x':randn(2,6),'y':randn(2,6)}
        elif task=='graph_attention':
            adjacency=(rand(12,12)>0.6).double();adjacency.fill_diagonal_(1)
            item={'x':randn(12,8),'adjacency':adjacency,'y':randint(3,12)}
        elif task=='gpt_nano':item={'x':randint(17,2,8),'y':randint(17,2,8)}
        elif task=='residual_cnn':item={'x':randn(2,3,16,16),'y':randint(5,2)}
        else: item={'x':randn(4,4),'action':randint(2,4),'return':randn(4)}
        result.append(item)
    return result


def loss_and_outputs(task, model, batch):
    if task=='graph_attention':
        output=model(batch['x'],batch['adjacency'])
        return F.nll_loss(output,batch['y']),output
    if task=='gpt_nano':
        logits,loss=model(batch['x'],batch['y'])
        return loss,logits
    if task=='variational_autoencoder':
        with patch('torch.randn_like',lambda tensor:batch['epsilon'].to(tensor)):
            reconstruction,mu,logvar=model(batch['x'])
        loss=F.binary_cross_entropy(reconstruction,batch['x'].view(2,784),reduction='sum')/2
        loss=loss-0.5*(1+logvar-mu.pow(2)-logvar.exp()).sum()/2
        return loss,(reconstruction,mu,logvar)
    if task=='recurrent_language_model':
        output,hidden=model(batch['x'],model.init_hidden(2))
        return F.nll_loss(output,batch['y']),(output,*hidden)
    output=model(batch['x'])
    if task=='residual_cnn':return F.cross_entropy(output,batch['y']),output
    if task in ('cnn_classifier','transformer_language_model'):
        return F.nll_loss(output.reshape(-1,output.shape[-1]),batch['y']),output
    if task=='actor_critic':
        probabilities,values=output
        selected=probabilities[torch.arange(4),batch['action']]
        loss=-(selected.log()*batch['return']).mean()+F.mse_loss(values.flatten(),batch['return'])
        return loss,output
    if task=='reinforce':
        selected=output[torch.arange(4),batch['action']]
        return -(selected.log()*batch['return']).mean(),output
    return F.mse_loss(output,batch['y']),output


def contracts():
    return {'status':'source workload contract draft; target healthy gate and native baseline smoke required before formal freeze',
      'scope':'Migrate extracted public model workloads with three consecutive optimizer steps; not dataset pipelines, environment interaction, adversarial GAN optimization, or whole applications.',
      'precision':'float64 in source and target; target JAX x64 enabled',
      'seeds':[8101,8102,8103],
      'parameter_contract':'Exact source parameter names/shapes/initial arrays; differentiate the declared loss with JAX in the external worker; compare full per-parameter gradients, updates and post-step parameters, never only norms.',
      'state_contract':'Optimizer state continues for three steps. DCGAN training BatchNorm running means/variances/num_batches_tracked are supplied and checked after every step. Language-model recurrent state starts at public zero tensors for each independent batch. Positional-encoding buffer supplied. Source-gradient None masks are explicit; target must not update those parameters.',
      'randomness':'Three fixed batches shared by all methods. VAE receives public epsilon with shape (2,20), replacing only the draw from torch.randn_like in the source adapter. Dropout disabled by eval mode for CNN/Transformer/REINFORCE and configured 0 for RNN; all parameters still differentiated and optimized. DCGAN remains train mode.',
      'acceptance_pending':'Freeze elementwise mixed absolute/relative tolerances, shape validation and independent JAX differentiation before first formal translation call. No result-selected thresholds.',
      'tasks':{name:{'source':row[0],'class':row[1],'constructor_args':row[2],'mode':row[3],
                     'constructor_expression':constructor(name),
                     'optimizer':{'type':'SGD','learning_rate':0.01,'momentum':0.9} if row[4]=='sgd' else {'type':'Adam','learning_rate':0.001,'betas':[0.9,0.999],'epsilon':1e-8},
                     'runtime_globals':{'nz':8,'ngf':4,'nc':1} if name=='gan_generator' else {}}
               for name,row in TASKS.items()}}


if __name__=='__main__':
    import json
    print(json.dumps(contracts(),indent=2))
