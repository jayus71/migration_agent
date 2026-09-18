"""Backend-neutral workload measurements; source and candidate run separately."""

import argparse
from contextlib import nullcontext
import hashlib
import importlib.util
import json
from pathlib import Path
import traceback

import numpy as np


def array(value):
    if hasattr(value, 'value') and not callable(value.value):
        value = value.value
    if hasattr(value, 'detach'):
        value = value.detach()
    if hasattr(value, 'asnumpy'):
        if 'bfloat16' in str(value.dtype).lower():
            import mindspore as ms
            return value.astype(ms.float32).asnumpy()
        return value.asnumpy()
    if hasattr(value, 'cpu'):
        value = value.cpu()
    if hasattr(value, 'numpy'):
        try:
            return value.numpy()
        except TypeError:
            return value.float().numpy()
    return np.asarray(value)


def gradient_tuple(value, count):
    result = value if isinstance(value, (tuple, list)) else (value,)
    if len(result) != count:
        raise ValueError(f'Expected {count} gradients, received {len(result)}')
    return tuple(result)


class Runtime:
    def __init__(self, name):
        self.name = name
        self.backend_calls = 0
        self.backend_events = []
        self.parameter_backend_evidence = []
        if name == 'mindspore':
            import mindspore as ms
            self.api = ms
        elif name == 'msadapter':
            import msadapter as api
            self.api = api
        else:
            import torch
            torch.set_num_threads(1)
            self.api = torch
        self.context = nullcontext()
        if name == 'torch4ms':
            import torch4ms
            self.context = torch4ms.default_env()
        if name != 'torch':
            import mindspore as ms
            ms.set_context(mode=ms.PYNATIVE_MODE, device_target='CPU')
            original = ms.ops.Primitive.__call__
            def observed(primitive, *args, **kwargs):
                self.backend_calls += 1
                return original(primitive, *args, **kwargs)
            ms.ops.Primitive.__call__ = observed

    def tensor(self, values, *, integer=False, boolean=False, grad=False, dtype=None):
        values = np.asarray(values, dtype=np.bool_ if boolean else np.int64 if integer else np.float32)
        if self.name == 'mindspore':
            return self.api.Tensor(values, dtype=getattr(self.api, dtype) if dtype else None)
        result = self.api.tensor(values, dtype=getattr(self.api, dtype) if dtype else None)
        if grad and self.name in ('torch', 'torch4ms', 'msadapter'):
            result.requires_grad_(True)
        return result

    def named(self, model):
        if hasattr(model, 'named_parameters'):
            return list(model.named_parameters())
        return list(model.parameters_and_names())

    def backend_tensor(self, value):
        if hasattr(value, 'value') and not callable(value.value):
            value = value.value
        if self.name == 'torch':
            return False
        import mindspore as ms
        if self.name == 'msadapter':
            return isinstance(value, self.api.Tensor)
        return isinstance(value, ms.Tensor)

    def align(self, model):
        # Same named parameters receive the same values, independently of backend RNG.
        state = {}
        for name, parameter in self.named(model):
            seed = int(hashlib.sha256(name.encode()).hexdigest()[:8], 16)
            rng = np.random.default_rng(seed)
            value = (rng.standard_normal(tuple(parameter.shape)) * .08 + .02).astype(np.float32)
            if hasattr(parameter, 'set_data'):
                import mindspore as ms
                parameter.set_data(ms.Tensor(value, dtype=parameter.dtype))
            else:
                with self.api.no_grad():
                    parameter.copy_(self.api.tensor(value, dtype=parameter.dtype))
            state[name] = value
        return state

    def evaluate(self, function, inputs, parameters=(), model=None, model_inputs=None):
        def scalar(*args):
            result = function(*args)
            if hasattr(result, 'value') and not callable(result.value):
                result = result.value
            if 'bfloat16' in str(result.dtype).lower() or 'float16' in str(result.dtype).lower():
                result = result.astype(self.api.float32) if self.name == 'mindspore' else result.float()
            return result.sum()
        before_forward = self.backend_calls
        value = function(*inputs)
        forward_calls = self.backend_calls - before_forward
        before_backward = self.backend_calls
        if self.name == 'torch4ms':
            import mindspore as ms
            env = self.context
            if model is not None:
                from torch4ms.autograd.forward_extractor import AutogradForwardExtractor
                extractor = AutogradForwardExtractor(model)
                forward = extractor.get_ms_forward_fn(env)
                raw_params = tuple(env.t2ms_iso(p) for p in extractor.get_trainable_params())
                actual_inputs = inputs if model_inputs is None else model_inputs
                raw_inputs = tuple(env.t2ms_iso(value) for value in actual_inputs)
                if inputs:
                    def pure(*args):
                        return forward(*args).sum()
                    count = len(raw_params) + len(raw_inputs)
                    grads = ms.grad(pure, grad_position=tuple(range(count)))(*raw_params, *raw_inputs)
                    grads = gradient_tuple(grads, count)
                    gradients = grads[len(raw_params):] + grads[:len(raw_params)]
                else:
                    def pure(*weights):
                        return forward(*weights, *raw_inputs).sum()
                    gradients = ms.grad(pure, grad_position=tuple(range(len(raw_params))))(*raw_params)
            else:
                raw = tuple(env.t2ms_iso(value) for value in inputs)
                def pure(*args):
                    return env.t2ms_iso(scalar(*env.ms2t_iso(args)))
                gradients = ms.grad(pure, grad_position=tuple(range(len(raw))))(*raw)
        elif self.name in ('torch', 'msadapter'):
            total = scalar(*inputs)
            targets = tuple(inputs) + tuple(parameters)
            gradients = self.api.autograd.grad(total, targets, allow_unused=True) if targets else ()
        else:
            import mindspore as ms
            positions = tuple(range(len(inputs))) if inputs else None
            weights = ms.ParameterTuple(parameters) if parameters else None
            grad_fn = ms.grad(scalar, grad_position=positions, weights=weights)
            gradients = grad_fn(*inputs)
            if inputs and parameters:
                gradients = gradient_tuple(gradients[0], len(inputs)) + gradient_tuple(gradients[1], len(parameters))
        gradients = gradient_tuple(gradients, len(inputs) + len(parameters))
        self.backend_events.append({'forward_calls': forward_calls,
                                    'backward_calls': self.backend_calls - before_backward,
                                    'forward_backend_tensor': self.backend_tensor(value),
                                    'gradient_backend_tensors': all(self.backend_tensor(g) for g in gradients if g is not None),
                                    'gradient_engine': self.name})
        return value, gradients


def measure(module, kind, variant, runtime, seed, interfaces=()):
    rng = np.random.default_rng(seed)
    values = {}
    schema = {}
    def record(name, value):
        if value is None:
            values[name] = None
            schema[name] = {'status': 'unavailable'}
            return
        data = np.asarray(array(value))
        original_dtype = str(getattr(value, 'dtype', data.dtype)).split('.')[-1].lower()
        aliases = {'float': 'float32', 'double': 'float64', 'long': 'int64',
                   'bool_': 'bool', 'bfloat16': 'bfloat16'}
        schema[name] = {'shape': list(data.shape), 'dtype': aliases.get(original_dtype, original_dtype)}
        if not np.isfinite(data).all():
            raise ValueError('Non-finite measurement: ' + name)
        values[name] = data.tolist()
    def tensor(shape, grad=True):
        return runtime.tensor(rng.normal(size=shape), grad=grad)
    def operation(name, function, inputs):
        output, gradients = runtime.evaluate(function, inputs)
        record('forward/' + name, output)
        for index, gradient in enumerate(gradients):
            record(f'gradient/{name}/input_{index}', gradient)
    def model_case(name, model, x, y=None, train=False):
        initial = runtime.align(model)
        parameters = runtime.named(model)
        for key, p in parameters:
            record(f'initial/{name}/{key}', initial[key])
            record(f'trainable/{name}/{key}', bool(p.requires_grad))
        eligible = [(key, p) for key, p in parameters if p.requires_grad]
        out, gradients = runtime.evaluate(lambda z: model(z), (x,), [p for _, p in eligible], model=model)
        record('forward/' + name, out)
        record(f'gradient/{name}/input', gradients[0])
        for (key, _), grad in zip(eligible, gradients[1:]):
            record(f'gradient/{name}/{key}', grad)
        if train:
            for step in (1, 2):
                before_training = runtime.backend_calls
                loss = module.train_step(model, x, y)
                runtime.backend_events.append({'training_calls': runtime.backend_calls - before_training})
                record(f'forward/{name}/step_{step}/loss', loss)
                for key, p in parameters:
                    record(f'update/{name}/step_{step}/{key}', array(p) - initial[key])

    with runtime.context:
        if kind == 'execution':
            x = tensor((2, 4))
            operation('boundary', lambda z: module.boundary_op(z).value, (x,))
            record('forward/norm', module.downstream_norm(module.boundary_op(x)))
            operation('matmul', module.dtype_sensitive_matmul, (tensor((2, 4)), tensor((4, 3))))
            low_precision = runtime.tensor(rng.normal(size=(2, 4)), grad=True, dtype='bfloat16')
            operation('matmul_bfloat16', module.dtype_sensitive_matmul, (low_precision, tensor((4, 3))))
            operation('gather', module.gather_tokens, (tensor((8, 4)),))
            record('forward/batch', module.require_mapping(module.input_batch()))
            operation('mean', module.run_registered_mean, (x,))
            operation('mean_dim', module.OP_REGISTRY['mean.dim'], (x,))
            record('forward/tuple', module.consume_tensor_tuple(module.tuple_tensor_op(x)))
            operation('projection', module.project_high_rank, (tensor((2, 3, 4, 5)),))
            if variant == 'cnn':
                data = tensor((2, 1, 4, 4))
            elif variant == 'mlp':
                data = tensor((2, 4))
            else:
                data = runtime.tensor([[1, 2, 3], [4, 5, 6]], integer=True)
            model = module.ExperimentModel()
            if variant in ('cnn', 'mlp'):
                model_case('model', model, data)
            else:
                initial = runtime.align(model)
                named = runtime.named(model)
                output, gradients = runtime.evaluate(lambda: model(data), (), [p for _, p in named],
                                                     model=model, model_inputs=(data,))
                record('forward/model', output)
                for (key, _), gradient in zip(named, gradients):
                    record('initial/model/' + key, initial[key])
                    record('gradient/model/' + key, gradient)
        elif kind == 'residual':
            model_case('model', module.build_model(), tensor((2, 4, 3, 3) if variant == 'cnn' else (2, 3, 4)))
            q, k, v = (tensor((1, 2, 3, 4)) for _ in range(3))
            mask = runtime.tensor([[0., -10000., 0.]] * 3)
            operation('attention', lambda q, k, v: module._candidate_attention(q, k, v, mask), (q, k, v))
            keep = runtime.tensor([[True, False, True, False]] * 3, boolean=True)
            operation('mask', lambda z: module._candidate_mask_fill(z, keep), (tensor((2, 3, 4)),))
            angles = np.repeat([.1, .5, .9], 2)
            cosine, sine = runtime.tensor(np.cos(angles)), runtime.tensor(np.sin(angles))
            operation('rotation', lambda z: module._candidate_rope(z, cosine, sine), (tensor((2, 3, 6)),))
        elif kind == 'softmax':
            model_case('model', module.build_model({'num_classes': 4}), tensor((3, 4)))
        elif kind == 'training':
            shape = (5, 3, 4, 4) if variant == 'cnn' else (5, 6 if variant == 'transformer' else 8, 3) if variant in ('transformer', 'causal_lm') else (5, 3)
            yshape = (5, 2, 4, 4) if variant == 'cnn' else shape[:-1] + (2,)
            model_case('model', module.build_model(), tensor(shape), tensor(yshape, grad=False), train=True)
            if 'apply_external_trainable_grads' in interfaces:
                model = module.build_model()
                runtime.align(model)
                named = runtime.named(model)
                named[0][1].requires_grad = False
                external = {name: runtime.tensor(np.full(tuple(p.shape), (i + 1) * .1))
                            for i, (name, p) in enumerate(named)}
                module.apply_external_trainable_grads(model, external)
                for name, p in named:
                    record('gradient/external/' + name, getattr(p, 'grad', None))
                    record('trainable/external/' + name, bool(p.requires_grad))
        elif kind == 'native':
            if hasattr(module, 'embedding_workload'):
                indices = runtime.tensor([0, 4, 8], integer=True)
                operation('embedding', lambda w: module.embedding_workload(indices, w), (tensor((9, 4)),))
            fn = getattr(module, 'attention_workload', getattr(module, 'workload', None))
            if 'query' not in fn.__code__.co_varnames:
                operation('relu', fn, (tensor((3, 4)),))
            else:
                for name in ('default', 'boolean', 'additive', 'causal', 'scale', 'gqa'):
                    q = tensor((1, 4 if name == 'gqa' else 2, 3, 4))
                    k, v = (tensor((1, 2, 3, 4)) for _ in range(2))
                    options = {}
                    if name == 'boolean':
                        options['attn_mask'] = runtime.tensor([[True, False, True]] * 3, boolean=True)
                    elif name == 'additive':
                        options['attn_mask'] = runtime.tensor([[0., -10000., 0.]] * 3)
                    elif name == 'causal':
                        options['is_causal'] = True
                    elif name == 'scale':
                        options['scale'] = .3
                    elif name == 'gqa':
                        options['enable_gqa'] = True
                    operation('attention_' + name, lambda q, k, v: fn(q, k, v, **options), (q, k, v))
        elif kind in ('parameters', 'optimizer'):
            # Minimal parameter container follows the public native interface mapping.
            if runtime.name in ('torch', 'torch4ms', 'msadapter'):
                model = runtime.api.nn.Module()
                model.register_parameter('frozen', runtime.api.nn.Parameter(runtime.tensor(np.ones((2, 3))), requires_grad=False))
                model.register_parameter('first', runtime.api.nn.Parameter(tensor((3, 2), grad=False)))
                model.register_parameter('second', runtime.api.nn.Parameter(tensor((2,), grad=False)))
            else:
                import mindspore as ms
                model = ms.nn.Cell()
                model.frozen = ms.Parameter(ms.Tensor(np.ones((2, 3), np.float32)), name='frozen', requires_grad=False)
                model.first = ms.Parameter(ms.Tensor(rng.normal(size=(3, 2)).astype(np.float32)), name='first')
                model.second = ms.Parameter(ms.Tensor(rng.normal(size=(2,)).astype(np.float32)), name='second')
            initial = runtime.align(model)
            if kind == 'parameters':
                selected = module.parameter_workload(model)
                for index, (name, parameter) in enumerate(selected):
                    runtime.parameter_backend_evidence.append(runtime.backend_tensor(parameter))
                    record('forward/selected/' + name, array(parameter))
                    gradient = runtime.tensor(np.full(tuple(parameter.shape), index + .5))
                    module.gradient_workload(parameter, gradient, None, model, index)
                    record('gradient/' + name, parameter.grad)
            else:
                parameters = [p for _, p in runtime.named(model)]
                runtime.parameter_backend_evidence.extend(runtime.backend_tensor(p) for p in parameters)
                optimizer = module.workload(parameters, {'learning_rate': .15})
                if runtime.name == 'mindspore':
                    gradients = tuple(runtime.tensor(np.ones(tuple(p.shape))) for p in optimizer.parameters)
                    optimizer(gradients)
                else:
                    for p in parameters:
                        p.grad = runtime.tensor(np.ones(tuple(p.shape)))
                    optimizer.step()
                for name, p in runtime.named(model):
                    record('update/' + name, array(p) - initial[name])
        else:
            raise ValueError(kind)
    return {'values': values, 'schema': schema,
            'backend': {'requested': runtime.name, 'primitive_calls': runtime.backend_calls,
                        'events': runtime.backend_events,
                        'parameter_backend_evidence': runtime.parameter_backend_evidence,
                        'observed': runtime.name != 'torch'
                        and (bool(runtime.backend_events) or bool(runtime.parameter_backend_evidence)
                             or runtime.backend_calls > 0)
                        and all(event.get('training_calls', 0) > 0 or
                                (event.get('forward_backend_tensor', False)
                                 and event.get('gradient_backend_tensors', False))
                                for event in runtime.backend_events)
                        and all(runtime.parameter_backend_evidence)}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--program', type=Path, required=True)
    parser.add_argument('--contract', type=Path, required=True)
    parser.add_argument('--kind', required=True)
    parser.add_argument('--runtime', choices=['torch', 'torch4ms', 'mindspore', 'msadapter'], required=True)
    parser.add_argument('--seed', type=int, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        runtime = Runtime(args.runtime)
        spec = importlib.util.spec_from_file_location('candidate', args.program)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        contract = json.loads(args.contract.read_text())
        result = measure(module, args.kind, contract['model_variant'], runtime, args.seed,
                         contract.get('public_interfaces', ()))
        result.update(status='completed', seed=args.seed)
    except Exception:
        result = {'status': 'execution_failed', 'seed': args.seed, 'error': traceback.format_exc(),
                  'values': None, 'schema': None, 'backend': {'observed': False}}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, allow_nan=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
