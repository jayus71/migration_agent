"""Offline contract checks for authored sources and score calibration."""

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import traceback

import numpy as np
import torch
import torch.nn as nn


def load(path):
    spec = importlib.util.spec_from_file_location('workload_' + path.parent.name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def near(actual, expected, atol=1e-6):
    torch.testing.assert_close(actual, expected, rtol=1e-5, atol=atol)
    assert torch.isfinite(actual).all()


def check_execution(module, checks):
    x = torch.randn(2, 4, requires_grad=True)
    near(module.boundary_op(x).value, x + 1)
    assert module.downstream_norm(module.boundary_op(x)) == float((x + 1).norm())
    checks.append('tensor_boundary_and_consumer')
    for dtype in (torch.float32, torch.float64):
        a, b = torch.randn(2, 4, dtype=dtype), torch.randn(4, 3, dtype=torch.float64)
        near(module.dtype_sensitive_matmul(a, b), (a.float() @ b.float()).to(dtype))
    checks.append('mixed_dtype_matmul')
    table = torch.arange(32, dtype=torch.float32).reshape(8, 4)
    near(module.gather_tokens(table), table[:6].sum())
    assert module.require_mapping(module.input_batch()) == 6.0
    near(module.run_registered_mean(x), x.sum() / x.numel())
    near(module.OP_REGISTRY['mean.dim'](x), x.sum(dim=0) / x.shape[0])
    pair = module.tuple_tensor_op(x)
    assert len(pair) == 2
    near(pair[0].value, x + 1)
    near(pair[1].value, x + 2)
    assert abs(module.consume_tensor_tuple(pair) - float((2 * x + 3).sum())) < 1e-5
    z = torch.arange(2 * 3 * 4 * 5.).reshape(2, 3, 4, 5)
    near(module.project_high_rank(z), z.transpose(1, 2).reshape(8, 3, 5))
    checks.extend(['indexing_and_mapping', 'scalar_and_axis_mean', 'tuple_boundary', 'rank_four_projection'])
    model = module.ExperimentModel()
    features = module._model_features()
    assert features.shape == (2, 4) and torch.isfinite(features).all()
    # The helper executes the actual declared architecture, including its parameters.
    features.square().sum().backward()
    checks.append('declared_model_forward_and_backward')


def check_residual(module, checks):
    model = module.build_model()
    x = torch.randn(2, 4, 3, 3) if isinstance(model.fc, nn.Conv2d) else torch.randn(2, 3, 4)
    near(model(x), torch.relu(model.fc(x)) + model.skip(x))
    model(x).sum().backward()
    assert model.skip.weight.grad is not None
    checks.append('residual_model_and_skip_gradient')
    q, k, v = (torch.randn(2, 2, 3, 4, requires_grad=True) for _ in range(3))
    mask = torch.zeros(3, 3)
    mask[:, -1] = -10000
    expected = torch.nn.functional.scaled_dot_product_attention(q, k, v, attn_mask=mask)
    near(module._candidate_attention(q, k, v, mask), expected)
    scores = torch.randn(2, 3, 4)
    keep = torch.tensor([True, False, True, False]).expand_as(scores)
    near(module._candidate_mask_fill(scores, keep), torch.where(keep, scores, torch.full_like(scores, -10000)))
    x = torch.randn(2, 3, 6, requires_grad=True)
    angle = torch.tensor([.1, .5, .9]).repeat_interleave(2)
    expected = x.clone()
    expected[..., 0::2] = x[..., 0::2] * angle[0::2].cos() - x[..., 1::2] * angle[1::2].sin()
    expected[..., 1::2] = x[..., 1::2] * angle[1::2].cos() + x[..., 0::2] * angle[0::2].sin()
    near(module._candidate_rope(x, angle.cos(), angle.sin()), expected)
    checks.extend(['additive_attention', 'masked_logits', 'adjacent_coordinate_rotation'])


def check_softmax(module, checks):
    for classes in (4, 7):
        model = module.build_model({'num_classes': classes})
        x = torch.randn(3, 4, requires_grad=True)
        value = model(x)
        near(value, torch.nn.functional.softmax(model.proj(x) * 1000, dim=-1))
        near(value.sum(-1), torch.ones(3))
        assert torch.isfinite(torch.autograd.grad(value.square().sum(), x)[0]).all()
    checks.extend(['extreme_logits_finite', 'probability_normalization', 'softmax_gradient'])


def check_training(module, checks):
    model = module.build_model()
    assert all(p.requires_grad for p in model.parameters())
    x, y = module._batch()
    reference = copy.deepcopy(model)
    loss = (reference(x) - y).square().mean()
    loss.backward()
    gradients = {name: p.grad.clone() for name, p in reference.named_parameters()}
    assert all(torch.isfinite(g).all() for g in gradients.values())
    assert any(gradients[n].abs().sum() > 0 for n in gradients if n.startswith('fc1'))
    assert any(gradients[n].abs().sum() > 0 for n in gradients if n.startswith('fc2'))
    with torch.no_grad():
        for p in reference.parameters():
            p.add_(p.grad, alpha=-.2)
    actual = module.train_step(model, x, y)
    assert abs(actual - loss.item()) < 1e-6
    for (_, actual), (_, expected) in zip(model.named_parameters(), reference.named_parameters()):
        near(actual, expected)
        assert actual.grad is None or torch.count_nonzero(actual.grad) == 0
    checks.extend(['all_layers_trainable', 'connected_gradients', 'full_sgd_update', 'post_step_gradient_clear'])
    if hasattr(module, 'apply_external_trainable_grads'):
        model = module.build_model()
        model.fc1.weight.requires_grad_(False)
        external = {name: torch.full_like(p, index + .25)
                    for index, (name, p) in enumerate(model.named_parameters())}
        module.apply_external_trainable_grads(model, external)
        for name, p in model.named_parameters():
            if p.requires_grad:
                near(p.grad, external[name])
            else:
                assert p.grad is None
        checks.append('external_gradients_by_name')


def parameter_model():
    model = nn.Module()
    model.register_parameter('frozen', nn.Parameter(torch.ones(2, 3), requires_grad=False))
    model.register_parameter('first', nn.Parameter(torch.randn(3, 2)))
    model.register_parameter('second', nn.Parameter(torch.randn(2)))
    return model


def check_parameters(module, checks):
    model = parameter_model()
    selected = module.parameter_workload(model)
    assert [name for name, _ in selected] == ['first', 'second']
    for index, (_, p) in enumerate(selected):
        gradient = torch.full_like(p, index + .5)
        module.gradient_workload(p, gradient, None, model, index)
        near(p.grad, gradient)
        assert p.grad.data_ptr() != gradient.data_ptr()
    assert model.frozen.grad is None
    checks.extend(['ordered_trainable_parameters', 'gradient_assignment_and_copy', 'frozen_parameter_unchanged'])


def check_optimizer(module, checks):
    model = parameter_model()
    optimizer = module.workload(model.parameters(), {'learning_rate': .15})
    selected = optimizer.param_groups[0]['params']
    assert [id(p) for p in selected] == [id(model.first), id(model.second)]
    before = {n: p.detach().clone() for n, p in model.named_parameters()}
    for p in model.parameters():
        p.grad = torch.ones_like(p)
    optimizer.step()
    near(model.frozen, before['frozen'])
    near(model.first, before['first'] - .15)
    near(model.second, before['second'] - .15)
    checks.extend(['optimizer_parameter_selection', 'sgd_transform_mapping', 'frozen_parameter_unchanged'])


def check_native(module, checks):
    if hasattr(module, 'embedding_workload'):
        for dtype in (torch.float32, torch.bfloat16):
            w = torch.randn(9, 4, dtype=dtype, requires_grad=True)
            index = torch.tensor([0, 4, 8])
            near(module.embedding_workload(index, w).float(), w[index].float())
        checks.append('embedding_float32_and_bfloat16')
    if hasattr(module, 'attention_workload'):
        attention = module.attention_workload
    elif 'query' in module.workload.__code__.co_varnames:
        attention = module.workload
    else:
        x = torch.randn(3, 4, requires_grad=True)
        near(module.workload(x), x.clamp_min(0))
        near(torch.autograd.grad(module.workload(x).sum(), x)[0], (x > 0).float())
        checks.append('relu_values_and_gradients')
        return
    for mode in ('default', 'boolean_mask', 'additive_mask', 'causal', 'explicit_scale', 'grouped_query'):
        heads = 4 if mode == 'grouped_query' else 2
        q = torch.randn(1, heads, 3, 4, requires_grad=True)
        k, v = (torch.randn(1, 2, 3, 4, requires_grad=True) for _ in range(2))
        options = {}
        if mode == 'boolean_mask':
            options['attn_mask'] = torch.tensor([[True, False, True]]).expand(3, 3)
        elif mode == 'additive_mask':
            options['attn_mask'] = torch.tensor([[0., -10000., 0.]]).expand(3, 3)
        elif mode == 'causal':
            options['is_causal'] = True
        elif mode == 'explicit_scale':
            options['scale'] = .3
        elif mode == 'grouped_query':
            options['enable_gqa'] = True
        actual = attention(q, k, v, **options)
        expected = torch.nn.functional.scaled_dot_product_attention(q, k, v, **options)
        near(actual, expected)
        ga = torch.autograd.grad(actual.sum(), (q, k, v), retain_graph=True)
        ge = torch.autograd.grad(expected.sum(), (q, k, v))
        for a, b in zip(ga, ge):
            near(a, b)
        checks.append('attention_' + mode + '_and_gradients')


CHECKS = {'execution': check_execution, 'residual': check_residual, 'softmax': check_softmax,
          'training': check_training, 'parameters': check_parameters, 'optimizer': check_optimizer,
          'native': check_native}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    torch.set_num_threads(1)
    manifest = json.loads((args.bundle / 'manifest.json').read_text())
    rows = []
    for item in manifest['tasks']:
        source = args.bundle / 'public' / item['task'] / 'source.py'
        assert hashlib.sha256(source.read_bytes()).hexdigest() == item['source_sha256']
        for seed in (101, 202, 303):
            torch.manual_seed(seed)
            np.random.seed(seed)
            checks = []
            try:
                CHECKS[item['input_form']](load(source), checks)
                rows.append({'task': item['task'], 'seed': seed, 'passed': True, 'checks': checks})
            except Exception:
                rows.append({'task': item['task'], 'seed': seed, 'passed': False,
                             'checks': checks, 'error': traceback.format_exc()})
    result = {'model_calls': 0, 'torch_version': torch.__version__, 'checks': len(rows),
              'passed': sum(r['passed'] for r in rows), 'rows': rows}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2))
    for row in rows:
        if not row['passed']:
            print(json.dumps(row))
    if result['passed'] != result['checks']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
