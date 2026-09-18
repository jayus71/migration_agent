"""Frozen six-task JAX evaluation using the v4 autonomous workflow.

The historical candidate mutations and backend are loaded from a fixed commit.
Only public runtime naming changes in the agent prompts. Reference execution,
injection code, labels and run history remain outside repair workspaces.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

REVISION = "3352f719636d0fd9eda6dcff2dc4578863ab542e"
SEEDS = (6701, 6702, 6703)
METHODS = ("autonomous_layered", "direct_shared_tools")
TASKS = [(model, fault) for model in ("mlp", "cnn") for fault in ("EX-01", "NU-01", "GR-01")]


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_text(repo, name):
    return subprocess.check_output(["git", "show", REVISION + ":" + name], cwd=repo, text=True)


def strip_reference(text):
    tree = ast.parse(text)
    tree.body = [node for node in tree.body if not isinstance(node, ast.FunctionDef) or node.name != "_reference_model"]
    return ast.unparse(tree) + "\n"


def source_program(text, model):
    node = next(n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == "_reference_model")
    return ast.unparse(node) + f"\n\ndef build_model():\n    return _reference_model({model!r})\n"


def prepare(repo, base, output):
    if output.exists():
        raise ValueError("Output already exists")
    manifest = json.loads((base / "manifest.json").read_text())
    if manifest["model"] != "deepseek-v4-flash" or manifest["workflow_policy"]["autonomous_layered"] != "progress_loop":
        raise ValueError("Expected frozen v4 DeepSeek evidence reference")
    output.mkdir(parents=True)
    shutil.copytree(base / "code_snapshot", output / "code_snapshot", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy2(__file__, output / "runner.py")
    historical = output / "private_backend"
    historical.mkdir()
    for name in ("autofix/backends/torchax_backend.py", "autofix/backends/track_c_external.py", "autofix/faults/torchax_candidate.py", "autofix/agents/fixer_torchax.py", "experiments/paper_section_67/run_track_c_baselines.py"):
        (historical / Path(name).name).write_text(git_text(repo, name))
    backend = (historical / "torchax_backend.py").read_text()
    public_backend = output / "public_backend"
    (public_backend / "autofix" / "backends").mkdir(parents=True)
    for package in (public_backend / "autofix", public_backend / "autofix" / "backends"):
        (package / "__init__.py").write_text("")
    worker = public_backend / "autofix/backends/torchax_backend.py"
    worker.write_text(strip_reference(backend))
    shutil.copy2(historical / "track_c_external.py", public_backend / "autofix/backends/track_c_external.py")
    (public_backend / "worker.py").write_text(
        "import os, runpy, sys\nfrom pathlib import Path\n"
        "sys.path.insert(0, str(Path(__file__).resolve().parent))\n"
        "os.environ['PATH'] = str(Path(sys.executable).resolve().parent) + ':' + os.environ['PATH']\n"
        "os.environ['HOME'] = os.environ['TMPDIR']\n"
        "os.environ['XDG_CACHE_HOME'] = os.environ['TMPDIR']\n"
        "ivy_root = Path(os.environ['TMPDIR']) / '.ivy'\n"
        "ivy_root.mkdir(exist_ok=True)\n"
        "os.environ['IVY_ROOT'] = str(ivy_root)\n"
        "os.chdir(os.environ['TMPDIR'])\n"
        "module = sys.argv.pop(1)\nrunpy.run_module(module, run_name='__main__')\n")
    namespace = {}
    exec(compile((historical / "torchax_candidate.py").read_text(), "frozen_faults", "exec"), namespace)
    rows = []
    for index, (model, fault) in enumerate(TASKS, 1):
        task = f"task_{index:03d}"
        target = output / "private_inputs" / task
        target.mkdir(parents=True)
        candidate = namespace["mutate_source"](fault, namespace["healthy_source"](model))
        (target / "candidate.py").write_text(candidate)
        (target / "source.py").write_text(source_program(backend, model))
        dump(target / "task.json", {"target_backend": "TorchAX/JAX", "model": model,
             "candidate_entry": "build_model", "batch_entry": "prepare_batch",
             "evaluation": "One SGD training step with cross-entropy loss, learning rate 0.01; three independent seeds.",
             "thresholds": {"loss_abs": .02, "grad_norm_abs": .05, "param_update_rel_l2": .03},
             "repair_scope": "candidate.py; source.py and task.json are immutable. scratch_tests/*.py may be created.",
             "backend_requirement": "Target forward, gradients and parameter updates must execute through TorchAX/JAX."})
        rows.append({"anonymous_id": task, "original_id": f"TC-{model.upper()}-{fault[:2]}", "model": model,
                     "fault": fault, "candidate_sha256": sha(target / "candidate.py"), "source_sha256": sha(target / "source.py")})
    manifest.update({"benchmark": "track_c_six_autonomous", "tasks": rows, "methods": list(METHODS),
                     "max_repair_attempts": 4, "original_task_revision": REVISION,
                     "base_manifest_sha256": sha(base / "manifest.json"), "base_run": str(base),
                     "selection": "All six historical JAX tasks; no outcome selection",
                     "no_fault_injection": False, "translation_reused": False,
                     "prompt_integration": "Replace torch4ms/MindSpore with TorchAX/JAX in migration prompt constants only",
                     "acceptance": {"loss_abs": .02, "grad_norm_abs": .05, "param_update_rel_l2": .03,
                                    "backend_required": True, "strict_seeds": list(SEEDS)}})
    manifest["workflow_policy"] = {"autonomous_layered": "progress_loop", "direct_shared_tools": "standard"}
    manifest["memory_policy"] = {"autonomous_layered": "evidence", "direct_shared_tools": "native"}
    manifest["diagnosis_policy"] = {method: "evidence" for method in METHODS}
    for key in ("adapter_archive_sha256", "development"):
        manifest.pop(key, None)
    manifest["study"] = "Six-task autonomous JAX generalization rerun"
    manifest["protocol_version"] = "maintext-jax-autonomous-v1"
    manifest["method_protocols"] = {key: value for key, value in manifest["method_protocols"].items() if key in METHODS}
    dump(output / "manifest.json", manifest)
    hashes = {str(p.relative_to(output)): sha(p) for p in output.rglob("*") if p.is_file()}
    dump(output / "frozen_hashes.json", hashes)
    return {"conditions": len(rows) * len(METHODS), "manifest": manifest}


def verify_frozen(run):
    hashes = json.loads((run / "frozen_hashes.json").read_text())
    for name, expected in hashes.items():
        if sha(run / name) != expected:
            raise RuntimeError("Frozen input changed: " + name)


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def measurements(reference, target):
    values = {"loss_abs": None, "grad_norm_abs": None, "param_update_rel_l2": None}
    if reference.get("status") != "ok" or target.get("status") != "ok":
        return values
    if finite(reference.get("loss")) and finite(target.get("loss")):
        values["loss_abs"] = abs(reference["loss"] - target["loss"])
    if finite(reference.get("grad_norm")) and finite(target.get("grad_norm")):
        values["grad_norm_abs"] = abs(reference["grad_norm"] - target["grad_norm"])
    left, right = reference.get("update_by_name", {}), target.get("update_by_name", {})
    if left and left.keys() == right.keys() and all(len(left[k]) == len(right[k]) for k in left):
        a = [v for k in sorted(left) for v in left[k]]
        b = [v for k in sorted(right) for v in right[k]]
        if all(finite(v) for v in a + b):
            values["param_update_rel_l2"] = math.sqrt(sum((x-y)**2 for x,y in zip(a,b))) / max(math.sqrt(sum(x*x for x in a)), 1e-12)
    return values


class JaxEvaluator:
    def __init__(self, run, task, workspace, evidence, python, backend="torchax"):
        self.run, self.task, self.workspace, self.evidence, self.python = run, task, workspace, evidence, python
        self.params = json.loads((workspace / "task.json").read_text())
        self.backend, self.calls = backend, 0
        self.immutable = {name: sha(workspace / name) for name in ("source.py", "task.json")}

    def paired(self, seed=None, timeout=180):
        from autofix.autonomous.sandbox import run_isolated
        seed = SEEDS[0] if seed is None else seed
        self.calls += 1
        folder = self.evidence / f"measurement_{self.calls:04d}"
        folder.mkdir(parents=True)
        module = "autofix.backends.torchax_backend" if self.backend == "torchax" else "autofix.backends.track_c_external"
        # Backend code is public runtime code with the healthy target removed.
        script = self.run / "public_backend/worker.py"
        args = [module, "--mode", self.backend, "--model", self.params["model"], "--candidate", str(self.workspace / "candidate.py"), "--seed", str(seed), "--lr", "0.01"]
        proc = run_isolated(self.workspace, self.python, script, timeout=timeout,
                            extra_reads=[str(self.run / "public_backend"), str(self.python.resolve().parent.parent)], args=args)
        dump(folder / "process.json", proc)
        try:
            target = json.loads(proc["stdout"].strip().splitlines()[-1])
        except (ValueError, IndexError):
            target = {"status": "failed", "error": proc["stdout"][-10000:], "error_type": "WorkerProcessError"}
        reference = json.loads((self.run / "private_reference" / self.params["model"] / f"{seed}.json").read_text())
        values = measurements(reference, target)
        backend = target.get("backend_evidence", {}).get("is_jax_array") is True
        execution = proc["returncode"] == 0 and target.get("status") == "ok"
        unchanged = all(sha(self.workspace / name) == digest for name, digest in self.immutable.items())
        thresholds = self.params["thresholds"]
        checks = {name: finite(v) and v <= thresholds[name] for name, v in values.items()}
        accepted = execution and backend and unchanged and all(checks.values())
        error = str(target.get("error", "")).replace(str(self.workspace), ".").replace(str(self.run), "verification")
        observation = {"execution": {"status": "ok" if execution else "failed", "error_type": target.get("error_type"), "message": error},
                       "measurements": {k: {"value": v, "threshold": thresholds[k], "status": "observed" if finite(v) else "unavailable"} for k,v in values.items()},
                       "target_backend_observed": backend, "source_immutable": unchanged,
                       "acceptance": {"accepted": accepted, "checks": checks},
                       "scope": "one SGD training step"}
        result = {"accepted": accepted, "observation": observation, "seed": seed, "measurement": str(folder)}
        dump(folder / "raw_target.json", target)
        dump(folder / "observation.json", result)
        return result

    def confirm(self):
        return [self.paired(seed=seed) for seed in SEEDS[1:]]

    def tool(self, request):
        if request["test"] in ("paired", "public"):
            return self.paired(timeout=min(180, request.get("timeout_seconds", 180)))["observation"]
        from autofix.autonomous.sandbox import run_isolated
        path = (self.workspace / request["test"]).resolve()
        if not path.is_relative_to(self.workspace / "scratch_tests") or path.suffix != ".py":
            raise ValueError("Only scratch tests may execute")
        proc = run_isolated(self.workspace, self.python, path, timeout=min(120, request.get("timeout_seconds", 120)))
        self.calls += 1
        dump(self.evidence / f"scratch_{self.calls:04d}.json", proc)
        return {**proc, "stdout": proc["stdout"][:16000]}


def runtime(run):
    sys.path.insert(0, str(run / "code_snapshot"))
    from autofix.autonomous import agent, experiment
    for name in ("SYSTEM_PROMPT", "FIXER_PROMPT", "EVIDENCE_SYSTEM_PROMPT", "EVIDENCE_FIXER_PROMPT"):
        setattr(agent, name, getattr(agent, name).replace("torch4ms/MindSpore", "TorchAX/JAX"))
    experiment.evaluator_for = lambda output, task, workspace, evidence, python, manifest: JaxEvaluator(output, task, workspace, evidence, python)
    return experiment


def preflight(run, python):
    verify_frozen(run)
    experiment = runtime(run)
    for model in ("mlp", "cnn"):
        for seed in SEEDS:
            path = run / "private_reference" / model / f"{seed}.json"
            if path.exists():
                continue
            proc = subprocess.run([str(python), str(run / "private_backend/torchax_backend.py"), "--mode", "torch", "--model", model,
                "--candidate", "/nonexistent", "--seed", str(seed), "--lr", "0.01"], capture_output=True, text=True,
                env={"PATH": str(python.parent) + ":/usr/bin:/bin", "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"}, timeout=180)
            value = json.loads(proc.stdout.strip().splitlines()[-1])
            if value.get("status") != "ok":
                raise RuntimeError("Reference runtime failed: " + str(value))
            dump(path, value)
    results = experiment.preflight(run, python)
    if len(results) != 6 or any(row["accepted"] for row in results):
        raise RuntimeError("Original six injected faults did not all trigger")
    # Confirm that the unchanged historical healthy candidates are measurable.
    namespace = {}
    exec((run / "private_backend/torchax_candidate.py").read_text(), namespace)
    clean = []
    for model in ("mlp", "cnn"):
        task = "task_001" if model == "mlp" else "task_004"
        workspace, evidence = experiment.workspace_for(run, task, "healthy_control")
        (workspace / "candidate.py").write_text(namespace["healthy_source"](model))
        evaluator = JaxEvaluator(run, task, workspace, evidence, python)
        clean.extend([evaluator.paired(seed=seed) for seed in SEEDS])
    dump(run / "healthy_controls.json", clean)
    if not all(row["accepted"] for row in clean):
        raise RuntimeError("Historical healthy target failed preflight")
    return {"faults_triggered": len(results), "healthy_checks_passed": len(clean)}


def converters(run):
    verify_frozen(run)
    experiment = runtime(run)
    namespace = {}
    exec((run / "private_backend/torchax_candidate.py").read_text(), namespace)
    rows = []
    for backend, python in (("ivy", Path("/media/main/whj/venvs/trackc_ivy/bin/python")),
                             ("torch2jax", Path("/media/main/whj/miniconda3/envs/torchax311/bin/python"))):
        gates = {}
        for model, task in (("mlp", "task_001"), ("cnn", "task_004")):
            workspace, evidence = experiment.workspace_for(run, task, backend + "_clean_gate")
            (workspace / "candidate.py").write_text(namespace["healthy_source"](model))
            gates[model] = JaxEvaluator(run, task, workspace, evidence, python, backend).paired()
        for index, (model, fault) in enumerate(TASKS, 1):
            task = f"task_{index:03d}"
            started = time.monotonic()
            if not gates[model]["accepted"]:
                error = gates[model]["observation"]["execution"].get("error_type")
                status = "infrastructure_error" if error in ("WorkerProcessError", "TimeoutExpired", "ModuleNotFoundError", "ImportError", "FileNotFoundError", "PermissionError") else "unsupported"
                row = {"task": task, "method": backend, "status": status, "accepted": None,
                       "reason": "Native converter failed historical healthy-candidate clean gate", "clean_gate": gates[model]}
            else:
                workspace, evidence = experiment.workspace_for(run, task, backend)
                evaluator = JaxEvaluator(run, task, workspace, evidence, python, backend)
                value = evaluator.paired()
                confirmation = evaluator.confirm() if value["accepted"] else []
                row = {"task": task, "method": backend, "status": "completed", "accepted": value["accepted"] and all(x["accepted"] for x in confirmation),
                       "evaluation": value, "confirmation": confirmation}
            row.update({"wall_time_sec": time.monotonic() - started, "llm_calls": 0, "llm_tokens": 0})
            rows.append(row)
            dump(run / "converter_results.json", rows)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "preflight", "worker", "converters"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-repo", type=Path)
    parser.add_argument("--base-run", type=Path)
    parser.add_argument("--task")
    parser.add_argument("--method", choices=METHODS)
    args = parser.parse_args()
    run = args.output.resolve()
    if args.action == "prepare":
        result = prepare(args.source_repo, args.base_run, run)
    elif args.action == "preflight":
        result = preflight(run, Path(sys.executable))
    elif args.action == "converters":
        result = converters(run)
    else:
        verify_frozen(run)
        if not (run / "healthy_controls.json").exists():
            raise RuntimeError("Successful preflight required")
        result = runtime(run).run_condition(run, args.task, args.method, Path(sys.executable))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
