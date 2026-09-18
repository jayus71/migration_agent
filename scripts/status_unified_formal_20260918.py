"""Read-only compact experiment status, excluding prompts and credentials."""
import argparse
from collections import Counter
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def summarize(root):
    control = root.parent / "formal_control"
    status = read(control / "status.json")
    status["scheduler_alive"] = Path(f"/proc/{status['scheduler_pid']}").exists()
    for job in status["active"]:
        job["process_alive"] = Path(f"/proc/{job['pid']}").exists()
    receipts = [read(p) for p in (control / "jobs").glob("*.json")]
    jobs = {job["id"]: job for job in read(control / "plan.json")}
    phases = {}
    active_ids = {job["job"] for job in status["active"]}
    receipts_by_id = {row["job"]: row for row in receipts if "job" in row}
    for job_id, job in jobs.items():
        phase = job["lane"]
        if phase == "analyses":
            phase = "plugin" if "_investigation__" in job_id else "ablation"
        row = phases.setdefault(phase, {"total": 0, "finished": 0, "running": 0, "needs_inspection": 0, "pending": 0})
        row["total"] += 1
        receipt = receipts_by_id.get(job_id)
        state = receipt["state"] if receipt else "running" if job_id in active_ids else "pending"
        row[state] = row.get(state, 0) + 1
    status["phases"] = phases
    status["dispatch_paused"] = (control / "PAUSE").exists()
    recovery = control / "ordinary_import_recovery.json"
    if recovery.exists():
        status["ordinary_import_recovery"] = read(recovery)
    terminal_restart = control / "terminal_failure_restart.json"
    if terminal_restart.exists():
        status["terminal_failure_restart"] = read(terminal_restart)
    status["outcomes"] = dict(Counter((r.get("result_status", "worker_error") + "/" + str(r.get("accepted"))) for r in receipts))
    status["inspection"] = [r for r in receipts if r["state"] == "needs_inspection"]
    responses = list(root.rglob("call_*_response.json"))
    responses += list((root / "cross_language/conditions").glob("*/ordinary_test_repair/repair_*/response.json"))
    responses += list((root.parent / "formal_generations").glob("*/*/response.json"))
    responses += list((root.parent / "formal_generations").glob("*/cte/provider/call_*/response.json"))
    models, usage, errors = Counter(), Counter(), 0
    for path in responses:
        try:
            value = read(path)
        except (ValueError, OSError):
            continue
        if "choices" in value:
            models[value.get("model", "unspecified")] += 1
            for name in ("prompt_tokens", "completion_tokens", "total_tokens"):
                usage[name] += (value.get("usage") or {}).get(name, 0) or 0
        elif "error" in value:
            errors += 1
    status.update(recorded_response_files=len(responses), response_models=dict(models),
                  observed_provider_usage=dict(usage), response_errors=errors,
                  usage_scope="Provider usage in recorded agent, ordinary-repair and translation responses; missing responses remain unmeasured.")
    return status


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", type=Path, required=True)
    print(json.dumps(summarize(parser.parse_args().review.resolve()), indent=2))
