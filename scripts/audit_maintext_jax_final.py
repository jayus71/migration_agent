"""Audit final JAX patches and recorded acceptance without rerunning models."""
import argparse
import ast
import difflib
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(run, output):
    if output.exists():
        raise FileExistsError("Preserve previous audits")
    output.mkdir(parents=True)
    manifest = read(run / "manifest.json")
    frozen = read(run / "frozen_hashes.json")
    issues = [{"kind": "frozen_hash_mismatch", "path": name} for name, digest in frozen.items()
              if sha(run / name) != digest]
    namespace = {}
    exec(compile((run / "private_backend/torchax_candidate.py").read_text(), "frozen_candidate_generator", "exec"), namespace)
    records = []
    for task in manifest["tasks"]:
        name = task["anonymous_id"]
        for method in manifest["methods"]:
            condition = run / "conditions" / name / method
            result = read(condition / "result.json")
            if result["status"] == "running":
                raise RuntimeError("Final audit requires all conditions to terminate")
            record = {"task": name, "method": method, "status": result["status"],
                      "accepted": result["accepted"], "issues": []}
            def require(check, issue):
                if not check:
                    record["issues"].append(issue)
            require(result["status"] == "completed", "noncompleted_episode")
            require(result["initial"]["accepted"] is False, "initial_candidate_was_not_rejected")
            initial = run / "private_inputs" / name / "candidate.py"
            final = condition / "workspace/candidate.py"
            for source in ("source.py", "task.json"):
                require(sha(condition / "workspace" / source) == sha(run / "private_inputs" / name / source), "immutable_input_changed:" + source)
            for snapshot in ("initial_code", "after_diagnosis"):
                require(sha(condition / "evidence" / snapshot / "candidate.py") == sha(initial), snapshot + "_candidate_mismatch")
            require(sha(condition / "evidence/final_code/candidate.py") == sha(final), "final_archive_candidate_mismatch")
            record["initial_candidate_sha256"] = sha(initial)
            record["final_candidate_sha256"] = sha(final)
            record["matches_original_healthy_ast"] = ast.dump(ast.parse(final.read_text()), include_attributes=False) == ast.dump(ast.parse(namespace["healthy_source"](task["model"])), include_attributes=False)
            patch = "".join(difflib.unified_diff(initial.read_text().splitlines(True), final.read_text().splitlines(True), fromfile="initial/candidate.py", tofile="final/candidate.py"))
            (output / f"{name}_{method}.patch").write_text(patch)
            record["patch"] = f"{name}_{method}.patch"
            record["accepted_measurements"] = []
            accepted = [attempt for attempt in result["attempts"] if attempt.get("accepted") is True]
            if result["accepted"]:
                require(bool(accepted), "accepted_without_accepted_attempt")
                attempt = accepted[-1]
                measurements = [attempt["evaluation"], *attempt["confirmation"]]
                require(sorted(row["seed"] for row in measurements) == [6701, 6702, 6703], "missing_confirmation_seed")
                for measurement in measurements:
                    folder = Path(measurement["measurement"])
                    require(folder.is_relative_to(condition / "evidence"), "measurement_outside_condition")
                    raw = read(folder / "raw_target.json")
                    observed = read(folder / "observation.json")
                    proc = read(folder / "process.json")
                    backend = raw.get("backend_evidence", {})
                    require(raw.get("status") == "ok" and raw.get("mode") == "torchax", "target_execution_not_torchax")
                    require(backend.get("is_jax_array") is True, "target_jax_storage_not_observed")
                    require(backend.get("training_api") == "JittableModule+jax_value_and_grad+optax.sgd", "target_training_api_unexpected")
                    require(proc["returncode"] == 0 and proc["isolation"] == "landlock+seccomp", "target_process_or_isolation_failed")
                    require(observed["accepted"] is True and all(observed["observation"]["acceptance"]["checks"].values()), "accepted_measurement_check_failed")
                    record["accepted_measurements"].append({"seed": measurement["seed"],
                        "path": str(folder.relative_to(run)), "raw_target_sha256": sha(folder / "raw_target.json"),
                        "backend_evidence": backend, "measurements": observed["observation"]["measurements"]})
            records.append(record)
            issues.extend({"task": name, "method": method, "kind": issue} for issue in record["issues"])
    value = {"run": str(run), "manifest_sha256": sha(run / "manifest.json"),
        "scope": "Recorded evidence and final code only; no new candidate execution or model calls",
        "conditions": len(records), "accepted": sum(row["accepted"] for row in records),
        "accepted_backend_measurements": sum(len(row["accepted_measurements"]) for row in records),
        "healthy_ast_matches": sum(row["matches_original_healthy_ast"] for row in records),
        "issues": issues, "records": records}
    (output / "audit.json").write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    return value


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.run.resolve(), args.output.resolve())
    print(json.dumps({key: result[key] for key in ("conditions", "accepted", "accepted_backend_measurements", "healthy_ast_matches", "issues")}))
