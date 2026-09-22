"""Trusted JAX x64 execution; candidate implements forward only."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import traceback
os.environ['JAX_PLATFORMS']='cpu'
os.environ['XLA_FLAGS']='--xla_cpu_multi_thread_eigen=false'
os.environ['JAX_ENABLE_X64']='true'
os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
import jax
import jax.numpy as jnp
import numpy as np
import optax
from formal_api import loss_from_outputs,make_optimizer


def outputs_tree(value):
    if isinstance(value,(tuple,list)):
        return {str(i):v for i,v in enumerate(value)}
    return {'0':value}


def main():
    workspace,seed,artifact=Path(sys.argv[1]),int(sys.argv[2]),Path(sys.argv[3])
    contract=json.loads((workspace/'task.json').read_text());task=contract['task']
    spec=importlib.util.spec_from_file_location('candidate',workspace/'candidate.py')
    candidate=importlib.util.module_from_spec(spec);spec.loader.exec_module(candidate)
    data=np.load(workspace/'inputs'/f'{seed}.npz')
    p={k[2:]:jnp.array(data[k]) for k in data.files if k.startswith('p:')}
    buffers={k[2:]:jnp.array(data[k]) for k in data.files if k.startswith('b:')}
    initial_shapes={k:v.shape for k,v in p.items()};buffer_shapes={k:v.shape for k,v in buffers.items()}
    values={'initial:p:'+k:np.asarray(v) for k,v in p.items()}
    values.update({'initial:b:'+k:np.asarray(v) for k,v in buffers.items()})
    optimizer=make_optimizer(contract);state=optimizer.init(p)
    for step in range(3):
        batch={k.split(':',2)[2]:jnp.array(data[k]) for k in data.files if k.startswith(f'batch:{step}:')}
        before={k:v for k,v in p.items()}
        def objective(params):
            outputs,new_buffers=candidate.forward(params,buffers,batch,task)
            return loss_from_outputs(task,outputs,batch),(outputs,new_buffers)
        (loss,(outputs,new_buffers)),gradients=jax.value_and_grad(objective,has_aux=True)(before)
        if gradients.keys()!=initial_shapes.keys() or any(gradients[k].shape!=initial_shapes[k] for k in gradients):
            raise ValueError('Gradient parameter names/shapes differ from source')
        if new_buffers.keys()!=buffer_shapes.keys() or any(new_buffers[k].shape!=buffer_shapes[k] for k in new_buffers):
            raise ValueError('Buffer names/shapes differ from source')
        updates,state=optimizer.update(gradients,state,before)
        p=optax.apply_updates(before,updates);buffers=new_buffers
        values[f'{step}:loss']=np.asarray(loss)
        for kind,tree in [('outputs',outputs_tree(outputs)),('gradients',gradients),('updates',{k:p[k]-before[k] for k in p}),('parameters',p),('buffers',buffers)]:
            for k,v in tree.items():
                if not isinstance(v,jax.Array): raise TypeError('Non-JAX result '+kind+':'+k)
                values[f'{step}:{kind}:{k}']=np.asarray(v)
    np.savez_compressed(artifact,**values)
    print(json.dumps({'status':'ok','artifact':artifact.name,'arrays':len(values),'backend':'jax.value_and_grad+optax','jax_x64':jax.config.x64_enabled}))


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(json.dumps({'status':'failed','error_type':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc()}))
        sys.exit(1)
