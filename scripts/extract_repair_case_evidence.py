"""Snapshot the archived grouped-query attention repair case; never execute candidate programs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "ascend-torch4ms/experiments/baselines/full_hier_fixed50"
OUTPUT = ROOT / "data/paper_figures/repair_case_evidence.json"


def load(method, instance):
    paths = list((ARCHIVE / method / "raw").glob(f"{instance}*.json"))
    if len(paths) != 1:
        raise ValueError(f"Expected one archived report: {method}/{instance}")
    path = paths[0]
    data = json.loads(path.read_text())
    source = {"path": path.relative_to(ROOT).as_posix(),
              "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    return data, data.get("raw", data), source


def numerical_probe(validation):
    probe = validation.get("probe")
    if probe is None:
        probe = validation.get("verification", {}).get("verify_outputs", [{}])[0]
    for line in probe.get("output", "").splitlines():
        if line.startswith("{"):
            payload = json.loads(line)
            if "max_abs_diff" in payload:
                return payload
    return None  # Execution failure supplies no numerical measurement.


def repair_evidence(method, attempt):
    generation = attempt.get("candidate", attempt.get("generation", {}))
    metadata = generation.get("metadata", {})
    if method == "r_swe":
        code = metadata.get("trajectory", {}).get("info", {}).get("submission", "")
    elif method == "r_matchfix":
        code = (metadata.get("matchfix_result", {}).get("results", {}).get("test_repair", {})
                .get("parsed_final_response", {}).get("correct_target_method_implementation", ""))
    else:
        code = "\n".join(e.get("replace_text", "") for e in generation.get("edits", []))
    return {
        "edited_files": sorted({e["file"] for e in generation.get("edits", [])}),
        "head_repetition_lines": [line for line in (code or "").splitlines()
                                  if any(token in line for token in
                                         ("key = mops.", "value = mops."))],
    }


def main():
    gqa = {
        "instance": "NU-07-B", "query_heads": 4, "key_value_heads": 2,
        "tolerance": 1e-4,
        "probe_source": "ascend-torch4ms/autofix/faults/core_qwen.py::_probe_only",
        "allowed_file": "torch4ms/ops/mtorch.py",
        "tiled_head_order": [0, 1, 0, 1],
        "required_head_order": [0, 0, 1, 1],
        "head_order_basis": "Analytical expansion of tile versus repetition of each head",
        "methods": {},
    }
    for method in ("r_direct", "r_swe", "r_matchfix", "r_hier"):
        data, raw, source = load(method, "NU-07-B")
        attempts = [{"attempt": i + 1, "status": a["validation"]["status"],
                     "probe": numerical_probe(a["validation"]),
                     "repair_evidence": repair_evidence(method, a)}
                    for i, a in enumerate(raw["attempts"])]
        gqa["methods"][method] = {
            "source": source, "accepted": data["episode"]["strict_success"],
            "attempts": attempts,
        }
    first = [gqa["methods"][m]["attempts"][0]["probe"]
             for m in ("r_direct", "r_swe", "r_hier")]
    assert all(p == first[0] for p in first)
    assert not first[0]["ok"] and first[0]["finite"]
    assert first[0]["actual_shape"] == first[0]["expected_shape"]
    for method in ("r_direct", "r_swe", "r_hier"):
        assert gqa["methods"][method]["attempts"][0]["repair_evidence"]["edited_files"] == [gqa["allowed_file"]]
    assert gqa["methods"]["r_hier"]["attempts"][1]["probe"]["ok"]
    result = {"description": "Read-only extraction from original Fixed50 reports; no rerun",
              "gqa_repair": gqa}
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
