import os
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms


def softmax(arrays):
    # Translated from ActivationFunction.softmax: returns log-softmax along classes.
    return [F.log_softmax(arrays[0], dim=1)]


def build_model():
    # SequentialBlock: batchFlattenBlock(28 * 28) -> Linear(10)
    return nn.Sequential(
        nn.Flatten(),
        nn.Linear(28 * 28, 10)
    )


class SoftmaxRegressionTraining:
    def __init__(self, context=None):
        self.context = context
        self.model = build_model()
        self.model = self.model.to(device=torch.device('cpu'), dtype=torch.float32)
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = torch.optim.SGD(self.model.parameters(), lr=0.1)
        self._params = list(self.model.parameters())
        self._updates = [0] * len(self._params)

    def parameters(self):
        return list(self.model.parameters())

    def buffers(self):
        return []

    def zero_grad(self):
        self.optimizer.zero_grad()

    def forward(self, inputs, labels=None):
        if not isinstance(inputs, (list, tuple)):
            inputs = [inputs]
        x = inputs[0]
        logits = self.model(x)
        return [logits]

    def loss(self, outputs, labels):
        if not isinstance(outputs, (list, tuple)):
            outputs = [outputs]
        if not isinstance(labels, (list, tuple)):
            labels = [labels]
        logits = outputs[0]
        target = labels[0]
        return F.cross_entropy(logits, target)

    def backward(self, loss):
        loss.backward()

    def step(self):
        self.optimizer.step()
        for i, p in enumerate(self._params):
            if p.grad is not None:
                self._updates[i] += 1

    def optimizer_state(self):
        return [{'updates': int(u)} for u in self._updates]


def build_training(context):
    return SoftmaxRegressionTraining(context)


def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    batch_size = 256
    random_shuffle = True
    num_epochs = 3

    transform = transforms.ToTensor()
    train_dataset = datasets.FashionMNIST(
        root='./data', train=True, download=True, transform=transform
    )
    val_dataset = datasets.FashionMNIST(
        root='./data', train=False, download=True, transform=transform
    )

    limit = os.environ.get('DATASET_LIMIT')
    if limit is not None:
        limit = int(limit)
        if limit < len(train_dataset):
            train_dataset = Subset(train_dataset, range(limit))
        if limit < len(val_dataset):
            val_dataset = Subset(val_dataset, range(limit))

    train_loader = DataLoader(
        train_dataset, batch_size=batch_size, shuffle=random_shuffle
    )
    val_loader = DataLoader(
        val_dataset, batch_size=batch_size, shuffle=False
    )

    model = build_model().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)

    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        for X, y in train_loader:
            X, y = X.to(device), y.to(device)
            optimizer.zero_grad()
            logits = model(X)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * X.size(0)
        train_loss = running_loss / len(train_loader.dataset)

        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for X, y in val_loader:
                X, y = X.to(device), y.to(device)
                logits = model(X)
                preds = logits.argmax(dim=1)
                correct += (preds == y).sum().item()
                total += y.size(0)
        val_acc = correct / total if total > 0 else 0.0
        print(
            f"Epoch {epoch + 1}/{num_epochs}, "
            f"train loss: {train_loss:.4f}, val acc: {val_acc:.4f}"
        )


if __name__ == '__main__':
    main()
