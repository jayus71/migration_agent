#!/usr/bin/env python3
"""Inventory interrupted conditions without executing or selecting new outcomes."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def inventory(report):
    counts = Counter()
    entries = []
    for benchmark, versions in report["studies"].items():
        for version, run in versions.items():
            records = {(r["task"], r["method"]): r for r in run["records"]}
            for method, stats in run["methods"].items():
                counts["planned"] += stats["planned"]
                counts["completed"] += stats["completed"]
                missing = dict(stats["noncompleted_terminal"])
                for task in stats["pending"]:
                    if task in missing:
                        raise ValueError("Condition appears in both pending and terminal lists")
                    row = records.get((task, method))
                    missing[task] = row["status"] if row else "not_started"
                if stats["completed"] + len(missing) != stats["planned"]:
                    raise ValueError("Incomplete condition accounting")
                for task, status in sorted(missing.items()):
                    row = records.get((task, method))
                    if status == "completed":
                        raise ValueError("Completed condition must not enter recovery inventory")
                    counts[status] += 1
                    entries.append({
                        "benchmark": benchmark, "version": version,
                        "task": task, "method": method, "original_status": status,
                        "original_run": run["run"],
                        "manifest_sha256": run["manifest_sha256"],
                        "recorded_calls": row.get("calls") if row else None,
                        "recorded_usage": row.get("usage") if row else None,
                        "recovery_executed": False,
                    })
    return {"counts": dict(counts), "conditions": entries,
            "policy": [
                "This inventory neither executes recovery nor replaces original results.",
                "Retain frozen per-version algorithms, inputs, budgets, and baseline settings.",
                "Do not rerun completed functional failures or choose the best of multiple runs.",
                "Keep original and recovery costs, unknown usage, and infrastructure failures.",
                "A fresh-budget restart is a separate infrastructure retry, not an uninterrupted budgeted run.",
                "Declare restart versus budget-preserving continuation before executing recovery.",
            ]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = args.report.read_bytes()
    result = inventory(json.loads(source))
    result["source_report"] = str(args.report)
    result["source_sha256"] = hashlib.sha256(source).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["counts"]))


if __name__ == "__main__":
    main()
