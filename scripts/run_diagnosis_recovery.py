#!/usr/bin/env python3
"""Complete frozen diagnosis evaluations after declared transport interruption."""
import argparse
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

import export_autonomous_diagnosis_evidence as exporter


VERSIONS = ("formal_v3", "progress_v4", "repair_window_v5", "productive_v6", "productive_v7")


def read(path):
    return json.loads(path.read_text())


def repair_finished(path):
    try:
        return read(path).get("status") == "completed"
    except (OSError, ValueError):
        return False


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n")
    tmp.replace(path)


def original_key(version):
    if version == "formal_v3":
        return "2026091703012026091703012026091703012026091703012026091703012026"
    return hashlib.sha256(("diagnosis-export-20260917:" + version).encode()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--implementation", type=Path, required=True)
    p.add_argument("--evaluation-root", type=Path, required=True)
    p.add_argument("--repair-recovery", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--execute", action="store_true")
    args = p.parse_args()
    if args.workers < 1:
        p.error("workers must be positive")
    root, output = args.evaluation_root.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    lock = (output / "scheduler.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if (output / "plan.json").exists():
        raise ValueError("Refuse implicit rerun of an existing diagnosis continuation")
    recovery = read(args.repair_recovery / "recovery_plan.json")
    recoveries = {(i["version"], i["task"], i["method"]): i for i in recovery["conditions"] if i["benchmark"] == "Fixed50"}
    jobs = []
    for version in VERSIONS:
        original = args.implementation.resolve() / "experiments/autonomous_fixed50_20260917" / version
        config = read(original / "manifest.json")
        for task in config["tasks"]:
            for method in config["methods"]:
                tid = task["anonymous_id"]
                replaced = recoveries.get((version, tid, method))
                jobs.append({"version": version, "task": tid, "method": method,
                    "original_run": str(original), "source_run": replaced["recovery_run"] if replaced else str(original),
                    "repair_restarted": bool(replaced)})
    save(output / "plan.json", {"created_at": datetime.now(timezone.utc).isoformat(), "jobs": jobs,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "policy": "Reuse completed frozen-v3 evaluations, including schema/input-limit outcomes. Only transport-interrupted evaluations receive one separate full two-phase restart. Newly completed repair retries are evaluated separately. Preserve all old requests, responses, unknown usage and costs; no best-of selection, rubric changes or evidence truncation.",
        "evaluator": "score_autonomous_diagnosis_spans.py", "execute": args.execute})

    def work(item):
        version, condition = item["version"], item["task"] + "/" + item["method"]
        run = Path(item["source_run"])
        old_pack = root / "exports/by_condition" / version / condition
        old_output, prior_status = None, None
        if not item["repair_restarted"] and (old_pack / "private/mapping.json").exists():
            cid = read(old_pack / "private/mapping.json")["cases"][0]["case_id"]
            old_output = root / "assessments_spans" / version / cid
            cov = old_output / "cases" / cid / "coverage.json"
            if cov.exists():
                prior_status = read(cov)["status"]
                if prior_status not in {"phase1_transport_error", "phase2_transport_error", "phase1_dry_run", "phase2_dry_run"}:
                    return {**item, "evaluation_status": prior_status, "action": "reuse_frozen_terminal",
                        "assessment_root": str(old_output), "evidence_export": str(old_pack), "new_api_attempt": False}
            pack = old_pack
        else:
            pack = output / "exports" / version / condition
            key = hashlib.sha256(("diagnosis-recovery-20260917:" + version).encode()).hexdigest() if item["repair_restarted"] else original_key(version)
            exporter.export(run, pack, conditions=[condition], key=key)
            cid = read(pack / "private/mapping.json")["cases"][0]["case_id"]
        target = output / "assessments" / version / cid
        log = output / "logs" / version / (cid + ".log")
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("x") as handle:
            proc = subprocess.run([sys.executable, str(root / "code/score_autonomous_diagnosis_spans.py"),
                "--evidence-export", str(pack), "--rubric", str(root / "code/fixed50-private-diagnosis-rubric-20260917.json"),
                "--run-config", str(run / "manifest.json"), "--output", str(target), "--case-id", cid,
                "--execute" if args.execute else "--dry-run"], stdout=handle, stderr=subprocess.STDOUT)
        coverage = target / "cases" / cid / "coverage.json"
        status = read(coverage)["status"] if coverage.exists() else "missing_coverage"
        return {**item, "evaluation_status": status, "returncode": proc.returncode,
            "action": "transport_restart" if prior_status and "transport_error" in prior_status else "new_evaluation",
            "prior_status": prior_status, "prior_assessment_root": str(old_output) if old_output else None,
            "assessment_root": str(target), "evidence_export": str(pack), "new_api_attempt": args.execute}

    pending, active, done, blocked = list(jobs), {}, [], False
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        while pending or active:
            for item in list(pending):
                if blocked or len(active) >= args.workers:
                    break
                result = Path(item["source_run"]) / "conditions" / item["task"] / item["method"] / "result.json"
                if not repair_finished(result):
                    continue
                pending.remove(item)
                active[pool.submit(work, item)] = item
            if active:
                finished, _ = wait(active, timeout=10, return_when=FIRST_COMPLETED)
                for future in finished:
                    item = active.pop(future)
                    try:
                        row = future.result()
                    except Exception as error:
                        row = {**item, "evaluation_status": "scheduler_error", "error_type": type(error).__name__}
                    done.append(row)
                    if row["evaluation_status"] in {"phase1_transport_error", "phase2_transport_error", "scheduler_error", "missing_coverage"}:
                        blocked = True
                    print(json.dumps({"event": "evaluation_finished", **row}), flush=True)
            elif blocked:
                break
            elif pending:
                dispatch = args.repair_recovery / "dispatch_result.json"
                if dispatch.exists():
                    break
                time.sleep(10)
            save(output / "progress.json", {"finished": done, "planned": len(jobs), "active": len(active),
                "pending": len(pending), "blocked": blocked, "updated_at": datetime.now(timezone.utc).isoformat()})
    save(output / "dispatch_result.json", {"finished": done, "not_started": pending, "blocked": blocked,
        "finished_at": datetime.now(timezone.utc).isoformat()})


if __name__ == "__main__":
    main()
