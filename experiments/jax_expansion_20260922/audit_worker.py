"""Additional development audit, separate from the frozen acceptance protocol.

Recomputes gradients through JAX from candidate.forward, validates each tensor's
shape, and snapshots the parameter dictionary before candidate.train_step.
"""
import importlib.util
import json
import os
from pathlib import Path
import sys
os.environ['JAX_PLATFORMS']='cpu'
os.environ['XLA_FLAGS']='--xla_cpu_multi_thread_eigen=false'
os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
import jax
import jax.numpy as jnp
import numpy as np
import optax


def main():
    workspace,seed=Path(sys.argv[1]),int(sys.argv[2])
    task=json.loads((workspace/'task.json').read_text())['task']
    spec=importlib.util.spec_from_file_location('candidate',workspace/'candidate.py')
    candidate=importlib.util.module_from_spec(spec);spec.loader.exec_module(candidate)
    data=np.load(workspace/'inputs'/f'{seed}.npz')
    p={k[2:]:jnp.array(data[k]) for k in data.files if k.startswith('p:')}
    shapes={k:v.shape for k,v in p.items()};state=candidate.init_optimizer(p,task);steps=[]
    for i in range(3):
        x,y=jnp.array(data[f'x:{i}']),jnp.array(data[f'y:{i}'])
        before={k:v for k,v in p.items()}
        trusted_loss,trusted_grad=jax.value_and_grad(lambda params:optax.softmax_cross_entropy_with_integer_labels(candidate.forward(params,x,task),y).mean())(before)
        p,state,loss,grad=candidate.train_step(p,state,x,y,task)
        shape_ok=p.keys()==shapes.keys() and grad.keys()==shapes.keys() and all(p[k].shape==shapes[k] and grad[k].shape==shapes[k] for k in shapes)
        grad_ok=shape_ok and all(np.allclose(np.asarray(grad[k]),np.asarray(trusted_grad[k]),rtol=2e-4,atol=2e-7) for k in shapes)
        loss_ok=np.allclose(np.asarray(loss),np.asarray(trusted_loss),rtol=0,atol=2e-5)
        steps.append({'step':i+1,'shape_ok':shape_ok,'independent_jax_gradient_ok':grad_ok,
                      'independent_loss_ok':bool(loss_ok),'update_l2':{k:float(jnp.linalg.norm(p[k]-before[k])) for k in before}})
    print(json.dumps({'status':'ok','accepted':all(s['shape_ok'] and s['independent_jax_gradient_ok'] and s['independent_loss_ok'] for s in steps),'steps':steps}))


if __name__=='__main__':main()
