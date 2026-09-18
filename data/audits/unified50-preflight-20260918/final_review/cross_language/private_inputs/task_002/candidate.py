import argparse
import os

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms


class LSTMMnistModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=28,
            hidden_size=64,
            num_layers=1,
            batch_first=True,
            dropout=0,
            bias=True,
        )
        # DJL BatchNorm momentum 0.9 corresponds to PyTorch momentum 0.1
        self.bn = nn.BatchNorm1d(28, eps=1e-5, momentum=0.1)
        self.fc = nn.Linear(1792, 10)

    def forward(self, x):
        batch_size = x.size(0)
        channel = x.size(3)
        time = x.numel() // (batch_size * channel)
        x = x.reshape(batch_size, time, channel)
        out, _ = self.lstm(x)
        out = self.bn(out)
        out = out.reshape(batch_size, -1)
        out = self.fc(out)
        return out


class LSTMMnistTraining:
    def __init__(self):
        self.model = LSTMMnistModel()
        self.model.train()
        self.criterion = nn.CrossEntropyLoss()
        self.param_list = list(self.model.parameters())
        self.optimizer = optim.SGD(self.param_list, lr=0.01)
        self.updates = [0] * len(self.param_list)

    def parameters(self):
        return self.param_list

    def buffers(self):
        return [self.model.bn.running_mean, self.model.bn.running_var]

    def zero_grad(self):
        self.optimizer.zero_grad()

    def forward(self, inputs, labels):
        x = inputs[0]
        out = self.model(x)
        return [out]

    def loss(self, outputs, labels):
        return self.criterion(outputs[0], labels[0].long())

    def backward(self, loss):
        loss.backward()

    def step(self):
        self.optimizer.step()
        for i in range(len(self.updates)):
            self.updates[i] += 1

    def optimizer_state(self):
        return [{'updates': self.updates[i]} for i in range(len(self.param_list))]


def build_training(context):
    return LSTMMnistTraining()


def get_data_loaders(args):
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])
    train_dataset = datasets.MNIST(root='./data', train=True, download=True, transform=transform)
    test_dataset = datasets.MNIST(root='./data', train=False, download=True, transform=transform)
    if args.limit > 0:
        train_dataset = Subset(train_dataset, range(min(args.limit, len(train_dataset))))
        test_dataset = Subset(test_dataset, range(min(args.limit, len(test_dataset))))
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=True)
    return train_loader, test_loader


def run_example(args):
    device = torch.device('cuda' if args.max_gpus != 0 and torch.cuda.is_available() else 'cpu')
    train_loader, test_loader = get_data_loaders(args)
    model = LSTMMnistModel().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=0.01)
    os.makedirs(args.output_dir, exist_ok=True)

    for epoch in range(1, args.epochs + 1):
        model.train()
        train_loss = 0.0
        correct = 0
        total = 0
        for data, target in train_loader:
            data, target = data.to(device), target.to(device)
            optimizer.zero_grad()
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * data.size(0)
            pred = output.argmax(dim=1)
            correct += pred.eq(target).sum().item()
            total += data.size(0)
        train_loss /= total
        train_acc = correct / total

        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        with torch.no_grad():
            for data, target in test_loader:
                data, target = data.to(device), target.to(device)
                output = model(data)
                loss = criterion(output, target)
                val_loss += loss.item() * data.size(0)
                pred = output.argmax(dim=1)
                val_correct += pred.eq(target).sum().item()
                val_total += data.size(0)
        val_loss /= val_total
        val_acc = val_correct / val_total

        print(f"Epoch {epoch}: train_loss={train_loss:.4f}, train_acc={train_acc:.4f}, "
              f"val_loss={val_loss:.4f}, val_acc={val_acc:.4f}")

        checkpoint = {
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'train_loss': train_loss,
            'val_loss': val_loss,
            'val_acc': val_acc,
        }
        torch.save(checkpoint, os.path.join(args.output_dir, f'epoch_{epoch}.pt'))

    torch.save(model.state_dict(), os.path.join(args.output_dir, 'final_model.pt'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train MNIST with LSTM using PyTorch')
    parser.add_argument('--epochs', type=int, default=10, help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=32, help='Training batch size')
    parser.add_argument('--output-dir', type=str, default='build/model', help='Output directory for checkpoints')
    parser.add_argument('--limit', type=int, default=0, help='Limit number of samples')
    parser.add_argument('--max-gpus', type=int, default=-1, help='Max number of GPUs to use')
    parser.add_argument('--engine', type=str, default='PyTorch', help='Engine (ignored)')
    args = parser.parse_args()
    run_example(args)
