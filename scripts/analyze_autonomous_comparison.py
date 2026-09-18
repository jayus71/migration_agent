#!/usr/bin/env python3
"""Analyze frozen autonomous-repair runs without changing their evidence.

Incomplete grids produce explicitly provisional tables. Costs include every
recorded condition, and paired comparisons require the full planned task set.
This evaluation-side script must not be placed in agent-visible workspaces.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def audit_ledger(condition: Path, row: dict) -> dict:
    folder = condition / "evidence" / "agent"
    requests = sorted(folder.glob("call_*_request.json"))
    if not folder.exists():
        return {"available": False}
    observed = {"calls": len(requests), "prompt_tokens": 0, "completion_tokens": 0,
                "unknown_usage_calls": 0}
    models = set()
    for request in requests:
        response = request.with_name(request.name.replace("_request", "_response"))
        payload = read(response) if response.exists() else {}
        usage = payload.get("usage") or {}
        known = True
        for field in ("prompt_tokens", "completion_tokens"):
            value = usage.get(field)
            if type(value) is int and value >= 0:
                observed[field] += value
            else:
                known = False
        observed["unknown_usage_calls"] += not known
        if payload.get("model"):
            models.add(payload["model"])
    budget = row.get("budget", {})
    recorded = {"calls": budget.get("calls"), **budget.get("usage", {})}
    mismatches = {k: {"raw": value, "recorded": recorded.get(k)}
                  for k, value in observed.items() if recorded.get(k) != value}
    return {"available": True, "observed": observed, "actual_models": sorted(models),
            "mismatches": mismatches}


def analyze(run: Path, *, verify_raw: bool = False) -> dict:
    manifest = read(run / "manifest.json")
    tasks = [row["anonymous_id"] for row in manifest["tasks"]]
    methods = manifest["methods"]
    if len(set(tasks)) != len(tasks) or len(set(methods)) != len(methods):
        raise ValueError("Duplicate task or method in frozen manifest")
    rows = {}
    unexpected = []
    for path in sorted((run / "conditions").glob("task_*/*/result.json")):
        row = read(path)
        key = (row["task"], row["method"])
        if key[0] not in tasks or key[1] not in methods:
            unexpected.append(str(path.relative_to(run)))
            continue
        if key in rows:
            raise ValueError(f"Duplicate result: {key}")
        if path.parent.name != key[1] or path.parent.parent.name != key[0]:
            raise ValueError(f"Result identity differs from path: {path}")
        rows[key] = row
    stats = {}
    records = []
    ledger_audits = {}
    for method in methods:
        found = [rows[(task, method)] for task in tasks if (task, method) in rows]
        completed = [row for row in found if row["status"] == "completed"]
        full = len(completed) == len(tasks)
        accepted = sum(row.get("accepted") is True for row in completed)
        unknown_initial = [r["task"] for r in completed if type(r.get("initially_accepted")) is not bool]
        if unknown_initial:
            raise ValueError(f"Missing initial outcome for {method}: {unknown_initial}")
        failed = [r for r in completed if not r["initially_accepted"]]
        healthy = [r for r in completed if r["initially_accepted"]]
        totals = {k: 0 for k in ("calls", "prompt_tokens", "completion_tokens", "unknown_usage_calls")}
        missing_ledgers = []
        wall = 0.0
        for row in found:
            task = row["task"]
            budget = row.get("budget", {})
            usage = budget.get("usage", {})
            # Only terminal ledgers count here; in-flight usage is volatile.
            if row["status"] == "running":
                continue
            if verify_raw and row["status"] != "unsupported":
                ledger_audits[f"{task}/{method}"] = audit_ledger(run / "conditions" / task / method, row)
            if not budget and row["status"] != "unsupported":
                missing_ledgers.append(task)
            for key in totals:
                value = budget.get(key, 0) if key == "calls" else usage.get(key, 0)
                if type(value) is not int or value < 0:
                    raise ValueError(f"Invalid usage {method}/{task}/{key}")
                totals[key] += value
            wall += row.get("wall_time_sec", 0.0)
            attempts = row.get("attempts", [])
            first = next((a["attempt"] for a in attempts if a.get("accepted")), None)
            if row.get("initially_accepted") and row.get("accepted"):
                first = 0
            if row["status"] == "completed" and row.get("accepted") and first is None:
                raise ValueError(f"Accepted result lacks accepted attempt: {method}/{task}")
            records.append({"task": task, "method": method, "status": row["status"],
                "initially_accepted": row.get("initially_accepted"), "accepted": row.get("accepted"),
                "first_accepted_attempt": first, "attempts": len(attempts),
                "stage_statuses": [a.get("stage", {}).get("status") for a in attempts],
                "last_changed_files": attempts[-1].get("changed_files", []) if attempts else [],
                "calls": budget.get("calls"), "usage": usage,
                "wall_time_sec": row.get("wall_time_sec")})
        method_records = [r for r in records if r["method"] == method and r["status"] == "completed"]
        cumulative = {str(n): sum(r["accepted"] is True and r["first_accepted_attempt"] <= n
                                  for r in method_records) for n in (1, 2, 4)}
        total_tokens = totals["prompt_tokens"] + totals["completion_tokens"]
        stats[method] = {"planned": len(tasks), "completed": len(completed), "complete": full,
            "pending": [t for t in tasks if (t, method) not in rows or rows[t, method]["status"] == "running"],
            "noncompleted_terminal": {r["task"]: r["status"] for r in found
                                      if r["status"] not in ("completed", "running")},
            "accepted": accepted, "acceptance_rate": accepted / len(tasks) if full else None,
            "accepted_by_attempt": cumulative,
            "initially_failed": len(failed), "repaired_initially_failed": sum(r["accepted"] for r in failed),
            "initially_healthy": len(healthy), "retained_healthy": sum(r["accepted"] for r in healthy),
            **totals, "total_tokens": total_tokens, "missing_ledgers": missing_ledgers,
            "tokens_per_accepted": total_tokens / accepted if full and accepted and not totals["unknown_usage_calls"] and not missing_ledgers else None,
            "wall_time_sum_sec": wall}
    paired = {}
    primary = "autonomous_layered"
    if primary in methods:
        for other in methods:
            if other == primary:
                continue
            pair = {"complete": stats[primary]["complete"] and stats[other]["complete"],
                    "ours_only": [], "other_only": [], "both_accepted": [], "neither_accepted": [],
                    "initial_outcome_mismatches": []}
            for task in tasks:
                a, b = rows.get((task, primary)), rows.get((task, other))
                if not a or not b or a["status"] != "completed" or b["status"] != "completed":
                    continue
                if a["initially_accepted"] != b["initially_accepted"]:
                    pair["initial_outcome_mismatches"].append(task)
                key = ("both_accepted" if b["accepted"] else "ours_only") if a["accepted"] else ("other_only" if b["accepted"] else "neither_accepted")
                pair[key].append(task)
            paired[other] = pair
    return {"run": str(run), "benchmark": manifest.get("benchmark", "natural_translation"),
        "manifest_sha256": hashlib.sha256((run / "manifest.json").read_bytes()).hexdigest(),
        "complete": all(s["complete"] for s in stats.values()),
        "all_terminal": all(not s["pending"] for s in stats.values()), "methods": stats,
        "paired_with_autonomous_layered": paired, "records": records, "unexpected_results": unexpected,
        "raw_ledger_audits": ledger_audits,
        "counting": "Fixed manifest task set; terminal costs include failures; incomplete or unknown-usage cost ratios are null. Healthy inputs are separate from repaired failures. Paired lists from incomplete grids are provisional."}


def markdown(report: dict) -> str:
    state = "完整结果" if report["complete"] else "已结束，含缺失结果" if report.get("all_terminal") else "进行中的临时统计"
    lines = [f"# 自主修复比较：{state}", "", f"运行：`{report['run']}`", "",
        "统计保留 manifest 的全部实例。健康输入与实际修复分别计数；费用包含失败条件，未知 usage 不按零补齐。", "",
        "| 方法 | 完成/计划 | 接受 | 1/2/4 次内接受 | 初始失败修复 | 健康保留 | 已结束条件 token | 每次接受 token |",
        "| --- | ---: | ---: | --- | --- | --- | ---: | ---: |"]
    for method, s in report["methods"].items():
        checkpoints = "/".join(str(s["accepted_by_attempt"][str(n)]) for n in (1, 2, 4))
        ratio = f"{s['tokens_per_accepted']:,.1f}" if s["tokens_per_accepted"] is not None else "n/a"
        lines.append(f"| {method} | {s['completed']}/{s['planned']} | {s['accepted']} | {checkpoints} | {s['repaired_initially_failed']}/{s['initially_failed']} | {s['retained_healthy']}/{s['initially_healthy']} | {s['total_tokens']:,} | {ratio} |")
    lines += ["", "逐例胜负、未完成状态、基础设施错误、未知用量和 manifest 哈希见同名 JSON。", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-raw", action="store_true", help="Reconcile terminal usage against every raw response")
    args = parser.parse_args()
    report = analyze(args.run.resolve(), verify_raw=args.verify_raw)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.with_suffix(".json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output.with_suffix(".md").write_text(markdown(report), encoding="utf-8")
    print(json.dumps({"complete": report["complete"], "methods": {m: {k: s[k] for k in ("completed", "planned", "accepted", "repaired_initially_failed")} for m, s in report["methods"].items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
