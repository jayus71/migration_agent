from __future__ import annotations
MODEL_VARIANT = 'causal_lm'
BATCH_SEED = 6501
import torch
import torch.nn as nn
import torch.optim as optim

class TinyNet(nn.Module):

    def __init__(self):
        super().__init__()
        self.fc1 = nn.Conv2d(3, 4, 1) if MODEL_VARIANT == 'cnn' else nn.Linear(3, 4)
        self.fc2 = nn.Conv2d(4, 2, 1) if MODEL_VARIANT == 'cnn' else nn.Linear(4, 2)

    def forward(self, x):
        return self.fc2(torch.relu(self.fc1(x)))

def build_model():
    return TinyNet()

def _batch():
    generator = torch.Generator().manual_seed(BATCH_SEED)
    if MODEL_VARIANT == 'cnn':
        shapes = ((5, 3, 4, 4), (5, 2, 4, 4))
    elif MODEL_VARIANT in ('transformer', 'causal_lm'):
        length = 6 if MODEL_VARIANT == 'transformer' else 8
        shapes = ((5, length, 3), (5, length, 2))
    else:
        shapes = ((5, 3), (5, 2))
    return tuple((torch.randn(shape, generator=generator) for shape in shapes))

def train_step(model, x, y):
    optimizer = optim.SGD([p for p in model.parameters() if p.requires_grad], lr=0.2)
    optimizer.zero_grad()
    loss = torch.nn.functional.mse_loss(model(x), y)
    loss.backward()
    optimizer.step()
    optimizer.zero_grad()
    return float(loss.detach().item())
