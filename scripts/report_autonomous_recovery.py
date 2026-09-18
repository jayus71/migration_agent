#!/usr/bin/env python3
"""Report predeclared infrastructure restarts and retain original campaign costs."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from analyze_autonomous_comparison import audit_ledger


VERSIONS = ("formal_v3", "progress_v4", "repair_window_v5", "productive_v6", "productive_v7")
FIELDS = ("prompt_tokens", "completion_tokens", "unknown_usage_calls")


def read(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def usage(rows):
    totals = {key: sum(r.get("budget", {}).get("usage", {}).get(key, 0) for r in rows) for key in FIELDS}
    totals["calls"] = sum(r.get("budget", {}).get("calls", 0) for r in rows)
    totals["known_total_tokens"] = totals["prompt_tokens"] + totals["completion_tokens"]
    totals["missing_ledgers"] = sum(not r.get("budget") for r in rows)
    totals["total_tokens"] = totals["known_total_tokens"] if not totals["unknown_usage_calls"] and not totals["missing_ledgers"] else None
    return totals


def report(implementation, recovery, verify=False):
    plan = read(recovery / "recovery_plan.json")
    lookup = {(i["benchmark"], i["version"], i["task"], i["method"]): i for i in plan["conditions"]}
    groups, ledger_checks = [], []
    for benchmark, folder in (("Fixed50", "autonomous_fixed50_20260917"), ("Natural10", "autonomous_verifier_20260917")):
        for version in VERSIONS:
            original = implementation / "experiments" / folder / version
            config = read(original / "manifest.json")
            for method in config["methods"]:
                selected, original_replaced, entries = [], [], []
                for task in config["tasks"]:
                    tid = task["anonymous_id"]
                    item = lookup.get((benchmark, version, tid, method))
                    old_path = original / "conditions" / tid / method / "result.json"
                    old = read(old_path)
                    path = Path(item["recovery_run"]) / "conditions" / tid / method / "result.json" if item else old_path
                    row = read(path)
                    if item and item["original_result_sha256"]:
                        if hashlib.sha256(old_path.read_bytes()).hexdigest() != item["original_result_sha256"]:
                            raise ValueError("Original interrupted result changed")
                        original_replaced.append(old)
                    if row and row["status"] != "running":
                        selected.append(row)
                    entries.append({"task": tid, "status": row["status"] if row else "pending",
                        "accepted": row.get("accepted") if row else None,
                        "source": "declared_recovery" if item else "original",
                        "path": str(path), "original_result": str(old_path) if item else None})
                    if verify:
                        for candidate, candidate_path in ((row, path), (old, old_path)) if item else ((row, path),):
                            if candidate and candidate["status"] != "running":
                                check = audit_ledger(candidate_path.parent, candidate)
                                ledger_checks.append({"path": str(candidate_path), **check})
                complete = [r for r in selected if r["status"] == "completed"]
                accepted = sum(bool(r["accepted"]) for r in complete)
                full = len(complete) == len(config["tasks"])
                attempt_counts = {}
                for n in (1, 2, 4):
                    attempt_counts[str(n)] = sum(bool(r["accepted"]) and (r.get("initially_accepted") or any(
                        a.get("accepted") and a["attempt"] <= n for a in r.get("attempts", []))) for r in complete)
                selected_cost, all_cost = usage(selected), usage(selected + original_replaced)
                groups.append({"benchmark": benchmark, "version": version, "method": method,
                    "planned": len(config["tasks"]), "completed": len(complete), "complete": full,
                    "accepted": accepted, "acceptance_rate": accepted / len(config["tasks"]) if full else None,
                    "accepted_by_attempt_within_selected_run": attempt_counts,
                    "repaired_initially_failed": sum(bool(r["accepted"]) and not r["initially_accepted"] for r in complete),
                    "initially_failed": sum(not r["initially_accepted"] for r in complete),
                    "retained_healthy": sum(bool(r["accepted"]) and r["initially_accepted"] for r in complete),
                    "initially_healthy": sum(r["initially_accepted"] for r in complete),
                    "selected_run_usage": selected_cost, "original_interrupted_usage": usage(original_replaced),
                    "all_attempts_usage": all_cost,
                    "all_attempts_tokens_per_accepted": all_cost["total_tokens"] / accepted if full and accepted and all_cost["total_tokens"] is not None else None,
                    "selected_statuses": dict(Counter(e["status"] for e in entries)), "conditions": entries})
    return {"generated_at": datetime.now(timezone.utc).isoformat(), "recovery_plan_sha256": hashlib.sha256((recovery / "recovery_plan.json").read_bytes()).hexdigest(),
        "protocol": plan["policy"], "complete": all(g["complete"] for g in groups), "groups": groups,
        "raw_verification_requested": verify, "ledger_audits": ledger_checks,
        "raw_ledger_problems": sum(not a["available"] or bool(a.get("mismatches")) for a in ledger_checks) if verify else None}


def markdown(value):
    lines = ["# 基础设施重试后的修复结果", "",
        "90 个中断条件各从冻结初始输入独立重跑一次，19 个未启动条件首次运行；其余正常完成结果沿用。各版本方法、输入、验收与单次预算相同。原中断轨迹及用量全部保留；重试前后总调用可能超过单次预算。", "",
        "| 任务组 | 版本 | 方法 | 正常完成/计划 | 接受 | 选定运行已知token | 全部尝试已知token | 未知用量调用 |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |"]
    for g in value["groups"]:
        lines.append(f"| {g['benchmark']} | {g['version']} | {g['method']} | {g['completed']}/{g['planned']} | {g['accepted']} | {g['selected_run_usage']['known_total_tokens']:,} | {g['all_attempts_usage']['known_total_tokens']:,} | {g['all_attempts_usage']['unknown_usage_calls']} |")
    lines += ["", "已知 token 是有 usage 回执的合计。存在未知用量时，完整总成本及每次接受成本为 n/a。进行中调用暂不汇总。1/2/4 次累计接受对应选定运行内的外部提交，不包含此前基础设施中断尝试。", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--implementation", type=Path, required=True)
    parser.add_argument("--recovery", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-raw", action="store_true")
    args = parser.parse_args()
    value = report(args.implementation.resolve(), args.recovery.resolve(), args.verify_raw)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.with_suffix(".json").write_text(json.dumps(value, indent=2) + "\n")
    args.output.with_suffix(".md").write_text(markdown(value))
    print(json.dumps({"complete": value["complete"], "completed": sum(g["completed"] for g in value["groups"]),
        "planned": sum(g["planned"] for g in value["groups"]), "raw_ledger_problems": value["raw_ledger_problems"]}))


if __name__ == "__main__":
    main()
