"""Run the frozen JAX repair grid with a bounded number of API workers."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


def transport_blocked(run):
    for error_file in (run / "conditions").glob("*/*/evidence/agent/call_*_error.json"):
        error = json.loads(error_file.read_text())
        if error.get("http_status") in (401, 402, 403):
            return True
        # The frozen v4 client records these statuses in the error message.
        if re.search(r"HTTP (401|402|403)\b", str(error.get("error", ""))):
            return True
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    run = args.run.resolve()
    manifest = json.loads((run / "manifest.json").read_text())
    clean = json.loads((run / "healthy_controls.json").read_text())
    faults = json.loads((run / "preflight.json").read_text())
    if len(clean) != 6 or not all(row["accepted"] is True for row in clean):
        raise ValueError("All six healthy verification checks must pass before API use")
    if len(faults) != 6 or any(row["accepted"] is not False for row in faults):
        raise ValueError("All six original injected faults must trigger before API use")
    grid = [(row["anonymous_id"], method) for row in manifest["tasks"] for method in manifest["methods"]]
    if not 1 <= args.workers <= 2:
        raise ValueError("Only one or two coordinated workers are supported")
    for task, method in grid:
        if (run / "conditions" / task / method).exists():
            raise ValueError("Refusing to replace or implicitly resume an episode")
    logs = run / "worker_logs"
    logs.mkdir()
    (run / "dispatch_manifest.json").write_text(json.dumps({
        "dispatcher_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "runner_sha256": hashlib.sha256((run / "runner.py").read_bytes()).hexdigest(),
        "workers": args.workers, "grid": grid, "python": sys.executable}, indent=2))

    def worker(pair):
        task, method = pair
        if transport_blocked(run):
            return {"task": task, "method": method, "status": "not_started_auth_blocker", "accepted": None}
        with (logs / f"{task}_{method}.log").open("w") as stream:
            proc = subprocess.run([sys.executable, str(run / "runner.py"), "worker", "--output", str(run),
                                   "--task", task, "--method", method], stdout=stream, stderr=subprocess.STDOUT)
        path = run / "conditions" / task / method / "result.json"
        value = json.loads(path.read_text()) if path.exists() else {"status": "worker_error", "accepted": None}
        return {"task": task, "method": method, "returncode": proc.returncode,
                "status": value["status"], "accepted": value.get("accepted"), "budget": value.get("budget")}

    rows = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for future in as_completed([pool.submit(worker, pair) for pair in grid]):
            rows.append(future.result())
            (run / "dispatch_progress.json").write_text(json.dumps({"planned": len(grid), "completed": rows}, indent=2))
            print(json.dumps(rows[-1]), flush=True)


if __name__ == "__main__":
    main()
