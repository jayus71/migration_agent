"""Reevaluate the original three signal fixtures with four repetitions each.

The July fixture inputs and predicates are preserved. Public measurements are
masked by observed field, with no true category or responsible path supplied.
"""
from __future__ import annotations

import argparse
import ast
import copy
import fcntl
import hashlib
import io
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
from concurrent.futures import ThreadPoolExecutor, FIRST_COMPLETED, wait


COMMIT = "19ca4e800ce478650293f08501edc2496c3d7bce"
VARIANTS = ("execution", "execution_forward", "all_observations")
FAULTS = ("EX-01", "NU-04", "GR-07")
FORWARD_FIELDS = {"max_abs_diff", "expected_norm", "actual_norm", "finite", "shape", "dtype", "value"}


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract(archive, output):
    sys.path.insert(0, str(archive))
    from autofix.faults import controlled_cases as old
    for fault in FAULTS:
        case = old._blind_case_for(fault)
        healthy = old._redact_fault_identity(old._healthy_source(fault))
        faulty = old._redact_fault_identity(old._mutate_source(fault, old._healthy_source(fault)))
        folder = output / fault
        folder.mkdir(parents=True)
        (folder / "healthy.py").write_text(healthy)
        (folder / "faulty.py").write_text(faulty)
        results = {mode: old._probe(folder / (mode + ".py"), case) for mode in ("healthy", "faulty")}
        dump(folder / "original.json", {"fault_id": fault, "case": case, "results": results})


def mask_observation(observation, variant):
    if variant not in VARIANTS:
        raise ValueError("Unknown signal condition")
    result = copy.deepcopy(observation)
    measured = observation.get("measurements", {})
    if variant == "execution":
        result["measurements"] = {}
        passed = observation["execution_passed"]
    elif variant == "execution_forward":
        result["measurements"] = {key: value for key, value in measured.items() if key in FORWARD_FIELDS}
        passed = observation["execution_passed"]
        if "max_abs_diff" in measured:
            difference = measured["max_abs_diff"]
            passed = passed and type(difference) in (int, float) and math.isfinite(difference) and difference <= 1e-6
        if measured.get("finite") is False:
            passed = False
    else:
        passed = observation["accepted"]
    if observation.get("contract_immutable") is False:
        passed = False
    result["accepted"] = bool(passed)
    result["acceptance"] = {"accepted": bool(passed), "contract": "available_observations_only"}
    result["provided_observations"] = variant
    return result


def prepare(repo, control, output):
    repo, control, output = repo.resolve(), control.resolve(), output.resolve()
    if output.exists():
        raise ValueError("Preparation output must be new")
    output.mkdir(parents=True)
    shutil.copy2(__file__, output / Path(__file__).name)
    archive_bytes = subprocess.check_output(["git", "archive", COMMIT, "autofix"], cwd=repo)
    archive = output / "private_archive"
    archive.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive_bytes)) as handle:
        for member in handle.getmembers():
            if member.issym() or member.islnk() or not (archive / member.name).resolve().is_relative_to(archive):
                raise ValueError("Unsafe archive member")
        handle.extractall(archive)
    fixtures = output / "private_fixtures"
    subprocess.run([sys.executable, str(Path(__file__).resolve()), "extract", "--repo", str(archive),
                    "--output", str(fixtures)], check=True)
    sys.path.insert(0, str(control / "code_snapshot"))
    from autofix.autonomous.fixed50 import split_candidate, _driver_text, Fixed50Evaluator, IDENTITY, FORBIDDEN
    control_manifest = json.loads((control / "manifest.json").read_text())
    method = "autonomous_layered"
    rows = []
    base_inputs = output / "inputs"
    private_cases = output / "private_cases"
    for repeat in range(4):
        for fault in FAULTS:
            index = len(rows) + 1
            task = f"task_{index:03d}"
            original = json.loads((fixtures / fault / "original.json").read_text())
            case_dir = private_cases / task
            case_dir.mkdir(parents=True)
            checks, candidates, private_text = {}, {}, None
            for mode in ("healthy", "faulty"):
                source = (fixtures / fault / (mode + ".py")).read_text()
                visible, hidden, relocations = split_candidate(source)
                if private_text is not None and hidden != private_text:
                    raise ValueError("The mutation changed the private predicate")
                private_text = hidden
                public = case_dir / mode
                public.mkdir()
                (public / "candidate.py").write_text(visible)
                # The original fixtures use PyTorch directly. This copied library
                # provides equal tools/file scope but is not claimed as exercised.
                shutil.copytree(control / "private_inputs/task_001/torch4ms", public / "torch4ms")
                dump(public / "task.json", {"task_kind": "library_unit_repair", "tests": ["public"],
                    "editable": ["candidate.py", "torch4ms/**/*.py"], "runtime": "PyTorch synthetic fixture",
                    "contract": "Preserve the public interfaces and intended computation. Public tests report available measured observations. Source reference is not supplied."})
                driver = _driver_text(hidden, "legacy_candidate", original["case"], "")
                (case_dir / "probe.py").write_text(driver)
                evaluator = Fixed50Evaluator(public, case_dir, Path(sys.executable), case_dir / (mode + "_preflight"))
                result = evaluator.paired()
                checks[mode] = {"original_accepted": original["results"][mode]["passed"],
                                "isolated_accepted": result["accepted"], "observation": result["observation"]}
                candidates[mode] = sha(public / "candidate.py")
            valid = (checks["healthy"]["original_accepted"] and checks["healthy"]["isolated_accepted"]
                     and not checks["faulty"]["original_accepted"] and not checks["faulty"]["isolated_accepted"])
            if not valid:
                dump(case_dir / "preflight_failed.json", checks)
                raise RuntimeError("Original and isolated fixture preflight failed: " + task)
            shutil.copytree(case_dir / "faulty", base_inputs / task)
            for path in (base_inputs / task).rglob("*.py"):
                if IDENTITY.search(path.read_text()) or FORBIDDEN.search(path.read_text()):
                    raise ValueError("Private identity in public input: " + str(path))
            rows.append({"anonymous_id": task, "status": "ready", "private_fixture": fault,
                         "repetition": repeat + 1, "preflight": checks, "candidate_hashes": candidates,
                         "probe_sha256": sha(case_dir / "probe.py")})
    manifest_hashes = {}
    for variant in VARIANTS:
        run = output / variant
        run.mkdir()
        shutil.copytree(base_inputs, run / "private_inputs")
        (run / "private_cases").mkdir()
        for row in rows:
            case = run / "private_cases" / row["anonymous_id"]
            case.mkdir()
            shutil.copy2(private_cases / row["anonymous_id"] / "probe.py", case / "probe.py")
        shutil.copytree(control / "code_snapshot", run / "code_snapshot",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        manifest = {**control_manifest, "tasks": rows, "methods": [method],
                    "benchmark": "fixed50_original", "study": "legacy_signal_three_fixtures_four_repeats",
                    "signal_variant": variant, "acceptance": "unchanged_original_fixture_predicate",
                    "signal_controller": "available observed checks control stopping; final scoring uses full original predicate"}
        dump(run / "manifest.json", manifest)
        hashes = {str(p.relative_to(run)): sha(p) for folder in ("private_inputs", "private_cases", "code_snapshot")
                  for p in (run / folder).rglob("*") if p.is_file()}
        dump(run / "frozen_hashes.json", hashes)
        manifest_hashes[variant] = sha(run / "manifest.json")
    plan = {"variants": VARIANTS, "tasks": rows, "condition_count": 36,
            "original_commit": COMMIT, "source_archive_sha256": hashlib.sha256(archive_bytes).hexdigest(),
            "runner_sha256": sha(output / Path(__file__).name), "variant_manifest_sha256": manifest_hashes,
            "four_model_claim": False, "reference_control_manifest_sha256": sha(control / "manifest.json")}
    dump(output / "plan.json", plan)
    return {"prepared": 36, "preflight_valid": len(rows), "runner_sha256": plan["runner_sha256"]}


def verify(run):
    plan = json.loads((run.parent / "plan.json").read_text())
    if sha(Path(__file__)) != plan["runner_sha256"] or sha(run / "manifest.json") != plan["variant_manifest_sha256"][run.name]:
        raise RuntimeError("Frozen runner or manifest changed")
    hashes = json.loads((run / "frozen_hashes.json").read_text())
    for relative, expected in hashes.items():
        if sha(run / relative) != expected:
            raise RuntimeError("Frozen input/code changed: " + relative)


def score_result(result, variant):
    result["controller_accepted"] = result["accepted"]
    result["initially_accepted_by_available_checks"] = result.get("initially_accepted")
    if "final" in result:
        result["accepted"] = result["final"]["full_evaluation"]["accepted"]
        result["initially_accepted"] = result["initial"]["full_evaluation"]["accepted"]
        for attempt in result["attempts"]:
            attempt["controller_accepted"] = attempt["accepted"]
            attempt["accepted"] = attempt["evaluation"]["full_evaluation"]["accepted"]
    result["signal_variant"] = variant
    return result


def worker(run, task):
    verify(run)
    sys.path.insert(0, str(run / "code_snapshot"))
    from autofix.autonomous import experiment
    variant = json.loads((run / "manifest.json").read_text())["signal_variant"]
    original_factory = experiment.evaluator_for
    class MaskedEvaluator:
        def __init__(self, base):
            self.base = base
        def paired(self, **kwargs):
            full = self.base.paired(**kwargs)
            observation = mask_observation(full["observation"], variant)
            return {**full, "accepted": observation["accepted"], "observation": observation,
                    "full_evaluation": full}
        def tool(self, request):
            if request["test"] in ("public", "paired"):
                return self.paired(timeout=min(180, float(request.get("timeout_seconds", 180))))["observation"]
            return self.base.tool(request)
        def confirm(self):
            return []
    experiment.evaluator_for = lambda *args: MaskedEvaluator(original_factory(*args))
    result = experiment.run_condition(run, task, "autonomous_layered", Path(sys.executable))
    score_result(result, variant)
    dump(run / "conditions" / task / "autonomous_layered/result.json", result)
    return result


def dispatch(output, workers):
    if not 1 <= workers <= 4:
        raise ValueError("Use one to four coordinated workers")
    lock = (output / "dispatch.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    plan = json.loads((output / "plan.json").read_text())
    grid = [(row["anonymous_id"], variant) for row in plan["tasks"] for variant in VARIANTS]
    for variant in VARIANTS:
        verify(output / variant)
        if (output / variant / "conditions").exists():
            raise RuntimeError("Refusing to overwrite or silently resume")
    sys.path.insert(0, str(output / VARIANTS[0] / "code_snapshot"))
    from autofix.autonomous.batch import finalize_worker
    pending, completed, blockers = list(grid), [], []
    def one(pair):
        task, variant = pair
        run = output / variant
        (run / "worker_logs").mkdir(exist_ok=True)
        with (run / "worker_logs" / (task + ".log")).open("w") as log:
            proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "worker", "--output", str(run),
                                   "--task", task], cwd=run / "code_snapshot", stdout=log, stderr=subprocess.STDOUT)
        return {**finalize_worker(run, task, "autonomous_layered", proc.returncode), "variant": variant}
    with ThreadPoolExecutor(max_workers=workers) as executor:
        active = set()
        while pending or active:
            blockers = [str(p) for p in output.glob("*/conditions/*/*/evidence/agent/call_*_error.json")
                        if any("HTTP " + str(code) in p.read_text() for code in (401, 402, 403))]
            while pending and len(active) < workers and not blockers:
                active.add(executor.submit(one, pending.pop(0)))
            if not active:
                break
            done, active = wait(active, timeout=1, return_when=FIRST_COMPLETED)
            for future in done:
                row = future.result()
                completed.append({key: row.get(key) for key in ("task", "variant", "status", "accepted")})
                dump(output / "progress.json", {"planned": 36, "completed": completed})
    dump(output / "dispatch_result.json", {"not_started": pending, "blockers": blockers, "completed": len(completed)})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("extract", "prepare", "dispatch", "worker"))
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--control", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--task")
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    if args.action == "extract":
        extract(args.repo, args.output)
    elif args.action == "prepare":
        print(json.dumps(prepare(args.repo, args.control, args.output)))
    elif args.action == "worker":
        worker(args.output.resolve(), args.task)
    else:
        dispatch(args.output.resolve(), args.workers)


if __name__ == "__main__":
    main()
