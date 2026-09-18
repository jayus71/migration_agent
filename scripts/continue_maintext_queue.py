"""Start the authorized signal queue using two released diagnosis slots."""
from __future__ import annotations
import argparse
import fcntl
import json
from pathlib import Path
import subprocess
import sys
import time


def write(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def finish(run):
    path = run / "dispatch_result.json"
    while not path.exists():
        time.sleep(5)
    result = json.loads(path.read_text())
    blockers = result.get("blocking_errors", result.get("blockers", []))
    if blockers or result.get("not_started"):
        raise RuntimeError("A preceding batch stopped; new API work was not started: " + str(run))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    lock = (root / "continuation.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    state = {"maximum_api_workers": 10, "stage": "starting_signal12", "started_at": time.time(),
             "allocation": {"fixed50": 4, "natural10": 4, "signal12": 2}}
    write(root / "continuation.json", state)
    try:
        # A billing/credential stop in Fixed50 must also block new signals.
        for path in (root / "fixed50_v3").glob("*/conditions/*/*/evidence/agent/call_*_error.json"):
            if any("HTTP " + str(code) in path.read_text() for code in (401, 402, 403)):
                raise RuntimeError("Fixed50 reported a blocking provider error")
        signal = root / "signal12_v3"
        state.update(stage="running_signal12", signal_started_at=time.time())
        write(root / "continuation.json", state)
        with (signal / "dispatch.log").open("w") as log:
            subprocess.run([sys.executable, str(signal / "run_signal_ablations.py"), "dispatch",
                            "--output", str(signal), "--workers", "2"],
                           cwd=signal, stdout=log, stderr=subprocess.STDOUT, check=True)
        finish(signal)
        state.update(stage="waiting_for_components", signal_completed_at=time.time())
        write(root / "continuation.json", state)
        finish(root / "natural10_v3")
        finish(root / "fixed50_v3")
        state.update(stage="completed", completed_at=time.time())
        write(root / "continuation.json", state)
    except Exception as exc:
        state.update(stage="stopped", reason=str(exc), stopped_at=time.time())
        write(root / "continuation.json", state)
        raise


if __name__ == "__main__":
    main()
