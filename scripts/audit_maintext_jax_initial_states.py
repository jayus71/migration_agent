"""Audit recorded initial states without modifying JAX acceptance decisions."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path


def compare_vectors(reference, target):
    if not isinstance(reference, list) or not isinstance(target, list):
        return {"status": "unavailable"}
    if not reference or not target:
        return {"status": "unavailable", "reference_length": len(reference), "target_length": len(target)}
    lengths = {"reference_length": len(reference), "target_length": len(target)}
    if not all(type(value) in (int, float) and math.isfinite(value) for value in reference + target):
        return {"status": "invalid", **lengths}
    if len(reference) != len(target):
        return {"status": "shape_mismatch", **lengths}
    delta = [right - left for left, right in zip(reference, target)]
    return {"status": "observed", **lengths,
            "exact_match": reference == target,
            "max_abs_difference": max(abs(value) for value in delta),
            "relative_l2": math.hypot(*delta) / max(math.hypot(*reference), 1e-12)}


def audit(run):
    manifest_path = run / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    models = {row["anonymous_id"]: row["model"] for row in manifest["tasks"]}
    rows = []
    for path in sorted((run / "conditions").glob("*/*/evidence/measurement_*/raw_target.json")):
        task, method = path.relative_to(run / "conditions").parts[:2]
        target = json.loads(path.read_text())
        observation_path = path.with_name("observation.json")
        observation = json.loads(observation_path.read_text())
        seed = observation["seed"]
        reference_path = run / "private_reference" / models[task] / f"{seed}.json"
        reference = json.loads(reference_path.read_text())
        comparison = compare_vectors(reference.get("initial_vector"), target.get("initial_vector"))
        rows.append({"task": task, "method": method, "seed": seed,
                     "accepted": observation["accepted"],
                     "target_execution_status": target.get("status"),
                     "measurement": str(path.parent.relative_to(run)),
                     "raw_target_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                     "reference_sha256": hashlib.sha256(reference_path.read_bytes()).hexdigest(),
                     "initial_state": comparison})
    statuses = Counter(row["initial_state"]["status"] for row in rows)
    accepted = [row for row in rows if row["accepted"]]
    return {"source_run": str(run),
            "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            "scope": "Every recorded target measurement, including preflight, clean controls and intermediate patches.",
            "interpretation": "Offline state comparison only; no candidate execution or acceptance changes. Missing vectors are unavailable, never matches.",
            "measurements": len(rows), "initial_state_statuses": dict(statuses),
            "accepted_measurements": len(accepted),
            "accepted_exact_initial_matches": sum(row["initial_state"].get("exact_match") is True for row in accepted),
            "accepted_without_exact_initial_match": [row for row in accepted if row["initial_state"].get("exact_match") is not True],
            "records": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    value = audit(args.run.resolve())
    if not value["measurements"]:
        raise ValueError("No recorded JAX measurements found")
    if args.output.exists():
        raise FileExistsError("Preserve the previous audit; use a new output path")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    print(json.dumps({key: value[key] for key in ("measurements", "initial_state_statuses", "accepted_measurements", "accepted_exact_initial_matches")}))


if __name__ == "__main__":
    main()
