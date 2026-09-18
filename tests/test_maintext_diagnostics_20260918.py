import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SPEC = importlib.util.spec_from_file_location(
    "diagnostics", Path(__file__).resolve().parents[1] / "scripts/run_maintext_diagnostics_20260918.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DiagnosticSummaryTests(unittest.TestCase):
    def fixture(self, root, missing=False):
        runtime = [{"model": "cnn", "seed": 300, "coupling": "free-running", "fault": "grad_wrong",
                    "steps": [{"observed": not missing, "target_forward_tensor": True}]}]
        MODULE.write(root / "runtime_backend.json", runtime)
        runs = []
        for fault in ("none", "grad_wrong", "param_wrong"):
            rows = [{"step": i + 1, "loss_abs_diff": value, "grad_norm_abs_diff": 0.1 if fault == "grad_wrong" else 0,
                     "param_update_rel_l2": 0.5 if fault == "param_wrong" else 0} for i, value in enumerate([0, 0.03])]
            if fault == "none":
                for row in rows:
                    row["loss_abs_diff"] = None if missing else 0
            runs.append({"fault": fault, "coupling": "free-running", "torch4ms_status": "ok", "steps": rows})
        raw = {"faults": ["none", "grad_wrong", "param_wrong"], "couplings": ["free-running"],
               "runs": runs, "steps": 2, "self_checks": {}}
        for study in ("experiment_c", "diagnostic_three_classes"):
            (root / study).mkdir()
            MODULE.write(root / study / "section65_per_step_divergence_raw_steps50.json", raw)

    def test_missing_measurements_do_not_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root, missing=True)
            result = MODULE.summarize(root)
            self.assertEqual(result["studies"]["experiment_c"]["counts"]["free-running/none"]["all_step_pass"], 0)
            self.assertEqual(len(result["backend"]["unexpected_missing_backward"]), 1)

    def test_signal_latency_separate_from_loss_latency(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root)
            result = MODULE.summarize(root)
            self.assertEqual(result["figure1"]["grad_wrong"]["signal_first_steps"], [1])
            self.assertEqual(result["figure1"]["grad_wrong"]["loss_first_steps"], [2])
            self.assertEqual(result["figure1"]["grad_wrong"]["mean_loss_first_step"], 2)
            self.assertEqual(result["backend"]["unexpected_missing_backward"], [])

    def test_execution_failure_is_not_intended_gradient_detection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root)
            path = root / "experiment_c/section65_per_step_divergence_raw_steps50.json"
            raw = json.loads(path.read_text())
            raw["runs"][1]["torch4ms_status"] = "failed"
            MODULE.write(path, raw)
            counts = MODULE.summarize(root)["studies"]["experiment_c"]["counts"]["free-running/grad_wrong"]
            self.assertEqual(counts["detected"], 1)
            self.assertEqual(counts["intended_signal_detected"], 0)


if __name__ == "__main__":
    unittest.main()
