import os
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms
import numpy as np
import matplotlib.pyplot as plt


def relu(X):
    """ReLU implemented from scratch using maximum."""
    return torch.maximum(X, torch.zeros_like(X))


class MLP(nn.Module):
    def __init__(self, num_inputs=784, num_hiddens=256, num_outputs=10):
        super().__init__()
        self.num_inputs = num_inputs
        self.W1 = nn.Parameter(torch.randn(num_inputs, num_hiddens) * 0.01)
        self.b1 = nn.Parameter(torch.zeros(num_hiddens))
        self.W2 = nn.Parameter(torch.randn(num_hiddens, num_outputs) * 0.01)
        self.b2 = nn.Parameter(torch.zeros(num_outputs))

    def forward(self, X):
        X = X.reshape(-1, self.num_inputs)
        H = relu(X @ self.W1 + self.b1)
        return H @ self.W2 + self.b2


def softmax_cross_entropy_loss(y_hat, y):
    return F.cross_entropy(y_hat, y, reduction='mean')


def sgd(params, lr, batch_size):
    with torch.no_grad():
        for p in params:
            if p.grad is not None:
                p -= lr * p.grad / batch_size
                p.grad.zero_()


class TrainingInterface:
    def __init__(self, context):
        self.context = context
        self.device = torch.device('cpu')
        self.dtype = torch.float32
        self.model = MLP().to(self.device, dtype=self.dtype)
        self.batch_size = 256
        self.lr = 0.5
        self.updates = 0
        self.params = [self.model.W1, self.model.b1, self.model.W2, self.model.b2]

    def parameters(self):
        return self.params

    def buffers(self):
        return []

    def zero_grad(self):
        for p in self.params:
            if p.grad is not None:
                p.grad.zero_()

    def forward(self, inputs, labels):
        X = inputs[0].to(self.device, dtype=self.dtype)
        y_hat = self.model(X)
        return [y_hat]

    def loss(self, outputs, labels):
        y_hat = outputs[0]
        y = labels[0].to(self.device, dtype=torch.long)
        return softmax_cross_entropy_loss(y_hat, y)

    def backward(self, loss):
        # Source: l = lossValue * batchSize; gc.backward(l)
        (loss * self.batch_size).backward()

    def step(self):
        sgd(self.params, self.lr, self.batch_size)
        self.updates += 1

    def optimizer_state(self):
        return [{'updates': self.updates} for _ in self.params]


def build_training(context):
    return TrainingInterface(context)


def train_fashion_mnist():
    batch_size = 256
    num_inputs = 784
    num_outputs = 10
    num_hiddens = 256
    lr = 0.5
    num_epochs = int(os.environ.get('MAX_EPOCH', 10))
    dataset_limit = int(os.environ.get('DATASET_LIMIT', -1))

    device = torch.device('cpu')
    dtype = torch.float32

    transform = transforms.ToTensor()
    train_dataset = datasets.FashionMNIST(
        root='./data', train=True, download=True, transform=transform
    )
    test_dataset = datasets.FashionMNIST(
        root='./data', train=False, download=True, transform=transform
    )

    if dataset_limit > 0:
        train_dataset = Subset(train_dataset, range(min(dataset_limit, len(train_dataset))))
        test_dataset = Subset(test_dataset, range(min(dataset_limit, len(test_dataset))))

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=True)

    model = MLP(num_inputs, num_hiddens, num_outputs).to(device, dtype=dtype)
    params = [model.W1, model.b1, model.W2, model.b2]

    train_loss = np.zeros(num_epochs)
    train_acc = np.zeros(num_epochs)
    test_acc = np.zeros(num_epochs)
    epoch_count = np.arange(1, num_epochs + 1)

    for epoch in range(1, num_epochs + 1):
        epoch_loss = 0.0
        accuracy_val = 0.0
        model.train()
        for X, y in train_loader:
            X = X.to(device, dtype=dtype)
            y = y.to(device, dtype=torch.long)

            for p in params:
                if p.grad is not None:
                    p.grad.zero_()

            y_hat = model(X)
            loss_value = softmax_cross_entropy_loss(y_hat, y)
            l = loss_value * batch_size

            accuracy_val += (y_hat.argmax(dim=1) == y).sum().item()
            epoch_loss += l.item()

            l.backward()
            sgd(params, lr, batch_size)

        train_loss[epoch - 1] = epoch_loss / len(train_dataset)
        train_acc[epoch - 1] = accuracy_val / len(train_dataset)

        accuracy_val = 0.0
        model.eval()
        with torch.no_grad():
            for X, y in test_loader:
                X = X.to(device, dtype=dtype)
                y = y.to(device, dtype=torch.long)
                y_hat = model(X)
                accuracy_val += (y_hat.argmax(dim=1) == y).sum().item()

        test_acc[epoch - 1] = accuracy_val / len(test_dataset)
        print(
            f"Epoch {epoch}: train loss {train_loss[epoch-1]:.4f}, "
            f"train acc {train_acc[epoch-1]:.4f}, test acc {test_acc[epoch-1]:.4f}"
        )

    print("Finished training!")

    plt.figure()
    plt.plot(epoch_count, train_loss, label='train loss')
    plt.plot(epoch_count, train_acc, label='train acc')
    plt.plot(epoch_count, test_acc, label='test acc')
    plt.xlabel('epoch')
    plt.ylabel('value')
    plt.legend()
    plt.savefig('mlp_scratch.png')
    plt.show()


if __name__ == '__main__':
    train_fashion_mnist()
