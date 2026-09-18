#!/usr/bin/env python3
"""Archive a stopped recovery tree with hashes for every regular file."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import stat
import tarfile


def digest(handle):
    value = hashlib.sha256()
    for block in iter(lambda: handle.read(1024 * 1024), b""):
        value.update(block)
    return value.hexdigest()


def sha(path):
    with path.open("rb") as handle:
        return digest(handle)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="New archive basename outside source")
    parser.add_argument("--verify", action="store_true", help="Verify an existing archive against its manifest")
    args = parser.parse_args()
    source, prefix = args.source.resolve(), args.output.resolve()
    archive, metadata = prefix.with_suffix(".tar.gz"), prefix.with_suffix(".json")
    if source == archive or source in archive.parents:
        raise ValueError("Archive output must be outside source")
    if args.verify:
        record = json.loads(metadata.read_text())
        if sha(archive) != record["archive_sha256"] or archive.stat().st_size != record["archive_bytes"]:
            raise ValueError("Outer archive hash or size mismatch")
        seen = set()
        with tarfile.open(archive, "r|gz") as tar:
            for member in tar:
                if not member.isfile() or not member.name.startswith(record["prefix"]):
                    raise ValueError("Unexpected archive member")
                rel = member.name[len(record["prefix"]):]
                if rel in seen or rel not in record["files"]:
                    raise ValueError("Duplicate or unlisted archive member")
                seen.add(rel)
                with tar.extractfile(member) as handle:
                    if digest(handle) != record["files"][rel]["sha256"] or member.size != record["files"][rel]["bytes"]:
                        raise ValueError("Archive member mismatch: " + rel)
        if seen != set(record["files"]):
            raise ValueError("Missing archive members")
        verified = {"verified_at": datetime.now(timezone.utc).isoformat(), "archive": str(archive),
                    "archive_sha256": record["archive_sha256"], "files_verified": len(seen), "errors": []}
        prefix.with_suffix(".verification.json").write_text(json.dumps(verified, indent=2) + "\n")
        print(json.dumps(verified))
        return
    terminal = source / "dispatch_result.json"
    if not terminal.exists():
        raise ValueError("Recovery dispatcher has not finished")
    partial = prefix.with_suffix(".partial")
    if any(path.exists() for path in (archive, metadata, partial)):
        raise ValueError("Refusing to overwrite archive")
    archive.parent.mkdir(parents=True, exist_ok=True)
    files, skipped = {}, []
    with tarfile.open(partial, "w:gz", compresslevel=3, dereference=False) as tar:
        for path in sorted(source.rglob("*")):
            relative = str(path.relative_to(source))
            mode = path.lstat().st_mode
            if stat.S_ISDIR(mode):
                continue
            if "__pycache__" in path.parts or path.suffix == ".pyc" or not stat.S_ISREG(mode):
                skipped.append(relative)
                continue
            files[relative] = {"sha256": sha(path), "bytes": path.stat().st_size}
            tar.add(path, arcname=prefix.name + "/" + relative, recursive=False)
    for relative, expected in files.items():
        if sha(source / relative) != expected["sha256"]:
            raise ValueError("Source changed while archiving: " + relative)
    partial.replace(archive)
    record = {"archived_at": datetime.now(timezone.utc).isoformat(), "source": str(source),
        "prefix": prefix.name + "/", "archive_sha256": sha(archive), "archive_bytes": archive.stat().st_size,
        "dispatch_result": json.loads(terminal.read_text()), "files": files, "skipped": skipped}
    metadata.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"archive": str(archive), "sha256": record["archive_sha256"], "bytes": record["archive_bytes"], "files": len(files)}))


if __name__ == "__main__":
    main()
