"""Run isolated component controls against an existing frozen autonomous run.

The source run is read-only. Each treatment gets a complete copied input and
code snapshot; the subclass below changes one public agent component only.
"""
from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait


VARIANTS = ("continuous_role", "without_repair_history", "without_progress_prompt",
            "without_edit_format_feedback")


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def transport_blockers(output):
    blockers = []
    for path in output.glob("*/conditions/*/*/evidence/agent/call_*_error.json"):
        value = json.loads(path.read_text())
        status = value.get("http_status")
        if status not in (401, 402, 403):
            match = re.search(r"HTTP (401|402|403)\b", str(value.get("error", "")))
            status = int(match.group(1)) if match else None
        if status:
            blockers.append({"http_status": status, "evidence": str(path.relative_to(output))})
    return blockers


def verify_frozen(run):
    plan = json.loads((run.parent / "plan.json").read_text())
    if sha(Path(__file__)) != plan["runner_sha256"]:
        raise RuntimeError("Frozen runner changed")
    if sha(run / "manifest.json") != plan["variant_manifest_sha256"][run.name]:
        raise RuntimeError("Frozen manifest changed")
    hashes = json.loads((run / "frozen_hashes.json").read_text())
    for relative, expected in hashes.items():
        path = run / relative
        if path.is_symlink() or sha(path) != expected:
            raise RuntimeError("Frozen input/code changed: " + relative)
    actual = {str(path.relative_to(run)) for folder in ("private_inputs", "private_cases", "code_snapshot")
              for path in (run / folder).rglob("*") if path.is_file()
              and path.suffix != ".pyc" and "__pycache__" not in path.parts}
    if actual != set(hashes):
        raise RuntimeError("Frozen input/code file inventory changed")


def agent_class(base, variant):
    if variant not in VARIANTS:
        raise ValueError("Unknown component control")

    class ComponentAgent(base):
        def _handoff_to_fixer(self):
            if variant != "continuous_role":
                result = super()._handoff_to_fixer()
                if variant == "without_repair_history":
                    old = "Your conversation persists across repair attempts."
                    new = ("Each repair attempt starts from the initial verifier investigation and the latest observation. "
                           "Earlier repair conversations are not retained; the current workspace is retained.")
                    system = self.history[0]
                    if system["role"] != "system" or system["content"].count(old) != 1:
                        raise RuntimeError("Expected history statement changed; refusing an inaccurate ablation")
                    system["content"] = system["content"].replace(old, new)
                    self._event("ablation_history_contract", {"conversation_reset": True,
                                "workspace_retained": True, "lifetime_budget_reset": False})
                    self._snapshot()
                return result
            # Preserve the original investigator's conversation and system
            # instructions, instead of reconstructing an independent role.
            self.verifier_history = copy.deepcopy(self.history)
            self.active_role = "continuous_agent"
            self._event("ablation_continuous_role", {
                "history_preserved": True, "independent_role_handoff": False})
            self._snapshot()

        def repair(self, observation, attempt=1):
            if variant == "without_repair_history":
                if not hasattr(self, "ablation_initial_handoff"):
                    self._handoff_to_fixer()
                    self.ablation_initial_handoff = copy.deepcopy(self.history)
                    self.ablation_handoff_records = copy.deepcopy(self.handoff_tool_records)
                    self.ablation_initial_diagnosis = copy.deepcopy(self.last_diagnosis)
                elif attempt > 1:
                    self.history = copy.deepcopy(self.ablation_initial_handoff)
                    self.handoff_tool_records = copy.deepcopy(self.ablation_handoff_records)
                    self.last_diagnosis = copy.deepcopy(self.ablation_initial_diagnosis)
                    self._event("ablation_history_reset", {
                        "attempt": attempt, "preserved": "initial verifier handoff and current workspace",
                        "removed": "prior repair conversations and reported hypotheses",
                        "lifetime_budget_reset": False})
            return super().repair(observation, attempt=attempt)

        def _event(self, kind, value):
            if variant == "without_progress_prompt" and kind == "stage_progress_checkpoint":
                expected = {"role": "user", "content": value["feedback"]}
                if self.history[-1] != expected:
                    raise RuntimeError("Progress prompt insertion changed; refusing an invalid ablation")
                self.history.pop()
                return super()._event("ablation_progress_prompt_omitted", value)
            return super()._event(kind, value)

        def _stage_tool_schemas(self, *, readonly):
            if variant == "without_edit_format_feedback":
                return self.tools.schemas(readonly=readonly)
            return super()._stage_tool_schemas(readonly=readonly)

        def _edit_format_feedback(self, arguments, error):
            if variant == "without_edit_format_feedback":
                self._event("ablation_edit_format_feedback_omitted", {"error": error})
                return None
            return super()._edit_format_feedback(arguments, error)

    return ComponentAgent


def prepare(source, output, variants):
    source, output = source.resolve(), output.resolve()
    if output.exists() or output.is_relative_to(source):
        raise ValueError("Output must be a new independent directory")
    manifest = json.loads((source / "manifest.json").read_text())
    if manifest["model"] != "deepseek-v4-flash":
        raise ValueError("Only the frozen current DeepSeek configuration is allowed")
    method = "autonomous_layered"
    if manifest.get("workflow_policy", {}).get(method) != "progress_loop":
        raise ValueError("Controls require the v4 progress_loop snapshot")
    if manifest.get("memory_policy", {}).get(method) != "evidence":
        raise ValueError("Controls require the v4 evidence-memory configuration")
    snapshot = source / "code_snapshot"
    source_hashes = {str(p.relative_to(snapshot)): sha(p) for p in snapshot.rglob("*.py")}
    if not source_hashes:
        raise ValueError("Source code snapshot is missing")
    output.mkdir(parents=True)
    shutil.copy2(__file__, output / "run_maintext_ablations.py")
    plan = {"source_run": str(source), "source_manifest_sha256": sha(source / "manifest.json"),
            "source_code_sha256": source_hashes, "variants": list(variants),
            "condition_count": len(variants) * len(manifest["tasks"]),
            "selection": "all tasks; no selection by outcome", "control": "progress_v4/autonomous_layered",
            "model": manifest["model"], "max_repair_attempts": manifest.get("max_repair_attempts", 4),
            "runner_sha256": sha(output / "run_maintext_ablations.py"), "variant_manifest_sha256": {}}
    for variant in variants:
        target = output / variant
        target.mkdir()
        for name in ("private_inputs", "private_cases", "code_snapshot"):
            if (source / name).exists():
                shutil.copytree(source / name, target / name,
                                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        changed = copy.deepcopy(manifest)
        changed["methods"] = [method]
        changed["ablation"] = {"variant": variant, "source_run": str(source),
                               "source_manifest_sha256": plan["source_manifest_sha256"]}
        write_json(target / "manifest.json", changed)
        plan["variant_manifest_sha256"][variant] = sha(target / "manifest.json")
        hashes = {}
        for folder in ("private_inputs", "private_cases", "code_snapshot"):
            for path in sorted((target / folder).rglob("*")):
                if not path.is_file():
                    continue
                rel = path.relative_to(target)
                if sha(path) != sha(source / rel):
                    raise RuntimeError("Copied frozen input/code changed: " + str(rel))
                hashes[str(rel)] = sha(path)
        write_json(target / "frozen_hashes.json", hashes)
    write_json(output / "plan.json", plan)
    return plan


def worker(run, task):
    verify_frozen(run)
    sys.path.insert(0, str(run / "code_snapshot"))
    from autofix.autonomous import agent, experiment
    manifest = json.loads((run / "manifest.json").read_text())
    agent.AutonomousAgent = agent_class(agent.AutonomousAgent, manifest["ablation"]["variant"])
    return experiment.run_condition(run, task, "autonomous_layered", Path(sys.executable))


def dispatch(output, workers):
    lock = (output / "dispatch.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    plan = json.loads((output / "plan.json").read_text())
    if sha(Path(__file__)) != plan["runner_sha256"]:
        raise RuntimeError("Run only the frozen runner")
    first = output / plan["variants"][0]
    sys.path.insert(0, str(first / "code_snapshot"))
    from autofix.autonomous.batch import finalize_worker
    grid = []
    tasks = json.loads((first / "manifest.json").read_text())["tasks"]
    for row in tasks:
        for variant in plan["variants"]:
            run = output / variant
            if (run / "conditions" / row["anonymous_id"]).exists():
                raise RuntimeError("Refusing to overwrite or silently resume a condition")
            grid.append((row["anonymous_id"], variant))
    for variant in plan["variants"]:
        verify_frozen(output / variant)

    def one(pair):
        task, variant = pair
        run = output / variant
        logs = run / "worker_logs"
        logs.mkdir(exist_ok=True)
        with (logs / (task + ".log")).open("w") as stream:
            result = subprocess.run([sys.executable, str(Path(__file__).resolve()), "worker",
                                     "--output", str(run), "--task", task],
                                    stdout=stream, stderr=subprocess.STDOUT,
                                    cwd=run / "code_snapshot", env=os.environ.copy())
        return {**finalize_worker(run, task, "autonomous_layered", result.returncode), "variant": variant}

    completed = []
    def finished(result):
        completed.append({k: result.get(k) for k in ("task", "method", "variant", "status", "accepted")})
        write_json(output / "progress.json", {"planned": len(grid), "completed": completed})

    if not 1 <= workers <= 4:
        raise ValueError("workers must be between one and four")
    slots_path = output / "worker_slots.json"
    write_json(slots_path, {"workers": workers})
    pending, started, blockers = list(grid), [], []
    with ThreadPoolExecutor(max_workers=4) as executor:
        active = set()
        while pending or active:
            blockers = transport_blockers(output)
            slots = json.loads(slots_path.read_text())["workers"]
            if type(slots) is not int or not 1 <= slots <= 4:
                raise ValueError("Invalid worker slot allocation")
            while pending and len(active) < slots and not blockers:
                pair = pending.pop(0)
                started.append(pair)
                active.add(executor.submit(one, pair))
            if not active:
                break
            done, active = wait(active, timeout=1, return_when=FIRST_COMPLETED)
            for future in done:
                finished(future.result())
    write_json(output / "dispatch_result.json", {
        "started": started, "not_started": pending, "blocking_errors": blockers})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "dispatch", "worker"))
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--variants", nargs="+", choices=VARIANTS, default=list(VARIANTS))
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--task")
    args = parser.parse_args()
    if args.action == "prepare":
        print(json.dumps(prepare(args.source, args.output, args.variants), indent=2))
    elif args.action == "worker":
        worker(args.output.resolve(), args.task)
    else:
        dispatch(args.output.resolve(), args.workers)


if __name__ == "__main__":
    main()
