import os
import argparse
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
import matplotlib.pyplot as plt


class MLP(nn.Module):
    def __init__(self, params=None):
        super().__init__()
        self.flatten = nn.Flatten()
        self.fc1 = nn.Linear(784, 256)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(256, 10)

        if params is not None:
            # params order: [fc1.weight, fc1.bias, fc2.weight, fc2.bias]
            self.fc1.weight = params[0]
            self.fc1.bias = params[1]
            self.fc2.weight = params[2]
            self.fc2.bias = params[3]
        else:
            self._init_weights()

    def _init_weights(self):
        # DJL NormalInitializer for weights, zero for biases (D2L style)
        torch.nn.init.normal_(self.fc1.weight, mean=0.0, std=0.01)
        torch.nn.init.zeros_(self.fc1.bias)
        torch.nn.init.normal_(self.fc2.weight, mean=0.0, std=0.01)
        torch.nn.init.zeros_(self.fc2.bias)

    def forward(self, x):
        x = self.flatten(x)
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        return x


class SGD:
    """SGD optimizer matching DJL's Optimizer.sgd().setLearningRateTracker(Tracker.fixed(0.5f)).build()."""
    def __init__(self, params, lr):
        self.params = list(params)
        self.lr = lr
        self.state = [{'updates': 0} for _ in self.params]

    def zero_grad(self):
        for p in self.params:
            if p.grad is not None:
                p.grad.zero_()

    def step(self):
        with torch.no_grad():
            for p, s in zip(self.params, self.state):
                if p.grad is None:
                    continue
                p.add_(p.grad, alpha=-self.lr)
                s['updates'] += 1

    def state_dict(self):
        return [dict(s) for s in self.state]


class TrainingInterface:
    def __init__(self, model, criterion, optimizer, params):
        self.model = model
        self.criterion = criterion
        self.optimizer = optimizer
        self.params = params

    def parameters(self):
        return self.params

    def buffers(self):
        return []

    def zero_grad(self):
        self.optimizer.zero_grad()

    def forward(self, inputs, labels):
        x = inputs[0] if isinstance(inputs, (list, tuple)) else inputs
        out = self.model(x)
        return [out]

    def loss(self, outputs, labels):
        out = outputs[0] if isinstance(outputs, (list, tuple)) else outputs
        y = labels[0] if isinstance(labels, (list, tuple)) else labels
        return self.criterion(out, y)

    def backward(self, loss):
        loss.backward()

    def step(self):
        self.optimizer.step()

    def optimizer_state(self):
        return self.optimizer.state_dict()


def build_training(context):
    raw_params = list(context.parameters)
    params = []
    for p in raw_params:
        if isinstance(p, nn.Parameter):
            params.append(p)
        else:
            params.append(nn.Parameter(p, requires_grad=True))

    model = MLP(params)
    criterion = nn.CrossEntropyLoss()
    optimizer = SGD(model.parameters(), lr=0.5)
    return TrainingInterface(model, criterion, optimizer, params)


def limit_dataset(dataset, limit):
    if limit is None or limit <= 0 or limit >= len(dataset):
        return dataset
    indices = list(range(limit))
    return torch.utils.data.Subset(dataset, indices)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-epoch', type=int, default=int(os.environ.get('MAX_EPOCH', 10)))
    parser.add_argument('--dataset-limit', type=int, default=int(os.environ.get('DATASET_LIMIT', -1)))
    parser.add_argument('--data-dir', type=str, default=os.environ.get('DATA_DIR', './data'))
    args = parser.parse_args()

    num_epochs = args.max_epoch
    dataset_limit = args.dataset_limit
    data_dir = args.data_dir

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    transform = transforms.ToTensor()
    train_dataset = torchvision.datasets.FashionMNIST(
        root=data_dir, train=True, download=True, transform=transform
    )
    test_dataset = torchvision.datasets.FashionMNIST(
        root=data_dir, train=False, download=True, transform=transform
    )
    train_dataset = limit_dataset(train_dataset, dataset_limit)
    test_dataset = limit_dataset(test_dataset, dataset_limit)

    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=256, shuffle=True)
    test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=256, shuffle=True)

    model = MLP()
    model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=0.5)

    train_losses = []
    train_accs = []
    test_accs = []

    for epoch in range(num_epochs):
        model.train()
        total_loss = 0.0
        correct = 0
        total = 0
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * inputs.size(0)
            _, predicted = outputs.max(1)
            correct += predicted.eq(labels).sum().item()
            total += labels.size(0)

        train_loss = total_loss / total
        train_acc = correct / total
        train_losses.append(train_loss)
        train_accs.append(train_acc)

        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for inputs, labels in test_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                _, predicted = outputs.max(1)
                correct += predicted.eq(labels).sum().item()
                total += labels.size(0)
        test_acc = correct / total
        test_accs.append(test_acc)

        print(f'Epoch {epoch+1}/{num_epochs}, Loss: {train_loss:.4f}, '
              f'Train Acc: {train_acc:.4f}, Test Acc: {test_acc:.4f}')

    epochs = range(1, num_epochs + 1)
    plt.figure()
    plt.plot(epochs, train_losses, label='train loss')
    plt.plot(epochs, train_accs, label='train acc')
    plt.plot(epochs, test_accs, label='test acc')
    plt.xlabel('epoch')
    plt.ylabel('value')
    plt.legend()
    plt.savefig('mlp_djl_metrics.png')
    print('Plot saved to mlp_djl_metrics.png')


if __name__ == '__main__':
    main()
