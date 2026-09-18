from __future__ import annotations

MODEL_VARIANT = 'mlp'
import math
import torch
import torch.nn as nn


class CandidateResidual(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Conv2d(4, 4, 1) if MODEL_VARIANT == 'cnn' else nn.Linear(4, 4)
        self.skip = nn.Conv2d(4, 4, 1) if MODEL_VARIANT == 'cnn' else nn.Linear(4, 4)

    def forward(self, x):
        return torch.relu(self.fc(x)) + self.skip(x)


def _candidate_attention(q, k, v, mask):
    scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(q.shape[-1])
    return torch.matmul(torch.softmax(scores + mask, dim=-1), v)


def _candidate_mask_fill(scores, keep_mask):
    return scores.masked_fill(~keep_mask, -10000.0)


def _rotate_half(x):
    return torch.stack((-x[..., 1::2], x[..., 0::2]), dim=-1).flatten(-2)


def _candidate_rope(x, cos, sin):
    return x * cos + _rotate_half(x) * sin


def build_model():
    return CandidateResidual()
