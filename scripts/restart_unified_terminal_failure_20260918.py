"""Gracefully load scheduler bookkeeping correction, preserving every outcome."""
import argparse
import fcntl
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from dispatch_unified_formal_20260918 import digest, now, read, result_path, save, terminal_native_failure


def check(root):
    from experiments.unified_migration50_20260918.integration import require_approval
    require_approval(root / "cross_language")
    control = root.parent / "formal_control"
    job = next(j for j in read(control / "plan.json") if j["id"] == "cross__task_003__test_repair")
    receipt = read(control / "jobs" / (job["id"] + ".json"))
    if receipt["state"] != "needs_inspection" or not terminal_native_failure(job, read(result_path(job))):
        raise RuntimeError("No matching verified native output failure to reconcile")
    return job


def restart(root):
    control = root.parent / "formal_control"
    restart_lock = (control / "terminal_failure_restart.lock").open("a")
    fcntl.flock(restart_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    job = check(root)
    result_hash = digest(result_path(job))
    pause = control / "PAUSE"
    with pause.open("x") as stream:
        stream.write("Drain current workers to load native terminal-outcome scheduler classification.\n")
    save(control / "terminal_failure_restart.json", {"state": "draining", "pid": os.getpid(),
         "timestamp": now(), "job": job["id"], "result_sha256": result_hash, "rerun": False})
    while read(control / "status.json")["active"]:
        time.sleep(5)
    lock = (root / "dispatch.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX)
    check(root)
    if digest(result_path(job)) != result_hash:
        raise RuntimeError("Completed result changed while draining")
    archive = control / "recoveries" / "terminal_failure_scheduler_restart"
    archive.mkdir(parents=True, exist_ok=False)
    for name in ("status.json", "launch.json"):
        shutil.copy2(control / name, archive / name)
    save(archive / "restart.json", {"timestamp": now(), "result_sha256": result_hash,
        "rerun": False, "method_code_changed": False,
        "dispatcher_sha256": digest(Path(__file__).with_name("dispatch_unified_formal_20260918.py"))})
    pause.unlink()
    lock.close()
    subprocess.run([sys.executable, str(Path(__file__).with_name("dispatch_unified_formal_20260918.py")),
                    "--review", str(root), "--workers", "4", "--launch"], check=True)
    save(control / "terminal_failure_restart.json", {"state": "restarted", "timestamp": now(),
         "job": job["id"], "result_sha256": result_hash, "rerun": False})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--launch", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.review.resolve()
    if args.check:
        job = check(root)
        print("Verified terminal response failure; result preserved:", digest(result_path(job)))
    elif args.launch:
        check(root)
        control = root.parent / "formal_control"
        with (control / "terminal_failure_restart.log").open("a") as stream:
            process = subprocess.Popen([sys.executable, "-u", str(Path(__file__).resolve()), "--review", str(root)],
                cwd=Path(__file__).resolve().parents[1], stdin=subprocess.DEVNULL,
                stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        print("Restart coordinator PID:", process.pid)
    else:
        restart(root)


if __name__ == "__main__":
    main()
