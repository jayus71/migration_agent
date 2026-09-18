#!/usr/bin/env python3
"""Compare complete declared recovery selections without rerunning models."""
import argparse
import hashlib
import json
from pathlib import Path


BASELINES = ("swe_native_isolated", "direct_shared_tools", "matchfix_full_orchestration")
LABELS = {
    "autonomous_layered": "Ours: evidence memory",
    "autonomous_layered_native": "Ours: native history",
    "autonomous_category_ablation": "Ours: category ablation",
    "swe_native_isolated": "SWE-agent 1.1.0",
    "direct_shared_tools": "Direct control",
    "matchfix_full_orchestration": "MatchFix + shared backend",
}


def indexed_groups(report):
    if not report.get("complete"):
        raise ValueError("A complete selected-run report is required")
    if not report.get("raw_verification_requested") or report.get("raw_ledger_problems") != 0:
        raise ValueError("A successful raw-ledger audit is required")
    result = {}
    for group in report["groups"]:
        key = (group["benchmark"], group["version"], group["method"])
        if key in result:
            raise ValueError("Duplicate group: " + repr(key))
        rows = group["conditions"]
        tasks = {r["task"]: r for r in rows}
        if len(tasks) != len(rows) or len(rows) != group["planned"]:
            raise ValueError("Duplicate or missing task: " + repr(key))
        if not group["complete"] or group["completed"] != group["planned"]:
            raise ValueError("Incomplete group: " + repr(key))
        if any(r["status"] != "completed" or type(r["accepted"]) is not bool for r in rows):
            raise ValueError("Invalid terminal outcome: " + repr(key))
        if sum(r["accepted"] for r in rows) != group["accepted"]:
            raise ValueError("Accepted count differs from selected records: " + repr(key))
        result[key] = group
    return result


def cost_ratio(left, right, field, per_accepted=False):
    a, b = left[field], right[field]
    if any(u["unknown_usage_calls"] or u["missing_ledgers"] or u["total_tokens"] is None for u in (a, b)):
        return None
    numerator, denominator = a["total_tokens"], b["total_tokens"]
    if per_accepted:
        if not left["accepted"] or not right["accepted"]:
            return None
        numerator /= left["accepted"]
        denominator /= right["accepted"]
    return numerator / denominator if denominator else None


def paired(left, right):
    a = {r["task"]: r["accepted"] for r in left["conditions"]}
    b = {r["task"]: r["accepted"] for r in right["conditions"]}
    if left["benchmark"] != right["benchmark"] or a.keys() != b.keys():
        raise ValueError("Paired comparison requires the same benchmark and exact task set")
    counts = {"left_only": [], "right_only": [], "both": [], "neither": []}
    for task in sorted(a):
        key = ("both" if b[task] else "left_only") if a[task] else ("right_only" if b[task] else "neither")
        counts[key].append(task)
    return {
        "benchmark": left["benchmark"],
        "left": {k: left[k] for k in ("version", "method", "accepted")},
        "right": {k: right[k] for k in ("version", "method", "accepted")},
        "planned": len(a),
        "acceptance_difference_pp": 100 * (left["accepted"] - right["accepted"]) / len(a),
        **counts,
        "left_over_right_cost": {
            field: {
                "total_tokens": cost_ratio(left, right, field),
                "tokens_per_accepted": cost_ratio(left, right, field, per_accepted=True),
            }
            for field in ("selected_run_usage", "all_attempts_usage")
        },
    }


def compare(report):
    groups = indexed_groups(report)
    baseline_pairs, ablations = [], []
    for (benchmark, version, method), left in groups.items():
        if method in BASELINES:
            continue
        for baseline in BASELINES:
            right = groups.get((benchmark, "formal_v3", baseline))
            if right is not None:
                baseline_pairs.append(paired(left, right))
    controls = (
        ("formal_v3", "autonomous_layered", "formal_v3", "autonomous_layered_native"),
        ("formal_v3", "autonomous_category_ablation", "formal_v3", "autonomous_layered"),
        ("progress_v4", "autonomous_layered", "formal_v3", "autonomous_layered"),
        ("progress_v4", "autonomous_layered_native", "formal_v3", "autonomous_layered_native"),
        ("progress_v4", "autonomous_layered", "progress_v4", "autonomous_layered_native"),
        ("repair_window_v5", "autonomous_layered_native", "progress_v4", "autonomous_layered_native"),
        ("productive_v6", "autonomous_layered", "progress_v4", "autonomous_layered"),
        ("productive_v7", "autonomous_layered", "productive_v6", "autonomous_layered"),
        ("productive_v7", "autonomous_layered", "progress_v4", "autonomous_layered"),
    )
    for benchmark in sorted({k[0] for k in groups}):
        for lv, lm, rv, rm in controls:
            if (benchmark, lv, lm) in groups and (benchmark, rv, rm) in groups:
                ablations.append(paired(groups[benchmark, lv, lm], groups[benchmark, rv, rm]))
    return {
        "planned": sum(g["planned"] for g in groups.values()),
        "groups": list(groups.values()), "baseline_pairs": baseline_pairs, "ablations": ablations,
        "interpretation": (
            "Every row uses the predeclared complete selected run. Versions remain separate. "
            "Ratios are left/right; below one means fewer tokens for the left method. "
            "Selected-run ratios exclude interrupted episodes; all-attempt ratios include them "
            "and are null when usage is unknown. Natural10 acceptance includes healthy retention. "
            "These are development-set comparisons; no significance or independent-test claim is made."
        ),
    }


def markdown(value):
    lines = ["# Completed Autonomous Repair Comparisons", "", value["interpretation"], "",
             "| Benchmark | Version | Method | Accepted | Attempts 1/2/4 | Failed inputs repaired | Healthy retained | Selected tokens | All attempts known tokens | Unknown calls |",
             "| --- | --- | --- | ---: | --- | --- | --- | ---: | ---: | ---: |"]
    for g in value["groups"]:
        checkpoints = "/".join(str(g["accepted_by_attempt_within_selected_run"][str(n)]) for n in (1, 2, 4))
        selected = g["selected_run_usage"]["total_tokens"]
        lines.append(f"| {g['benchmark']} | {g['version']} | {LABELS.get(g['method'], g['method'])} | "
                     f"{g['accepted']}/{g['planned']} | {checkpoints} | "
                     f"{g['repaired_initially_failed']}/{g['initially_failed']} | "
                     f"{g['retained_healthy']}/{g['initially_healthy']} | "
                     f"{selected if selected is not None else 'n/a'} | "
                     f"{g['all_attempts_usage']['known_total_tokens']} | {g['all_attempts_usage']['unknown_usage_calls']} |")
    lines += ["", "## Same-Task Comparisons", "",
              "Each task appears exactly once in each comparison. Detailed task lists and cost ratios are in the JSON.", "",
              "| Benchmark | Left | Right | Left only | Right only | Both | Neither | Difference (pp) |",
              "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |"]
    for row in value["baseline_pairs"] + value["ablations"]:
        names = [f"{row[s]['version']}: {LABELS.get(row[s]['method'], row[s]['method'])}" for s in ("left", "right")]
        counts = " | ".join(str(len(row[k])) for k in ("left_only", "right_only", "both", "neither"))
        lines.append(f"| {row['benchmark']} | {names[0]} | {names[1]} | {counts} | {row['acceptance_difference_pp']:+.1f} |")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    raw = args.report.read_bytes()
    value = compare(json.loads(raw))
    value["source_report"] = str(args.report.resolve())
    value["source_report_sha256"] = hashlib.sha256(raw).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.with_suffix(".json").write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    args.output.with_suffix(".md").write_text(markdown(value), encoding="utf-8")
    print(json.dumps({"planned": value["planned"], "baseline_pairs": len(value["baseline_pairs"]), "ablations": len(value["ablations"])}))


if __name__ == "__main__":
    main()
