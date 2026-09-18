"""Author full native modules using public inputs only; do not load fault probes."""

import argparse
import ast
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROVENANCE = 'Newly authored native PyTorch program based on the complete public interface and declared semantics; not a recovered historical source.'
SEMANTICS = {
    'execution': 'Preserve all model and utility interfaces. Wrapped tensor producers return objects with a value tensor; mean returns a scalar; matrix multiplication accumulates in float32 and returns the input dtype; indices are integers; batch is a mapping; projection exchanges axes 1 and 2 before merging batch and axis 2.',
    'residual': 'Residual output is relu(fc(x)) + skip(x). Attention uses additive masking and inverse-square-root head scaling. A false keep-mask entry has logit -10000. Rotary embedding pairs adjacent coordinates and computes x*cos + rotate_half(x)*sin.',
    'softmax': 'Compute a linear projection times 1000 followed by finite, normalized softmax probabilities along the final axis.',
    'training': 'Train every parameter of the two-layer model using mean squared error and SGD with learning rate 0.2. train_step performs backward and parameter update, then clears gradients. External gradients bind by parameter name and apply only to trainable parameters.',
    'parameters': 'parameter_workload returns ordered (name, parameter) pairs for trainable parameters. gradient_workload assigns the supplied gradient to the parameter at the corresponding trainable index. environment is an opaque interoperability argument and unused in native PyTorch.',
    'optimizer': 'workload constructs an SGD optimizer over trainable parameters. The public transform mapping has a learning_rate field. This mapping replaces the adapter-specific optax-style transform object in the new migration contract.',
    'native': 'Preserve every public PyTorch workload function and its standard operator semantics, including optional attention masks, causal attention and grouped-query attention.',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(text):
    return sha(ast.dump(ast.parse(text), include_attributes=False).encode())


def family(tree):
    names = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    for name, kind in [('ExperimentModel', 'execution'), ('CandidateResidual', 'residual'),
                       ('StableSoftmaxNet', 'softmax'), ('TinyNet', 'training'),
                       ('parameter_workload', 'parameters')]:
        if name in names:
            return kind
    if any(isinstance(n, ast.ImportFrom) and n.module == 'torch4ms.optim.optimizer' for n in tree.body):
        return 'optimizer'
    return 'native'


def template(kind):
    return (ROOT / 'templates' / (kind + '.py')).read_text()


def build(row, paired):
    tree = ast.parse(row['candidate'])
    kind = family(tree)
    variant = row['contract']['model_variant']
    prefix = 'from __future__ import annotations\n\n'
    if kind == 'native':
        path = paired / row['task'] / 'source.py'
        assert path.exists(), path
        return path.read_text(), kind, 'Retained byte-for-byte from the completed paired workload protocol.'
    if kind == 'execution':
        definitions = [n for n in tree.body if isinstance(n, (ast.ClassDef, ast.FunctionDef))
                       and n.name in ('ExperimentModel', '_model_features')]
        assert len(definitions) == 2
        source = prefix + template(kind) + '\n\n' + '\n\n'.join(ast.unparse(n) for n in definitions) + '\n'
    else:
        source = prefix + f'MODEL_VARIANT = {variant!r}\n' + template(kind)
    if kind == 'training':
        batch = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_batch')
        seeds = [ast.literal_eval(n.args[0]) for n in ast.walk(batch) if isinstance(n, ast.Call)
                 and ast.unparse(n.func) == 'torch.manual_seed']
        assert len(seeds) == 1
        source = source.replace('import torch\n', f'BATCH_SEED = {seeds[0]}\nimport torch\n', 1)
        original = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
        if '_optimizer' not in original:
            source = source.replace('optimizer = _optimizer(model)',
                                    'optimizer = optim.SGD([p for p in model.parameters() if p.requires_grad], lr=0.2)')
            authored = ast.parse(source)
            authored.body = [n for n in authored.body if not (isinstance(n, ast.FunctionDef)
                             and n.name in ('_optimizer', 'apply_external_trainable_grads'))]
            source = ast.unparse(authored) + '\n'
    return source, kind, PROVENANCE


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--paired-inputs', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError('Prepared inputs are immutable; use a fresh output directory')
    audit = json.loads(args.audit.read_text())
    assert len(audit['tasks']) == 50
    planned = []
    for row in audit['tasks']:
        source, kind, provenance = build(row, args.paired_inputs)
        before = {n.name: ast.dump(n.args) for n in ast.parse(row['candidate']).body if isinstance(n, ast.FunctionDef)}
        after = {n.name: ast.dump(n.args) for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)}
        # Native optimizer/gradient interface names are retained; their new mapping is explicit.
        assert before == after, (row['task'], before.keys(), after.keys())
        contract = {
            'source_reference': 'source.py', 'target_framework': 'MindSpore',
            'public_interfaces': sorted(before), 'semantics': SEMANTICS[kind],
            'model_variant': row['contract']['model_variant'],
            'editable': ['candidate.py', 'torch4ms/**/*.py'],
            'tests': ['public'], 'seed': 101,
            'evaluation': {'final_seeds': [101, 202, 303], 'initial_state': 'explicit_parameter_value_alignment',
                           'forward_atol': 1e-4, 'forward_rtol': 1e-4,
                           'gradient_atol': 1e-4, 'gradient_rtol': 1e-3,
                           'update_atol': 1e-5, 'update_rtol': 1e-3,
                           'bf16_atol': .01, 'backend_execution_required': True},
        }
        planned.append((row, source, kind, provenance, contract))
    records = []
    for row, source, kind, provenance, contract in planned:
        folder = args.out / 'public' / row['task']
        folder.mkdir(parents=True)
        (folder / 'source.py').write_text(source)
        (folder / 'task.json').write_text(json.dumps(contract, indent=2) + '\n')
        records.append({'task': row['task'], 'input_form': kind, 'source_sha256': sha(source.encode()),
                        'source_ast_sha256': canonical(source), 'contract_sha256': sha((folder / 'task.json').read_bytes()),
                        'original_candidate_sha256': row['candidate_sha256'],
                        'source_provenance': provenance,
                        'source_retained': kind == 'native',
                        'legacy_interface_mapping_changed': kind in ('parameters', 'optimizer')})
    groups = defaultdict(list)
    for r in records:
        groups[(r['source_sha256'], r['contract_sha256'])].append(r['task'])
    manifest = {'tasks': records, 'task_count': 50, 'formal_execution_authorized': False,
                'real_model_calls': 0, 'author_inputs': [{'path': str(args.audit), 'sha256': sha(args.audit.read_bytes())}],
                'templates': {p.name: sha(p.read_bytes()) for p in sorted((ROOT / 'templates').glob('*.py'))},
                'family_counts': dict(Counter(r['input_form'] for r in records)),
                'unique_source_bytes': len({r['source_sha256'] for r in records}),
                'unique_source_and_contract': len(groups),
                'shared_translation_groups': [{'source_sha256': k[0], 'contract_sha256': k[1], 'tasks': v}
                                              for k, v in groups.items()],
                'review_required': ['Newly declared source semantics and four adapter-interface mappings',
                                    'Duplicate source/contract groups and generation reuse',
                                    'Acceptance thresholds, task coverage and formal budget']}
    (args.out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({k: v for k, v in manifest.items() if k not in ('tasks', 'shared_translation_groups', 'templates')}, indent=2))


if __name__ == '__main__':
    main()
