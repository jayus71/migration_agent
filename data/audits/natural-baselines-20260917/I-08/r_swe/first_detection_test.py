import json, random, copy
import numpy as np
import torch
import importlib.util, sys

p = json.load(open('task.json'))

def make_data(seed):
    gen = torch.Generator(device='cpu').manual_seed(seed)
    x = torch.randn(*p['input_shape'], generator=gen)
    y = torch.randint(0, p['num_classes'], (p['input_shape'][0],), generator=gen, dtype=torch.long)
    return x, y

# load source module
spec_s = importlib.util.spec_from_file_location("src_mod", "source.py")
src = importlib.util.module_from_spec(spec_s)
spec_s.loader.exec_module(src)

import candidate

random.seed(p['seed']); np.random.seed(p['seed']); torch.manual_seed(p['seed'])
m_src = src.build_model()
state0 = {k: v.clone() for k, v in m_src.state_dict().items()}

# same init for candidate
torch.manual_seed(p['seed'])
m_cand = candidate.build_model()
for k in state0:
    m_cand.state_dict()[k].copy_(state0[k])

x, y = make_data(p['seed']+101)

m_src.train()
loss_s = src.train_one_step(m_src, x.clone(), y.clone(), lr=p['lr'])
m_cand.train()
loss_c = candidate.train_one_step(m_cand, x.clone(), y.clone(), lr=p['lr'])

print("loss_src", loss_s, "loss_cand", loss_c)
for k in state0:
    d = (m_src.state_dict()[k] - m_cand.state_dict()[k]).abs().max().item()
    print(f"param {k}: maxdiff {d}, src_change {(m_src.state_dict()[k]-state0[k]).abs().max().item()}, cand_change {(m_cand.state_dict()[k]-state0[k]).abs().max().item()}")
