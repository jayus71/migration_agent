"""Read-only audit of archived Fixed50 attempts; no repair or model execution."""
from __future__ import annotations

import collections
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "ascend-torch4ms/experiments/baselines/full_hier_fixed50"
OUT = Path(__file__).resolve().parent
METHODS = ("r_hier", "r_swe", "r_matchfix")
TOKEN_KEYS = ("prompt_tokens", "completion_tokens", "total_tokens")


def llm_usages(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "llm_call" and isinstance(item, dict):
                if isinstance(item.get("usage"), dict):
                    yield item["usage"]
            else:
                yield from llm_usages(item)
    elif isinstance(value, list):
        for item in value:
            yield from llm_usages(item)


def sum_usage(value):
    found = list(llm_usages(value))
    return {k: sum(int(u.get(k, 0) or 0) for u in found) for k in TOKEN_KEYS}


rows = list(csv.DictReader((DATA / "instances.csv").open()))
summary = {r["baseline_id"]: r for r in csv.DictReader((DATA / "summary.csv").open())}
snapshot = ROOT / "data/paper_figures/fixed50_original_summary.csv"
assert snapshot.read_bytes() == (DATA / "summary.csv").read_bytes()
indexed = {m: {r["instance_id"]: r for r in rows if r["baseline_id"] == m} for m in METHODS}
assert all(len(v) == 50 for v in indexed.values())
failures = {m: {i for i, r in indexed[m].items() if r["repair_at_1"] != "True"} for m in METHODS}
audit = {"source": str(DATA.relative_to(ROOT)), "methods": {}, "token_omissions": [],
         "shared_baseline_first_failures": sorted(failures["r_swe"] & failures["r_matchfix"]),
         "matchfix_component_usage": {}, "source_hashes": {}}
component_usage = collections.defaultdict(collections.Counter)
for method in METHODS:
    total = collections.Counter()
    first_total = collections.Counter()
    failure_rows = []
    call_count = 0
    per_instance = []
    for path in sorted((DATA / method / "raw").glob("*.json")):
        d = json.loads(path.read_text())
        episode = d["episode"]
        instance = episode["instance_id"]
        row = indexed[method][instance]
        raw = d.get("raw", d)
        attempts = raw.get("attempts", [])
        selected = attempts if attempts else raw.get("generation", {})
        usage = sum_usage(selected)
        first_usage = sum_usage(attempts[0] if attempts else selected)
        total.update(usage)
        first_total.update(first_usage)
        relative_path = str(path.relative_to(ROOT))
        audit["source_hashes"][relative_path] = hashlib.sha256(path.read_bytes()).hexdigest()
        if usage["total_tokens"] != int(row["total_tokens"]):
            assert method == "r_hier" and int(row["total_tokens"]) == 0
            audit["token_omissions"].append({"instance": instance, "summary_tokens": 0,
                                            "raw_usage": usage, "raw_report": relative_path})
        per_instance.append({"instance": instance, "official_first_acceptance": row["repair_at_1"] == "True",
                             "official_final_acceptance": row["strict_success"] == "True",
                             "scope": indexed["r_hier"][instance]["scope"],
                             "summary_tokens": int(row["total_tokens"]), "raw_usage": usage,
                             "first_usage": first_usage})
        if method == "r_hier":
            call_count += len(list(llm_usages(selected)))
            continue
        for attempt in attempts:
            metadata = attempt["generation"].get("metadata", {})
            if method == "r_swe":
                stats = metadata.get("trajectory", {}).get("info", {}).get("model_stats", {})
                call_count += int(stats.get("api_calls", 0))
            else:
                result = metadata.get("matchfix_result", {})
                call_count += int(result.get("usage", {}).get("api_calls", 0))
                results = result.get("results", {})
                parts = {**results.get("semantic_analyzer_analyses", {}),
                         **{k: results.get(k, {}) for k in ("test_repair", "verdict")}}
                for name, part in parts.items():
                    u = part.get("usage", {})
                    component_usage[name].update({k: int(u.get(k, 0)) for k in TOKEN_KEYS})
        if instance not in failures[method]:
            continue
        a = attempts[0]
        generation = a["generation"]
        metadata = generation.get("metadata", {})
        item = {"instance": instance, "raw_report": relative_path,
                "edits": generation.get("edits", []), "first_usage": first_usage,
                "validation_status": a["validation"].get("status"),
                "out_of_scope_edit_count": episode.get("out_of_scope_edit_count", 0),
                "final_accepted": row["strict_success"] == "True"}
        if method == "r_swe":
            info = metadata["trajectory"]["info"]
            item["exit_status"] = info["exit_status"]
            if not item["edits"]:
                item["classification"] = "no_patch_format" if info["exit_status"] == "exit_format" else "no_patch_call_limit"
            elif item["validation_status"] == "verified_restored":
                item["classification"] = "functional_pass_scope_rejection"
            else:
                item["classification"] = "patch_functional_failure"
        else:
            tr = metadata["matchfix_result"]["results"]["test_repair"]
            parsed = tr.get("parsed_final_response", {})
            item["parser_explanation"] = parsed.get("explanation", "")
            if parsed.get("is_equivalent") == "error":
                text = tr["result"]
                recovered = json.loads(text)  # Offline syntax inspection only.
                assert "<final_response_format>" not in text
                assert recovered.get("correct_target_method_implementation")
                item["classification"] = "valid_json_missing_wrapper_tags"
            else:
                item["classification"] = "single_function_incomplete_repair"
        failure_rows.append(item)
    assert len(per_instance) == 50
    if method != "r_hier":
        assert all(total[k] == int(summary[method][k]) for k in TOKEN_KEYS)
    accepted = sum(r["strict_success"] == "True" for r in indexed[method].values())
    audit["methods"][method] = {
        "first_accepted": 50 - len(failures[method]), "final_accepted": accepted,
        "summary_usage": {k: int(summary[method][k]) for k in TOKEN_KEYS},
        "raw_usage": dict(total), "first_usage": dict(first_total),
        "raw_tokens_per_accepted_repair": total["total_tokens"] / accepted,
        "recorded_api_calls": call_count,
        "first_failure_counts": dict(collections.Counter(r["classification"] for r in failure_rows)),
        "first_failures": failure_rows, "per_instance": per_instance,
        "paired_comparison_with_hier": {
            "hier_first_only": sorted(failures[method] - failures["r_hier"]),
            "baseline_first_only": sorted(failures["r_hier"] - failures[method]),
        },
    }
audit["matchfix_component_usage"] = {k: dict(v) for k, v in component_usage.items()}
assert sum(v["total_tokens"] for v in component_usage.values()) == int(summary["r_matchfix"]["total_tokens"])
assert len(audit["token_omissions"]) == 14
assert audit["methods"]["r_hier"]["raw_usage"]["total_tokens"] == 589239
for path in [DATA / "instances.csv", DATA / "summary.csv", snapshot,
             ROOT / "ascend-torch4ms/autofix/examples/run_external_repair_pilot.py",
             ROOT / "ascend-torch4ms/experiments/paper_section_65_66/summarize_track_b_fixed50.py"]:
    audit["source_hashes"][str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
(OUT / "audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"methods": {m: {k: v for k, v in info.items() if k not in
      ("first_failures", "per_instance", "paired_comparison_with_hier")} for m, info in audit["methods"].items()},
      "token_omissions": len(audit["token_omissions"]),
      "shared_baseline_first_failures": audit["shared_baseline_first_failures"]}, indent=2))
