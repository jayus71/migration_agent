import json, random
import numpy as np
import torch
import importlib.util
def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m
p = json.load(open('task.json'))
def make(seed, mod):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    model = mod.build_model()
    gen = torch.Generator(device='cpu').manual_seed(seed+101)
    x = torch.randn(*p['input_shape'], generator=gen)
    y = torch.randint(0, p['num_classes'], (p['input_shape'][0],), generator=gen, dtype=torch.long)
    model.train()
    return model, x, y
src = load('source.py','source'); cand = load('candidate.py','candidate')

sm,x,y = make(p['seed'],src)
sm_init = {n: p.clone() for n,p in sm.named_parameters()}
l1 = src.train_one_step(sm,x,y,lr=p['lr'])
print("sources moves:")
for n,pp in sm.named_parameters():
    print("  ", n, (pp.detach()-sm_init[n]).abs().max().item())

cm,cx,cy = make(p['seed'],cand)
cm_init = {n: pp.clone() for n,pp in cm.named_parameters()}
l2 = cand.train_one_step(cm,cx,cy,lr=p['lr'])
print("candidate moves:")
for n,pp in cm.named_parameters():
    print("  ", n, (pp.detach()-cm_init[n]).abs().max().item())
