"""Native JAX translation implementing the public source contract."""
import jax
import jax.numpy as jnp
import optax


def linear(p, name, x):
    return x @ p[name + '.weight'].T + p.get(name + '.bias', 0.0)


def forward(p, x, task):
    if task == 'task_001':
        h = jnp.tanh(linear(p, 'input', x))
        h = h + jnp.tanh(linear(p, 'residual', h))
        return linear(p, 'output', h)
    q = linear(p, 'query', x)
    k = linear(p, 'key', x)
    v = linear(p, 'value', x)
    weights = jax.nn.softmax(q @ jnp.swapaxes(k, -1, -2) / (6 ** 0.5), -1)
    h = jnp.mean(weights @ v + x, axis=1)
    return linear(p, 'output', h)


def optimizer(task):
    if task == 'task_001':
        return optax.sgd(learning_rate=0.03, momentum=0.9)
    return optax.adam(learning_rate=0.01, b1=0.9, b2=0.999, eps=1e-8)


def init_optimizer(p, task):
    return optimizer(task).init(p)


def train_step(p, state, x, y, task):
    def loss_fn(params):
        logits = forward(params, x, task)
        return optax.softmax_cross_entropy_with_integer_labels(logits, y).mean()
    loss, gradients = jax.value_and_grad(loss_fn)(p)
    updates, state = optimizer(task).update(gradients, state, p)
    return optax.apply_updates(p, updates), state, loss, gradients
