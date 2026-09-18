import torch
import torch.nn as nn


class StableSoftmaxNet(nn.Module):
    def __init__(self, num_classes: int = 4) -> None:
        super().__init__()
        self.proj = nn.Linear(4, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.softmax(self.proj(x) * 1000.0, dim=-1)


def build_model(params: dict | None = None) -> nn.Module:
    params = params or {}
    return StableSoftmaxNet(num_classes=int(params.get('num_classes', 4)))
