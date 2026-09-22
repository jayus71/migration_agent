"""Public target runtime; contains no reference implementation or expected values."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import traceback

os.environ['JAX_PLATFORMS'] = 'cpu'
os.environ['XLA_FLAGS'] = '--xla_cpu_multi_thread_eigen=false'
os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:2])

import jax
import jax.numpy as jnp
import numpy as np


def vector_tree(tree):
    return {k: np.asarray(v).reshape(-1).tolist() for k, v in sorted(tree.items())}


def main():
    workspace, seed = Path(sys.argv[1]), int(sys.argv[2])
    task = json.loads((workspace / 'task.json').read_text())['task']
    spec = importlib.util.spec_from_file_location('candidate', workspace / 'candidate.py')
    candidate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(candidate)
    data = np.load(workspace / 'inputs' / f'{seed}.npz')
    p = {k[2:]: jnp.array(data[k]) for k in data.files if k.startswith('p:')}
    initial = vector_tree(p)
    state = candidate.init_optimizer(p, task)
    steps = []
    for step in range(3):
        x, y = jnp.array(data[f'x:{step}']), jnp.array(data[f'y:{step}'])
        before = p
        logits = candidate.forward(p, x, task)
        p, state, loss, gradients = candidate.train_step(p, state, x, y, task)
        updates = {k: p[k] - before[k] for k in before}
        observed = all(isinstance(v, jax.Array) for v in [logits, loss, *p.values(), *gradients.values()])
        steps.append({'loss': float(loss), 'logits': np.asarray(logits).reshape(-1).tolist(),
                      'gradients': vector_tree(gradients), 'updates': vector_tree(updates),
                      'parameters': vector_tree(p), 'jax_arrays': observed})
    print(json.dumps({'status': 'ok', 'initial': initial, 'steps': steps}))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(json.dumps({'status': 'failed', 'error_type': type(exc).__name__,
                          'error': str(exc), 'traceback': traceback.format_exc()}))
        sys.exit(1)
