"""Four actual model programs with measured execution/forward/gradient/update feedback."""
from __future__ import annotations
import argparse
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys

MODELS = {'cnn': ('PaperCnn', [4, 3, 12, 12], 6, None, None),
          'mlp': ('TinyImageMLP', [4, 3, 4, 4], 5, None, None),
          'transformer': ('TinyTransformerClassifier', [4, 9], 3, 'token_classification', 72),
          'tiny_causal_lm': ('TinyCausalLM', [4, 10], 80, 'causal_lm', 80)}
FAULTS = ('execution', 'forward', 'gradient', 'update')
VARIANTS = ('execution', 'execution_forward', 'execution_forward_gradient', 'all_observations')
PERSISTENT = ('schema_version', 'expected_backend', 'execution', 'target_backend_observed', 'source_immutable')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n')


def model_program(models_text, name, target, fault=None):
    model_class = MODELS[name][0]
    classes = [node for node in ast.parse(models_text).body if isinstance(node, ast.ClassDef)
               and node.name in (model_class, 'CausalLMLoss')]
    code = 'import torch\nimport torch.nn as nn\n\n' + '\n\n'.join(ast.unparse(node) for node in classes)
    code += f'\n\ndef build_model(params=None):\n    return {model_class}()\n'
    criterion = 'CausalLMLoss()' if name == 'tiny_causal_lm' else 'nn.CrossEntropyLoss()'
    if not target:
        return code + f'''\n\ndef train_one_step(model, x, y, lr=0.01):
    optimizer = torch.optim.SGD(model.parameters(), lr=lr)
    optimizer.zero_grad()
    loss = {criterion}(model(x), y)
    loss.backward()
    optimizer.step()
    return float(loss.detach().item())
'''
    code += '''\n\nimport torch4ms
from torch4ms.autograd.ms_autograd_function import extract_and_wrap_loss_fn
from torch4ms.optim import Torch4msOptimizer
'''
    code += f'''\n\ndef train_one_step(model, x, y, lr=0.01):
    base_optimizer = torch.optim.SGD(model.parameters(), lr=lr)
    optimizer = Torch4msOptimizer(base_optimizer, model)
    with torch4ms.default_env():
        optimizer.zero_grad()
        wrapped = extract_and_wrap_loss_fn(model, {criterion}, x, y)
        loss = wrapped.output
        loss.backward(module=model)
        optimizer.step()
        loss_value = float(loss.detach().item())
    return loss_value
'''
    if fault == 'execution':
        code = code.replace('torch.optim.SGD(model.parameters(), lr=lr)',
                            'torch.optim.SGD(model.parameters(), learning_rate=lr)')
    elif fault == 'forward':
        # A real forward loss offset, executed inside the differentiated closure.
        code = code.replace(f'wrapped = extract_and_wrap_loss_fn(model, {criterion}, x, y)',
            f'''criterion = {criterion}
        def criterion_with_offset(logits, labels):
            return criterion(logits, labels) + 0.25
        wrapped = extract_and_wrap_loss_fn(model, criterion_with_offset, x, y)''')
    elif fault == 'gradient':
        code = code.replace('        optimizer.step()', '''        for parameter in model.parameters():
            if parameter.grad is not None:
                parameter.grad = parameter.grad * 1.5
        optimizer.step()''')
    elif fault == 'update':
        code = code.replace('torch.optim.SGD(model.parameters(), lr=lr)',
                            'torch.optim.SGD(model.parameters(), lr=lr * 1.5)')
    elif fault is not None:
        raise ValueError('Unknown private construction')
    return code


def mask(observation, variant):
    if variant not in VARIANTS:
        raise ValueError('Unknown signal setting')
    if variant == 'all_observations':
        result = copy.deepcopy(observation)
        result['provided_observations'] = variant
        return result
    result = {key: copy.deepcopy(observation[key]) for key in PERSISTENT if key in observation}
    original = observation['acceptance']
    names = {'schema', 'backend_attested', 'source_immutable', 'command_execution',
             'reference_execution', 'target_execution', 'training_reported'}
    result['measurements'] = {}
    result['layer_differences'] = []
    result['parameter_updates'] = []
    if variant != 'execution':
        result['measurements']['loss_abs_diff'] = copy.deepcopy(observation['measurements']['loss_abs_diff'])
        result['layer_differences'] = copy.deepcopy(observation['layer_differences'])
        names.update(('loss_abs_diff', 'layer_differences_coverage', 'layer_differences_agreement'))
    if variant == 'execution_forward_gradient':
        result['measurements']['grad_norm_abs_diff'] = copy.deepcopy(observation['measurements']['grad_norm_abs_diff'])
        result['gradient_vector_comparison'] = copy.deepcopy(observation['gradient_vector_comparison'])
        names.update(('grad_norm_abs_diff', 'gradient_vector_l2'))
    checks = {key: original['checks'].get(key, False) for key in sorted(names)}
    accepted = all(value is True for value in checks.values())
    thresholds = {key: value for key, value in original['thresholds'].items()
                  if key == 'loss_abs' and variant != 'execution' or key == 'grad_norm_abs' and variant == 'execution_forward_gradient'}
    result['acceptance'] = {'accepted': accepted, 'checks': checks,
        'reasons': [key for key, value in checks.items() if value is not True],
        'thresholds': thresholds, 'contract': 'available_observations_only'}
    result['provided_observations'] = variant
    return result


def expected_signature(observation, fault):
    visible = [mask(observation, variant)['acceptance']['accepted'] for variant in VARIANTS]
    expected = {'execution': [False, False, False, False],
                'forward': [True, False, False, False],
                'gradient': [True, True, False, False],
                'update': [True, True, True, False]}[fault]
    return {'visible_accepted': visible, 'expected': expected, 'valid': visible == expected}


def prepare(control, diagnostics, output, recovery_launcher):
    if output.exists():
        raise ValueError('Preparation directory must be new')
    output.mkdir(parents=True)
    shutil.copy2(__file__, output / Path(__file__).name)
    shutil.copy2(recovery_launcher, output / 'recover_maintext_ablations.py')
    text = (diagnostics / 'experiments/paper_section_65_66/models.py').read_text()
    model_sha = sha(diagnostics / 'experiments/paper_section_65_66/models.py')
    source_manifest = read(control / 'manifest.json')
    sys.path.insert(0, str(control / 'code_snapshot'))
    from autofix.autonomous.evaluation import Evaluator
    private = output / 'private_preparation'
    rows, preflights = [], []
    for model, (_, shape, classes, batch_mode, vocab) in MODELS.items():
        clean = private / model / 'healthy'
        clean.mkdir(parents=True)
        shutil.copytree(diagnostics / 'torch4ms', clean / 'torch4ms',
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        (clean / 'source.py').write_text(model_program(text, model, False))
        (clean / 'candidate.py').write_text(model_program(text, model, True))
        params = {'input_shape': shape, 'num_classes': classes, 'lr': .01, 'steps': 1, 'seed': 4101}
        if batch_mode:
            params.update(batch_mode=batch_mode, vocab_size=vocab)
        save(clean / 'task.json', params)
        evaluator = Evaluator(clean, private / model / 'healthy_evidence', Path(sys.executable))
        checks = [evaluator.paired(seed=seed) for seed in (4101, 5101, 6101)]
        record = {'model': model, 'construction': 'healthy', 'checks': checks}
        preflights.append(record)
        save(output / 'preflight_progress.json', preflights)
        if not all(check['accepted'] for check in checks):
            raise ValueError('Healthy model failed: ' + model)
        for fault in FAULTS:
            task = f'task_{len(rows) + 1:03d}'
            public = private / task
            shutil.copytree(clean, public)
            (public / 'candidate.py').write_text(model_program(text, model, True, fault))
            evaluator = Evaluator(public, private / (task + '_evidence'), Path(sys.executable))
            checks = [evaluator.paired(seed=seed) for seed in (4101, 5101, 6101)]
            signatures = [expected_signature(check['observation'], fault) for check in checks]
            record = {'task': task, 'model': model, 'construction': fault,
                      'checks': checks, 'signatures': signatures}
            preflights.append(record)
            save(output / 'preflight_progress.json', preflights)
            if not all(row['valid'] for row in signatures):
                raise ValueError('Measured signature differs from declared signal: ' + task)
            rows.append({'anonymous_id': task, 'model': model, 'construction': fault,
                         'candidate_sha256': sha(public / 'candidate.py'),
                         'source_sha256': sha(public / 'source.py')})
    manifest_hashes, jobs = {}, []
    for variant in VARIANTS:
        run = output / variant
        run.mkdir()
        shutil.copytree(control / 'code_snapshot', run / 'code_snapshot',
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for task in rows:
            shutil.copytree(private / task['anonymous_id'], run / 'private_inputs' / task['anonymous_id'])
        manifest = copy.deepcopy(source_manifest)
        manifest.update(tasks=rows, methods=['autonomous_layered'], benchmark='training_signal16',
                        no_fault_injection=False, translation_reused=False, signal_variant=variant,
                        selection='All four models and all four declared program mutations, without outcome selection')
        save(run / 'manifest.json', manifest)
        manifest_hashes[variant] = sha(run / 'manifest.json')
        hashes = {str(path.relative_to(run)): sha(path) for directory in ('private_inputs', 'code_snapshot')
                  for path in (run / directory).rglob('*') if path.is_file()}
        save(run / 'frozen_hashes.json', hashes)
        jobs.extend({'study': 'training_signal16', 'variant': variant, 'task': task['anonymous_id'],
                     'run': str(run), 'runner': str(output / Path(__file__).name),
                     'selection_reason': 'complete_predeclared_grid'} for task in rows)
    save(output / 'plan.json', {'created_at': datetime.now(timezone.utc).isoformat(),
         'condition_count': len(jobs), 'tasks': rows, 'variants': VARIANTS,
         'runner_sha256': sha(output / Path(__file__).name), 'variant_manifest_sha256': manifest_hashes,
         'model_definition_sha256': model_sha, 'control_manifest_sha256': sha(control / 'manifest.json'),
         'protocol': 'Same public program per task. Mask only measured feedback. Controller stops on visible checks. '
                     'Final evaluation uses all signals on three seeds. Extra scratch tests remain available.',
         'preflight': preflights})
    jobs.sort(key=lambda job: (job['task'], job['variant']))
    save(output / 'recovery_plan.json', {'launcher_sha256': sha(output / 'recover_maintext_ablations.py'),
         'jobs': jobs, 'policy': 'First execution of every predeclared condition; no automatic retry'})
    print(json.dumps({'prepared': len(jobs), 'preflight_rows': len(preflights)}), flush=True)


def verify(run):
    plan = read(run.parent / 'plan.json')
    if sha(Path(__file__)) != plan['runner_sha256'] or sha(run / 'manifest.json') != plan['variant_manifest_sha256'][run.name]:
        raise ValueError('Runner or manifest changed')
    for name, expected in read(run / 'frozen_hashes.json').items():
        if sha(run / name) != expected:
            raise ValueError('Frozen input changed: ' + name)


def worker(run, task):
    verify(run)
    sys.path.insert(0, str(run / 'code_snapshot'))
    from autofix.autonomous import experiment
    from autofix.autonomous.evaluation import Evaluator
    variant = read(run / 'manifest.json')['signal_variant']
    class Masked(Evaluator):
        def paired(self, **kwargs):
            full = super().paired(**kwargs)
            observation = mask(full['observation'], variant)
            self.latest_full = full
            return {**full, 'observation': observation, 'accepted': observation['acceptance']['accepted'],
                    'full_evaluation': full}
    active = []
    def factory(_run, _task, workspace, evidence, python, _manifest):
        evaluator = Masked(workspace, evidence, python)
        active.append(evaluator)
        return evaluator
    experiment.evaluator_for = factory
    result = experiment.run_condition(run, task, 'autonomous_layered', Path(sys.executable))
    result['controller_accepted'] = result['accepted']
    result['initially_accepted_by_available_checks'] = result.get('initially_accepted')
    if result['status'] == 'completed':
        checks = [active[0].paired(seed=seed)['full_evaluation'] for seed in (4101, 5101, 6101)]
        result['full_final_confirmation'] = checks
        result['accepted'] = all(check['accepted'] for check in checks)
        result['initially_accepted'] = result['initial']['full_evaluation']['accepted']
        for attempt in result.get('attempts', []):
            attempt['controller_accepted'] = attempt['accepted']
            full_checks = [attempt['evaluation']['full_evaluation']] + [row['full_evaluation'] for row in attempt.get('confirmation', [])]
            attempt['accepted'] = all(row['accepted'] for row in full_checks)
    save(run / 'conditions' / task / 'autonomous_layered/result.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--control', type=Path, required=True)
    parser.add_argument('--diagnostics', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--recovery-launcher', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.control.resolve(), args.diagnostics.resolve(), args.output.resolve(), args.recovery_launcher.resolve())


if __name__ == '__main__':
    main()
