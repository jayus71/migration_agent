#!/usr/bin/env python3
"""Isolated evaluator scheduling; never writes repair workspaces."""
import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import threading
import time

import export_autonomous_diagnosis_evidence as exporter

VERSIONS = ("formal_v3", "progress_v4", "repair_window_v5", "productive_v6", "productive_v7")
PILOT_METHODS = ("autonomous_layered", "autonomous_layered_native", "autonomous_category_ablation",
                 "swe_native_isolated", "direct_shared_tools")
KEYS = {v: hashlib.sha256(("diagnosis-export-20260917:" + v).encode()).hexdigest() for v in VERSIONS}
KEYS["formal_v3"] = "2026091703012026091703012026091703012026091703012026091703012026"


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--implementation", type=Path, required=True)
    parser.add_argument("--evaluation-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--evaluator", choices=("expanded", "spans"), default="expanded")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    root = args.evaluation_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    lock = (root / "scheduler.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    mutex = threading.Lock()
    stop_dispatch = threading.Event()
    ledger = root / "scheduling.jsonl"

    def event(**values):
        values["time"] = datetime.now(timezone.utc).isoformat()
        with mutex, ledger.open("a") as out:
            out.write(json.dumps(values) + "\n")
            out.flush()
        print(json.dumps(values), flush=True)

    configs = {}
    jobs = []
    for version in VERSIONS:
        run = args.implementation.resolve() / "experiments/autonomous_fixed50_20260917" / version
        config = read(run / "manifest.json")
        configs[version] = run
        for task in config["tasks"]:
            for method in config["methods"]:
                condition = task["anonymous_id"] + "/" + method
                if args.pilot and not (version == "formal_v3" and (
                    task["anonymous_id"] == "task_001" and method in PILOT_METHODS or
                    task["anonymous_id"] == "task_017" and method == "autonomous_layered_native")):
                    continue
                jobs.append((version, condition))
    event(event="scheduler_start", jobs=len(jobs), workers=args.workers, execute=args.execute,
          script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), pilot=args.pilot,
          evaluator=args.evaluator)

    def work(version, condition):
        run = configs[version]
        pack = root / "exports/by_condition" / version / condition
        if not (pack / "private/mapping.json").exists():
            exporter.export(run, pack, conditions=[condition], key=KEYS[version])
        mapping = read(pack / "private/mapping.json")
        if len(mapping["cases"]) != 1 or mapping["cases"][0]["condition"] != condition:
            raise ValueError("Unexpected or incomplete export")
        cid = mapping["cases"][0]["case_id"]
        output = root / ("assessments_" + args.evaluator) / version / cid
        event(event="case_start", version=version, condition=condition, case_id=cid)
        logs = root / "logs" / args.evaluator / version
        logs.mkdir(parents=True, exist_ok=True)
        with (logs / (cid + ".log")).open("a") as handle:
            command = [sys.executable, str(root / ("code/score_autonomous_diagnosis_" + args.evaluator + ".py")),
                       "--evidence-export", str(pack), "--rubric",
                       str(root / "code/fixed50-private-diagnosis-rubric-20260917.json"),
                       "--run-config", str(run / "manifest.json"), "--output", str(output),
                       "--case-id", cid, "--execute" if args.execute else "--dry-run"]
            completed = subprocess.run(command, stdout=handle, stderr=subprocess.STDOUT)
        coverage = output / "cases" / cid / "coverage.json"
        outcome = read(coverage) if coverage.exists() else None
        if outcome and outcome.get("status") in {"phase1_transport_error", "phase2_transport_error"}:
            stop_dispatch.set()
            event(event="transport_circuit_open", version=version, condition=condition,
                  note="No new requests will be scheduled. Active workers may finish; no automatic retries.")
        event(event="case_end", version=version, condition=condition, case_id=cid,
              returncode=completed.returncode, coverage=outcome)
        if completed.returncode:
            raise RuntimeError("Evaluator subprocess failed; see preserved log")

    pending, active, finished, failed = set(jobs), {}, set(), []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        while pending or active:
            for job in sorted(pending):
                if stop_dispatch.is_set() or len(active) >= args.workers:
                    break
                path = configs[job[0]] / "conditions" / job[1] / "result.json"
                if not path.exists() or read(path).get("status") not in {"completed", "infrastructure_error"}:
                    continue
                pending.remove(job)
                active[pool.submit(work, *job)] = job
            if active:
                done, _ = wait(active, timeout=30, return_when=FIRST_COMPLETED)
                for future in done:
                    job = active.pop(future)
                    try:
                        future.result()
                        finished.add(job)
                    except Exception as error:
                        failed.append(job)
                        event(event="scheduler_error", version=job[0], condition=job[1], error_type=type(error).__name__)
            elif pending:
                if stop_dispatch.is_set():
                    event(event="scheduler_stopped_transport", pending=sorted(pending), completed=len(finished))
                    break
                terminal = all((run / "complete.json").exists() for run in configs.values())
                if terminal:
                    event(event="unavailable_repair_conditions", conditions=sorted(pending))
                    failed.extend(pending)
                    pending.clear()
                else:
                    time.sleep(30)
    event(event="scheduler_finished", completed=len(finished), failed=len(failed))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
