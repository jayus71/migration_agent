import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import torchvision
from torchvision import transforms
import matplotlib.pyplot as plt

# Use CPU float32 as required.
torch.set_default_dtype(torch.float32)


def softmax(X):
    X_exp = torch.exp(X)
    partition = X_exp.sum(dim=1, keepdim=True)
    return X_exp / partition


class SoftmaxRegressionScratch:
    def __init__(self, num_inputs=784, num_outputs=10, lr=0.1):
        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.lr = lr
        self.W = nn.Parameter(torch.randn(num_inputs, num_outputs) * 0.01)
        self.b = nn.Parameter(torch.zeros(num_outputs))
        self._batch_size = None
        self._updates = 0

    def parameters(self):
        return [self.W, self.b]

    def buffers(self):
        return []

    def zero_grad(self):
        for p in self.parameters():
            p.grad = None

    def forward(self, inputs, labels=None):
        X = inputs[0]
        if labels is not None and len(labels) > 0:
            y = labels[0]
            self._batch_size = y.shape[0]
        else:
            self._batch_size = X.shape[0]

        X = X.reshape(-1, self.num_inputs)
        logits = X @ self.W + self.b
        return [softmax(logits)]

    def loss(self, outputs, labels):
        y_hat = outputs[0]
        y = labels[0].long()
        loss = -torch.log(y_hat.gather(1, y.view(-1, 1)))
        return loss

    def backward(self, loss):
        loss.sum().backward()

    def step(self):
        with torch.no_grad():
            for p in self.parameters():
                if p.grad is not None:
                    p -= self.lr * p.grad / self._batch_size
        self._updates += 1

    def optimizer_state(self):
        return [{'updates': self._updates} for _ in self.parameters()]


def accuracy(y_hat, y):
    y = y.long()
    if y_hat.shape[1] > 1:
        return (y_hat.argmax(dim=1) == y).sum().item()
    else:
        return (y_hat == y).sum().item()


def evaluate_accuracy(model, data_iter):
    batch = next(iter(data_iter))
    X, y = batch
    with torch.no_grad():
        y_hat = model.forward([X], [y])[0]
        acc = accuracy(y_hat, y)
    return acc / y.shape[0]


def train_epoch_ch3(model, train_iter):
    metric = [0.0, 0.0, 0.0]  # loss sum, accuracy sum, num examples
    for X, y in train_iter:
        model.zero_grad()
        y_hat = model.forward([X], [y])[0]
        l = model.loss([y_hat], [y])
        model.backward(l)
        model.step()

        metric[0] += l.sum().item()
        metric[1] += accuracy(y_hat, y)
        metric[2] += y.shape[0]

    return metric[0] / metric[2], metric[1] / metric[2]


def train_ch3(model, train_iter, test_iter, num_epochs):
    for epoch in range(1, num_epochs + 1):
        train_loss, train_acc = train_epoch_ch3(model, train_iter)
        test_acc = evaluate_accuracy(model, test_iter)

        print(f"Epoch {epoch}: Test Accuracy: {test_acc:f}")
        print(f"Train Accuracy: {train_acc:f}")
        print(f"Train Loss: {train_loss:f}")


def predict_ch3(model, dataset, number, device='cpu'):
    model.eval()
    batch = next(iter(dataset))
    X, y = batch
    X = X.to(device)

    with torch.no_grad():
        y_hat = model.forward([X])[0]

    preds = y_hat.argmax(dim=1).cpu().numpy()
    fig, axes = plt.subplots(1, number, figsize=(number * 2, 2))
    if number == 1:
        axes = [axes]

    for i in range(number):
        img = X[i].cpu().numpy().squeeze()
        axes[i].imshow(img, cmap='gray')
        axes[i].set_title(f"true: {y[i].item()}\npred: {preds[i]}")
        axes[i].axis('off')

    plt.show()


def build_training(context=None):
    num_inputs = 784
    num_outputs = 10

    if context is not None:
        params = None
        if hasattr(context, 'parameters'):
            params = context.parameters
        elif isinstance(context, dict) and 'parameters' in context:
            params = context['parameters']

        if params is not None:
            shapes = []
            for p in params:
                if isinstance(p, dict):
                    shape = p.get('shape')
                elif hasattr(p, 'shape'):
                    shape = p.shape
                else:
                    shape = p
                if shape is not None:
                    shapes.append(tuple(shape))

            if len(shapes) >= 2:
                num_inputs = shapes[0][0]
                num_outputs = shapes[0][1]

    model = SoftmaxRegressionScratch(num_inputs, num_outputs, lr=0.1)
    return model


if __name__ == '__main__':
    batch_size = 256
    num_epochs = 5
    lr = 0.1

    transform = transforms.ToTensor()
    train_dataset = torchvision.datasets.FashionMNIST(
        root='./data', train=True, download=True, transform=transform)
    test_dataset = torchvision.datasets.FashionMNIST(
        root='./data', train=False, download=True, transform=transform)

    train_iter = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_iter = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    model = SoftmaxRegressionScratch(num_inputs=784, num_outputs=10, lr=lr)
    train_ch3(model, train_iter, test_iter, num_epochs)

    predict_ch3(model, test_iter, 6)
