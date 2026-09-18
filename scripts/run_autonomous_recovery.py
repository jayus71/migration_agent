#!/usr/bin/env python3
"""Run declared infrastructure restarts with exact frozen experiment code."""
import argparse
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import urllib.error
import urllib.request


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(value, indent=2) + "\n")
    temp.replace(path)


def copied_tree(source, target):
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    hashes = {}
    for path in sorted(target.rglob("*")):
        if path.is_file():
            rel = str(path.relative_to(target))
            hashes[rel] = sha(path)
            if hashes[rel] != sha(source / rel):
                raise ValueError("Copied input differs: " + rel)
    return hashes


def prepare(implementation, inventory, output):
    if output.exists():
        raise ValueError("Recovery output must be new")
    selected = read(inventory)
    checked, originals = [], {}
    for item in selected["conditions"]:
        if item["original_status"] not in {"not_started", "infrastructure_error"}:
            raise ValueError("Only infrastructure errors and unstarted conditions are eligible")
        original = implementation / item["original_run"]
        manifest = original / "manifest.json"
        if sha(manifest) != item["manifest_sha256"]:
            raise ValueError("Original manifest changed")
        path = original / "conditions" / item["task"] / item["method"] / "result.json"
        if item["original_status"] == "not_started":
            if path.exists() or path.parent.exists():
                raise ValueError("Unstarted condition already has artifacts")
        elif not path.exists() or read(path)["status"] != "infrastructure_error":
            raise ValueError("Original condition is no longer an infrastructure failure")
        checked.append({**item, "original_result_sha256": sha(path) if path.exists() else None})
        originals[(item["benchmark"], item["version"])] = original
    if len({(i["benchmark"], i["version"], i["task"], i["method"]) for i in checked}) != len(checked):
        raise ValueError("Duplicate recovery condition")
    output.mkdir(parents=True)
    snapshots = {}
    for (benchmark, version), original in sorted(originals.items()):
        target = output / benchmark / version
        target.mkdir(parents=True)
        shutil.copy2(original / "manifest.json", target / "manifest.json")
        files = {"code_snapshot": copied_tree(original / "code_snapshot", target / "code_snapshot")}
        for name in ("implementation.json", "implementation.patch"):
            if (original / name).exists():
                shutil.copy2(original / name, target / name)
        tasks = sorted({i["task"] for i in checked if i["benchmark"] == benchmark and i["version"] == version})
        for task in tasks:
            for directory in ("private_inputs", "private_cases"):
                if (original / directory / task).exists():
                    files[directory + "/" + task] = copied_tree(original / directory / task, target / directory / task)
        snapshots[benchmark + "/" + version] = files
    priority = {"formal_v3": 0, "productive_v7": 1, "repair_window_v5": 2, "productive_v6": 3}
    checked.sort(key=lambda i: (priority[i["version"]], i["benchmark"] != "Natural10", i["task"], i["method"]))
    for item in checked:
        item["recovery_run"] = str(output / item["benchmark"] / item["version"])
    plan = {"created_at": datetime.now(timezone.utc).isoformat(), "implementation": str(implementation),
            "inventory_sha256": sha(inventory), "launcher_sha256": sha(Path(__file__)),
            "policy": "One independent fresh-input restart per infrastructure failure; first execution for unstarted conditions. Exact original model, algorithm, inputs, acceptance and per-run budget. All original attempts and costs retained separately. No best-of selection, completed-condition retry or automatic transport retry.",
            "conditions": checked, "copied_file_hashes": snapshots}
    save(output / "recovery_plan.json", plan)
    return plan


def worker(run, task, method):
    # Capture only status outside the frozen client; requests and errors are unchanged.
    original_urlopen = urllib.request.urlopen
    condition = run / "conditions" / task / method
    if condition.exists():
        raise ValueError("Refusing to overwrite condition")
    def observed_urlopen(*args, **kwargs):
        try:
            return original_urlopen(*args, **kwargs)
        except urllib.error.HTTPError as error:
            if error.code in (401, 402, 403):
                save(condition / "transport_block.json", {"http_status": error.code})
            raise
    urllib.request.urlopen = observed_urlopen
    sys.path.insert(0, str(run / "code_snapshot"))
    sys.argv = ["autofix.autonomous.experiment", "run", "--run", str(run), "--task", task, "--method", method]
    runpy.run_module("autofix.autonomous.experiment", run_name="__main__")


def execute(output, workers):
    if workers < 1:
        raise ValueError("workers must be positive")
    lock = (output / "scheduler.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    plan = read(output / "recovery_plan.json")
    if plan["launcher_sha256"] != sha(Path(__file__)):
        raise ValueError("Recovery launcher changed after declaration")
    jobs = list(plan["conditions"])
    for item in jobs:
        folder = Path(item["recovery_run"]) / "conditions" / item["task"] / item["method"]
        if folder.exists():
            raise ValueError("Existing recovery artifacts; refuse implicit restart")
    def one(item):
        run = Path(item["recovery_run"])
        config = read(run / "manifest.json")
        env = os.environ.copy()
        env.update(PYTHONPATH=str(run / "code_snapshot"), AUTOFIX_LLM_MODEL=config["model"],
                   AUTOFIX_LLM_TEMPERATURE=str(config["temperature"]), OMP_NUM_THREADS="1",
                   OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
        log = run / "logs" / (item["task"] + "_" + item["method"] + ".log")
        log.parent.mkdir(exist_ok=True)
        with log.open("x") as handle:
            process = subprocess.run([sys.executable, str(Path(__file__).resolve()), "worker", "--run", str(run),
                "--task", item["task"], "--method", item["method"]], cwd=run / "code_snapshot", env=env,
                stdout=handle, stderr=subprocess.STDOUT)
        path = run / "conditions" / item["task"] / item["method"] / "result.json"
        result = read(path) if path.exists() else {}
        return {"benchmark": item["benchmark"], "version": item["version"], "task": item["task"],
                "method": item["method"], "returncode": process.returncode,
                "status": result.get("status", "missing_result"), "accepted": result.get("accepted"),
                "result_path": str(path)}
    pending, active, done, blocked = list(jobs), {}, [], False
    with ThreadPoolExecutor(max_workers=workers) as pool:
        while pending or active:
            blocked = blocked or bool(list(output.glob("*/*/conditions/*/*/transport_block.json")))
            while pending and len(active) < workers and not blocked:
                item = pending.pop(0)
                active[pool.submit(one, item)] = item
            if not active:
                break
            finished, _ = wait(active, timeout=1, return_when=FIRST_COMPLETED)
            for future in finished:
                item = active.pop(future)
                try:
                    row = future.result()
                except Exception as error:
                    row = {"task": item["task"], "method": item["method"], "status": "scheduler_error", "error_type": type(error).__name__}
                done.append(row)
                if row["status"] != "completed" or row.get("returncode", 1) != 0:
                    blocked = True
                print(json.dumps({"event": "condition_finished", **row}), flush=True)
            save(output / "progress.json", {"completed": done, "planned": len(jobs), "active": len(active),
                 "pending": len(pending), "blocked": blocked, "updated_at": datetime.now(timezone.utc).isoformat()})
    save(output / "dispatch_result.json", {"completed": done, "not_started": pending, "blocked": blocked,
        "finished_at": datetime.now(timezone.utc).isoformat()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "execute", "worker"))
    parser.add_argument("--implementation", type=Path)
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--run", type=Path)
    parser.add_argument("--task")
    parser.add_argument("--method")
    args = parser.parse_args()
    if args.command == "prepare":
        plan = prepare(args.implementation.resolve(), args.inventory.resolve(), args.output.resolve())
        print(json.dumps({"conditions": len(plan["conditions"]), "plan": str(args.output / "recovery_plan.json")}))
    elif args.command == "execute":
        execute(args.output.resolve(), args.workers)
    else:
        worker(args.run.resolve(), args.task, args.method)


if __name__ == "__main__":
    main()
