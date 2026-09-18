"""Private healthy MindSpore calibration implementation, excluded from agent inputs."""

import mindspore as ms
from mindspore import nn, ops

MODEL_VARIANT = 'transformer'


class TinyNet(nn.Cell):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Conv2d(3, 4, 1, has_bias=True) if MODEL_VARIANT == 'cnn' else nn.Dense(3, 4)
        self.fc2 = nn.Conv2d(4, 2, 1, has_bias=True) if MODEL_VARIANT == 'cnn' else nn.Dense(4, 2)

    def construct(self, x):
        return self.fc2(ops.relu(self.fc1(x)))


def build_model():
    return TinyNet()


def apply_external_trainable_grads(model, external_grads):
    for name, parameter in model.parameters_and_names():
        parameter.grad = None
        if parameter.requires_grad and name in external_grads:
            parameter.grad = ops.identity(external_grads[name])


def train_step(model, x, y):
    optimizer = nn.SGD(model.trainable_params(), learning_rate=.2)
    def loss_fn(data, target):
        return ops.mean((model(data) - target) ** 2)
    loss, gradients = ms.value_and_grad(loss_fn, grad_position=None, weights=optimizer.parameters)(x, y)
    optimizer(gradients)
    return float(loss.asnumpy())
