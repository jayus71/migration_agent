#!/usr/bin/env python3
"""Build a Git-friendly result view and an immutable full-snapshot asset."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = "experiment-results-local-20260906"
TAG = "experiment-data-20260906-v1"
REPO = "jayus71/migration_agent"
EXCLUDED_PARTS = {
    "raw", "checkpoints", "tool_runs", "workspace", "tasks", "autofix",
    "__pycache__", "generated_harnesses", "reports",
}


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def select(path, size):
    if EXCLUDED_PARTS.intersection(path.parts) or ":" in path.name:
        return False
    if path.suffix == ".md":
        return size <= 1024 * 1024
    if path.suffix == ".csv":
        return size <= 5 * 1024 * 1024
    if path.suffix == ".json":
        return size <= 1024 * 1024 and "raw" not in path.stem.lower()
    return False


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = ROOT / SNAPSHOT
    data = ROOT / "data"
    selected_root = data / "experiments"
    if selected_root.exists() or (data / "paper_section_65_66").exists():
        parser.error("generated data directories already exist; use a fresh checkout")
    args.output.mkdir(parents=True, exist_ok=True)
    archive = args.output / f"{TAG}.tar.gz"
    if archive.exists():
        parser.error(f"refusing to replace {archive}")
    paths = sorted(source.rglob("*"))
    if any(p.is_symlink() or not (p.is_file() or p.is_dir()) for p in paths):
        parser.error("snapshot contains links or special files")
    paths = [p for p in paths if p.is_file()]
    if not paths:
        parser.error("source snapshot is empty or missing")
    data.mkdir(exist_ok=True)
    records, selected = [], []
    for path in paths:
        relative = path.relative_to(source)
        record = {
            "path": f"{SNAPSHOT}/{relative.as_posix()}",
            "size": path.stat().st_size,
            "sha256": digest(path),
        }
        records.append(record)
        if select(relative, record["size"]):
            target = selected_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            selected.append({**record, "destination": target.relative_to(ROOT).as_posix()})

    # Preserve the manuscript's older inputs separately from the new A-K runs.
    legacy = ROOT / "ascend-torch4ms/experiments/paper_section_65_66"
    paper_records = []
    for directory in (
        "results_section65_per_step_divergence",
        "results_realdata_66",
        "results_section65_signal_sanity_current",
    ):
        for path in sorted((legacy / directory).iterdir()):
            if path.suffix not in {".csv", ".json", ".md"}:
                continue
            target = data / "paper_section_65_66" / path.relative_to(legacy)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            paper_records.append({
                "path": path.relative_to(ROOT).as_posix(),
                "destination": target.relative_to(ROOT).as_posix(),
                "size": path.stat().st_size,
                "sha256": digest(path),
            })

    with archive.open("xb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w|", format=tarfile.PAX_FORMAT) as tar:
                for path, record in zip(paths, records):
                    info = tar.gettarinfo(str(path), arcname=record["path"])
                    info.uid = info.gid = 0
                    info.uname = info.gname = ""
                    info.mtime = 0
                    info.mode = 0o644
                    with path.open("rb") as stream:
                        tar.addfile(info, stream)
    write_json(data / "archive-manifest.json", {
        "schema_version": 1,
        "repository": REPO,
        "release_tag": TAG,
        "snapshot_root": SNAPSHOT,
        "asset": archive.name,
        "url": f"https://github.com/{REPO}/releases/download/{TAG}/{archive.name}",
        "archive_sha256": digest(archive),
        "archive_bytes": archive.stat().st_size,
        "file_count": len(records),
        "uncompressed_bytes": sum(r["size"] for r in records),
        "files": records,
    })
    write_json(data / "selected-manifest.json", {
        "schema_version": 1,
        "snapshot_root": SNAPSHOT,
        "selection": "Markdown/JSON <=1 MiB and CSV <=5 MiB, excluding raw execution trees and raw JSON. See scripts/prepare_experiment_data.py.",
        "selected_files": selected,
        "paper_input_files": paper_records,
    })
    (args.output / "SHA256SUMS").write_text(f"{digest(archive)}  {archive.name}\n")
    print(f"Full archive: {len(records)} files, {archive.stat().st_size} compressed bytes")
    print(f"Git view: {len(selected)} result files, {len(paper_records)} original paper inputs")


if __name__ == "__main__":
    main()
