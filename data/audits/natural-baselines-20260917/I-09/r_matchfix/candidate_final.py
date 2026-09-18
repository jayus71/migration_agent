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
        wrapped_params = tuple(loss_wrapper.inputs)
        forward_fn = loss_wrapper.forward_fn

        # Backprop through the torch4ms/MindSpore graph, explicitly binding the
        # wrapped forward function and the full ordered list of trainable
        # parameter tensors so gradients are produced for EVERY parameter
        # (Conv2d / GroupNorm / Linear), not only the final Linear layer.
        loss.backward(inputs=wrapped_params, forward_fn=forward_fn)

        # The torch4ms backward stores gradients on the wrapped parameter
        # tensors; make sure each of them is propagated to the matching
        # PyTorch parameter before the native Adam step runs.
        from torch4ms.ops import mappings
        import torch.utils._mode_utils as mode_utils

        for i, param in enumerate(model.parameters()):
            if i >= len(wrapped_params):
                break
            wrapped = wrapped_params[i]
            grad = getattr(wrapped, "_t4ms_grad", None)
            if grad is None and isinstance(param, torch4ms.Tensor):
                grad = getattr(param, "_t4ms_grad", None)
            if grad is not None and getattr(param, "grad", None) is None:
                with mode_utils.no_dispatch(), torch._C.DisableTorchFunction():
                    grad_torch = mappings.ms2t(grad._elem)
                with torch.no_grad():
                    param.grad = grad_torch

        optimizer.step()
        return float(loss.detach().item())
