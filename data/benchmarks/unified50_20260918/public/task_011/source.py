import torch

def workload(value):
    return torch.ops.aten.relu.default(value)
