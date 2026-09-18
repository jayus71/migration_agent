import os
import time
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms


class LeNet(nn.Module):
    def __init__(self):
        super(LeNet, self).__init__()
        self.conv1 = nn.Conv2d(1, 6, kernel_size=5, padding=2, bias=False)
        self.conv2 = nn.Conv2d(6, 16, kernel_size=5, bias=True)
        self.pool = nn.AvgPool2d(kernel_size=5, stride=2, padding=2)
        self.flatten = nn.Flatten()
        self.fc1 = nn.Linear(16 * 5 * 5, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)
        self._initialize_weights()

    def _initialize_weights(self):
        for m in self.modules():
            if isinstance(m, (nn.Conv2d, nn.Linear)):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, x):
        x = self.pool(torch.sigmoid(self.conv1(x)))
        x = self.pool(torch.sigmoid(self.conv2(x)))
        x = self.flatten(x)
        x = torch.sigmoid(self.fc1(x))
        x = torch.sigmoid(self.fc2(x))
        x = self.fc3(x)
        return x


class LeNetTraining:
    def __init__(self):
        self.model = LeNet()
        self.loss_fn = nn.CrossEntropyLoss()
        self.optimizer = torch.optim.SGD(self.model.parameters(), lr=0.9)
        self._updates = [0] * len(list(self.model.parameters()))

    def parameters(self):
        return list(self.model.parameters())

    def buffers(self):
        return list(self.model.buffers())

    def zero_grad(self):
        self.optimizer.zero_grad()

    def forward(self, inputs, labels):
        x = inputs[0]
        out = self.model(x)
        return [out]

    def loss(self, outputs, labels):
        return self.loss_fn(outputs[0], labels[0])

    def backward(self, loss):
        loss.backward()

    def step(self):
        self.optimizer.step()
        for i in range(len(self._updates)):
            self._updates[i] += 1

    def optimizer_state(self):
        return [{"updates": self._updates[i]} for i in range(len(self._updates))]


def build_training(context=None):
    return LeNetTraining()


def main():
    torch.manual_seed(1111)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(1111)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    batch_size = 256
    num_epochs = int(os.environ.get('MAX_EPOCH', 10))
    dataset_limit = int(os.environ.get('DATASET_LIMIT', 0))

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

    model = LeNet().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.9)

    train_losses = []
    train_accs = []
    test_accs = []

    for epoch in range(num_epochs):
        model.train()
        total_loss = 0.0
        total_correct = 0
        total_samples = 0
        start_time = time.time()

        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * images.size(0)
            _, predicted = outputs.max(1)
            total_correct += predicted.eq(labels).sum().item()
            total_samples += labels.size(0)

        avg_train_loss = total_loss / total_samples
        train_acc = total_correct / total_samples
        train_losses.append(avg_train_loss)
        train_accs.append(train_acc)
        epoch_time = time.time() - start_time

        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for images, labels in test_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                _, predicted = outputs.max(1)
                correct += predicted.eq(labels).sum().item()
                total += labels.size(0)

        test_acc = correct / total
        test_accs.append(test_acc)

        print(f"loss {avg_train_loss:.3f}, train acc {train_acc:.3f}, test acc {test_acc:.3f}")
        print(f"{total_samples / epoch_time:.1f} examples/sec")


if __name__ == '__main__':
    main()
