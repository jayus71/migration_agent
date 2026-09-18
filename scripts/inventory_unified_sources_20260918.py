"""Inventory source programs without using candidates, outcomes, or private fault labels."""
import ast
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

BASE = Path('/media/main/whj/projects/torch4ms')
OLD = BASE / 'ascend-torch4ms-autonomous-verifier-20260917'
COLLECTIONS = {
    'translation_sources': (BASE / 'ascend-torch4ms-e-baselines-current-20260918/experiments/paper_section_63_64/section642_heldout_sources', '*.py'),
    'natural_translation_sources': (OLD / 'experiments/autonomous_verifier_20260917/progress_v4/private_inputs', '*/source.py'),
    'jax_sources': (BASE / 'experiments/maintext_jax_autonomous_20260918/formal_v5/private_inputs', '*/source.py'),
}


def main():
    rows = []
    for collection, (root, pattern) in COLLECTIONS.items():
        paths = sorted(root.glob(pattern))
        assert paths, f'Missing collection: {collection}'
        for path in paths:
            text = path.read_text(encoding='utf-8-sig')
            tree = ast.parse(text)
            # Ignore comments and docstrings when detecting repeated programs.
            for node in ast.walk(tree):
                if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if node.body and isinstance(node.body[0], ast.Expr):
                        value = node.body[0].value
                        if isinstance(value, ast.Constant) and isinstance(value.value, str):
                            node.body = node.body[1:]
            canonical = ast.dump(tree, include_attributes=False)
            functions = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
            imports = sorted({a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
                | {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module})
            rows.append(dict(collection=collection, path=str(path),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                ast_sha256=hashlib.sha256(canonical.encode()).hexdigest(),
                functions=functions, classes=[n.name for n in tree.body if isinstance(n, ast.ClassDef)],
                imports=imports, has_training_interface=all(n in functions for n in ('build_model', 'train_one_step'))))
    groups = defaultdict(list)
    for row in rows:
        groups[row['ast_sha256']].append(row)
    report = dict(real_model_calls=0, selection_inputs='Source programs only; no candidate outcomes or private fault labels.',
        source_records=len(rows), collection_counts=dict(Counter(r['collection'] for r in rows)),
        unique_byte_hashes=len({r['sha256'] for r in rows}), unique_ast_programs=len(groups),
        unique_programs_with_training_interface=sum(v[0]['has_training_interface'] for v in groups.values()),
        groups=[dict(ast_sha256=k, occurrences=len(v), origins=v) for k, v in sorted(groups.items())])
    out = BASE / 'unified-migration-dataset-20260918'
    out.mkdir(exist_ok=True)
    (out / 'source_inventory.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'groups'}, indent=2))
    print(json.dumps([dict(occurrences=len(v), origins=sorted({r['collection'] for r in v}),
        classes=v[0]['classes'], training_interface=v[0]['has_training_interface']) for v in groups.values()], indent=2))


if __name__ == '__main__':
    main()
