# Frozen held-out bottleneck autoencoder-style classifier (torch4ms adapter).
import torch
import torch.nn as nn
import torch4ms
from torch4ms.autograd.ms_autograd_function import extract_and_wrap_loss_fn
from torch4ms.optim import Torch4msOptimizer


class AutoencoderHead(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(15, 10), nn.Tanh(), nn.Linear(10, 4))
        self.decoder = nn.Linear(4, 10)
        self.head = nn.Linear(14, 5)

    def forward(self, x):
        latent = self.encoder(x)
        reconstruction_feature = torch.relu(self.decoder(latent))
        return self.head(torch.cat((latent, reconstruction_feature), dim=1))


def build_model(params=None):
    return AutoencoderHead()


def train_one_step(model, x, y, lr=1e-3):
    env = torch4ms.default_env()
    base_optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    optimizer = Torch4msOptimizer(base_optimizer, model)
    with env:
        optimizer.zero_grad()
        loss_wrapper = extract_and_wrap_loss_fn(model, nn.CrossEntropyLoss(), x, y)
        loss = loss_wrapper.output
        # NOTE: the wrapped loss already carries the functional forward (all 8 params)
        # and the exact parameter list it was built from. Propagate that context
        # explicitly instead of relying on attribute lookup inside _ms_backward --
        # otherwise the GradOperation used for backward is out of sync with the
        # forward that produced the loss and encoder.0.{weight,bias} get a zero grad.
        loss.backward(
            module=model,
            inputs=loss_wrapper.inputs,
            forward_fn=loss_wrapper.forward_fn,
        )
        optimizer.step()
        return float(loss.detach().item())
