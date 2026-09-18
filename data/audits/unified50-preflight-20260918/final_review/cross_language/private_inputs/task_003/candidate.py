import math
import os
import urllib.request
import argparse
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader, random_split

# ---------------------------------------------------------------------------
# Loss
# ---------------------------------------------------------------------------
class TabNetRegressionLoss(nn.Module):
    def __init__(self, lambda_sparse=1e-3):
        super().__init__()
        self.lambda_sparse = lambda_sparse

    def forward(self, outputs, labels):
        pred, mask = outputs
        mse = F.mse_loss(pred, labels)
        sparsity = (mask * torch.log(mask + 1e-15)).mean()
        return mse - self.lambda_sparse * sparsity


# ---------------------------------------------------------------------------
# Blocks
# ---------------------------------------------------------------------------
class GhostBatchNorm(nn.Module):
    def __init__(self, num_features, virtual_batch_size=128, momentum=0.01, eps=1e-5):
        super().__init__()
        self.bn = nn.BatchNorm1d(num_features, momentum=momentum, eps=eps)
        self.virtual_batch_size = virtual_batch_size

    def forward(self, x):
        if not self.training or x.shape[0] <= self.virtual_batch_size:
            return self.bn(x)
        chunks = torch.split(x, self.virtual_batch_size, dim=0)
        return torch.cat([self.bn(chunk) for chunk in chunks], dim=0)


class SequentialBlock(nn.Module):
    def __init__(self, input_dim, output_dim):
        super().__init__()
        self.add_module("01Linear", nn.Linear(input_dim, output_dim * 2))
        self.add_module("02GhostBatchNorm", GhostBatchNorm(output_dim * 2))

    def forward(self, x):
        x = self._modules["01Linear"](x)
        x = self._modules["02GhostBatchNorm"](x)
        x = x.view(x.shape[0], 2, x.shape[1] // 2)
        x = x[:, 0] * torch.sigmoid(x[:, 1])
        return x


class ParallelBlock(nn.Module):
    def __init__(self, input_dim, output_dim):
        super().__init__()
        self.add_module("01SequentialBlock", SequentialBlock(input_dim, output_dim))

    def forward(self, x):
        out = self._modules["01SequentialBlock"](x)
        return (out + x) * math.sqrt(0.5)


class FeatureTransformer(nn.Module):
    def __init__(self):
        super().__init__()
        self.add_module("01SequentialBlock", SequentialBlock(5, 128))
        self.add_module("02ParallelBlock", ParallelBlock(128, 128))
        self.add_module("03ParallelBlock", ParallelBlock(128, 128))
        self.add_module("04ParallelBlock", ParallelBlock(128, 128))

    def forward(self, x):
        x = self._modules["01SequentialBlock"](x)
        x = self._modules["02ParallelBlock"](x)
        x = self._modules["03ParallelBlock"](x)
        x = self._modules["04ParallelBlock"](x)
        return x


def sparsemax(z, dim=-1):
    z = z - z.max(dim=dim, keepdim=True).values
    z_sorted, _ = torch.sort(z, dim=dim, descending=True)
    cumsum = torch.cumsum(z_sorted, dim=dim)
    k = torch.arange(1, z.shape[dim] + 1, device=z.device, dtype=z.dtype)
    support = 1 + k * z_sorted > cumsum
    k_max = support.sum(dim=dim, keepdim=True).clamp(min=1)
    cumsum_k = cumsum.gather(dim, k_max - 1)
    tau = (cumsum_k - 1) / k_max.to(z.dtype)
    return torch.clamp(z - tau, min=0)


class AttentionTransformer(nn.Module):
    def __init__(self):
        super().__init__()
        self.add_module("01fullyConnected", nn.Linear(64, 5))
        self.add_module("02ghostBatchNorm", GhostBatchNorm(5))

    def forward(self, x, prior):
        x = self._modules["01fullyConnected"](x)
        x = self._modules["02ghostBatchNorm"](x)
        x = x * prior
        x = sparsemax(x, dim=-1)
        return x


class Step(nn.Module):
    def __init__(self):
        super().__init__()
        self.add_module("01featureTransformer", FeatureTransformer())
        self.add_module("02attentionTransformer", AttentionTransformer())


# ---------------------------------------------------------------------------
# Full model
# ---------------------------------------------------------------------------
class TabNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.add_module("01batchNorm", nn.BatchNorm1d(5, momentum=0.01, eps=1e-5))
        self.add_module("02sharedfc0", nn.Linear(5, 256))
        self.add_module("03sharedfc1", nn.Linear(128, 256))
        self.add_module("04featureTransformer", FeatureTransformer())
        self.add_module("05steps1", Step())
        self.add_module("06steps2", Step())
        self.add_module("07steps3", Step())
        self.add_module("08steps4", Step())
        self.add_module("09fullyConnected", nn.Linear(64, 1))

    def shared_glu(self, x):
        x = self._modules["02sharedfc0"](x)
        x = x.view(x.shape[0], 2, x.shape[1] // 2)
        x = x[:, 0] * torch.sigmoid(x[:, 1])
        res = x
        x = self._modules["03sharedfc1"](x)
        x = x.view(x.shape[0], 2, x.shape[1] // 2)
        x = x[:, 0] * torch.sigmoid(x[:, 1])
        x = (x + res) * math.sqrt(0.5)
        return x

    def forward(self, x):
        x = self._modules["01batchNorm"](x)

        shared_init = self.shared_glu(x)
        specific_init = self._modules["04featureTransformer"](x)
        init_out = shared_init + specific_init
        a = init_out[:, 64:]

        prior = torch.ones(x.shape[0], 5, device=x.device)
        output = torch.zeros(x.shape[0], 64, device=x.device)
        M_last = None

        for i in range(4):
            step_module = self._modules[f"0{5 + i}steps{i + 1}"]
            att = step_module._modules["02attentionTransformer"]
            ft = step_module._modules["01featureTransformer"]

            M = att(a, prior)
            masked_x = M * x

            shared_step = self.shared_glu(masked_x)
            specific_step = ft(masked_x)
            step_out = shared_step + specific_step

            d = step_out[:, :64]
            a = step_out[:, 64:]

            output += F.relu(d)
            prior = prior * (1.3 - M)
            M_last = M

        final = self._modules["09fullyConnected"](output)
        return final, M_last


# ---------------------------------------------------------------------------
# Training context for harness
# ---------------------------------------------------------------------------
class TrainingContext:
    def __init__(self, model, optimizer, loss_fn):
        self.model = model
        self.optimizer = optimizer
        self.loss_fn = loss_fn

    def parameters(self):
        return [p for p in self.model.parameters() if p.requires_grad]

    def buffers(self):
        return [b for b in self.model.buffers() if not b.requires_grad]

    def zero_grad(self):
        self.optimizer.zero_grad()

    def forward(self, inputs, labels):
        x = inputs[0]
        out = self.model(x)
        return list(out)

    def loss(self, outputs, labels):
        return self.loss_fn(outputs, labels[0])

    def backward(self, loss):
        loss.backward()

    def step(self):
        self.optimizer.step()

    def optimizer_state(self):
        state = []
        for p in self.parameters():
            if p in self.optimizer.state:
                s = self.optimizer.state[p]
                step = s["step"].item() if isinstance(s["step"], torch.Tensor) else s["step"]
                state.append({
                    "updates": int(step),
                    "means": s["exp_avg"],
                    "variances": s["exp_avg_sq"],
                })
            else:
                state.append({
                    "updates": 0,
                    "means": torch.zeros_like(p),
                    "variances": torch.zeros_like(p),
                })
        return state


def build_training(context):
    model = TabNet()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001, betas=(0.9, 0.999), eps=1e-8)
    loss_fn = TabNetRegressionLoss(lambda_sparse=1e-3)
    return TrainingContext(model, optimizer, loss_fn)


# ---------------------------------------------------------------------------
# Airfoil dataset (minimal implementation)
# ---------------------------------------------------------------------------
class AirfoilDataset(Dataset):
    def __init__(self, features, labels):
        self.features = torch.tensor(features, dtype=torch.float32)
        self.labels = torch.tensor(labels, dtype=torch.float32).view(-1, 1)

    def __len__(self):
        return len(self.features)

    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]


def load_airfoil_data(data_dir="data"):
    os.makedirs(data_dir, exist_ok=True)
    file_path = os.path.join(data_dir, "airfoil_self_noise.dat")
    if not os.path.exists(file_path):
        url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00291/airfoil_self_noise.dat"
        urllib.request.urlretrieve(url, file_path)

    features = []
    labels = []
    with open(file_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue
            vals = [float(v) for v in parts]
            features.append(vals[:5])
            labels.append(vals[5])
    return AirfoilDataset(features, labels)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--epoch", type=int, default=10)
    parser.add_argument("--output-dir", type=str, default="build/model")
    parser.add_argument("--data-dir", type=str, default="data")
    args = parser.parse_args()

    device = torch.device("cpu")
    dataset = load_airfoil_data(args.data_dir)

    # 8:2 train/validation split
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_set, val_set = random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_set, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_set, batch_size=args.batch_size, shuffle=False)

    model = TabNet().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001, betas=(0.9, 0.999), eps=1e-8)
    loss_fn = TabNetRegressionLoss(lambda_sparse=1e-3).to(device)

    os.makedirs(args.output_dir, exist_ok=True)

    for epoch in range(args.epoch):
        model.train()
        total_loss = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            out = model(x)
            loss = loss_fn(out, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * x.size(0)

        train_loss = total_loss / len(train_set)

        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                out = model(x)
                loss = loss_fn(out, y)
                val_loss += loss.item() * x.size(0)
        val_loss /= len(val_set)

        print(f"Epoch {epoch+1}/{args.epoch} - train_loss: {train_loss:.5f} - val_loss: {val_loss:.5f}")

        # Checkpoint
        ckpt_path = os.path.join(args.output_dir, f"tabnet_epoch_{epoch+1}.pt")
        torch.save({
            "epoch": epoch + 1,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "train_loss": train_loss,
            "val_loss": val_loss,
        }, ckpt_path)

    print("Training finished.")


if __name__ == "__main__":
    main()
