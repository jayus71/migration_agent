"""Verify the distributed file list and hashes using only the standard library."""
import hashlib
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    expected = {}
    for line in (root / "MANIFEST.sha256").read_text().splitlines():
        digest, name = line.split("  ", 1)
        p = root / name
        if not p.resolve().is_relative_to(root) or p.is_symlink():
            raise RuntimeError("Unsafe member: " + name)
        if hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            raise RuntimeError("Hash mismatch: " + name)
        expected[name] = digest
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()
              and "__pycache__" not in p.parts and not p.relative_to(root).parts[0].startswith(".")
              and p.name != "MANIFEST.sha256"}
    if actual != set(expected):
        raise RuntimeError("Unexpected or missing distributed files: " + repr(actual ^ set(expected)))
    print(f"Verified {len(expected)} files.")


if __name__ == "__main__":
    main()
