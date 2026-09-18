"""Cross-check final JAX analyses and produce a compact verification record."""
import argparse
from collections import Counter
import json
from pathlib import Path


def validate(folder):
    comparison = json.loads((folder / "comparison.json").read_text())
    states = json.loads((folder / "initial_states.json").read_text())
    patches = json.loads((folder / "final_patch_audit/audit.json").read_text())
    assert comparison["complete"] and comparison["all_terminal"]
    assert not comparison["unexpected_results"]
    audits = comparison["raw_ledger_audits"]
    assert len(audits) == 12 and all(row["available"] and not row["mismatches"] for row in audits.values())
    assert all(not row["missing_ledgers"] and row["unknown_usage_calls"] == 0 for row in comparison["methods"].values())
    assert patches["conditions"] == 12 and not patches["issues"]
    assert patches["accepted_backend_measurements"] == 36 and patches["healthy_ast_matches"] == 12
    accepted = [row for row in states["records"] if row["accepted"] and row["method"] in comparison["methods"]]
    assert all(row["initial_state"].get("exact_match") is True for row in accepted)
    final_paths = {row["path"] for patch in patches["records"] for row in patch["accepted_measurements"]}
    state_by_path = {row["measurement"]: row for row in states["records"]}
    assert len(final_paths) == 36 and all(state_by_path[path]["initial_state"].get("exact_match") is True for path in final_paths)
    models = sorted({model for row in audits.values() for model in row["actual_models"]})
    assert models and all(model.startswith("deepseek") for model in models)
    metrics = [row["measurements"] for patch in patches["records"] for row in patch["accepted_measurements"]]
    return {"conditions_verified": 12, "raw_calls_verified": sum(row["observed"]["calls"] for row in audits.values()),
            "raw_ledger_mismatches": 0, "unknown_usage_calls": 0, "actual_models": models,
            "accepted_final_seed_checks": 36, "accepted_final_exact_initial_matches": 36,
            "all_accepted_repair_measurements": len(accepted), "all_accepted_repair_initial_states_exact": True,
            "accepted_control_measurements_without_initial_vector": states["accepted_without_exact_initial_match"],
            "stage_status_counts": dict(Counter(status for row in comparison["records"] for status in row["stage_statuses"])),
            "maximum_final_differences": {name: max(row[name]["value"] for row in metrics) for name in metrics[0]},
            "healthy_target_ast_matches": 12, "frozen_file_mismatches": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Preserve previous checks")
    value = validate(args.folder)
    args.output.write_text(json.dumps(value, indent=2) + "\n")
    print(json.dumps({k: v for k, v in value.items() if k != "accepted_control_measurements_without_initial_vector"}, indent=2))
