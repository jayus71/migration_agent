"""Four-process execution of the approved frozen matrix; never resample a job.

This file controls scheduling only. All model calls and evaluations use the
reviewed experiment modules. Run from the implementation repository on Linux.
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

PACKAGE = "experiments.unified_migration50_20260918"
ADAPTERS = {
    "ladim": "autonomous_layered",
    "swe": "swe_native_isolated",
    "matchfix": "matchfix_full_orchestration",
    "test_repair": "ordinary_test_repair",
}
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def reviews(root):
    return [root, root / "cross_language", *sorted((root / "analyses").iterdir())]


def approve(root):
    index = read(root / "review_index.json")
    expected = {root: index["main_manifest_sha256"],
                root / "cross_language": index["cross_language_manifest_sha256"]}
    expected.update({root / "analyses" / name: value
                     for name, value in index["analysis_manifests"].items()})
    for review, value in expected.items():
        if digest(review / "manifest.json") != value:
            raise RuntimeError("Review manifest hash changed: " + str(review))
    for review, value in expected.items():
        receipt = review / "review_approval.json"
        if receipt.exists():
            if read(receipt).get("manifest_sha256") != value or read(receipt).get("approved_by_user") is not True:
                raise RuntimeError("Conflicting approval receipt")
            continue
        save(receipt, {"manifest_sha256": value, "approved_by_user": True,
                       "authorization": "User explicitly approved all 391 conditions and parallel execution.",
                       "user_messages": ["可以 直接开始跑吧", "最好能并行跑 这样快一些"],
                       "timestamp": now()})


def plan(root):
    jobs = []
    for group in read(root / "manifest.json")["translation_reuse"]:
        for method in ("direct", "cte", "msadapter", "ladim", "swe", "matchfix"):
            jobs.append({"id": f"main__{group['group']}__{method}", "lane": "main",
                         "review": str(root), "group": group["group"], "task": group["tasks"][0],
                         "method": method, "kind": "nonagent" if method in ("direct", "cte", "msadapter") else "repair",
                         "dependency": f"main__{group['group']}__direct" if method in ADAPTERS else None})
    cross = root / "cross_language"
    for row in read(cross / "manifest.json")["tasks"]:
        for method in ("ladim", "swe", "matchfix", "test_repair"):
            jobs.append({"id": f"cross__{row['anonymous_id']}__{method}", "lane": "cross_language",
                         "review": str(cross), "task": row["anonymous_id"], "method": method,
                         "kind": "ordinary" if method == "test_repair" else "repair", "dependency": None})
    for review in sorted((root / "analyses").iterdir()):
        if not (review / "manifest.json").is_file():
            continue
        manifest = read(review / "manifest.json")
        for group in manifest["translation_reuse"]:
            for method in manifest["methods"]:
                jobs.append({"id": f"{review.name}__{group['group']}__{method}", "lane": "analyses",
                             "review": str(review), "task": group["tasks"][0], "group": group["group"],
                             "method": method, "kind": "repair", "dependency": f"main__{group['group']}__direct"})
    counts = Counter(job["lane"] for job in jobs)
    assert counts == {"main": 174, "cross_language": 72, "analyses": 145}, counts
    assert len({job["id"] for job in jobs}) == 391
    assert all(job["dependency"] is None or job["dependency"] in {j["id"] for j in jobs} for job in jobs)
    return jobs


def materialize_group(root, generations, group_id):
    """Parent-only immutable copies; never rewrite inputs used by active jobs."""
    main = read(root / "manifest.json")
    group = next(g for g in main["translation_reuse"] if g["group"] == group_id)
    generation = generations / group_id / "direct"
    receipt = read(generation / "generation.json")
    if receipt["status"] != "generated":
        return
    if digest(generation / "candidate.py") != receipt["candidate_sha256"]:
        raise RuntimeError("Generated candidate changed")
    bundle, reference = Path(main["source_bundle"]), Path(main["reference_directory"])
    targets = [root, *[p for p in sorted((root / "analyses").iterdir()) if (p / "manifest.json").is_file()]]
    for review in targets:
        for task in group["tasks"]:
            destination = review / "private_inputs" / task
            if not destination.exists():
                shutil.copytree(bundle / "public" / task, destination)
                shutil.copy2(generation / "candidate.py", destination / "candidate.py")
            for filename, expected in (("source.py", group["source_sha256"]),
                                       ("task.json", group["contract_sha256"]),
                                       ("candidate.py", receipt["candidate_sha256"])):
                if digest(destination / filename) != expected:
                    raise RuntimeError("Existing input differs: " + str(destination / filename))
            for seed in (101, 202, 303):
                source = reference / group_id / "torch" / str(seed) / "measurement.json"
                target = review / "private_references" / task / str(seed) / "measurement.json"
                measurement = read(source)
                if measurement["status"] != "completed" or measurement["seed"] != seed:
                    raise RuntimeError("Source reference incomplete")
                if target.exists():
                    if digest(target) != digest(source):
                        raise RuntimeError("Reference changed")
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
    save(root.parent / "formal_control" / "materialized" / (group_id + ".json"),
         {"timestamp": now(), "candidate_sha256": receipt["candidate_sha256"], "tasks": group["tasks"]})


def result_path(job):
    review = Path(job["review"])
    if job["kind"] == "nonagent":
        return review / "nonagent_conditions" / job["group"] / job["method"] / "result.json"
    return review / "conditions" / job["task"] / ADAPTERS[job["method"]] / "result.json"


def prepare_ordinary_imports():
    # The current controller already loaded autofix. The unchanged historical
    # evaluator supplies another subpackage under that name; sys.path alone
    # cannot extend an already imported package's search locations.
    import autofix
    from experiments.unified_migration50_20260918.extensions import REPO
    native_package = str(REPO / "autofix")
    if native_package not in autofix.__path__:
        autofix.__path__.append(native_package)


def perform(job, generations):
    from experiments.unified_migration50_20260918.integration import require_approval, run_repair
    from experiments.unified_migration50_20260918.evaluate_outputs import evaluate_output
    review = Path(job["review"])
    manifest = require_approval(review)
    target = result_path(job)
    if target.exists():
        raise RuntimeError("Existing condition must be reconciled before dispatch")
    if job["kind"] == "nonagent":
        bundle, references = Path(manifest["source_bundle"]), Path(manifest["reference_directory"])
        if job["method"] in ("direct", "cte"):
            generation = generations / job["group"] / job["method"]
            if generation.exists():
                raise RuntimeError("Existing generation must be reconciled; never regenerate")
            subprocess.run([sys.executable, "-m", PACKAGE + ".translation", "--review", str(review),
                            "--bundle", str(bundle), "--group", job["group"], "--method", job["method"],
                            "--out", str(generation)], check=True)
        return evaluate_output(review, bundle, references, generations, job["group"], job["method"])
    if job.get("dependency"):
        initial = read(generations / job["group"] / "direct/generation.json")
        if initial["status"] != "generated":
            result = {"task": job["task"], "method": ADAPTERS[job["method"]],
                      "status": "initial_generation_failed", "accepted": False,
                      "budget": {"calls": 0, "usage": None},
                      "shared_initial_generation": str(generations / job["group"] / "direct")}
            save(target, result)
            return result
    if job["kind"] == "ordinary":
        prepare_ordinary_imports()
        from experiments.unified_migration50_20260918.ordinary_repair import run
        return run(review, job["task"])
    return run_repair(review, job["task"], ADAPTERS[job["method"]], Path(sys.executable),
                      variant=manifest.get("variant"), plugin=manifest.get("plugin", False))


def terminal_native_failure(job, result):
    """Verify that the native runner stopped on an archived model response."""
    failure = result.get("generation_failure") or {}
    category = failure.get("failure_category")
    if (job["kind"] != "ordinary" or result.get("status") != "generation_error"
            or result.get("accepted") is not False
            or category not in ("output_truncated", "empty_response")):
        return False
    case = result_path(job).parent
    for generation in case.glob("repair_*/generation.json"):
        try:
            if read(generation) != failure:
                continue
            response = read(generation.parent / "response.json")
            choice = response["choices"][0]
            if category == "output_truncated" and choice["finish_reason"] == "length":
                return True
            if category == "empty_response" and not choice["message"].get("content"):
                return True
        except (OSError, ValueError, KeyError, IndexError, TypeError):
            continue
    return False


def result_state(job, result):
    if terminal_native_failure(job, result):
        return "finished"
    return "needs_inspection" if result["status"] in ("infrastructure_error", "generation_error") else "finished"


def reconcile_terminal_receipt(control, job, receipt):
    path = result_path(job)
    if receipt.get("state") != "needs_inspection" or not path.is_file():
        return receipt
    result = read(path)
    if not terminal_native_failure(job, result):
        return receipt
    archive = control / "reconciled_native_failures" / job["id"]
    archive.mkdir(parents=True, exist_ok=False)
    save(archive / "original_dispatch_receipt.json", receipt)
    revised = dict(receipt, state="finished", reconciliation={
        "timestamp": now(), "reason": "Native terminal generation failure verified against its saved response.",
        "result_sha256": digest(path), "result_modified": False, "rerun": False})
    save(control / "jobs" / (job["id"] + ".json"), revised)
    return revised


def worker(control, generations, job):
    receipt = {"job": job["id"], "pid": os.getpid(), "started_at": now(),
               "result_file": str(result_path(job))}
    try:
        result = perform(job, generations)
        receipt.update(state=result_state(job, result),
                       result_status=result["status"], accepted=result.get("accepted"))
    except Exception as exc:
        receipt.update(state="needs_inspection", error=f"{type(exc).__name__}: {exc}")
        traceback.print_exc()
    receipt["finished_at"] = now()
    save(control / "jobs" / (job["id"] + ".json"), receipt)
    print(json.dumps(receipt), flush=True)


def global_api_failure(job, generations):
    """Provider denial pauses launches; native functional failures stay local."""
    paths = [result_path(job)]
    if job.get("group") and job["method"] in ("direct", "cte"):
        paths.append(generations / job["group"] / job["method"] / "generation.json")
        paths.extend((generations / job["group"] / job["method"] / "provider").glob("call_*/ledger.json"))
    for path in paths:
        if not path.is_file():
            continue
        value = path.read_text()
        if any(marker in value for marker in ("HTTP 401", "HTTP 402", "HTTP 403", "HTTP 429",
                                               '"http_status": 401', '"http_status": 402',
                                               '"http_status": 403', '"http_status": 429',
                                               "Insufficient Balance", "insufficient_quota")):
            return True
    return False


def dispatch(root, control, generations, workers):
    from experiments.unified_migration50_20260918.integration import require_approval
    control.mkdir(parents=True, exist_ok=True)
    lock = (root / "dispatch.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    for review in reviews(root):
        require_approval(review)
    jobs = plan(root)
    planfile = control / "plan.json"
    if planfile.exists() and read(planfile) != jobs:
        raise RuntimeError("Dispatch plan changed")
    save(planfile, jobs)
    active, states, blocked = {}, {}, set()
    pause = False
    for job in jobs:
        receipt = control / "jobs" / (job["id"] + ".json")
        started = control / "started" / (job["id"] + ".json")
        if receipt.exists():
            states[job["id"]] = reconcile_terminal_receipt(control, job, read(receipt))
        elif started.exists() or result_path(job).parent.exists():
            raise RuntimeError("Interrupted job requires inspection: " + job["id"])
        if receipt.exists() and states[job["id"]]["state"] == "needs_inspection":
            blocked.add(job["method"])
            pause |= global_api_failure(job, generations)
    cursor = 0
    lanes = ("main", "cross_language", "analyses")
    prepared = set()
    print(json.dumps({"event": "scheduler_started", "pid": os.getpid(), "workers": workers,
                      "conditions": len(jobs), "timestamp": now()}), flush=True)
    while True:
        for name, (process, stream, job) in list(active.items()):
            if process.poll() is None:
                continue
            stream.close()
            receipt = control / "jobs" / (name + ".json")
            if receipt.exists():
                states[name] = reconcile_terminal_receipt(control, job, read(receipt))
            else:
                states[name] = {"state": "needs_inspection", "returncode": process.returncode,
                                "error": "Worker exited without a final receipt"}
                save(receipt, states[name])
            if states[name]["state"] == "needs_inspection":
                blocked.add(job["method"])
                pause |= global_api_failure(job, generations)
            print(json.dumps({"event": "worker_finished", "job": name, **states[name]}), flush=True)
            del active[name]
        while len(active) < workers and not pause and not (control / "PAUSE").exists():
            selected = None
            for offset in range(len(lanes)):
                lane = lanes[(cursor + offset) % len(lanes)]
                selected = next((j for j in jobs if j["lane"] == lane and j["id"] not in states
                                 and j["id"] not in active and j["method"] not in blocked
                                 and (not j["dependency"] or states.get(j["dependency"], {}).get("state") == "finished")), None)
                if selected:
                    cursor = (cursor + offset + 1) % len(lanes)
                    break
            if selected is None:
                break
            job = selected
            if job.get("dependency") and job["group"] not in prepared:
                materialize_group(root, generations, job["group"])
                prepared.add(job["group"])
            log = control / "logs" / (job["id"] + ".log")
            log.parent.mkdir(parents=True, exist_ok=True)
            save(control / "started" / (job["id"] + ".json"), {"timestamp": now(), "job": job})
            stream = log.open("a")
            process = subprocess.Popen([sys.executable, "-u", str(Path(__file__).resolve()),
                                        "--review", str(root), "--worker", job["id"]],
                                       stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT)
            active[job["id"]] = (process, stream, job)
            print(json.dumps({"event": "worker_started", "job": job["id"], "pid": process.pid,
                              "timestamp": now()}), flush=True)
        counts = Counter(s["state"] for s in states.values())
        status = {"timestamp": now(), "scheduler_pid": os.getpid(), "workers": workers, "total": len(jobs),
                  "finished": counts["finished"], "needs_inspection": counts["needs_inspection"],
                  "pending": len(jobs) - len(states) - len(active), "global_api_pause": pause,
                  "blocked_methods": sorted(blocked),
                  "active": [{"job": name, "pid": p.pid} for name, (p, _, _) in active.items()],
                  "state": "running" if active else "completed" if len(states) == len(jobs) else "attention_required"}
        save(control / "status.json", status)
        if not active:
            print(json.dumps(status), flush=True)
            return
        time.sleep(2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4, choices=range(1, 5))
    parser.add_argument("--approve", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--launch", action="store_true")
    parser.add_argument("--worker")
    args = parser.parse_args()
    root = args.review.resolve()
    control, generations = root.parent / "formal_control", root.parent / "formal_generations"
    if args.approve:
        approve(root)
    if args.check:
        from experiments.unified_migration50_20260918.integration import require_approval
        for review in reviews(root):
            require_approval(review)
        jobs = plan(root)
        print(json.dumps({"conditions": len(jobs), "counts": dict(Counter(j["lane"] for j in jobs)),
                          "workers": args.workers, "real_model_calls": 0, "status": "ready"}))
    elif args.launch:
        if not os.environ.get("AUTOFIX_LLM_API_KEY"):
            raise RuntimeError("Configured model credential is unavailable")
        control.mkdir(parents=True, exist_ok=True)
        environment = dict(os.environ)
        environment.update(AUTOFIX_LLM_MODEL="deepseek-v4-flash", OMP_NUM_THREADS="1",
                           OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", NUMEXPR_NUM_THREADS="1",
                           PYTHONUNBUFFERED="1")
        with (control / "scheduler.log").open("a") as stream:
            process = subprocess.Popen([sys.executable, "-u", str(Path(__file__).resolve()),
                                        "--review", str(root), "--workers", str(args.workers)],
                                       cwd=Path(__file__).resolve().parents[1], env=environment,
                                       stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT,
                                       start_new_session=True)
        save(control / "launch.json", {"scheduler_pid": process.pid, "timestamp": now(),
                                       "workers": args.workers, "dispatcher_sha256": digest(Path(__file__))})
        print(json.dumps({"scheduler_pid": process.pid, "status": "launched", "control": str(control)}))
    elif args.worker:
        jobs = read(control / "plan.json")
        worker(control, generations, next(j for j in jobs if j["id"] == args.worker))
    else:
        dispatch(root, control, generations, args.workers)


if __name__ == "__main__":
    main()
