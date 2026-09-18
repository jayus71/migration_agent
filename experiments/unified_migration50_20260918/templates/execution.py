import torch
import torch.nn as nn


class TorchLikeTensor:
    def __init__(self, value):
        self.value = value


def input_batch():
    return {'input_ids': torch.arange(4)}


def boundary_op(x):
    return TorchLikeTensor(x + 1.0)


def downstream_norm(x):
    return float(x.value.float().norm().item())


def dtype_sensitive_matmul(x, weight):
    return torch.matmul(x.float(), weight.float()).to(x.dtype)


def gather_tokens(table):
    return table[torch.arange(6, dtype=torch.long)].sum()


def require_mapping(batch):
    return float(batch['input_ids'].float().sum().item())


OP_REGISTRY = {'mean.default': lambda x: x.mean(), 'mean.dim': lambda x: x.mean(dim=0)}


def run_registered_mean(x):
    return OP_REGISTRY['mean.default'](x)


def tuple_tensor_op(x):
    return TorchLikeTensor(x + 1.0), TorchLikeTensor(x + 2.0)


def consume_tensor_tuple(pair):
    return float((pair[0].value + pair[1].value).float().sum().item())


def project_high_rank(x):
    return x.permute(0, 2, 1, 3).reshape(x.shape[0] * x.shape[2], x.shape[1], x.shape[3])
