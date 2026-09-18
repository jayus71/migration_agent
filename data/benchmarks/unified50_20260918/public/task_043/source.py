from __future__ import annotations

MODEL_VARIANT = 'mlp'
import torch


def parameter_workload(model):
    return [(name, parameter) for name, parameter in model.named_parameters() if parameter.requires_grad]


def gradient_workload(parameter, gradient, environment, model, index):
    named = parameter_workload(model)
    if index < 0 or index >= len(named):
        raise IndexError('Trainable parameter index is out of range')
    _, destination = named[index]
    if destination is not parameter:
        raise ValueError('Parameter and trainable index disagree')
    if gradient.shape != destination.shape:
        raise ValueError('Gradient shape does not match parameter')
    destination.grad = gradient.detach().to(device=destination.device, dtype=destination.dtype).clone()
