import os, sys, random, copy, json
import numpy as np
import torch, torch.nn as nn
sys.path.insert(0, os.getcwd())
import source, candidate

torch.manual_seed(0); np.random.seed(0); random.seed(0)
m_src = source.build_model()
m_cand = candidate.build_model()
m_cand.load_state_dict(m_src.state_dict())

gen = torch.Generator().manual_seed(123)
x = torch.randn(2,3,8,8, generator=gen)
y = torch.randint(0,5,(2,), generator=gen, dtype=torch.long)

# reference loss before update
with torch.no_grad():
    ref_loss = float(nn.CrossEntropyLoss()(m_src(x), y).item())
print("ref pre-update loss:", ref_loss)

# candidate
before = [p.detach().clone() for p in m_cand.parameters()]
l_cand = candidate.train_one_step(m_cand, x.clone(), y.clone(), lr=7e-4)
after = [p.detach().clone() for p in m_cand.parameters()]
print("cand loss:", l_cand)
print("cand param changed:", [float((a-b).abs().max()) for a,b in zip(after,before)])

# source
before_s = [p.detach().clone() for p in m_src.parameters()]
l_src = source.train_one_step(m_src, x.clone(), y.clone(), lr=7e-4)
after_s = [p.detach().clone() for p in m_src.parameters()]
print("src loss:", l_src)
print("src param changed:", [float((a-b).abs().max()) for a,b in zip(after_s,before_s)])

print("loss diff:", abs(l_cand-l_src))
print("param max diff vs source:", max(float((a-b).abs().max()) for a,b in zip(after, after_s)))
