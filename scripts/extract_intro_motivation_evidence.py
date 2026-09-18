"""Snapshot the archived I-09 probe for the introduction diagram; runs no experiment."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = Path(
    "experiment-results-local-20260906/09_experiment_I_real_translation/"
    "runs_real_core_v3/tasks/I-09/r_hier/reports/"
    "I-09__r_hier_iter1_paired_report.json"
)
DESTINATION = ROOT / "data/paper_figures/intro_motivation_evidence.json"


def main():
    raw = (ROOT / REPORT).read_bytes()
    report = json.loads(raw)
    comparison = report["comparison"]
    parameters = comparison["parameter_update_diagnostics"]["parameters"]
    source = report["results"]["torch"]
    target = report["results"]["torch4ms"]
    assert source["status"] == target["status"] == "ok"
    assert report["config"]["sync_initial_state"] is True
    assert len(source["losses"]) == len(target["losses"]) == 1
    zero_updates = [
        p["name"] for p in parameters
        if p["candidate_update_norm"] == 0 and p["reference_update_norm"] > 0
    ]
    matching_updates = [p["name"] for p in parameters if p["update_diff_norm"] == 0]
    evidence = {
        "instance": "I-09",
        "source_report": REPORT.as_posix(),
        "source_report_sha256": hashlib.sha256(raw).hexdigest(),
        "source_framework": "PyTorch",
        "target_framework": "MindSpore via torch4ms",
        "observation": "Initial synchronized training step, before repair",
        "source_loss": source["losses"][0],
        "target_loss": target["losses"][0],
        "loss_absolute_difference": comparison["last_step_abs_loss_diff"],
        "gradient_norm_absolute_difference": comparison["last_step_abs_grad_norm_diff"],
        "parameter_update_relative_l2_difference": comparison["param_update_rel_l2"],
        "zero_target_update_parameters": zero_updates,
        "matching_update_parameters": matching_updates,
        "parameter_update_diagnostics": parameters,
        "code_review": "docs/natural-translation-cause-review-20260916.md",
        "mechanism_evidence": "Static review of archived operator registration and fallback code",
        "repair_outcome": "STOP_NO_PROGRESS",
    }
    DESTINATION.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(DESTINATION.relative_to(ROOT))
    print(f"{len(zero_updates)} parameter tensors have zero target updates; "
          f"{len(matching_updates)} have matching updates.")


if __name__ == "__main__":
    main()
