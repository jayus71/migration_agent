"""Resume only never-started conditions after an audited dispatcher drain."""
from __future__ import annotations
import argparse
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def write(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def inventory(root, plan):
    first = root / plan["variants"][0]
    tasks = json.loads((first / "manifest.json").read_text())["tasks"]
    pending, retained = [], []
    expected = set()
    for task in tasks:
        for variant in plan["variants"]:
            pair = (task["anonymous_id"], variant)
            directory = root / variant / "conditions" / pair[0]
            expected.add(directory)
            if not directory.exists():
                pending.append(pair)
                continue
            result_path = directory / "autonomous_layered/result.json"
            if not result_path.exists():
                raise RuntimeError("Existing condition has no terminal result: " + str(directory))
            result = json.loads(result_path.read_text())
            if result.get("status") not in ("completed", "infrastructure_error", "unsupported"):
                raise RuntimeError("Existing condition is nonterminal: " + str(directory))
            retained.append({"task": pair[0], "variant": variant, "method": "autonomous_layered",
                             "status": result["status"], "accepted": result.get("accepted")})
    actual = {path for variant in plan["variants"]
              for path in (root / variant / "conditions").glob("*") if path.is_dir()}
    if actual - expected:
        raise RuntimeError("Unknown condition directories exist")
    return pending, retained


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, required=True)
    args = parser.parse_args()
    if not 1 <= args.workers <= 16:
        raise ValueError("Expected 1 through 16 workers")
    root = args.output.resolve()
    lock = (root / "dispatch.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if (root / "dispatch_result.json").exists() or (root / "continuation_dispatch.json").exists():
        raise RuntimeError("Refusing a completed or previously resumed dispatcher")
    plan = json.loads((root / "plan.json").read_text())
    runner = root / "run_maintext_ablations.py"
    spec = importlib.util.spec_from_file_location("frozen_maintext_runner", runner)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if module.sha(runner) != plan["runner_sha256"]:
        raise RuntimeError("Frozen runner hash changed")
    for variant in plan["variants"]:
        module.verify_frozen(root / variant)
    pending, retained = inventory(root, plan)
    sys.path.insert(0, str(root / plan["variants"][0] / "code_snapshot"))
    from autofix.autonomous.batch import finalize_worker
    state = {"started_at": time.time(), "workers": args.workers,
             "scheduler_sha256": module.sha(Path(__file__)), "frozen_runner_sha256": module.sha(runner),
             "retained_conditions": retained, "pending_initial": pending,
             "started": [], "completed": [], "blocking_errors": []}
    state_path = root / "continuation_dispatch.json"
    write(state_path, state)

    def one(pair):
        task, variant = pair
        run = root / variant
        if (run / "conditions" / task).exists():
            raise RuntimeError("Condition was started by another owner: " + task)
        logs = run / "worker_logs"
        logs.mkdir(exist_ok=True)
        with (logs / (task + ".log")).open("x") as stream:
            result = subprocess.run([sys.executable, str(runner), "worker", "--output", str(run),
                                     "--task", task], cwd=run / "code_snapshot", env=os.environ.copy(),
                                    stdout=stream, stderr=subprocess.STDOUT)
        value = finalize_worker(run, task, "autonomous_layered", result.returncode)
        return {"variant": variant, **{key: value.get(key) for key in
                ("task", "method", "status", "accepted")}}

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        active = set()
        while pending or active:
            state["blocking_errors"] = module.transport_blockers(root)
            while pending and len(active) < args.workers and not state["blocking_errors"]:
                pair = pending.pop(0)
                state["started"].append(pair)
                active.add(executor.submit(one, pair))
                write(state_path, state)
            if not active:
                break
            done, active = wait(active, timeout=1, return_when=FIRST_COMPLETED)
            for future in done:
                state["completed"].append(future.result())
                write(state_path, state)
    state.update(completed_at=time.time(), not_started=pending)
    write(state_path, state)
    write(root / "dispatch_result.json", {
        "retained_conditions": retained, "started": state["started"], "not_started": pending,
        "blocking_errors": state["blocking_errors"], "continuation_scheduler": str(Path(__file__))})


if __name__ == "__main__":
    main()
