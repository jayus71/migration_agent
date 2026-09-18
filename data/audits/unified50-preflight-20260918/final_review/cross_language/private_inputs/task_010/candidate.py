import argparse
import os
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from torchvision.datasets import ImageFolder
from torchvision.models import resnet18, ResNet18_Weights

MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]
BATCH_SIZE = 32
NUM_EPOCHS = 10
LR = 0.001
BASE_LR = 0.1 * LR


class SoftmaxCrossEntropy(nn.Module):
    """DJL SoftmaxCrossEntropy custom loss, operating on probabilities."""

    def __init__(self, name="SoftmaxCrossEntropy"):
        super().__init__()
        self.name = name

    def forward(self, labels, predictions):
        # labels: [N, C] one-hot
        # predictions: [N, C] probabilities
        pred = predictions.log()
        lab = labels.reshape(pred.shape)
        loss = -(pred * lab).sum(dim=-1, keepdim=True)
        return loss.mean()


class TransferFreshFruitModel(nn.Module):
    """ResNet18 embedding + squeeze + Linear(512, 2) + softmax."""

    def __init__(self, train_param=False):
        super().__init__()
        self.base = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)
        self.base.fc = nn.Identity()
        self.linear = nn.Linear(512, 2)
        self.train_param = train_param
        if not train_param:
            for p in self.base.parameters():
                p.requires_grad = False

    def forward(self, x):
        x = self.base(x)
        x = x.squeeze(2).squeeze(3)  # [N,512,1,1] -> [N,512]
        x = self.linear(x)
        x = torch.softmax(x, dim=1)
        return x


class FruitsFreshAndRotten(Dataset):
    """Minimal ImageFolder-backed dataset with one-hot targets."""

    def __init__(self, root, usage="train", transform=None):
        self.root = Path(root) / usage
        self.dataset = ImageFolder(str(self.root), transform=transform)
        self.classes = self.dataset.classes

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, idx):
        img, label = self.dataset[idx]
        target = torch.zeros(2, dtype=torch.float32)
        target[label] = 1.0
        return img, target


def get_transforms(train=True):
    if train:
        return transforms.Compose(
            [
                transforms.RandomResizedCrop(256),
                transforms.RandomVerticalFlip(),
                transforms.RandomHorizontalFlip(),
                transforms.Resize((256, 256)),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(mean=MEAN, std=STD),
            ]
        )
    else:
        return transforms.Compose(
            [
                transforms.Resize((256, 256)),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(mean=MEAN, std=STD),
            ]
        )


def get_data(usage, batch_size, data_root):
    train = usage == "train"
    transform = get_transforms(train)
    dataset = FruitsFreshAndRotten(data_root, usage, transform)
    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=train,
        num_workers=4,
        pin_memory=True,
    )
    return loader


class TrainingContextAdapter:
    """Implements the common translated-program interface."""

    def __init__(self, context):
        self.context = context

        train_param = False
        if context is not None:
            if isinstance(context, dict):
                train_param = context.get("train_param", False)
            else:
                train_param = getattr(context, "train_param", False)
        self.train_param = train_param

        self.model = TransferFreshFruitModel(train_param=train_param)

        # Load shared frozen asset if supplied.
        ctx_assets = None
        if context is not None:
            if isinstance(context, dict):
                ctx_assets = context.get("assets", None)
            else:
                ctx_assets = getattr(context, "assets", None)
        if ctx_assets and "resnet18_embedding" in ctx_assets:
            self._load_pretrained(ctx_assets["resnet18_embedding"])

        # Copy supplied frozen buffers.
        ctx_buffers = None
        if context is not None:
            if isinstance(context, dict):
                ctx_buffers = context.get("buffers", None)
            else:
                ctx_buffers = getattr(context, "buffers", None)
        if ctx_buffers is not None:
            base_params = list(self.model.base.parameters())
            for bp, buf in zip(base_params, ctx_buffers):
                if isinstance(buf, torch.Tensor):
                    bp.data.copy_(buf.data)

        # Copy supplied trainable parameters.
        ctx_params = None
        if context is not None:
            if isinstance(context, dict):
                ctx_params = context.get("parameters", None)
            else:
                ctx_params = getattr(context, "parameters", None)
        if ctx_params is not None:
            lin_params = [self.model.linear.weight, self.model.linear.bias]
            for lp, cp in zip(lin_params, ctx_params):
                if isinstance(cp, torch.Tensor):
                    lp.data.copy_(cp.data)

        # Collect trainable parameters in source order.
        if train_param:
            self._params = list(self.model.parameters())
        else:
            self._params = [self.model.linear.weight, self.model.linear.bias]

        for p in self._params:
            p.requires_grad = True

        # Optimizer with per-variable learning rates.
        param_groups = []
        if train_param:
            base_params = list(self.model.base.parameters())
            param_groups.append({"params": base_params, "lr": BASE_LR})
        param_groups.append(
            {"params": [self.model.linear.weight, self.model.linear.bias], "lr": LR}
        )
        self.optimizer = optim.Adam(
            param_groups,
            betas=(0.9, 0.999),
            eps=1e-8,
            weight_decay=0.0,
        )

        # Initialize Adam state to zero for every trainable parameter.
        for p in self._params:
            self.optimizer.state[p] = {
                "step": 0,
                "exp_avg": torch.zeros_like(p),
                "exp_avg_sq": torch.zeros_like(p),
            }

        self.loss_fn = SoftmaxCrossEntropy()

    def _load_pretrained(self, path):
        if not os.path.exists(path):
            return
        try:
            obj = torch.load(path, map_location="cpu")
        except Exception:
            return

        if isinstance(obj, dict):
            state_dict = obj
            if "state_dict" in state_dict:
                state_dict = state_dict["state_dict"]
            base_params = list(self.model.base.parameters())
            values = [v for v in state_dict.values() if isinstance(v, torch.Tensor)]
            if len(values) >= len(base_params):
                for bp, v in zip(base_params, values):
                    if bp.shape == v.shape:
                        bp.data.copy_(v.data)
            else:
                try:
                    self.model.base.load_state_dict(state_dict, strict=False)
                except Exception:
                    pass
        elif isinstance(obj, nn.Module):
            try:
                self.model.base.load_state_dict(obj.state_dict(), strict=False)
            except Exception:
                pass

    def parameters(self):
        return list(self._params)

    def buffers(self):
        if self.train_param:
            return []
        return list(self.model.base.parameters())

    def zero_grad(self):
        self.optimizer.zero_grad()

    def forward(self, inputs, labels):
        x = inputs[0]
        out = self.model(x)
        return [out]

    def loss(self, outputs, labels):
        return self.loss_fn(labels[0], outputs[0])

    def backward(self, loss):
        loss.backward()

    def step(self):
        self.optimizer.step()

    def optimizer_state(self):
        states = []
        for p in self._params:
            st = self.optimizer.state.get(p, None)
            if st is None:
                states.append(
                    {
                        "updates": 0,
                        "means": torch.zeros_like(p),
                        "variances": torch.zeros_like(p),
                    }
                )
            else:
                step = st.get("step", 0)
                if isinstance(step, torch.Tensor):
                    step = int(step.item())
                else:
                    step = int(step)
                states.append(
                    {
                        "updates": step,
                        "means": st.get("exp_avg", torch.zeros_like(p)),
                        "variances": st.get("exp_avg_sq", torch.zeros_like(p)),
                    }
                )
        return states


def build_training(context):
    return TrainingContextAdapter(context)


def setup_training_config(model, train_param):
    param_groups = []
    if train_param:
        base_params = list(model.base.parameters())
        param_groups.append({"params": base_params, "lr": BASE_LR})
    param_groups.append(
        {"params": [model.linear.weight, model.linear.bias], "lr": LR}
    )
    optimizer = optim.Adam(
        param_groups,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0.0,
    )
    return optimizer


def train_epoch(model, loader, optimizer, loss_fn, device):
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0
    for inputs, labels in loader:
        inputs = inputs.to(device)
        labels = labels.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = loss_fn(labels, outputs)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * inputs.size(0)
        preds = outputs.argmax(dim=1)
        targets = labels.argmax(dim=1)
        correct += (preds == targets).sum().item()
        total += inputs.size(0)
    return total_loss / total, correct / total


def validate(model, loader, loss_fn, device):
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    with torch.no_grad():
        for inputs, labels in loader:
            inputs = inputs.to(device)
            labels = labels.to(device)
            outputs = model(inputs)
            loss = loss_fn(labels, outputs)
            total_loss += loss.item() * inputs.size(0)
            preds = outputs.argmax(dim=1)
            targets = labels.argmax(dim=1)
            correct += (preds == targets).sum().item()
            total += inputs.size(0)
    return total_loss / total, correct / total


def save_checkpoint(model, optimizer, epoch, train_loss, train_acc, val_loss, val_acc, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    checkpoint = {
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "train_loss": train_loss,
        "train_acc": train_acc,
        "val_loss": val_loss,
        "val_acc": val_acc,
        "Accuracy": f"{val_acc:.5f}",
        "Loss": f"{val_loss:.5f}",
    }
    torch.save(checkpoint, os.path.join(output_dir, f"checkpoint-{epoch:04d}.pt"))
    torch.save(checkpoint, os.path.join(output_dir, "checkpoint-latest.pt"))


def run_example(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--train-param", action="store_true")
    parser.add_argument("--data-root", type=str, default="data/fruits")
    parser.add_argument("--output-dir", type=str, default="build/fruits")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--epochs", type=int, default=NUM_EPOCHS)
    args = parser.parse_args(args)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = TransferFreshFruitModel(train_param=args.train_param)
    model.to(device)

    optimizer = setup_training_config(model, args.train_param)
    loss_fn = SoftmaxCrossEntropy()

    train_loader = get_data("train", args.batch_size, args.data_root)
    test_loader = get_data("test", args.batch_size, args.data_root)

    for epoch in range(1, args.epochs + 1):
        train_loss, train_acc = train_epoch(
            model, train_loader, optimizer, loss_fn, device
        )
        val_loss, val_acc = validate(model, test_loader, loss_fn, device)
        print(
            f"Epoch {epoch}: "
            f"train_loss={train_loss:.4f}, train_acc={train_acc:.4f}, "
            f"val_loss={val_loss:.4f}, val_acc={val_acc:.4f}"
        )
        save_checkpoint(
            model,
            optimizer,
            epoch,
            train_loss,
            train_acc,
            val_loss,
            val_acc,
            args.output_dir,
        )

    return model


if __name__ == "__main__":
    run_example(None)
