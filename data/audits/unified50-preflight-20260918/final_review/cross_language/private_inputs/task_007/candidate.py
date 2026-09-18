import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from typing import List, Dict, Any, Tuple
import math

class DeepARModel(nn.Module):
    """DeepAR network matching the DJL DeepARNetwork architecture."""
    def __init__(self, cardinality: List[int], embedding_dims: List[int],
                 hidden_size: int = 40, num_layers: int = 2, dropout: float = 0.0):
        super().__init__()
        self.cardinality = cardinality
        self.embedding_dims = embedding_dims
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.num_lags = 17

        # Static categorical embeddings
        self.embeddings = nn.ModuleList([
            nn.Embedding(card, dim) for card, dim in zip(cardinality, embedding_dims)
        ])

        # LSTM input size = static_dim (sum emb + 1) + time_feat (3) + observed (1) + is_pad (1) + lags (17)
        static_dim = sum(embedding_dims) + 1  # +1 for static real
        time_feat_dim = 3
        observed_dim = 1
        is_pad_dim = 1
        lstm_input_size = static_dim + time_feat_dim + observed_dim + is_pad_dim + self.num_lags
        assert lstm_input_size == 86, f"Expected LSTM input 86, got {lstm_input_size}"

        self.lstm = nn.LSTM(
            input_size=lstm_input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            batch_first=True
        )

        # Distribution output projections (NegativeBinomial: total_count and logits)
        self.total_count_proj = nn.Linear(hidden_size, 1)
        self.logits_proj = nn.Linear(hidden_size, 1)

    def forward(self, inputs: List[torch.Tensor]) -> List[torch.Tensor]:
        (
            feat_static_cat,
            feat_static_real,
            past_time_feat,
            past_target,
            past_observed,
            past_is_pad,
            future_time_feat,
            future_target,
            future_observed
        ) = inputs

        # 1. Static features
        emb_list = [emb(feat_static_cat[:, i]) for i, emb in enumerate(self.embeddings)]
        static_cat_emb = torch.cat(emb_list, dim=-1)          # (N, 63)
        static_feat = torch.cat([static_cat_emb, feat_static_real], dim=-1)  # (N, 64)

        # 2. Concatenate past and future along time dimension
        time_feat = torch.cat([past_time_feat, future_time_feat], dim=1)   # (N, 169, 3)
        target = torch.cat([past_target, future_target], dim=1)            # (N, 169)
        observed = torch.cat([past_observed, future_observed], dim=1)      # (N, 169)

        # Future is_pad is zeros
        future_is_pad = torch.zeros_like(future_target)                    # (N, 4)
        is_pad = torch.cat([past_is_pad, future_is_pad], dim=1)            # (N, 169)

        # 3. Compute scale from past target and past observed (GluonTS style)
        past_obs_sum = past_observed.sum(dim=1, keepdim=True)              # (N, 1)
        past_obs_sum = torch.clamp(past_obs_sum, min=1.0)
        scale = (past_target * past_observed).abs().sum(dim=1, keepdim=True) / past_obs_sum
        scale = torch.clamp(scale, min=1e-10)                              # (N, 1)

        # 4. Scale target
        scaled_target = target / scale                                     # (N, 169)

        # 5. Create lag features (lags 1..17)
        N, T = scaled_target.shape
        lag_feat = torch.zeros(N, T, self.num_lags, device=scaled_target.device)
        for lag in range(1, self.num_lags + 1):
            if lag < T:
                lag_feat[:, lag:, lag-1] = scaled_target[:, :-lag]         # (N, 169, 17)

        # 6. Prepare LSTM input
        static_feat_exp = static_feat.unsqueeze(1).expand(-1, T, -1)       # (N, 169, 64)
        observed_exp = observed.unsqueeze(-1)                              # (N, 169, 1)
        is_pad_exp = is_pad.unsqueeze(-1)                                  # (N, 169, 1)

        lstm_input = torch.cat([
            static_feat_exp,
            time_feat,
            observed_exp,
            is_pad_exp,
            lag_feat
        ], dim=-1)                                                         # (N, 169, 86)

        # 7. LSTM
        lstm_out, _ = self.lstm(lstm_input)                                # (N, 169, 40)

        # 8. Distribution parameters for the last 11 steps (matches label shape)
        out_len = 11
        lstm_out_last = lstm_out[:, -out_len:, :]                          # (N, 11, 40)

        total_count = self.total_count_proj(lstm_out_last).squeeze(-1)     # (N, 11)
        logits = self.logits_proj(lstm_out_last).squeeze(-1)               # (N, 11)

        # NegativeBinomial total_count must be positive
        total_count = F.softplus(total_count) + 1e-5

        # Mean of the distribution (auxiliary output)
        mean = total_count * torch.exp(logits)                             # (N, 11)

        return [total_count, scale, logits, mean]


class DeepARTrainer:
    """Training interface for the DeepAR model."""
    def __init__(self, context: Dict[str, Any]):
        self.context = context
        self.device = torch.device('cpu')

        # Fixed configuration from the original source
        cardinality = [3, 10, 3, 7, 3049]
        embedding_dims = [2, 5, 2, 4, 50]

        self.model = DeepARModel(cardinality, embedding_dims)
        self.model.to(self.device)

        # Map parameters to context order
        self.param_names = [p['name'] for p in context['parameters']]
        self.param_shapes = [tuple(p['shape']) for p in context['parameters']]

        # Build ordered parameter list matching context.parameters order
        self.ordered_params = []
        # Projections
        self.ordered_params.append(self.model.total_count_proj.weight)
        self.ordered_params.append(self.model.total_count_proj.bias)
        self.ordered_params.append(self.model.logits_proj.weight)
        self.ordered_params.append(self.model.logits_proj.bias)
        # Embeddings
        for emb in self.model.embeddings:
            self.ordered_params.append(emb.weight)
        # LSTM layer 0
        self.ordered_params.append(self.model.lstm.weight_ih_l0)
        self.ordered_params.append(self.model.lstm.weight_hh_l0)
        self.ordered_params.append(self.model.lstm.bias_ih_l0)
        self.ordered_params.append(self.model.lstm.bias_hh_l0)
        # LSTM layer 1
        self.ordered_params.append(self.model.lstm.weight_ih_l1)
        self.ordered_params.append(self.model.lstm.weight_hh_l1)
        self.ordered_params.append(self.model.lstm.bias_ih_l1)
        self.ordered_params.append(self.model.lstm.bias_hh_l1)

        # Verify shapes
        for i, (param, name, shape) in enumerate(zip(self.ordered_params, self.param_names, self.param_shapes)):
            assert tuple(param.shape) == shape, f"Param {name} shape mismatch: {tuple(param.shape)} vs {shape}"

        # Optimizer: Adam with DJL defaults
        self.optimizer = optim.Adam(
            self.ordered_params,
            lr=0.001,
            betas=(0.9, 0.999),
            eps=1e-8
        )

    def parameters(self) -> List[torch.Tensor]:
        return self.ordered_params

    def buffers(self) -> List[torch.Tensor]:
        return []

    def zero_grad(self):
        self.optimizer.zero_grad()

    def forward(self, inputs: List[torch.Tensor], labels: List[torch.Tensor] = None) -> List[torch.Tensor]:
        return self.model(inputs)

    def loss(self, outputs: List[torch.Tensor], labels: List[torch.Tensor]) -> torch.Tensor:
        total_count, scale, logits, mean = outputs
        target = labels[0]  # (N, 11)
        dist = torch.distributions.NegativeBinomial(total_count=total_count, logits=logits)
        loss = -dist.log_prob(target).mean()
        return loss

    def backward(self, loss: torch.Tensor):
        loss.backward()

    def step(self):
        self.optimizer.step()

    def optimizer_state(self) -> List[Dict[str, Any]]:
        states = []
        for param in self.ordered_params:
            state = {'updates': 0}
            if param in self.optimizer.state:
                opt_state = self.optimizer.state[param]
                state['updates'] = opt_state['step'].item() if 'step' in opt_state else 0
                if 'exp_avg' in opt_state:
                    state['means'] = opt_state['exp_avg']
                if 'exp_avg_sq' in opt_state:
                    state['variances'] = opt_state['exp_avg_sq']
            states.append(state)
        return states


def build_training(context: Dict[str, Any]) -> DeepARTrainer:
    """Entry point for the paired training interface."""
    return DeepARTrainer(context)


if __name__ == '__main__':
    # Expensive training is guarded here.
    # The actual M5 dataset is not bundled with this translation.
    # Use build_training(context) for the paired training interface.
    print("DeepAR training entry point. Use build_training(context) for the interface.")
