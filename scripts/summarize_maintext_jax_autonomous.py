"""Summarize completed JAX episodes, retaining missing and failed conditions."""
import argparse
import json
from pathlib import Path


def summarize(run):
    manifest = json.loads((run / "manifest.json").read_text())
    summaries = []
    for method in manifest["methods"]:
        rows = []
        for task in manifest["tasks"]:
            path = run / "conditions" / task["anonymous_id"] / method / "result.json"
            if path.exists():
                rows.append(json.loads(path.read_text()))
        terminal = [row for row in rows if row.get("status") != "running"]
        complete = len(rows) == len(manifest["tasks"]) and all(row.get("status") == "completed" for row in rows)
        accepted = sum(row.get("status") == "completed" and row.get("accepted") is True for row in rows)
        tokens = sum(row.get("budget", {}).get("usage", {}).get("total_tokens", 0) for row in terminal)
        unknown = sum(row.get("budget", {}).get("usage", {}).get("unknown_usage_calls", 0) for row in terminal)
        elapsed = sum(row.get("wall_time_sec", 0) for row in terminal)
        summaries.append({"method": method, "planned": len(manifest["tasks"]), "recorded": len(rows),
            "completed": sum(row.get("status") == "completed" for row in rows), "complete": complete, "accepted": accepted,
            "first_attempt_accepted": sum(row.get("accepted") is True and len(row.get("attempts", [])) == 1 for row in rows),
            "known_total_tokens": tokens, "unknown_usage_calls": unknown,
            "tokens_per_accepted": tokens / accepted if complete and accepted and not unknown else None,
            "wall_time_sec": elapsed, "seconds_per_accepted": elapsed / accepted if complete and accepted else None,
            "calls": sum(row.get("budget", {}).get("calls", 0) for row in terminal)})
    converters = json.loads((run / "converter_results.json").read_text()) if (run / "converter_results.json").exists() else []
    for method in ("ivy", "torch2jax"):
        rows = [row for row in converters if row["method"] == method]
        summaries.append({"method": method, "planned": 6, "recorded": len(rows),
            "completed": sum(row["status"] == "completed" for row in rows),
            "accepted": sum(row["accepted"] is True for row in rows),
            "unavailable": sum(row["accepted"] is None for row in rows),
            "known_total_tokens": 0, "calls": 0,
            "candidate_wall_time_sec": sum(row["wall_time_sec"] for row in rows),
            "clean_gate_wall_time_sec": sum(json.loads(path.read_text())["wall_time_sec"] for path in
                (run / "conditions").glob(f"*/{method}_clean_gate/evidence/measurement_*/process.json"))})
    return {"run": str(run), "summaries": summaries}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    value = summarize(args.run.resolve())
    text = json.dumps(value, indent=2, allow_nan=False)
    if args.output:
        if args.output.exists():
            raise FileExistsError("Choose a new summary path")
        args.output.write_text(text + "\n")
    print(text)
