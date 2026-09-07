#!/usr/bin/env python3
"""Download and verify the complete experiment snapshot using only Python's stdlib."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify(directory, manifest):
    expected = {r["path"] for r in manifest["files"]}
    actual = {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()}
    if actual != expected:
        raise ValueError("snapshot file inventory differs from the manifest")
    for record in manifest["files"]:
        path = directory / record["path"]
        if path.is_symlink() or path.stat().st_size != record["size"] or digest(path) != record["sha256"]:
            raise ValueError(f"snapshot checksum mismatch: {record['path']}")


def extract(archive, directory, manifest):
    expected = {r["path"]: r for r in manifest["files"]}
    seen = set()
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar:
            name = PurePosixPath(member.name)
            if (name.is_absolute() or ".." in name.parts or not member.isfile()
                    or member.name not in expected or member.name in seen):
                raise ValueError(f"unexpected archive entry: {member.name}")
            record = expected[member.name]
            if member.size != record["size"]:
                raise ValueError(f"archive size mismatch: {member.name}")
            target = directory / member.name
            target.parent.mkdir(parents=True, exist_ok=True)
            with tar.extractfile(member) as source, target.open("xb") as output:
                shutil.copyfileobj(source, output)
            if digest(target) != record["sha256"]:
                raise ValueError(f"archive checksum mismatch: {member.name}")
            seen.add(member.name)
    if seen != expected.keys():
        raise ValueError("archive is missing files")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, help="use an already downloaded .tar.gz")
    parser.add_argument("--destination", type=Path, default=ROOT / ".experiment-data/20260906-v1")
    parser.add_argument("--verify-only", action="store_true", help="verify an existing extracted snapshot")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "data/archive-manifest.json").read_text())
    destination = args.destination.resolve()
    if args.verify_only or destination.exists():
        verify(destination, manifest)
        print(f"Verified {manifest['file_count']} files in {destination}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Extract into a new sibling directory, then publish it only after all checks pass.
    with tempfile.TemporaryDirectory(prefix=".experiment-download-", dir=destination.parent) as temporary:
        temporary = Path(temporary)
        archive = args.archive
        if archive is None:
            archive = temporary / manifest["asset"]
            request = urllib.request.Request(manifest["url"], headers={"User-Agent": "migration-agent-data/1"})
            print(f"Downloading {manifest['url']}", flush=True)
            with urllib.request.urlopen(request, timeout=120) as response, archive.open("xb") as output:
                shutil.copyfileobj(response, output)
        if archive.stat().st_size != manifest["archive_bytes"] or digest(archive) != manifest["archive_sha256"]:
            raise ValueError("archive SHA-256/size mismatch; nothing was installed")
        unpacked = temporary / "snapshot"
        unpacked.mkdir()
        extract(archive, unpacked, manifest)
        if destination.exists():
            raise FileExistsError(f"refusing to overwrite {destination}")
        unpacked.rename(destination)
    print(f"Verified {manifest['file_count']} files in {destination}")


if __name__ == "__main__":
    main()
