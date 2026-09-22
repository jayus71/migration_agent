"""Public PyTorch source contracts for an explicitly controlled development set.

These source programs were written first from PyTorch training semantics. They
are not recovered from a hidden target. Inputs and initial parameters are shared
with the target by the external evaluator.
"""
import torch
from torch import nn


class ResidualMLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.input = nn.Linear(6, 8)
        self.residual = nn.Linear(8, 8)
        self.output = nn.Linear(8, 3)

    def forward(self, x):
        h = torch.tanh(self.input(x))
        h = h + torch.tanh(self.residual(h))
        return self.output(h)


class TinyAttention(nn.Module):
    def __init__(self):
        super().__init__()
        self.query = nn.Linear(6, 6)
        self.key = nn.Linear(6, 6, bias=False)
        self.value = nn.Linear(6, 6)
        self.output = nn.Linear(6, 3)

    def forward(self, x):
        q, k, v = self.query(x), self.key(x), self.value(x)
        weights = torch.softmax(q @ k.transpose(-1, -2) / (6 ** 0.5), -1)
        h = (weights @ v + x).mean(dim=1)
        return self.output(h)


def build_model(task):
    return ResidualMLP() if task == 'task_001' else TinyAttention()


def build_optimizer(task, parameters):
    if task == 'task_001':
        return torch.optim.SGD(parameters, lr=0.03, momentum=0.9)
    return torch.optim.Adam(parameters, lr=0.01, betas=(0.9, 0.999), eps=1e-8)


def make_batches(task, seed):
    generator = torch.Generator().manual_seed(seed + 10000)
    shape = (7, 6) if task == 'task_001' else (7, 4, 6)
    return [(torch.randn(shape, generator=generator),
             torch.randint(0, 3, (7,), generator=generator)) for _ in range(3)]
