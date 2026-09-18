import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import TensorDataset, DataLoader
from pathlib import Path
from collections import OrderedDict


def synthetic_data(num_examples, w, b, noise=0.01):
    features = torch.normal(0.0, 1.0, (num_examples, w.shape[0]))
    labels = features @ w + b
    labels += torch.normal(0.0, noise, labels.shape)
    return features, labels


def mse_loss(pred, target):
    target = target.reshape(pred.shape)
    return F.mse_loss(pred, target)


def create_linear_model(weight=None, bias=None):
    model = nn.Sequential(OrderedDict([("01Linear", nn.Linear(2, 1))]))
    if weight is not None:
        model[0].weight = weight
        model[0].bias = bias
    return model


class TrainingSession:
    def __init__(self, model, loss_fn, optimizer, parameters):
        self.model = model
        self.loss_fn = loss_fn
        self.optimizer = optimizer
        self._parameters = parameters
        self._updates = [0] * len(parameters)

    def parameters(self):
        return self._parameters

    def buffers(self):
        return []

    def zero_grad(self):
        self.optimizer.zero_grad()

    def forward(self, inputs, labels):
        x = inputs[0]
        return [self.model(x)]

    def loss(self, outputs, labels):
        return self.loss_fn(outputs[0], labels[0])

    def backward(self, loss):
        loss.backward()

    def step(self):
        self.optimizer.step()
        for i in range(len(self._updates)):
            self._updates[i] += 1

    def optimizer_state(self):
        return [{"updates": self._updates[i]} for i in range(len(self._parameters))]


def build_training(context):
    weight = context.parameters[0]
    bias = context.parameters[1]
    if not isinstance(weight, nn.Parameter):
        weight = nn.Parameter(weight)
    if not isinstance(bias, nn.Parameter):
        bias = nn.Parameter(bias)

    model = create_linear_model(weight, bias)
    optimizer = torch.optim.SGD([weight, bias], lr=0.03)
    return TrainingSession(model, mse_loss, optimizer, [weight, bias])


def main():
    true_w = torch.tensor([2.0, -3.4], dtype=torch.float32)
    true_b = 4.2
    features, labels = synthetic_data(1000, true_w, true_b)

    batch_size = 10
    dataset = TensorDataset(features, labels)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

    model = create_linear_model()
    loss_fn = mse_loss
    optimizer = torch.optim.SGD(model.parameters(), lr=0.03)
    session = TrainingSession(model, loss_fn, optimizer, list(model.parameters()))

    num_epochs = 3
    for epoch in range(1, num_epochs + 1):
        print(f"Epoch {epoch}")
        for X, y in dataloader:
            session.zero_grad()
            outputs = session.forward([X], [y])
            loss = session.loss(outputs, [y])
            session.backward(loss)
            session.step()

    w_param = model[0].weight.detach()
    b_param = model[0].bias.detach()
    w_error = true_w - w_param.reshape(true_w.shape)
    b_error = true_b - b_param.item()
    print(f"Error in estimating w: [{w_error[0]:f} {w_error[1]:f}]")
    print(f"Error in estimating b: {b_error:f}")

    model_dir = Path("../models/lin-reg")
    model_dir.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "epoch": num_epochs,
            "properties": {"Epoch": str(num_epochs)},
        },
        model_dir / "lin-reg.pt",
    )


if __name__ == "__main__":
    main()
