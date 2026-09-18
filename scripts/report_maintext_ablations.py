"""Read-only counts, raw-request accounting and component activation audit."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path


def treatment_violations(payload, variant):
    reasons = []
    messages = list(payload.get("messages", []))
    for message in list(messages):
        if message.get("role") == "user":
            try:
                content = json.loads(message.get("content", ""))
            except (TypeError, ValueError):
                content = None
            if isinstance(content, dict) and isinstance(content.get("verifier_record"), dict):
                messages.append(content["verifier_record"])
    if variant == "without_progress_prompt" and any(
            message.get("role") == "user" and isinstance(message.get("content"), str)
            and message["content"].startswith("Stage progress checkpoint:") for message in messages):
        reasons.append("omitted progress prompt reached the provider")
    if variant == "without_edit_format_feedback":
        for schema in payload.get("tools", []):
            function = schema.get("function", {})
            if function.get("name") == "edit" and "Argument format (all example values are placeholders):" in function.get("description", ""):
                reasons.append("omitted edit-format schema example reached the provider")
        for message in messages:
            if message.get("role") != "tool":
                continue
            try:
                content = json.loads(message.get("content", ""))
            except (TypeError, ValueError):
                continue
            if isinstance(content, dict) and "schema_feedback" in content:
                reasons.append("omitted edit-format error feedback reached the provider")
    return sorted(set(reasons))


def condition(path):
    result = json.loads(path.read_text())
    events = Counter()
    schema_feedback = 0
    evidence = path.parent / "evidence/agent"
    for file in evidence.glob("event_*.json"):
        value = json.loads(file.read_text())
        events[value["kind"]] += 1
        data = value.get("data", {})
        schema_feedback += bool(data.get("result", {}).get("schema_feedback"))
    calls = 0
    usage = Counter()
    actual_models = Counter()
    violations = []
    variant = path.parents[3].name
    for request in evidence.glob("call_*_request.json"):
        calls += 1
        payload = json.loads(request.read_text())
        violations.extend({"request": request.name, "reason": reason}
                          for reason in treatment_violations(payload, variant))
        response = request.with_name(request.name.replace("_request", "_response"))
        if not response.exists():
            usage["unknown_usage_calls"] += 1
            continue
        value = json.loads(response.read_text())
        actual_models[value.get("model", "missing")] += 1
        values = value.get("usage") or {}
        unknown = False
        for key in ("prompt_tokens", "completion_tokens"):
            amount = values.get(key)
            if type(amount) is int and amount >= 0:
                usage[key] += amount
            else:
                unknown = True
        usage["unknown_usage_calls"] += unknown
    terminal = result.get("status") in ("completed", "infrastructure_error", "unsupported")
    recorded = result.get("budget", {}).get("usage", {})
    mismatch = terminal and any(recorded.get(key) != usage[key] for key in ("prompt_tokens", "completion_tokens"))
    return {"task": result.get("task"), "status": result.get("status"), "accepted": result.get("accepted"),
            "controller_accepted": result.get("controller_accepted"),
            "initially_accepted_by_available_checks": result.get("initially_accepted_by_available_checks"),
            "attempts": len(result.get("attempts", [])), "initially_accepted": result.get("initially_accepted"),
            "accepted_at": next((row["attempt"] for row in result.get("attempts", []) if row.get("accepted")),
                                0 if result.get("initially_accepted") else None),
            "calls": calls, "usage": dict(usage), "events": dict(events), "schema_feedback": schema_feedback,
            "actual_models": dict(actual_models), "wall_time_sec": result.get("wall_time_sec"),
            "ledger_mismatch": mismatch, "request_treatment_violations": violations, "path": str(path)}


def group(run, planned):
    rows = [condition(path) for path in sorted((run / "conditions").glob("*/autonomous_layered/result.json"))]
    statuses = Counter(row["status"] for row in rows)
    complete = statuses["completed"] == planned and len(rows) == planned
    finished = [row for row in rows if row["status"] == "completed"]
    accepted = sum(bool(row["accepted"]) for row in finished)
    usage, events, models = Counter(), Counter(), Counter()
    for row in rows:
        usage.update(row["usage"])
        events.update(row["events"])
        models.update(row["actual_models"])
    tokens = usage["prompt_tokens"] + usage["completion_tokens"]
    seconds = sum(row["wall_time_sec"] or 0 for row in rows)
    return {"planned": planned, "statuses": dict(statuses), "complete": complete,
            "accepted": accepted, "accepted_rate": accepted / planned if complete else None,
            "initially_healthy": sum(bool(row["initially_accepted"]) for row in finished),
            "healthy_preserved": sum(bool(row["initially_accepted"]) and bool(row["accepted"]) for row in finished),
            "initially_failed": sum(not row["initially_accepted"] for row in finished),
            "actual_faults_repaired": sum(not row["initially_accepted"] and bool(row["accepted"]) for row in finished),
            "controller_accepted": sum(row["controller_accepted"] is True for row in finished),
            "controller_acceptance_failed_full_predicate": sum(row["controller_accepted"] is True and not row["accepted"] for row in finished),
            "initially_accepted_by_available_checks": sum(row["initially_accepted_by_available_checks"] is True for row in finished),
            "accepted_at_1": sum(row["accepted"] and row["accepted_at"] is not None and row["accepted_at"] <= 1 for row in finished),
            "accepted_at_2": sum(row["accepted"] and row["accepted_at"] is not None and row["accepted_at"] <= 2 for row in finished),
            "accepted_at_4": sum(row["accepted"] and row["accepted_at"] is not None and row["accepted_at"] <= 4 for row in finished),
            "calls": sum(row["calls"] for row in rows), "usage": dict(usage), "total_tokens": tokens,
            "tokens_per_accepted": tokens / accepted if complete and accepted and not usage["unknown_usage_calls"] else None,
            "seconds_per_accepted": seconds / accepted if complete and accepted else None,
            "events": dict(events), "actual_models": dict(models),
            "conditions_with_multiple_attempts": sum(row["attempts"] > 1 for row in finished),
            "conditions_with_history_reset": sum(row["events"].get("ablation_history_reset", 0) > 0 for row in rows),
            "conditions_with_progress_omission": sum(row["events"].get("ablation_progress_prompt_omitted", 0) > 0 for row in rows),
            "schema_feedback_count": sum(row["schema_feedback"] for row in rows),
            "request_treatment_violations": [{"task": row["task"], **violation}
                                             for row in rows for violation in row["request_treatment_violations"]],
            "ledger_mismatches": [row["task"] for row in rows if row["ledger_mismatch"]], "rows": rows}


def report(root):
    plan = json.loads((root / "plan.json").read_text())
    source = Path(plan["source_run"]) if "source_run" in plan else None
    variants = list(plan["variants"])
    manifest = json.loads((root / variants[0] / "manifest.json").read_text())
    planned = len(manifest["tasks"])
    groups = {variant: group(root / variant, planned) for variant in variants}
    if source:
        groups["reference_v4_evidence"] = group(source, planned)
        reference = groups["reference_v4_evidence"]
        baseline = {row["task"]: row for row in reference["rows"]}
        for variant in variants:
            current = groups[variant]
            if current["complete"] and reference["complete"]:
                pairs = [(row, baseline[row["task"]]) for row in current["rows"]]
                current["paired_with_reference"] = {
                    "both_accepted": sum(bool(a["accepted"]) and bool(b["accepted"]) for a, b in pairs),
                    "only_variant_accepted": sum(bool(a["accepted"]) and not b["accepted"] for a, b in pairs),
                    "only_reference_accepted": sum(not a["accepted"] and bool(b["accepted"]) for a, b in pairs),
                    "neither_accepted": sum(not a["accepted"] and not b["accepted"] for a, b in pairs),
                    "accepted_count_delta": current["accepted"] - reference["accepted"],
                    "total_tokens_delta": current["total_tokens"] - reference["total_tokens"],
                }
    return {"root": str(root), "condition_count": plan["condition_count"], "groups": groups}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = report(args.root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({name: {key: value for key, value in row.items() if key not in ("rows", "events")}
                      for name, row in result["groups"].items()}, indent=2))


if __name__ == "__main__":
    main()
