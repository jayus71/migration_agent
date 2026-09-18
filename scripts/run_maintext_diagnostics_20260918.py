"""Replay the archived main-text diagnostic protocol with runtime evidence."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tarfile
import time
import math


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def summarize(out):
    """Recompute counts and latency from individual measured trajectories."""
    out = Path(out)
    limits = {"loss_abs_diff": 0.02, "grad_norm_abs_diff": 0.05, "param_update_rel_l2": 0.03}
    runtime = json.loads((out / "runtime_backend.json").read_text())
    result = {"studies": {}, "backend": {}, "figure1": {}}
    result["backend"] = {
        "recorded_runs": len(runtime),
        "target_forward_steps": sum(s["target_forward_tensor"] for r in runtime for s in r["steps"]),
        "observed_backward_steps": sum(s["observed"] for r in runtime for s in r["steps"]),
        "unexpected_missing_backward": [{k: r[k] for k in ("model", "seed", "coupling", "fault")}
            for r in runtime if r["fault"] != "training" and any(not s["observed"] for s in r["steps"])],
    }
    for study in ("experiment_c", "diagnostic_three_classes"):
        raw = json.loads((out / study / "section65_per_step_divergence_raw_steps50.json").read_text())
        counts = {}
        for fault in raw["faults"]:
            for coupling in raw["couplings"]:
                runs = [r for r in raw["runs"] if r["fault"] == fault and r["coupling"] == coupling]
                detected = 0
                intended = 0
                passed = 0
                for run in runs:
                    rows = run["steps"]
                    execution_failure = run["torch4ms_status"] != "ok"
                    failing = any(row.get(field) is None or not math.isfinite(row[field]) or row[field] > limit
                                  for row in rows for field, limit in limits.items())
                    detected += bool(execution_failure or failing)
                    passed += bool(not execution_failure and not failing and len(rows) == raw["steps"])
                    field = {"numeric": "loss_abs_diff", "grad_wrong": "grad_norm_abs_diff",
                             "param_wrong": "param_update_rel_l2", "training": "param_update_rel_l2"}.get(fault)
                    if fault == "execution":
                        intended += execution_failure and run.get("torch4ms_failed_step") == 20
                    elif field:
                        intended += not execution_failure and any(row[field] is not None and row[field] > limits[field] for row in rows)
                counts[f"{coupling}/{fault}"] = {"runs": len(runs), "all_step_pass": passed, "detected": detected,
                                                  "intended_signal_detected": intended if fault != "none" else None}
        result["studies"][study] = {"counts": counts, "self_checks": raw["self_checks"]}
        if study == "experiment_c":
            for fault, signal in (("grad_wrong", "grad_norm_abs_diff"), ("param_wrong", "param_update_rel_l2")):
                runs = [r for r in raw["runs"] if r["fault"] == fault and r["coupling"] == "free-running"]
                def first(rows, field):
                    return next((r["step"] for r in rows if r[field] is not None and r[field] > limits[field]), None)
                mean_rows = []
                for step in range(raw["steps"]):
                    values = [r["steps"][step]["loss_abs_diff"] for r in runs]
                    mean_rows.append({"step": step + 1, "loss_abs_diff": sum(values) / len(values) if all(v is not None for v in values) else None})
                result["figure1"][fault] = {"runs": len(runs), "signal_first_steps": [first(r["steps"], signal) for r in runs],
                    "loss_first_steps": [first(r["steps"], "loss_abs_diff") for r in runs],
                    "mean_loss_first_step": first(mean_rows, "loss_abs_diff")}
    write(out / "analysis.json", result)
    paper = Path(__file__).resolve().parents[1]
    archived_c = paper / "data/experiments/03_experiment_C_gradient_and_parameter_faults/results_per_step/section65_per_step_divergence_steps50.csv"
    if archived_c.exists() and (out / "experiment_c/section65_per_step_divergence_steps50.csv").exists():
        comparison = {}
        pairs = [("experiment_c", archived_c, out / "experiment_c/section65_per_step_divergence_steps50.csv"),
                 ("synchronized_three_classes", paper / "data/paper_section_65_66/results_section65_per_step_divergence/section65_per_step_divergence_steps50.csv",
                  out / "diagnostic_three_classes/section65_per_step_divergence_steps50.csv")]
        for name, old_path, new_path in pairs:
            key_fields = ["model", "seed", "coupling", "fault", "step"]
            def keyed(path):
                with path.open(newline="") as stream:
                    rows = list(csv.DictReader(stream))
                # 625d06c::_display_model explicitly renamed the image MLP to nlp.
                for row in rows:
                    if row["model"] == "nlp":
                        row["model"] = "mlp"
                return {tuple(r[f] for f in key_fields): r for r in rows}
            old, new = keyed(old_path), keyed(new_path)
            deltas = {f: 0.0 for f in limits}
            decisions = {f: 0 for f in limits}
            differing = 0
            for key, row in new.items():
                prior = old[key]
                differing += row != prior
                for field in limits:
                    if row[field] and prior[field]:
                        deltas[field] = max(deltas[field], abs(float(row[field]) - float(prior[field])))
                        decisions[field] += (float(row[field]) > limits[field]) != (float(prior[field]) > limits[field])
                    elif bool(row[field]) != bool(prior[field]):
                        raise ValueError(f"Measurement presence changed: {name}/{key}/{field}")
            comparison[name] = {"compared_rows": len(new), "different_serialized_rows": differing,
                                "max_absolute_numeric_change": deltas, "threshold_decision_changes": decisions,
                                "legacy_model_alias": "nlp -> mlp, documented in 625d06c::_display_model",
                                "archive_sha256": digest(old_path),
                                "rerun_sha256": digest(new_path)}
        historical = out / "historical_signal36/section65_signal_effectiveness_raw.json"
        old_historical = paper / "data/paper_section_65_66/results_section65_signal_sanity_current/section65_signal_effectiveness_raw.json"
        if historical.exists():
            comparison["historical_signal36"] = {"all_36_records_equal":
                json.loads(historical.read_text())["rows"] == json.loads(old_historical.read_text())["rows"]}
        write(out / "archive_comparison.json", comparison)
    return result


def signal36(root, archive_repo):
    """Replay the separate synthetic single-step grid preserved in a30e411."""
    root = Path(root).resolve()
    out = root / "historical_signal36"
    out.mkdir(exist_ok=False)
    source = root / "source"
    section = source / "experiments/paper_section_65_66"
    recovered = out / "run_section65_signal_effectiveness.py"
    recovered.write_bytes(subprocess.check_output(["git", "-C", archive_repo, "show",
        "a30e411:experiments/paper_section_65_66/run_section65_signal_effectiveness.py"]))
    os.chdir(source)
    sys.path[:0] = [str(section), str(source)]
    experiment = load("historical_signal36", recovered)
    import torch
    import mindspore
    torch.set_num_threads(1)
    backend = load("signal_backend", root / "backend_execution.py")
    write(out / "provenance.json", {"script_commit": "a30e411", "script_sha256": digest(recovered),
        "dependencies_commit": json.loads((root / "provenance.json").read_text())["source_commit"],
        "runner_sha256": digest(__file__), "torch": torch.__version__, "mindspore": mindspore.__version__,
        "models": ["cnn", "mlp", "transformer", "tiny_causal_lm"], "seeds": [200, 201, 202],
        "data": "synthetic make_batches; one step", "learning_rate": 0.01})
    original_run = experiment._run_torch4ms_fault
    original_extract = experiment.extract_and_wrap_loss_fn
    records = []

    def run(name, init_state, batch, lr, seed, fault):
        state = {}
        def extract(model, criterion, x, y):
            observer = backend.TargetBackendObserver(model)
            state["observer"] = observer
            observer.start()
            observer.begin_step()
            wrapper = original_extract(model, criterion, x, y)
            state["loss"] = experiment.safe_float(wrapper.output)
            state["forward"] = isinstance(getattr(wrapper.output, "_elem", None), mindspore.Tensor)
            return wrapper
        experiment.extract_and_wrap_loss_fn = extract
        try:
            result = original_run(name, init_state, batch, lr, seed, fault)
            observer = state.get("observer")
            if observer and state.get("loss") is not None:
                try:
                    observer.check_step(state["loss"])
                except backend.TargetBackendNotObserved:
                    pass
            records.append({"model": name, "seed": seed, "fault": fault, "target_forward": state.get("forward"),
                            "backend": observer.report() if observer else None, "status": result["status"]})
            return result
        finally:
            experiment.extract_and_wrap_loss_fn = original_extract
            if state.get("observer"):
                state["observer"].stop()
    experiment._run_torch4ms_fault = run
    experiment.main(["--models", "cnn,mlp,transformer,tiny_causal_lm", "--seeds", "3", "--output-dir", str(out)])
    write(out / "runtime_backend.json", records)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-repo", required=True)
    parser.add_argument("--observer", required=True)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--steps", type=int, default=50)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--models", default="cnn,mlp,transformer,tiny_causal_lm")
    args = parser.parse_args()
    out = Path(args.output_dir).resolve()
    out.mkdir(parents=True, exist_ok=False)
    source = out / "source"
    source.mkdir()
    archive = out / "source.tar"
    with archive.open("wb") as stream:
        subprocess.run(["git", "-C", args.archive_repo, "archive", "HEAD"], stdout=stream, check=True)
    with tarfile.open(archive) as stream:
        stream.extractall(source, filter="data")
    observer_path = out / "backend_execution.py"
    observer_path.write_bytes(Path(args.observer).read_bytes())
    os.environ.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", MPLBACKEND="Agg")
    os.chdir(source)
    sys.path.insert(0, str(source))
    section = source / "experiments/paper_section_65_66"
    sys.path.insert(0, str(section))
    experiment = load("diagnostic_experiment", section / "run_section66_realdata_training_consistency.py")
    import torch
    import mindspore
    torch.set_num_threads(1)
    backend = load("diagnostic_backend", observer_path)
    checks = experiment.validate_realdata_dir(args.data_dir)
    if not all(v["ok"] for v in checks.values()):
        raise RuntimeError(checks)
    # The historical validator hashes the archive but only checks extracted batch existence.
    data_root = Path(args.data_dir)
    with tarfile.open(data_root / "cifar10/cifar-10-python.tar.gz") as stream:
        for i in range(1, 6):
            name = f"cifar-10-batches-py/data_batch_{i}"
            expected = hashlib.sha256(stream.extractfile(name).read()).hexdigest()
            actual = digest(data_root / "cifar10" / name)
            if actual != expected:
                raise RuntimeError(f"Extracted CIFAR batch mismatch: {name}")
    data_hashes = {str(p.relative_to(data_root)): digest(p) for p in data_root.rglob("*") if p.is_file()}
    provenance = {
        "started_unix": time.time(), "argv": sys.argv, "python": sys.version,
        "platform": platform.platform(), "torch": torch.__version__, "mindspore": mindspore.__version__,
        "source_commit": subprocess.check_output(["git", "-C", args.archive_repo, "rev-parse", "HEAD"], text=True).strip(),
        "source_archive_sha256": digest(archive), "runner_sha256": digest(__file__),
        "observer_sha256": digest(observer_path), "data_checks": checks, "data_sha256": data_hashes,
        "source_sha256": {str(p.relative_to(source)): digest(p) for p in source.rglob("*.py")},
        "protocol": {"steps": args.steps, "seeds": args.seeds, "models": args.models,
                     "batch_size": 4, "learning_rate": 0.01, "grad_wrong_scale": 1.5,
                     "thresholds": {"loss": 0.02, "gradient_norm": 0.05, "update_relative_l2": 0.03}},
    }
    write(out / "provenance.json", provenance)
    original_run = experiment._run_torch4ms_model
    original_extract = experiment.extract_and_wrap_loss_fn
    evidence = []

    def observed_run(name, init_state, batches, lr, seed, **kwargs):
        record = {"model": name, "seed": seed, "coupling": kwargs["coupling"], "fault": kwargs["fault"], "steps": []}
        state = {"observer": None, "loss": None, "forward": False}

        def finish():
            observer = state["observer"]
            if observer is None or state["loss"] is None:
                return
            try:
                observer.check_step(state["loss"])
            except backend.TargetBackendNotObserved:
                pass
            record["steps"].append({**observer.steps[-1], "target_forward_tensor": state["forward"]})
            state["loss"] = None

        def extract(model, criterion, x, y):
            finish()
            if state["observer"] is None:
                state["observer"] = backend.TargetBackendObserver(model)
                state["observer"].start()
            state["observer"].begin_step()
            wrapper = original_extract(model, criterion, x, y)
            state["loss"] = experiment.safe_float(wrapper.output)
            state["forward"] = isinstance(getattr(wrapper.output, "_elem", None), mindspore.Tensor)
            return wrapper

        experiment.extract_and_wrap_loss_fn = extract
        try:
            result = original_run(name, init_state, batches, lr, seed, **kwargs)
            finish()
            record.update(status=result["status"], error=result["error"])
            evidence.append(record)
            write(out / "runtime_backend.json", evidence)
            return result
        finally:
            experiment.extract_and_wrap_loss_fn = original_extract
            if state["observer"] is not None:
                state["observer"].stop()

    experiment._run_torch4ms_model = observed_run
    common = ["--per-step-divergence", "--models", args.models, "--steps", str(args.steps), "--seeds", str(args.seeds),
              "--data-dir", args.data_dir, "--grad-wrong-scale", "1.5"]
    outcomes = []
    for label, couplings, faults in [
        ("experiment_c", "teacher-forced,free-running", "none,grad_wrong,param_wrong"),
        ("diagnostic_three_classes", "teacher-forced", "execution,numeric,training"),
    ]:
        command = common + ["--couplings", couplings, "--faults", faults, "--output-dir", str(out / label)]
        try:
            experiment.main(command)
            outcomes.append({"study": label, "passed": True, "argv": command})
        except Exception as exc:
            outcomes.append({"study": label, "passed": False, "error": repr(exc), "argv": command})
            print(json.dumps(outcomes[-1]), flush=True)
        write(out / "outcomes.json", outcomes)
    provenance["finished_unix"] = time.time()
    provenance["data_unchanged"] = all(digest(data_root / p) == h for p, h in data_hashes.items())
    provenance["source_unchanged"] = all(digest(source / p) == h for p, h in provenance["source_sha256"].items())
    write(out / "provenance.json", provenance)
    if not all(v["passed"] for v in outcomes):
        raise SystemExit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--signal36":
        signal36(sys.argv[2], sys.argv[3])
    elif len(sys.argv) > 1 and sys.argv[1] == "--summarize":
        print(json.dumps(summarize(sys.argv[2]), indent=2))
    else:
        main()
