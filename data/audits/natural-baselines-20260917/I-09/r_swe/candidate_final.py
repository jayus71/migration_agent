# torch4ms-adapted frozen held-out gated spatial vision classifier
import torch
import torch.nn as nn
import torch4ms
from torch4ms.autograd.ms_autograd_function import extract_and_wrap_loss_fn
from torch4ms.optim import Torch4msOptimizer

class GatedVision(nn.Module):
    def __init__(self):
        super().__init__()
        self.value = nn.Conv2d(3, 7, 3, padding=1)
        self.gate = nn.Conv2d(3, 7, 1)
        self.norm = nn.GroupNorm(1, 7)
        self.head = nn.Linear(7, 5)

    def forward(self, x):
        x = self.norm(torch.relu(self.value(x)) * torch.sigmoid(self.gate(x)))
        return self.head(x.mean(dim=(2, 3)))

def build_model(params=None):
    return GatedVision()

def train_one_step(model, x, y, lr=7e-4):
    criterion = nn.CrossEntropyLoss()
    base_optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    optimizer = Torch4msOptimizer(base_optimizer, model)
    env = torch4ms.default_env()
    with env:
        optimizer.zero_grad()
        loss_wrapper = extract_and_wrap_loss_fn(model, criterion, x, y)
        loss = loss_wrapper.output
        loss.backward(module=model)
        optimizer.step()
        return float(loss.detach().item())
