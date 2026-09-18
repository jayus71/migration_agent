"""Create or stream-verify a complete, immutable JAX evidence archive."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile


def digest_stream(stream):
    digest = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(chunk)
    return digest.hexdigest()


def sha(path):
    with path.open("rb") as stream:
        return digest_stream(stream)


def create(root, archive):
    if archive.exists() or archive.is_relative_to(root):
        raise ValueError("Archive must be a new file outside the evidence root")
    run = root / "formal_v5"
    manifest = json.loads((run / "manifest.json").read_text())
    for task in manifest["tasks"]:
        for method in manifest["methods"]:
            row = json.loads((run / "conditions" / task["anonymous_id"] / method / "result.json").read_text())
            if row["status"] == "running":
                raise RuntimeError("A formal worker is still running")
    for name in ("summary.json", "comparison.json", "initial_states.json", "final_patch_audit/audit.json"):
        if not (run / "final_analysis" / name).is_file():
            raise RuntimeError("Missing final analysis: " + name)
    index = root / "final_file_manifest.json"
    if index.exists():
        raise FileExistsError("Final inventory already exists")
    entries = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            entries[path.relative_to(root).as_posix()] = {"type": "symlink", "target": str(path.readlink())}
        elif path.is_file():
            entries[path.relative_to(root).as_posix()] = {"type": "file", "bytes": path.stat().st_size, "sha256": sha(path)}
    payload = {"scope": "All JAX development versions, converter evidence, complete formal v5 repair evidence, and final audits",
               "formal_manifest_sha256": sha(run / "manifest.json"), "entries": entries,
               "self_exclusion": "This inventory excludes its own file; the archive digest covers it."}
    index.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    with tarfile.open(archive, "w:gz") as tf:
        tf.add(root, arcname=root.name, recursive=True)
    return verify(archive)


def verify(archive):
    with tarfile.open(archive, "r:gz") as tf:
        members = tf.getmembers()
        inventory_members = [m for m in members if m.name.endswith("/final_file_manifest.json")]
        if len(inventory_members) != 1:
            raise ValueError("Expected exactly one final inventory")
        inventory_member = inventory_members[0]
        prefix = str(PurePosixPath(inventory_member.name).parent) + "/"
        manifest = json.load(tf.extractfile(inventory_member))
        observed = set()
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("Unsafe archive path")
            if member.isdir() or member.name == inventory_member.name:
                continue
            if not member.name.startswith(prefix):
                raise ValueError("Unexpected archive root")
            relative = member.name[len(prefix):]
            if relative in observed:
                raise ValueError("Duplicate archive entry")
            expected = manifest["entries"][relative]
            if member.issym():
                if expected != {"type": "symlink", "target": member.linkname}:
                    raise ValueError("Symlink mismatch: " + relative)
            elif member.isfile():
                if expected["type"] != "file" or member.size != expected["bytes"] or digest_stream(tf.extractfile(member)) != expected["sha256"]:
                    raise ValueError("File mismatch: " + relative)
            else:
                raise ValueError("Unexpected archive member type")
            observed.add(relative)
        if observed != set(manifest["entries"]):
            raise ValueError("Incomplete archive")
    return {"archive": str(archive), "bytes": archive.stat().st_size, "sha256": sha(archive),
            "verified_entries": len(observed), "formal_manifest_sha256": manifest["formal_manifest_sha256"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("create", "verify"))
    parser.add_argument("archive", type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    value = create(args.root.resolve(), args.archive.resolve()) if args.action == "create" else verify(args.archive.resolve())
    text = json.dumps(value, indent=2) + "\n"
    if args.report:
        if args.report.exists():
            raise FileExistsError("Preserve prior verification records")
        args.report.write_text(text)
    print(text)
