"""Private independent target controls for calibrating every public input family."""

import math
import mindspore as ms
from mindspore import nn, ops

KIND = 'execution'
MODEL_VARIANT = 'mlp'
NATIVE_FORM = 'attention'
HAS_EMBEDDING = False


class TorchLikeTensor:
    def __init__(self, value):
        self.value = value


def input_batch():
    return {'input_ids': ops.arange(4).astype(ms.int64)}


def boundary_op(x):
    return TorchLikeTensor(x + 1.)


def downstream_norm(x):
    return float(ops.sqrt(ops.sum(x.value.astype(ms.float32) ** 2)).asnumpy())


def dtype_sensitive_matmul(x, weight):
    return ops.matmul(x.astype(ms.float32), weight.astype(ms.float32)).astype(x.dtype)


def gather_tokens(table):
    return ops.gather(table, ops.arange(6).astype(ms.int64), 0).sum()


def require_mapping(batch):
    return float(batch['input_ids'].astype(ms.float32).sum().asnumpy())


OP_REGISTRY = {'mean.default': lambda x: x.mean(), 'mean.dim': lambda x: x.mean(axis=0)}


def run_registered_mean(x):
    return OP_REGISTRY['mean.default'](x)


def tuple_tensor_op(x):
    return TorchLikeTensor(x + 1.), TorchLikeTensor(x + 2.)


def consume_tensor_tuple(pair):
    return float((pair[0].value + pair[1].value).astype(ms.float32).sum().asnumpy())


def project_high_rank(x):
    return ops.transpose(x, (0, 2, 1, 3)).reshape(x.shape[0] * x.shape[2], x.shape[1], x.shape[3])


class Embedding(nn.Cell):
    def __init__(self, size):
        super().__init__()
        self.weight = ms.Parameter(ops.zeros((size, 4), ms.float32), name='weight')

    def construct(self, indices):
        return ops.gather(self.weight, indices, 0)


class Attention(nn.Cell):
    def __init__(self):
        super().__init__()
        self.in_proj_weight = ms.Parameter(ops.zeros((12, 4), ms.float32), name='in_proj_weight')
        self.in_proj_bias = ms.Parameter(ops.zeros((12,), ms.float32), name='in_proj_bias')
        self.out_proj = nn.Dense(4, 4)

    def construct(self, x, causal=False):
        packed = ops.matmul(x, self.in_proj_weight.transpose()) + self.in_proj_bias
        projected = ops.split(packed, 4, axis=-1)
        q, k, v = [t.reshape(x.shape[0], x.shape[1], 2, 2).swapaxes(1, 2) for t in projected]
        scores = ops.matmul(q, k.swapaxes(-2, -1)) / math.sqrt(2.)
        if causal:
            mask = ops.arange(x.shape[1])[:, None] < ops.arange(x.shape[1])[None, :]
            scores = ops.where(mask, ms.Tensor(float('-inf'), ms.float32), scores)
        result = ops.matmul(ops.softmax(scores, axis=-1), v)
        return self.out_proj(result.swapaxes(1, 2).reshape(x.shape))


class LayerNorm(nn.Cell):
    def __init__(self):
        super().__init__()
        self.weight = ms.Parameter(ops.ones((4,), ms.float32), name='weight')
        self.bias = ms.Parameter(ops.zeros((4,), ms.float32), name='bias')

    def construct(self, x):
        mean = x.mean(axis=-1, keep_dims=True)
        variance = ((x - mean) ** 2).mean(axis=-1, keep_dims=True)
        return (x - mean) / ops.sqrt(variance + 1e-5) * self.weight + self.bias


class Encoder(nn.Cell):
    def __init__(self):
        super().__init__()
        self.self_attn = Attention()
        self.linear1 = nn.Dense(4, 8)
        self.linear2 = nn.Dense(8, 4)
        self.norm1, self.norm2 = LayerNorm(), LayerNorm()

    def construct(self, x):
        x = self.norm1(x + self.self_attn(x))
        return self.norm2(x + self.linear2(ops.relu(self.linear1(x))))


class ExperimentModel(nn.Cell):
    def __init__(self):
        super().__init__()
        if MODEL_VARIANT == 'cnn':
            self.network = nn.SequentialCell(nn.Conv2d(1, 4, 3, pad_mode='pad', padding=1, has_bias=True),
                                             nn.ReLU(), nn.AdaptiveAvgPool2d(1))
        elif MODEL_VARIANT == 'mlp':
            self.network = nn.SequentialCell(nn.Dense(4, 8), nn.ReLU(), nn.Dense(8, 4))
        else:
            self.embedding = Embedding(17 if MODEL_VARIANT == 'transformer' else 19)
            if MODEL_VARIANT == 'transformer':
                self.encoder = Encoder()
            else:
                self.attn = Attention()

    def construct(self, x):
        if MODEL_VARIANT == 'cnn':
            return self.network(x).reshape(x.shape[0], 4)
        if MODEL_VARIANT == 'mlp':
            return self.network(x)
        if MODEL_VARIANT == 'transformer':
            return self.encoder(self.embedding(x)).mean(axis=1)
        return self.attn(self.embedding(x), True)[:, -1]


class Model(nn.Cell):
    def __init__(self, num_classes=4):
        super().__init__()
        if KIND == 'softmax':
            self.proj = nn.Dense(4, num_classes)
        elif KIND == 'residual':
            factory = lambda: nn.Conv2d(4, 4, 1, has_bias=True) if MODEL_VARIANT == 'cnn' else nn.Dense(4, 4)
            self.fc, self.skip = factory(), factory()
        else:
            self.fc1 = nn.Conv2d(3, 4, 1, has_bias=True) if MODEL_VARIANT == 'cnn' else nn.Dense(3, 4)
            self.fc2 = nn.Conv2d(4, 2, 1, has_bias=True) if MODEL_VARIANT == 'cnn' else nn.Dense(4, 2)

    def construct(self, x):
        if KIND == 'softmax':
            return ops.softmax(self.proj(x) * 1000., axis=-1)
        if KIND == 'residual':
            return ops.relu(self.fc(x)) + self.skip(x)
        return self.fc2(ops.relu(self.fc1(x)))


def build_model(params=None):
    return Model((params or {}).get('num_classes', 4))


def _candidate_attention(q, k, v, mask):
    scores = ops.matmul(q, k.swapaxes(-2, -1)) / math.sqrt(q.shape[-1])
    return ops.matmul(ops.softmax(scores + mask, axis=-1), v)


def _candidate_mask_fill(scores, keep_mask):
    return ops.where(keep_mask, scores, ms.Tensor(-10000., ms.float32))


def _candidate_rope(x, cosine, sine):
    rotation = ops.stack((-x[..., 1::2], x[..., 0::2]), axis=-1).reshape(x.shape)
    return x * cosine + rotation * sine


def train_step(model, x, y):
    optimizer = nn.SGD(model.trainable_params(), learning_rate=.2)
    def loss_fn(data, target):
        return ops.mean((model(data) - target) ** 2)
    loss, gradients = ms.value_and_grad(loss_fn, grad_position=None, weights=optimizer.parameters)(x, y)
    optimizer(gradients)
    return float(loss.asnumpy())


def apply_external_trainable_grads(model, external_grads):
    for name, parameter in model.parameters_and_names():
        parameter.grad = None
        if parameter.requires_grad and name in external_grads:
            parameter.grad = ops.identity(external_grads[name])


def parameter_workload(model):
    return [(name, parameter) for name, parameter in model.parameters_and_names() if parameter.requires_grad]


def gradient_workload(parameter, gradient, environment, model, index):
    name, destination = parameter_workload(model)[index]
    assert destination is parameter and gradient.shape == parameter.shape
    destination.grad = ops.identity(gradient)


if KIND == 'optimizer':
    def workload(parameters, transform):
        return nn.SGD([p for p in parameters if p.requires_grad], learning_rate=transform['learning_rate'])
elif NATIVE_FORM == 'relu':
    def workload(value):
        return ops.relu(value)
else:
    def workload(query, key, value, attn_mask=None, dropout_p=0., is_causal=False, scale=None, enable_gqa=False, **options):
        assert dropout_p == 0.
        if enable_gqa:
            repeats = query.shape[-3] // key.shape[-3]
            key, value = (ops.repeat_interleave(t, repeats, axis=-3) for t in (key, value))
        scores = ops.matmul(query, key.swapaxes(-2, -1)) * (scale if scale is not None else query.shape[-1] ** -.5)
        if attn_mask is not None:
            if attn_mask.dtype == ms.bool_:
                scores = ops.where(attn_mask, scores, ms.Tensor(float('-inf'), ms.float32))
            else:
                scores = scores + attn_mask
        if is_causal:
            keep = ops.arange(query.shape[-2])[:, None] >= ops.arange(key.shape[-2])[None, :]
            scores = ops.where(keep, scores, ms.Tensor(float('-inf'), ms.float32))
        return ops.matmul(ops.softmax(scores, axis=-1), value)

if HAS_EMBEDDING:
    def embedding_workload(indices, weight):
        return ops.gather(weight, indices, 0)
