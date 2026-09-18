"""Drain current workers and restore one proven pre-inference import failure."""
import argparse
import fcntl
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from dispatch_unified_formal_20260918 import digest, now, plan, read, result_path, save, prepare_ordinary_imports


JOB = "cross__task_001__test_repair"
ERROR = "ModuleNotFoundError: No module named 'autofix.backends'"


def check(root):
    from experiments.unified_migration50_20260918.integration import require_approval
    require_approval(root / "cross_language")
    prepare_ordinary_imports()
    from experiments.unified_migration50_20260918.ordinary_repair import native_module
    module = native_module()
    assert callable(module.evaluate) and callable(module.call)
    job = next(row for row in plan(root) if row["id"] == JOB)
    control = root.parent / "formal_control"
    receipt = read(control / "jobs" / (JOB + ".json"))
    if receipt.get("error") != ERROR or receipt["state"] != "needs_inspection":
        raise RuntimeError("Failure no longer matches the inspected import error")
    if result_path(job).parent.exists():
        raise RuntimeError("A condition exists; cannot assert zero model calls")
    return job


def recover(root):
    control = root.parent / "formal_control"
    recovery_lock = (control / "ordinary_import_recovery.lock").open("a")
    fcntl.flock(recovery_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    check(root)
    pause = control / "PAUSE"
    with pause.open("x") as stream:
        stream.write("Drain workers for the inspected pre-inference import-path recovery.\n")
    save(control / "ordinary_import_recovery.json", {"state": "draining", "pid": os.getpid(),
         "timestamp": now(), "job": JOB, "real_model_calls_before_failure": 0})
    while read(control / "status.json")["active"]:
        time.sleep(5)
    # The running dispatcher exits after draining. Its lock guarantees that no
    # worker can be dispatched while start/failure receipts are being archived.
    dispatch_lock = (root / "dispatch.lock").open("a")
    fcntl.flock(dispatch_lock, fcntl.LOCK_EX)
    check(root)
    archive = control / "recoveries" / "ordinary_import_before_inference"
    archive.mkdir(parents=True, exist_ok=False)
    for relative in (f"jobs/{JOB}.json", f"started/{JOB}.json", f"logs/{JOB}.log", "launch.json", "status.json"):
        source = control / relative
        target = archive / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if relative in ("launch.json", "status.json"):
            shutil.copy2(source, target)
        else:
            source.rename(target)
    save(archive / "recovery.json", {"timestamp": now(), "reason": ERROR,
         "intervention": "Extend the worker package search path to the existing original evaluator package.",
         "prior_condition_directory_exists": False, "prior_model_calls": 0,
         "dispatcher_sha256": digest(Path(__file__).with_name("dispatch_unified_formal_20260918.py")),
         "method_code_changed": False})
    pause.unlink()
    dispatch_lock.close()
    subprocess.run([sys.executable, str(Path(__file__).with_name("dispatch_unified_formal_20260918.py")),
                    "--review", str(root), "--workers", "4", "--launch"], check=True)
    save(control / "ordinary_import_recovery.json", {"state": "restarted", "timestamp": now(),
         "job": JOB, "archive": str(archive)})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--launch", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.review.resolve()
    if args.check:
        check(root)
        print("Original evaluator imports successfully; failed condition has no workspace or model calls.")
    elif args.launch:
        check(root)
        control = root.parent / "formal_control"
        with (control / "ordinary_import_recovery.log").open("a") as stream:
            process = subprocess.Popen([sys.executable, "-u", str(Path(__file__).resolve()), "--review", str(root)],
                cwd=Path(__file__).resolve().parents[1], stdin=subprocess.DEVNULL,
                stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        print("Recovery coordinator PID:", process.pid)
    else:
        recover(root)


if __name__ == "__main__":
    main()
