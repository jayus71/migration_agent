import json, random
import numpy as np
import torch, torch.nn as nn
import importlib.util, sys

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name]=m
    spec.loader.exec_module(m)
    return m

p=json.load(open('task.json'))
random.seed(p['seed']); np.random.seed(p['seed']); torch.manual_seed(p['seed'])
src = load('src_frag','source.py')
model_s = src.build_model()
gen=torch.Generator(device='cpu').manual_seed(p['seed']+101)
x=torch.randn(*p['input_shape'],generator=gen)
y=torch.randint(0,p['num_classes'],(p['input_shape'][0],),generator=gen,dtype=torch.long)

# native grads
opt = torch.optim.AdamW(model_s.parameters(), lr=p['lr'])
opt.zero_grad()
loss = nn.CrossEntropyLoss()(model_s(x), y)
loss.backward()
grads_s = {k:(v.grad.clone() if v.grad is not None else None) for k,v in model_s.named_parameters()}

# candidate
random.seed(p['seed']); np.random.seed(p['seed']); torch.manual_seed(p['seed'])
cand = load('cand_frag','candidate.py')
model_c = cand.build_model()
loss_c = cand.train_one_step(model_c, x, y, lr=p['lr'])
grads_c = {k:(v.grad.clone() if v.grad is not None else None) for k,v in model_c.named_parameters()}

for k in grads_s:
    gs = grads_s[k]; gc = grads_c.get(k)
    if gc is None:
        print(k, "cand grad None"); continue
    print(f"{k:20s} native_norm={gs.norm().item():.6e} cand_norm={gc.norm().item():.6e} close={torch.allclose(gs,gc,atol=1e-5)} maxdiff={(gs-gc).abs().max().item():.3e}")
