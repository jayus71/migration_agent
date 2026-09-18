#!/usr/bin/env python3
"""Wait for both dispatchers, verify complete grids, and archive frozen evidence."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time


def read(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--implementation", type=Path, required=True)
    parser.add_argument("--repair", type=Path, required=True)
    parser.add_argument("--evaluation-root", type=Path, required=True)
    parser.add_argument("--diagnosis", type=Path, required=True)
    args = parser.parse_args()
    destination = args.implementation / "output/recovery_finalization.json"
    if destination.exists():
        raise ValueError("Finalization record already exists")
    last = None
    while True:
        repair = read(args.repair / "dispatch_result.json")
        diagnosis = read(args.diagnosis / "dispatch_result.json")
        for kind, result in (("repair", repair), ("diagnosis", diagnosis)):
            if result and (result["blocked"] or result["not_started"]):
                raise RuntimeError(kind + " stopped with unfinished work; requires inspection")
        a = read(args.repair / "progress.json") or {}
        b = read(args.diagnosis / "progress.json") or {}
        current = (len(a.get("completed", [])), len(b.get("finished", [])))
        if current != last:
            print(json.dumps({"repair_finished": current[0], "diagnosis_finished": current[1],
                              "time": datetime.now(timezone.utc).isoformat()}), flush=True)
            last = current
        if repair and diagnosis:
            break
        time.sleep(30)
    def run(*command):
        subprocess.run([sys.executable, *map(str, command)], check=True)
    output = args.implementation / "output"
    run(output / "report_autonomous_recovery.py", "--implementation", args.implementation,
        "--recovery", args.repair, "--output", output / "autonomous_recovery_final", "--verify-raw")
    repair_report = read(output / "autonomous_recovery_final.json")
    if not repair_report["complete"] or repair_report["raw_ledger_problems"] != 0:
        raise ValueError("Repair report incomplete or raw ledger mismatch")
    run(args.evaluation_root / "code/report_diagnosis_recovery.py", "--root", args.evaluation_root,
        "--continuation", args.diagnosis, "--output", args.evaluation_root / "reports/recovery_final")
    archives = []
    for name, source in (("autonomous_repair_recovery_round1", args.repair),
                         ("autonomous_diagnosis_recovery_round1", args.diagnosis)):
        prefix = output / "archives" / name
        run(output / "archive_autonomous_recovery.py", "--source", source, "--output", prefix)
        archives.append(str(prefix.with_suffix(".json")))
    destination.write_text(json.dumps({"finished_at": datetime.now(timezone.utc).isoformat(),
        "repair_complete": True, "diagnosis_dispatch_complete": True, "diagnosis_scores_may_be_unavailable": True,
        "raw_ledger_problems": 0, "archives": archives}, indent=2) + "\n")
    print(destination, flush=True)


if __name__ == "__main__":
    main()
