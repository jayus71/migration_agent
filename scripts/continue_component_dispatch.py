"""Drain a verified dispatcher and schedule only its never-started conditions."""
from __future__ import annotations

import argparse
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def process(pid):
    folder = Path("/proc") / str(pid)
    try:
        text = (folder / "stat").read_text()
        fields = text[text.rindex(")") + 2:].split()
        command = (folder / "cmdline").read_bytes().split(b"\0")
        return {"pid": pid, "state": fields[0], "parent": int(fields[1]),
                "start_ticks": fields[19],
                "command": [part.decode() for part in command if part]}
    except (FileNotFoundError, ProcessLookupError):
        return None


def descendants(pid):
    records = {}
    for item in Path("/proc").iterdir():
        if item.name.isdigit():
            record = process(int(item.name))
            if record:
                records[record["pid"]] = record
    found, frontier = [], [pid]
    while frontier:
        parents = set(frontier)
        children = [row for row in records.values() if row["parent"] in parents]
        found.extend(children)
        frontier = [row["pid"] for row in children]
    return found


def grid(run, module):
    plan = json.loads((run / "plan.json").read_text())
    pairs = []
    for variant in plan["variants"]:
        module.verify_frozen(run / variant)
    tasks = json.loads((run / plan["variants"][0] / "manifest.json").read_text())["tasks"]
    for task in tasks:
        for variant in plan["variants"]:
            pairs.append((task["anonymous_id"], variant))
    return pairs


def inventory(run, pairs):
    finished, pending = [], []
    for task, variant in pairs:
        directory = run / variant / "conditions" / task
        result = directory / "autonomous_layered/result.json"
        if not directory.exists():
            pending.append((task, variant))
            continue
        if not result.is_file():
            raise ValueError("Existing condition lacks a terminal result: " + str(directory))
        data = json.loads(result.read_text())
        if data.get("status") not in ("completed", "infrastructure_error"):
            raise ValueError("Nonterminal existing condition: " + str(result))
        finished.append({"task": task, "variant": variant, "method": "autonomous_layered",
                         "status": data["status"], "accepted": data.get("accepted")})
    return finished, pending


def drain(run, pid, record_dir):
    expected = process(pid)
    if not expected or "dispatch" not in expected["command"]:
        raise ValueError("Expected dispatcher is not running")
    if str(run / "run_maintext_ablations.py") not in expected["command"]:
        raise ValueError("Dispatcher command does not match the frozen runner")
    if str(run) not in expected["command"]:
        raise ValueError("Dispatcher does not own the specified run")
    save(record_dir / "original_process.json", expected)
    for name in ("progress.json", "worker_slots.json", "dispatch.log"):
        if (run / name).exists():
            shutil.copy2(run / name, record_dir / ("before_" + name))
    os.kill(pid, signal.SIGSTOP)
    killed = False
    try:
        for _ in range(100):
            stopped = process(pid)
            if stopped and stopped["state"] in ("T", "t"):
                break
            time.sleep(0.01)
        else:
            raise ValueError("Dispatcher did not stop")
        known = {row["pid"]: row for row in descendants(pid)}
        save(record_dir / "original_descendants.json", list(known.values()))
        started = time.monotonic()
        while True:
            current = process(pid)
            if not current or current["start_ticks"] != expected["start_ticks"]:
                raise ValueError("Dispatcher process identity changed")
            if current["state"] not in ("T", "t"):
                raise ValueError("Dispatcher is no longer stopped")
            for row in descendants(pid):
                known.setdefault(row["pid"], row)
            active = []
            for child, identity in known.items():
                row = process(child)
                if row and row["start_ticks"] == identity["start_ticks"] and row["state"] != "Z":
                    active.append(row)
            save(record_dir / "drain_progress.json", {
                "checked_at": time.time(), "active": active,
                "wait_seconds": time.monotonic() - started})
            if not active:
                break
            if time.monotonic() - started > 3600:
                raise TimeoutError("Original workers did not drain within one hour")
            time.sleep(5)
        # Every existing directory must have a terminal result before ownership
        # moves. No model call or candidate process is interrupted by this kill.
        module = load_runner(run)
        completed, pending = inventory(run, grid(run, module))
        save(record_dir / "drained_inventory.json", {"completed": completed, "pending": pending})
        os.kill(pid, signal.SIGKILL)
        killed = True
        for name in ("progress.json", "dispatch.log"):
            if (run / name).exists():
                shutil.copy2(run / name, record_dir / ("after_drain_" + name))
    finally:
        if not killed:
            row = process(pid)
            if row and row["start_ticks"] == expected["start_ticks"]:
                os.kill(pid, signal.SIGCONT)


def load_runner(run):
    spec = importlib.util.spec_from_file_location("frozen_component_runner", run / "run_maintext_ablations.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dispatch(run, record_dir, workers):
    lock = (run / "dispatch.lock").open("a")
    deadline = time.monotonic() + 30
    while True:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.2)
    module = load_runner(run)
    pairs = grid(run, module)
    existing, pending = inventory(run, pairs)
    sys.path.insert(0, str(run / pairs[0][1] / "code_snapshot"))
    from autofix.autonomous.batch import finalize_worker

    save(record_dir / "continuation_plan.json", {
        "created_at": time.time(), "workers": workers, "existing": existing, "pending": pending,
        "frozen_runner_sha256": module.sha(run / "run_maintext_ablations.py"),
        "policy": "Retain every terminal episode; only absent condition directories may start."})
    started, completed = [], list(existing)
    blockers = []

    def one(pair):
        task, variant = pair
        target = run / variant
        if (target / "conditions" / task).exists():
            raise ValueError("Condition was concurrently created: " + str(pair))
        path = record_dir / (variant + "_" + task + ".log")
        with path.open("x") as stream:
            result = subprocess.run([sys.executable, str(run / "run_maintext_ablations.py"), "worker",
                                     "--output", str(target), "--task", task],
                                    stdout=stream, stderr=subprocess.STDOUT,
                                    cwd=target / "code_snapshot", env=os.environ.copy())
        row = finalize_worker(target, task, "autonomous_layered", result.returncode)
        return {"task": task, "variant": variant, "method": "autonomous_layered",
                "status": row.get("status"), "accepted": row.get("accepted")}

    with ThreadPoolExecutor(max_workers=workers) as pool:
        active = set()
        while pending or active:
            blockers = module.transport_blockers(run)
            while pending and len(active) < workers and not blockers:
                pair = pending.pop(0)
                started.append(pair)
                active.add(pool.submit(one, pair))
            if not active:
                break
            done, active = wait(active, timeout=1, return_when=FIRST_COMPLETED)
            for future in done:
                row = future.result()
                completed.append(row)
                print(json.dumps(row), flush=True)
                state = {"planned": len(pairs), "completed": completed,
                         "continuation": str(record_dir)}
                save(record_dir / "progress.json", state)
                save(run / "progress.json", state)
    final, absent = inventory(run, pairs)
    if set(absent) != set(pending) or len(final) != len(completed):
        raise ValueError("Final directory inventory differs from dispatch records")
    result = {"started": [list(pair) for pair in pairs if pair not in pending],
              "continuation_started": started, "preserved_terminal_conditions": len(existing),
              "not_started": pending, "blocking_errors": blockers, "completed": final,
              "continuation": str(record_dir), "finished_at": time.time()}
    save(record_dir / "dispatch_result.json", result)
    save(run / "dispatch_result.json", result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--dispatcher-pid", type=int, required=True)
    parser.add_argument("--workers", type=int, required=True)
    args = parser.parse_args()
    if not 1 <= args.workers <= 16:
        raise ValueError("Continuation supports one to sixteen workers")
    run = args.run.resolve()
    if (run / "dispatch_result.json").exists():
        raise ValueError("Original dispatcher has already finished")
    records = run / "parent_concurrency_continuation"
    records.mkdir(exist_ok=False)
    shutil.copy2(__file__, records / Path(__file__).name)
    drain(run, args.dispatcher_pid, records)
    dispatch(run, records, args.workers)


if __name__ == "__main__":
    main()
