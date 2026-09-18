#!/usr/bin/env python3
"""Read selected trajectories for measured costs and actual memory events."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from compare_autonomous_recovery import indexed_groups


def profile(report):
    groups = []
    for key, group in indexed_groups(report).items():
        usage = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "unknown_usage_calls": 0}
        models, requested, stages = Counter(), Counter(), {}
        compressed = []
        events_total, cache_hits, unknown_cache = 0, 0, 0
        for record in group["conditions"]:
            folder = Path(record["path"]).parent / "evidence/agent"
            events = sorted(folder.glob("event_*_evidence_memory.json"))
            events_total += len(events)
            if events:
                compressed.append({"task": record["task"], "events": [str(p) for p in events]})
            for request in sorted(folder.glob("call_*_request.json")):
                response_path = request.with_name(request.name.replace("_request", "_response"))
                metadata_path = request.with_name(request.name.replace("_request", "_metadata"))
                request_data = json.loads(request.read_text())
                response = json.loads(response_path.read_text()) if response_path.exists() else {}
                metadata = json.loads(metadata_path.read_text()) if metadata_path.exists() else {}
                measured = response.get("usage") or {}
                unknown = any(type(measured.get(k)) is not int for k in ("prompt_tokens", "completion_tokens"))
                requested[request_data.get("model", "unrecorded")] += 1
                models[response.get("model", "unrecorded")] += 1
                stage = stages.setdefault(metadata.get("stage", "unrecorded"), dict.fromkeys(usage, 0))
                for total in (usage, stage):
                    total["calls"] += 1
                    total["unknown_usage_calls"] += unknown
                    for name in ("prompt_tokens", "completion_tokens"):
                        if type(measured.get(name)) is int:
                            total[name] += measured[name]
                hit = measured.get("prompt_cache_hit_tokens")
                if type(hit) is int:
                    cache_hits += hit
                else:
                    unknown_cache += 1
        for name, value in usage.items():
            if value != group["selected_run_usage"][name]:
                raise ValueError(f"Selected request usage differs for {key}: {name}")
        groups.append({"benchmark": key[0], "version": key[1], "method": key[2],
                       "conditions": group["planned"], "usage": usage,
                       "requested_models": dict(requested), "response_models": dict(models),
                       "compression_events": events_total, "conditions_with_compression": compressed,
                       "stages": stages, "measured_cache_hit_tokens": cache_hits,
                       "unknown_cache_usage_calls": unknown_cache})
    return {"groups": groups,
            "scope": "Exactly the selected complete episodes in the declared recovery report. No model calls or candidate execution.",
            "cost_note": "Cache hits remain included in prompt_tokens. No monetary price assumed. Interrupted episodes remain in the separate all-attempt cost report.",
            "memory_note": "Only actual evidence_memory events count as compression. Handoff-history differences are separate mechanisms."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    raw = args.report.read_bytes()
    value = profile(json.loads(raw))
    value["source_report_sha256"] = hashlib.sha256(raw).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"conditions": sum(g["conditions"] for g in value["groups"]),
                      "calls": sum(g["usage"]["calls"] for g in value["groups"]),
                      "compression_events": sum(g["compression_events"] for g in value["groups"])}))


if __name__ == "__main__":
    main()
