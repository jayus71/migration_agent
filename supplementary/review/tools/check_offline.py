"""Run each measured implementation's offline suite in a separate process."""
import ast
import os
from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    files = [p for p in root.rglob("*.py") if not any(x.startswith(".") for x in p.relative_to(root).parts)]
    for path in files:
        ast.parse(path.read_text(), filename=path.relative_to(root).as_posix())
    print(f"Syntax checked {len(files)} Python files.", flush=True)
    for variant in ("program", "repository"):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        env["PYTHONPATH"] = os.pathsep.join(map(str, [root / variant, root / variant / "scripts", root]))
        subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(root / "tests" / variant), "-p", "test_*.py"], cwd=root, env=env, check=True)


if __name__ == "__main__":
    main()
