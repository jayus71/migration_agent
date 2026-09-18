import argparse
import os
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

CIFAR10_MEAN = (0.4914, 0.4822, 0.4465)
CIFAR10_STD = (0.2470, 0.2435, 0.2616)


class MainBranch(nn.Module):
    def __init__(self, in_channels, mid_channels, out_channels, stride):
        super().__init__()
        self.add_module('01Conv2d', nn.Conv2d(in_channels, mid_channels, 1, 1, 0, bias=True))
        self.add_module('02BatchNorm', nn.BatchNorm2d(mid_channels))
        self.add_module('04Conv2d', nn.Conv2d(mid_channels, mid_channels, 3, stride, 1, bias=False))
        self.add_module('05BatchNorm', nn.BatchNorm2d(mid_channels))
        self.add_module('07Conv2d', nn.Conv2d(mid_channels, out_channels, 1, 1, 0, bias=True))
        self.add_module('08BatchNorm', nn.BatchNorm2d(out_channels))

    def forward(self, x):
        x = F.relu(self._modules['02BatchNorm'](self._modules['01Conv2d'](x)))
        x = F.relu(self._modules['05BatchNorm'](self._modules['04Conv2d'](x)))
        x = self._modules['08BatchNorm'](self._modules['07Conv2d'](x))
        return x


class ShortcutBranch(nn.Module):
    def __init__(self, in_channels, out_channels, stride):
        super().__init__()
        self.add_module('01Conv2d', nn.Conv2d(in_channels, out_channels, 1, stride, 0, bias=False))
        self.add_module('02BatchNorm', nn.BatchNorm2d(out_channels))

    def forward(self, x):
        return self._modules['02BatchNorm'](self._modules['01Conv2d'](x))


class ParallelBlock(nn.Module):
    def __init__(self, in_channels, mid_channels, out_channels, stride, use_shortcut):
        super().__init__()
        self.add_module('01SequentialBlock', MainBranch(in_channels, mid_channels, out_channels, stride))
        if use_shortcut:
            self.add_module('02SequentialBlock', ShortcutBranch(in_channels, out_channels, stride))

    def forward(self, x):
        out = self._modules['01SequentialBlock'](x)
        if hasattr(self, '02SequentialBlock'):
            out = out + self._modules['02SequentialBlock'](x)
        else:
            out = out + x
        return F.relu(out)


class ResNetV1(nn.Module):
    def __init__(self, out_size=10):
        super().__init__()
        self.add_module('01Conv2d', nn.Conv2d(3, 64, 3, 1, 1, bias=False))
        configs = [
            (64, 64, 256, 1, True),
            (256, 64, 256, 1, False),
            (256, 64, 256, 1, False),
            (256, 128, 512, 2, True),
            (512, 128, 512, 1, False),
            (512, 128, 512, 1, False),
            (512, 128, 512, 1, False),
            (512, 256, 1024, 2, True),
            (1024, 256, 1024, 1, False),
            (1024, 256, 1024, 1, False),
            (1024, 256, 1024, 1, False),
            (1024, 256, 1024, 1, False),
            (1024, 256, 1024, 1, False),
            (1024, 512, 2048, 2, True),
            (2048, 512, 2048, 1, False),
            (2048, 512, 2048, 1, False),
        ]
        for i, (in_c, mid_c, out_c, stride, use_shortcut) in enumerate(configs):
            block_name = f"{i+2:02d}ParallelBlock"
            self.add_module(block_name, ParallelBlock(in_c, mid_c, out_c, stride, use_shortcut))
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.add_module('20Linear', nn.Linear(2048, out_size))

    def forward(self, x):
        x = F.relu(self._modules['01Conv2d'](x))
        for name, module in self._modules.items():
            if 'ParallelBlock' in name:
                x = module(x)
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        x = self._modules['20Linear'](x)
        return x


class TrainingWrapper:
    def __init__(self, model, loss_fn, optimizer, optimizer_name, batch_size, pre_trained, device):
        self.model = model
        self.loss_fn = loss_fn
        self.optimizer = optimizer
        self.optimizer_name = optimizer_name
        self.batch_size = batch_size
        self.pre_trained = pre_trained
        self.device = device
        self.step_count = 0
        if optimizer_name == 'sgd':
            if pre_trained:
                epochs = [2, 5, 8]
            else:
                epochs = [20, 60, 90, 120, 180]
            self.steps = [(k * 60000) // batch_size for k in epochs]
        else:
            self.steps = None

    def parameters(self):
        return list(self.model.parameters())

    def buffers(self):
        return list(self.model.buffers())

    def zero_grad(self):
        self.optimizer.zero_grad()

    def forward(self, inputs, labels):
        x = inputs[0].to(self.device)
        self.model.train()
        logits = self.model(x)
        return [logits]

    def loss(self, outputs, labels):
        logits = outputs[0]
        target = labels[0].to(self.device)
        return self.loss_fn(logits, target)

    def backward(self, loss):
        loss.backward()
        if self.optimizer_name == 'sgd':
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=5.0)

    def step(self):
        if self.optimizer_name == 'sgd':
            lr = self._get_sgd_lr(self.step_count)
            for param_group in self.optimizer.param_groups:
                param_group['lr'] = lr
        self.optimizer.step()
        self.step_count += 1

    def _get_sgd_lr(self, step):
        if step < 200:
            begin_value = 1e-4
            main_value = self._get_main_lr(200)
            return begin_value + (main_value - begin_value) * (step / 200.0)
        else:
            return self._get_main_lr(step)

    def _get_main_lr(self, step):
        base = 1e-3
        factor = math.sqrt(0.1)
        mult = 1.0
        for s in self.steps:
            if step >= s:
                mult *= factor
        return base * mult

    def optimizer_state(self):
        states = []
        for p in self.model.parameters():
            d = {'updates': self.step_count}
            if self.optimizer_name == 'adam' and p in self.optimizer.state:
                state = self.optimizer.state[p]
                d['means'] = state['exp_avg']
                d['variances'] = state['exp_avg_sq']
            states.append(d)
        return states


def create_training_wrapper(optimizer_name, batch_size, pre_trained, device):
    if pre_trained:
        print("Warning: Pretrained model loading is not supported in this PyTorch translation. Using random initialization.")
    model = ResNetV1(out_size=10)
    model.to(device)
    loss_fn = nn.CrossEntropyLoss()
    if optimizer_name == 'adam':
        optimizer = optim.Adam(model.parameters())
    elif optimizer_name == 'sgd':
        optimizer = optim.SGD(model.parameters(), lr=1e-3, weight_decay=0.001)
    else:
        raise ValueError(f"Unknown optimizer: {optimizer_name}")
    return TrainingWrapper(model, loss_fn, optimizer, optimizer_name, batch_size, pre_trained, device)


def build_training(context):
    if context is None:
        context = {}
    optimizer_name = getattr(context, 'optimizer', 'adam') if not isinstance(context, dict) else context.get('optimizer', 'adam')
    batch_size = getattr(context, 'batch_size', 32) if not isinstance(context, dict) else context.get('batch_size', 32)
    pre_trained = getattr(context, 'pre_trained', False) if not isinstance(context, dict) else context.get('pre_trained', False)
    device = torch.device('cpu')
    return create_training_wrapper(optimizer_name, batch_size, pre_trained, device)


def get_dataset(usage, batch_size, limit, shuffle=True):
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(CIFAR10_MEAN, CIFAR10_STD),
    ])
    if usage == 'train':
        dataset = datasets.CIFAR10(root='./data', train=True, download=True, transform=transform)
    else:
        dataset = datasets.CIFAR10(root='./data', train=False, download=True, transform=transform)
    if limit > 0:
        indices = list(range(min(limit, len(dataset))))
        dataset = torch.utils.data.Subset(dataset, indices)
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle, num_workers=2)


def evaluate(model, dataloader, loss_fn, device):
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    with torch.no_grad():
        for inputs, labels in dataloader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss = loss_fn(outputs, labels)
            total_loss += loss.item() * inputs.size(0)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
    avg_loss = total_loss / total if total > 0 else 0.0
    accuracy = correct / total if total > 0 else 0.0
    return avg_loss, accuracy


def train(args):
    device = torch.device('cuda' if torch.cuda.is_available() and args.max_gpus > 0 else 'cpu')
    wrapper = create_training_wrapper(args.optimizer, args.batch_size, args.pre_trained, device)
    train_loader = get_dataset('train', args.batch_size, args.limit, shuffle=True)
    val_loader = get_dataset('test', args.batch_size, args.limit, shuffle=True)
    for epoch in range(args.epoch):
        wrapper.model.train()
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            wrapper.zero_grad()
            outputs = wrapper.forward([inputs], [labels])
            loss = wrapper.loss(outputs, [labels])
            wrapper.backward(loss)
            wrapper.step()
        val_loss, val_acc = evaluate(wrapper.model, val_loader, wrapper.loss_fn, device)
        print(f"Epoch {epoch}: val_loss={val_loss:.4f}, val_acc={val_acc:.4f}")
        os.makedirs(args.output_dir, exist_ok=True)
        save_path = os.path.join(args.output_dir, "resnetv1.pt")
        torch.save(wrapper.model.state_dict(), save_path)
    return wrapper


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--epoch', '-e', type=int, default=10)
    parser.add_argument('--batch-size', '-b', type=int, default=32)
    parser.add_argument('--output-dir', '-o', type=str, default='build/output')
    parser.add_argument('--limit', '-l', type=int, default=0)
    parser.add_argument('--max-gpus', '-g', type=int, default=0)
    parser.add_argument('--pre-trained', '-p', action='store_true')
    parser.add_argument('--engine', type=str, default='PyTorch')
    parser.add_argument('--optimizer', '-z', type=str, default='adam')
    args = parser.parse_args()
    train(args)


if __name__ == '__main__':
    main()
