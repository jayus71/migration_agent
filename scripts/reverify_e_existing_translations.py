"""Re-evaluate all existing Direct and translator outputs without model calls."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

BASE = Path("/media/main/whj/projects/torch4ms")
ROOT = BASE / "e-existing-translations-20260918"
REPO = BASE / "ascend-torch4ms-e-baselines-current-20260918"
EXP = "experiments/experiment_request_20260820/05_experiment_E_track_a_rerun"
VERIFIER = REPO / "experiments/baselines/track_a/T-DIRECT/verify_t_direct_candidate.py"


def load(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2))


def main():
    assert not ROOT.exists(), "Keep every previous evaluation; use a new root"
    ROOT.mkdir()
    preflight = load(BASE / "e-baselines-current-20260918/formal/preflight.json")
    assert preflight["passed"] and preflight["verifier_sha256"] == sha(VERIFIER)
    direct_path = BASE / "ascend-torch4ms-exp-e-final-5f3351f" / EXP / "final_4508d0e962d1/T-DIRECT/formal_5x3/summary.json"
    translator_path = BASE / "e-baselines-current-20260918/translator_reuse_audit.json"
    jobs = []
    for method, path in (("Direct", direct_path), ("Frozen Translator", translator_path)):
        shutil.copy2(path, ROOT / (method.replace(" ", "_") + "_provenance.json"))
        for row in load(path)["rows"]:
            task = row.get("task", row.get("task_id"))
            source = REPO / "experiments/paper_section_63_64/section642_heldout_sources" / (task + ".py")
            assert sha(source) == row.get("source_sha256", row.get("source_hash"))
            candidate = Path(row["candidate_path"])
            case = ROOT / method.replace(" ", "_") / (task + "_" + str(row["seed"]))
            case.mkdir(parents=True)
            shutil.copy2(candidate, case / "candidate.py")
            shutil.copy2(source, case / "source.py")
            jobs.append(dict(method=method, task=task, seed=row["seed"],
                source_sha256=sha(source), candidate_sha256=sha(candidate), case=str(case),
                candidate_origin=str(candidate),
                original_accepted=row.get("historical_strict_accepted", row.get("strict_success")),
                historical_tokens=row.get("historical_translator_tokens", row.get("total_tokens"))))
    assert len(jobs) == 30
    save(ROOT / "manifest.json", dict(jobs=jobs, new_model_calls=0,
        verifier_sha256=sha(VERIFIER), runner_sha256=sha(Path(__file__)),
        selection="All existing outputs, without regeneration or outcome selection"))
    shutil.copy2(VERIFIER, ROOT / "verify_t_direct_candidate.py")
    shutil.copy2(__file__, ROOT / Path(__file__).name)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BASE / "e-baselines-current-20260918/deps") + ":" + str(REPO)
    env.update(OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
    rows = []
    for job in jobs:
        case = Path(job["case"])
        command = [sys.executable, str(VERIFIER), "--candidate", str(case / "candidate.py"),
            "--reference", str(case / "source.py"), "--task", job["task"],
            "--seed", str(job["seed"]), "--backend-path",
            "MindSpore" if job["method"] == "Direct" else "torch4ms",
            "--output", str(case / "verification.json")]
        completed = subprocess.run(command, cwd=REPO, env=env, capture_output=True, text=True, timeout=300)
        (case / "stdout.txt").write_text(completed.stdout)
        (case / "stderr.txt").write_text(completed.stderr)
        assert completed.returncode == 0, completed.stderr[-2000:]
        assert sha(case / "candidate.py") == job["candidate_sha256"]
        result = load(case / "verification.json")
        rows.append({**job, "verification": result})
        save(ROOT / "progress.json", dict(completed=len(rows), expected=30, rows=rows))
        print(json.dumps(dict(completed=len(rows), method=job["method"], task=job["task"],
            accepted=result["translation_success_at_1"], errors=result["errors"])), flush=True)
    summaries = []
    for method in ("Direct", "Frozen Translator"):
        selected = [r for r in rows if r["method"] == method]
        summaries.append(dict(method=method, conditions=len(selected),
            accepted=sum(r["verification"]["translation_success_at_1"] for r in selected),
            forward=sum(r["verification"]["execution_success"] for r in selected),
            trained=sum(r["verification"]["training_success"] for r in selected),
            historical_tokens=sum(r["historical_tokens"] for r in selected),
            new_model_calls=0, changed_outcomes=sum(r["original_accepted"] != r["verification"]["translation_success_at_1"] for r in selected)))
    save(ROOT / "summary.json", dict(complete=True, summaries=summaries, rows=rows))
    print(json.dumps(summaries), flush=True)


if __name__ == "__main__":
    main()
