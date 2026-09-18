#!/usr/bin/env python3
"""Profile measured model costs and actual compression events, without token estimates."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def profile(run):
    groups = {}
    for result_path in sorted((run / "conditions").glob("*/*/result.json")):
        result = read(result_path)
        if result.get("status") != "completed":
            continue
        condition = result_path.parent
        method = condition.name
        group = groups.setdefault(method, {"completed_conditions": 0, "initially_healthy": 0,
            "initially_failed": 0, "calls": 0, "missing_response_usage": 0,
            "compression_events": 0, "conditions_with_compression": [], "phases": {},
            "initial_status_costs": {}, "call_output_status": Counter()})
        group["completed_conditions"] += 1
        status = "initially_healthy" if result.get("initially_accepted") else "initially_failed"
        group[status] += 1
        events = list((condition / "evidence/agent").glob("event_*_evidence_memory.json"))
        group["compression_events"] += len(events)
        if events:
            group["conditions_with_compression"].append(condition.parent.name)
        for request in sorted((condition / "evidence/agent").glob("call_*_request.json")):
            prefix = request.name.removesuffix("_request.json")
            response = request.with_name(prefix + "_response.json")
            metadata = request.with_name(prefix + "_metadata.json")
            meta = read(metadata) if metadata.exists() else {}
            stage = meta.get("stage", "unrecorded_stage")
            reply = read(response) if response.exists() else {}
            usage = reply.get("usage") or {}
            output_state = request.with_name(prefix + "_completion_status.json")
            group["call_output_status"][read(output_state).get("status", "unknown") if output_state.exists() else "unknown"] += 1
            group["calls"] += 1
            missing = any(type(usage.get(k)) is not int for k in ("prompt_tokens", "completion_tokens"))
            group["missing_response_usage"] += missing
            for mapping, key in ((group["phases"], stage), (group["initial_status_costs"], status)):
                row = mapping.setdefault(key, {"calls": 0, "missing_response_usage": 0,
                    "measured_prompt_tokens": 0, "measured_completion_tokens": 0,
                    "measured_cache_hit_tokens": 0, "cache_hit_usage_unknown_calls": 0})
                row["calls"] += 1
                row["missing_response_usage"] += missing
                for field in ("prompt_tokens", "completion_tokens"):
                    value = usage.get(field)
                    if type(value) is int:
                        row["measured_" + field] += value
                hit = usage.get("prompt_cache_hit_tokens")
                if type(hit) is int:
                    row["measured_cache_hit_tokens"] += hit
                else:
                    row["cache_hit_usage_unknown_calls"] += 1
    return {"run": str(run), "complete": (run / "complete.json").exists(), "methods": groups}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    reports = [profile(args.root / "experiments" / group / version)
               for group in ("autonomous_fixed50_20260917", "autonomous_verifier_20260917")
               for version in ("formal_v3", "progress_v4", "repair_window_v5", "productive_v6", "productive_v7")]
    output = args.output.resolve()
    if any(Path(r["run"]).resolve() in output.parents for r in reports):
        raise ValueError("Output must remain outside frozen runs")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"generated_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Completed conditions only. Known token fields are measured sums; missing usage remains counted separately.",
        "cache_note": "Cache-hit tokens remain part of prompt_tokens. No monetary rate assumed.",
        "compression_note": "Count actual evidence_memory events; do not attribute savings to an inactive mechanism.",
        "runs": reports}, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"runs": len(reports), "completed": sum(s["completed_conditions"] for r in reports for s in r["methods"].values()),
                      "actual_compression_events": sum(s["compression_events"] for r in reports for s in r["methods"].values())}))


if __name__ == "__main__":
    main()
