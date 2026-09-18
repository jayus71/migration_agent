import torch


def workload(parameters, transform):
    selected = [parameter for parameter in parameters if parameter.requires_grad]
    return torch.optim.SGD(selected, lr=float(transform['learning_rate']))
