"""Inventory three public repository candidates without modifying their code."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'tmp/repository-pilot-assessment-20260920'
OUT = ROOT / 'output/repository-pilot-assessment-20260920'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    for name in ('time-series-forecasting-pytorch', 'two_tower_models', 'simple-moe'):
        root = BASE / name
        tracked = subprocess.check_output(['git', '-C', str(root), 'ls-files'], text=True).splitlines()
        files, failures = [], []
        for rel in tracked:
            path = root / rel
            if path.suffix != '.py':
                continue
            text = path.read_text()
            try:
                tree = ast.parse(text, filename=rel)
                classes = [n.name for n in tree.body if isinstance(n, ast.ClassDef)]
                tests = sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith('test_') for n in ast.walk(tree))
            except SyntaxError as exc:
                classes, tests = [], 0
                failures.append({'file': rel, 'line': exc.lineno, 'error': exc.msg})
            files.append({'path': rel, 'lines': len(text.splitlines()),
                          'nonempty_noncomment_lines': sum(bool(s.strip()) and not s.lstrip().startswith('#') for s in text.splitlines()),
                          'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                          'classes': classes, 'tests': tests})
        records.append({'repository': name,
                        'url': subprocess.check_output(['git', '-C', str(root), 'remote', 'get-url', 'origin'], text=True).strip(),
                        'commit': subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip(),
                        'tracked_files': len(tracked), 'python_files': len(files),
                        'python_physical_lines': sum(f['lines'] for f in files),
                        'test_functions': sum(f['tests'] for f in files),
                        'syntax_failures': failures, 'files': files})
    (OUT / 'inventory.json').write_text(json.dumps(records, indent=2) + '\n')
    print(json.dumps(records, indent=2))


if __name__ == '__main__':
    main()
