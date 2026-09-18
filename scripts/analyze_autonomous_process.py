#!/usr/bin/env python3
"""Read public agent events; compare process metrics on matched completed tasks.

Example:
  python3 scripts/analyze_autonomous_process.py \
    --run fixed50 formal_v3 /path/to/formal_v3 \
    --run fixed50 progress_v4 /path/to/progress_v4 --output process.json

Only result status, protocol metadata and selected public event logs are read.
No private cases, acceptance outcomes, source workspaces or model API are used.
The output is an evaluation artifact and must not enter an agent workspace.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


METHODS = ("autonomous_layered", "autonomous_layered_native", "autonomous_category_ablation")
EVENT_KINDS = {"stage_start", "stage_end", "api_start", "tool", "stage_progress_checkpoint"}
INSPECTION = {"read", "search", "list"}
EDIT_STRUCTURE_ERRORS = {
    "Unknown or missing tool arguments": "top_level_keys",
    "Tool arguments must be an object": "argument_object_type",
    "Every edit requires only path, old and new": "entry_keys_or_type",
    "edits must contain between 1 and 30 replacements": "edit_array_type_or_length",
    "old and new must be strings": "replacement_text_type",
}
METRICS = (
    "llm_calls_started", "read_requests", "search_requests", "list_requests",
    "run_test_requests", "run_test_observations", "edit_requests",
    "successful_production_edit_operations", "successful_scratch_edit_operations",
    "changed_production_file_records", "changed_scratch_file_records",
    "successful_edits_without_byte_change", "unverifiable_edit_file_records",
    "tool_errors", "edit_structure_errors", "repeated_identical_reads",
    "repeated_identical_reads_without_file_change", "peak_inspection_only_rounds",
    "investigation_only_stages", "unvalidated_repair_stages",
    "progress_checkpoints", "format_feedbacks",
)
DEFINITIONS = {
    "llm_calls_started": "Distinct api_start call numbers, including pending or subsequently failed calls; no usage estimate.",
    "tool_counts": "Recorded tool events. Tests returning execution failures remain test observations; controller-wrapped errors with ok=false and error_type are not observations.",
    "edits": "An operation needs result.ok=true and at least one file with a valid after_sha256 differing from a valid before_sha256 (or before=null for creation). Production means candidate.py or torch4ms/; scratch means scratch_tests/. A mixed operation counts in both. No-op, rejected and unverifiable edits do not count as byte changes.",
    "repeated_reads": "Successful read events with identical canonical JSON arguments and complete result. One count per recurrence. The additional no-file-change count resets after any verified byte-changing edit, including scratch files.",
    "inspection_peak": "Consecutive closed model-call rounds in the same stage with one or more tool events, all read/search/list. A final answer, non-inspection tool or stage boundary breaks the streak. A live last call is excluded because its tool batch may still be incomplete.",
    "edit_structure_errors": EDIT_STRUCTURE_ERRORS | {"JSONDecodeError": "invalid_json_arguments"},
    "follow_through": "For each progress prompt or schema_feedback tool event, record next call, remaining current stage, and next stage separately. Only greater call numbers can respond to feedback; later tools in the same preselected batch are excluded. Actual tests and byte-changing edits are counted, without inferring diagnosis or causality.",
    "open_windows": "Counts describe the observed prefix. A true action remains observed; absent actions are null while a window is open/pending, false after a closed/not-reached terminal window.",
    "completion": "completed requires result.status=completed, a stable result file, at least one stage, all started stages closed and no parse/sequence problems. Budget-exhausted stages remain completed observations when the condition itself completes. Other terminal statuses and running/missing conditions stay separate.",
    "pairing": "Per suite and method, intersect eligible completed task IDs across the two requested versions. Include failures as well as successes. Unmatched tasks are listed; no differences are computed between unmatched completion subsets.",
    "scope": "Discover condition directories for the three ours methods only. Uncreated conditions are not inferred from private manifests. Acceptance and final diagnoses are never read as scoring evidence.",
}


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def valid_hash(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{64}", value) is not None


def analyze_condition(condition: Path, *, suite: str, version: str) -> dict:
    condition = condition.resolve()
    sources, issues, stages, calls, actions, triggers = [], [], [], {}, [], []
    metrics = Counter({key: 0 for key in METRICS})
    errors, structural_errors, other_tools = Counter(), Counter(), Counter()
    seen_reads, epoch_reads, duplicate_reads, changed_edits = {}, {}, [], []

    def read(path, purpose):
        try:
            raw = path.read_bytes()
            sources.append({"path": str(path.relative_to(condition)), "sha256": digest(raw), "purpose": purpose})
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise ValueError("Expected a JSON object")
            return value, digest(raw)
        except (OSError, ValueError) as exc:
            issues.append({"path": str(path.relative_to(condition)), "error_type": type(exc).__name__})
            return {}, None

    result_path = condition / "result.json"
    before, before_hash = read(result_path, "status_before") if result_path.exists() else ({}, None)
    folder = condition / "evidence" / "agent"
    protocol, _ = read(folder / "protocol.json", "protocol") if (folder / "protocol.json").exists() else ({}, None)
    selected = []
    for path in sorted(folder.glob("event_*.json")):
        if not any(path.name.endswith("_" + kind + ".json") for kind in EVENT_KINDS):
            continue
        event, _ = read(path, "public_event")
        if event:
            selected.append((str(path.relative_to(condition)), event))
    current = None
    for source, event in selected:
        kind, data = event.get("kind"), event.get("data")
        if not isinstance(data, dict):
            issues.append({"path": source, "error_type": "InvalidEventData"})
            continue
        if kind == "stage_start":
            if current is not None:
                issues.append({"path": source, "error_type": "UnclosedPreviousStage"})
            current = len(stages)
            stages.append({"index": current, "stage": data.get("stage"), "attempt": data.get("attempt"),
                           "start_source": source, "end_source": None, "status": "running", "calls": []})
        elif kind == "stage_end":
            if current is None:
                issues.append({"path": source, "error_type": "StageEndWithoutStart"})
                continue
            stages[current].update(status=data.get("status"), end_source=source, reported_calls=data.get("calls"))
            if data.get("status") in {"investigation_only", "unvalidated_repair"}:
                metrics[data["status"] + "_stages"] += 1
            current = None
        elif kind == "api_start":
            number = data.get("call")
            if type(number) is not int or number < 1 or number in calls:
                issues.append({"path": source, "error_type": "InvalidOrDuplicateCallNumber"})
                continue
            calls[number] = {"stage_index": current, "tool_names": [], "source": source}
            if current is not None:
                stages[current]["calls"].append(number)
            else:
                issues.append({"path": source, "error_type": "CallWithoutStage"})
        elif kind == "stage_progress_checkpoint":
            metrics["progress_checkpoints"] += 1
            triggers.append({"kind": "progress_checkpoint", "call": data.get("call"), "stage_index": current, "source": source})
        elif kind == "tool":
            number, name = data.get("call"), data.get("name")
            if not isinstance(name, str):
                name = "invalid_name"
            call = calls.get(number)
            if call is None:
                issues.append({"path": source, "error_type": "ToolWithoutRecordedCall"})
                continue
            call["tool_names"].append(name)
            metric = {"read": "read_requests", "search": "search_requests", "list": "list_requests",
                      "run_test": "run_test_requests", "edit": "edit_requests"}.get(name)
            if metric:
                metrics[metric] += 1
            else:
                other_tools[name] += 1
            result = data.get("result")
            has_result_object = isinstance(result, dict)
            result = result if has_result_object else {}
            failed = result.get("ok") is False
            wrapped_error = failed and "error_type" in result
            if failed:
                metrics["tool_errors"] += 1
                errors[str(result.get("error_type", "unspecified"))] += 1
            if name == "edit" and failed:
                error_text = result.get("error")
                reason = EDIT_STRUCTURE_ERRORS.get(error_text) if isinstance(error_text, str) else None
                if result.get("error_type") == "JSONDecodeError":
                    reason = "invalid_json_arguments"
                if reason:
                    metrics["edit_structure_errors"] += 1
                    structural_errors[reason] += 1
            action = {"call": number, "stage_index": call["stage_index"], "source": source,
                      "test_observation": name == "run_test" and has_result_object and not wrapped_error,
                      "production_edit": False, "scratch_edit": False}
            if action["test_observation"]:
                metrics["run_test_observations"] += 1
            changed = []
            if name == "edit" and result.get("ok") is True:
                files = result.get("files", [])
                if not isinstance(files, list) or not files:
                    metrics["unverifiable_edit_file_records"] += 1
                    files = []
                for item in files:
                    if not isinstance(item, dict):
                        metrics["unverifiable_edit_file_records"] += 1
                        continue
                    before_sha, after_sha, path = item.get("before_sha256"), item.get("after_sha256"), item.get("path")
                    if ("before_sha256" not in item or not valid_hash(after_sha)
                            or (before_sha is not None and not valid_hash(before_sha)) or not isinstance(path, str)):
                        metrics["unverifiable_edit_file_records"] += 1
                        continue
                    if before_sha == after_sha:
                        continue
                    changed.append({"path": path, "before_sha256": before_sha, "after_sha256": after_sha})
                    if path == "candidate.py" or path.startswith("torch4ms/"):
                        action["production_edit"] = True
                        metrics["changed_production_file_records"] += 1
                    elif path.startswith("scratch_tests/"):
                        action["scratch_edit"] = True
                        metrics["changed_scratch_file_records"] += 1
                if changed:
                    epoch_reads.clear()
                    changed_edits.append({"source": source, "call": number, "files": changed})
                elif files and all(isinstance(f, dict) and valid_hash(f.get("before_sha256"))
                                   and f.get("before_sha256") == f.get("after_sha256") for f in files):
                    metrics["successful_edits_without_byte_change"] += 1
                metrics["successful_production_edit_operations"] += action["production_edit"]
                metrics["successful_scratch_edit_operations"] += action["scratch_edit"]
            if name == "read" and not failed and "lines" in result:
                fingerprint = digest(canonical({"arguments": data.get("arguments"), "result": result}).encode())
                if fingerprint in seen_reads:
                    metrics["repeated_identical_reads"] += 1
                    duplicate_reads.append({"source": source, "previous_source": seen_reads[fingerprint],
                                            "fingerprint": fingerprint, "without_file_change": fingerprint in epoch_reads})
                if fingerprint in epoch_reads:
                    metrics["repeated_identical_reads_without_file_change"] += 1
                seen_reads[fingerprint] = epoch_reads[fingerprint] = source
            if "schema_feedback" in result:
                metrics["format_feedbacks"] += 1
                triggers.append({"kind": "edit_format_feedback", "call": number,
                                 "stage_index": call["stage_index"], "source": source})
            actions.append(action)

    after, after_hash = read(result_path, "status_after") if result_path.exists() else ({}, None)
    stable_result = before_hash == after_hash
    if not stable_result:
        issues.append({"path": "result.json", "error_type": "ResultChangedDuringRead"})
    status = after.get("status") or before.get("status") or ("running_without_result" if selected else "not_started")
    terminal = status not in {"running", "running_without_result", "not_started"}
    metrics["llm_calls_started"] = len(calls)
    last_call = max(calls, default=0)

    def call_closed(number):
        idx = calls[number]["stage_index"]
        return number < last_call or (idx is not None and stages[idx]["end_source"] is not None)

    for stage in stages:
        streak, peak = 0, 0
        for number in stage["calls"]:
            names = calls[number]["tool_names"]
            streak = streak + 1 if call_closed(number) and names and all(n in INSPECTION for n in names) else 0
            peak = max(peak, streak)
        stage["peak_inspection_only_rounds"] = peak
        metrics["peak_inspection_only_rounds"] = max(metrics["peak_inspection_only_rounds"], peak)
        if stage.get("reported_calls") is not None and stage["reported_calls"] != len(stage["calls"]):
            issues.append({"path": stage["end_source"], "error_type": "StageCallCountMismatch"})

    def window(selected_actions, window_status, *, stage_index=None, call_number=None):
        counts = {key: sum(bool(a[key]) for a in selected_actions)
                  for key in ("test_observation", "production_edit", "scratch_edit")}
        closed = window_status in {"closed", "not_reached_before_completion"}
        observed = {key: True if value else (False if closed else None) for key, value in counts.items()}
        return {"status": window_status, "stage_index": stage_index, "call": call_number,
                "counts": counts, "observed": observed,
                "test_or_edit": True if any(counts.values()) else (False if closed else None),
                "action_sources": [a["source"] for a in selected_actions if any(a[k] for k in counts)]}

    for trigger in triggers:
        number, idx = trigger["call"], trigger["stage_index"]
        if type(number) is not int or idx is None:
            issues.append({"path": trigger["source"], "error_type": "TriggerWithoutCallOrStage"})
            trigger["follow_through"] = None
            continue
        next_number = number + 1
        next_status = ("closed" if call_closed(next_number) else "open") if next_number in calls else (
            "not_reached_before_completion" if terminal else "pending")
        remainder = [a for a in actions if a["call"] > number and a["stage_index"] == idx]
        next_stage = idx + 1 if idx + 1 < len(stages) else None
        next_stage_status = ("closed" if stages[next_stage]["end_source"] else "open") if next_stage is not None else (
            "not_reached_before_completion" if terminal else "pending")
        trigger["follow_through"] = {
            "next_call": window([a for a in actions if a["call"] == next_number], next_status, call_number=next_number),
            "remaining_current_stage": window(remainder, "closed" if stages[idx]["end_source"] else "open", stage_index=idx),
            "next_stage": window([a for a in actions if next_stage is not None and a["stage_index"] == next_stage],
                                 next_stage_status, stage_index=next_stage),
        }
    eligible = status == "completed" and stable_result and bool(stages) and all(s["end_source"] for s in stages) and not issues
    return {"suite": suite, "version": version, "task": condition.parent.name, "method": condition.name,
            "condition_root": str(condition), "result_status": status, "eligible_completed": eligible,
            "observation_state": "completed" if eligible else ("terminal_incomplete_log" if status == "completed" else
                ("terminal_other" if terminal else "running_or_pending")),
            "policy": {k: protocol.get("config", {}).get(k) for k in ("memory_policy", "workflow_policy", "diagnosis_policy")},
            "protocol_sha256": protocol.get("protocol_sha256"), "metrics": dict(metrics),
            "tool_errors_by_type": dict(errors), "edit_structure_errors_by_type": dict(structural_errors),
            "other_tool_requests": dict(other_tools), "stages": stages, "feedback_follow_through": triggers,
            "changed_edits": changed_edits, "duplicate_read_evidence": duplicate_reads,
            "open_call_numbers": [n for n in calls if not call_closed(n)], "read_issues": issues,
            "source_digest": digest(canonical(sources).encode()), "sources": sources}


def aggregate(rows):
    sums = {key: sum(r["metrics"][key] for r in rows) for key in METRICS}
    errors, structures = Counter(), Counter()
    for row in rows:
        errors.update(row["tool_errors_by_type"])
        structures.update(row["edit_structure_errors_by_type"])
    follow = {}
    for kind in ("progress_checkpoint", "edit_format_feedback"):
        follow[kind] = {}
        triggers = [t for r in rows for t in r["feedback_follow_through"] if t["kind"] == kind and t["follow_through"]]
        for name in ("next_call", "remaining_current_stage", "next_stage"):
            windows = [t["follow_through"][name] for t in triggers]
            follow[kind][name] = {"events": len(windows), "observed_test_or_edit": sum(w["test_or_edit"] is True for w in windows),
                                 "closed_without_test_or_edit": sum(w["test_or_edit"] is False for w in windows),
                                 "still_pending_without_action": sum(w["test_or_edit"] is None for w in windows),
                                 "window_status_counts": dict(Counter(w["status"] for w in windows))}
    return {"conditions": len(rows), "tasks": sorted(r["task"] for r in rows), "metric_sums": sums,
            "metric_means": {k: v / len(rows) if rows else None for k, v in sums.items()},
            "tool_errors_by_type": dict(errors), "edit_structure_errors_by_type": dict(structures),
            "feedback_follow_through": follow}


def build_report(runs, *, tasks=None, versions=("formal_v3", "progress_v4")):
    rows, identities = [], set()
    for suite, version, root in runs:
        root = Path(root).resolve()
        if (suite, version) in identities:
            raise ValueError(f"Duplicate suite/version: {suite}/{version}")
        if not (root / "conditions").is_dir():
            raise ValueError(f"Missing conditions directory: {root}")
        identities.add((suite, version))
        for condition in sorted((root / "conditions").glob("*/*")):
            if condition.is_dir() and condition.name in METHODS and (not tasks or condition.parent.name in tasks):
                rows.append(analyze_condition(condition, suite=suite, version=version))
    summaries = []
    for suite, version, method in sorted({(r["suite"], r["version"], r["method"]) for r in rows}):
        group = [r for r in rows if (r["suite"], r["version"], r["method"]) == (suite, version, method)]
        summaries.append({"suite": suite, "version": version, "method": method,
                          "result_status_counts": dict(Counter(r["result_status"] for r in group)),
                          "completed": aggregate([r for r in group if r["eligible_completed"]]),
                          "running_or_other_incomplete": aggregate([r for r in group if not r["eligible_completed"]])})
    pairs = []
    left, right = versions
    for suite, method in sorted({(r["suite"], r["method"]) for r in rows}):
        lookup = {v: {r["task"]: r for r in rows if r["suite"] == suite and r["method"] == method and r["version"] == v}
                  for v in versions}
        completed = {v: {t for t, r in lookup[v].items() if r["eligible_completed"]} for v in versions}
        common = sorted(completed[left] & completed[right])
        paired = {v: aggregate([lookup[v][t] for t in common]) for v in versions}
        pairs.append({"suite": suite, "method": method, "left_version": left, "right_version": right,
                      "paired_tasks": common, "paired_conditions": len(common),
                      "completed_but_unmatched": {v: sorted(completed[v] - set(common)) for v in versions},
                      "incomplete_or_missing": {v: sorted((set(lookup[left]) | set(lookup[right])) - completed[v]) for v in versions},
                      "paired_aggregates": paired,
                      "mean_difference_right_minus_left": {k: (paired[right]["metric_means"][k] - paired[left]["metric_means"][k]) if common else None for k in METRICS},
                      "per_task_differences": [{"task": t, "metrics_right_minus_left": {k: lookup[right][t]["metrics"][k] - lookup[left][t]["metrics"][k] for k in METRICS}} for t in common]})
    return {"schema_version": "autonomous-process-analysis-v1", "generated_utc": datetime.now(timezone.utc).isoformat(),
            "definitions": DEFINITIONS, "selection": {"methods": list(METHODS), "tasks": sorted(tasks) if tasks else "all discovered",
            "paired_versions": list(versions)}, "runs": [{"suite": s, "version": v, "root": str(Path(p).resolve())} for s, v, p in runs],
            "conditions": rows, "summaries": summaries, "paired_comparisons": pairs}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", nargs=3, action="append", required=True, metavar=("SUITE", "VERSION", "ROOT"))
    parser.add_argument("--task", action="append", help="Limit validation to explicit anonymous task IDs; repeat as needed.")
    parser.add_argument("--paired-versions", nargs=2, default=("formal_v3", "progress_v4"))
    parser.add_argument("--output", required=True, help="Output JSON path, or - for stdout; input roots are protected.")
    args = parser.parse_args()
    if args.output != "-":
        output = Path(args.output).resolve()
        if any(output.is_relative_to(Path(root).resolve()) for _, _, root in args.run):
            parser.error("Output must be outside every input run directory")
    report = build_report(args.run, tasks=set(args.task or []), versions=tuple(args.paired_versions))
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output == "-":
        print(text, end="")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
