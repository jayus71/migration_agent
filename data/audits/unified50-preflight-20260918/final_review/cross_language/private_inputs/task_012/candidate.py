import torch


def synthetic_data(w, b, num_examples):
    X = torch.normal(mean=0.0, std=1.0, size=(num_examples, w.shape[0]), dtype=torch.float32)
    y = X @ w + b
    y += torch.normal(mean=0.0, std=0.01, size=y.shape, dtype=torch.float32)
    return X, y


def linreg(X, w, b):
    return X @ w + b


def squared_loss(y_hat, y):
    return (y_hat - y.reshape(y_hat.shape)) ** 2 / 2


def sgd(params, lr, batch_size):
    with torch.no_grad():
        for param in params:
            if param.grad is not None:
                param.data.sub_(param.grad.mul(lr).div(batch_size))


def data_iter(features, labels, batch_size):
    num_examples = features.shape[0]
    for i in range(0, num_examples, batch_size):
        j = min(i + batch_size, num_examples)
        yield features[i:j], labels[i:j]


class ScratchLinearRegression:
    def __init__(self, parameters, buffers=None, lr=0.03, batch_size=10):
        self._parameters = list(parameters)
        self._buffers = list(buffers) if buffers is not None else []
        self.lr = float(lr)
        self.batch_size = int(batch_size)
        self._updates = 0

    def parameters(self):
        return self._parameters

    def buffers(self):
        return self._buffers

    def zero_grad(self):
        for p in self._parameters:
            if p.grad is not None:
                p.grad.detach_()
                p.grad.zero_()

    def forward(self, inputs, labels=None):
        X = inputs[0]
        w = self._parameters[0]
        b = self._parameters[1]
        return [linreg(X, w, b)]

    def loss(self, outputs, labels):
        y_hat = outputs[0]
        y = labels[0]
        return squared_loss(y_hat, y)

    def backward(self, loss):
        if loss.requires_grad:
            loss.sum().backward()

    def step(self):
        sgd(self._parameters, self.lr, self.batch_size)
        self._updates += 1

    def optimizer_state(self):
        return [{"updates": self._updates} for _ in self._parameters]


def build_training(context):
    def get(key, default=None):
        if isinstance(context, dict):
            return context.get(key, default)
        return getattr(context, key, default)

    ctx_params = get("parameters", None)
    params = None

    if ctx_params is not None:
        if isinstance(ctx_params, (list, tuple)) and len(ctx_params) > 0:
            first = ctx_params[0]
            if isinstance(first, torch.Tensor):
                params = list(ctx_params)
            elif isinstance(first, dict) and "shape" in first:
                params = []
                for spec in ctx_params:
                    shape = tuple(spec["shape"])
                    p = torch.nn.Parameter(torch.empty(shape, dtype=torch.float32))
                    params.append(p)
            elif hasattr(first, "shape") and hasattr(first, "data"):
                params = list(ctx_params)

    if params is None:
        w = torch.nn.Parameter(torch.normal(0.0, 0.01, size=(2, 1), dtype=torch.float32))
        b = torch.nn.Parameter(torch.zeros(1, dtype=torch.float32))
        params = [w, b]
    else:
        for p in params:
            if isinstance(p, torch.Tensor):
                p.requires_grad_(True)

    ctx_buffers = get("buffers", [])
    buffers = []
    if ctx_buffers:
        if isinstance(ctx_buffers, (list, tuple)):
            for buf in ctx_buffers:
                if isinstance(buf, torch.Tensor):
                    buffers.append(buf)
                elif isinstance(buf, dict) and "shape" in buf:
                    buffers.append(torch.empty(tuple(buf["shape"]), dtype=torch.float32))

    lr = get("lr", get("learning_rate", 0.03))
    batch_size = get("batch_size", 10)

    return ScratchLinearRegression(params, buffers, lr=lr, batch_size=batch_size)


def main():
    true_w = torch.tensor([2.0, -3.4], dtype=torch.float32)
    true_b = 4.2
    features, labels = synthetic_data(true_w, true_b, 1000)

    print(f"features: [{features[0, 0].item():f}, {features[0, 1].item():f}]")
    print(f"label: {labels[0].item()}")

    batch_size = 10
    w = torch.normal(0.0, 0.01, size=(2, 1), dtype=torch.float32, requires_grad=True)
    b = torch.zeros(1, dtype=torch.float32, requires_grad=True)
    params = [w, b]

    lr = 0.03
    num_epochs = 3

    for epoch in range(num_epochs):
        for X, y in data_iter(features, labels, batch_size):
            for p in params:
                if p.grad is not None:
                    p.grad.zero_()
            l = squared_loss(linreg(X, w, b), y)
            l.sum().backward()
            sgd(params, lr, batch_size)

        train_l = squared_loss(linreg(features, w, b), labels)
        print(f"epoch {epoch + 1}, loss {train_l.mean().item():f}")

    w_error = true_w - w.detach().reshape(true_w.shape)
    print(f"Error in estimating w: [{w_error[0].item():f}, {w_error[1].item():f}]")
    b_error = true_b - b.item()
    print(f"Error in estimating b: {b_error:f}")


if __name__ == "__main__":
    main()
