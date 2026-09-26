"""Connect LaDiM's recorded controller to independently prepared native inputs."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "program"), str(ROOT)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--method", choices=["autonomous_layered", "swe_native_isolated", "matchfix_full_orchestration", "direct_shared_tools"], default="autonomous_layered")
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    args = parser.parse_args()
    from autofix.autonomous import experiment
    from evaluation.native.evaluator import UnifiedEvaluator
    from evaluation.native.domain import declared_domain
    run = args.run.resolve()
    manifest = json.loads((run / "manifest.json").read_text())
    row = next(row for row in manifest["tasks"] if row["anonymous_id"] == args.task)
    for name in ("source.py", "candidate.py", "task.json"):
        if not (run / "private_inputs" / args.task / name).is_file():
            raise FileNotFoundError("Missing independently supplied input: " + name)
    def evaluator(root, task, workspace, evidence, python, current_manifest):
        return UnifiedEvaluator(workspace, evidence, python, kind=row["input_form"],
                                runtime=manifest["runtime"], references=run / "private_references" / task)
    with patch.object(experiment, "evaluator_for", evaluator), declared_domain("PyTorch", "MindSpore"):
        result = experiment.run_condition(run, args.task, args.method, args.python.resolve())
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
