"""Measurement masking never derives observations from a fixture label."""
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / "scripts/run_signal_ablations.py"
if not path.exists():
    path = Path(__file__).with_name("run_signal_ablations.py")
spec = importlib.util.spec_from_file_location("signal_runner", path)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class SignalMaskTests(unittest.TestCase):
    def observation(self, measurements, execution=True, accepted=False):
        return {"execution_passed": execution, "accepted": accepted, "measurements": measurements,
                "acceptance": {"accepted": accepted, "contract": "original_unit_probe"}, "error": None}

    def test_hidden_forward_failure_does_not_leak_through_acceptance(self):
        original = self.observation({"max_abs_diff": 0.3, "expected_norm": 1.0})
        masked = runner.mask_observation(original, "execution")
        self.assertEqual(masked["measurements"], {})
        self.assertTrue(masked["accepted"])
        self.assertTrue(masked["acceptance"]["accepted"])
        self.assertFalse(original["accepted"])
        self.assertFalse(runner.mask_observation(original, "execution_forward")["accepted"])

    def test_hidden_gradients_do_not_leak_through_measurements(self):
        original = self.observation({"grad_norms": {"a": None, "b": 1.2}, "trainable": {"a": True}})
        masked = runner.mask_observation(original, "execution_forward")
        self.assertEqual(masked["measurements"], {})
        self.assertTrue(masked["accepted"])
        self.assertFalse(runner.mask_observation(original, "all_observations")["accepted"])

    def test_execution_failure_and_missing_values_remain_failures(self):
        original = self.observation({"max_abs_diff": None}, execution=False)
        for variant in runner.VARIANTS:
            masked = runner.mask_observation(original, variant)
            self.assertFalse(masked["accepted"])
            self.assertNotEqual(masked["measurements"].get("max_abs_diff"), 0)

    def test_reported_but_unavailable_forward_metric_does_not_pass(self):
        for unavailable in (None, float("nan"), float("inf")):
            original = self.observation({"max_abs_diff": unavailable}, execution=True)
            self.assertFalse(runner.mask_observation(original, "execution_forward")["accepted"])

    def test_task_tampering_is_rejected_in_every_condition(self):
        original = {**self.observation({}, accepted=True), "contract_immutable": False}
        for variant in runner.VARIANTS:
            self.assertFalse(runner.mask_observation(original, variant)["accepted"])

    def test_final_scoring_never_counts_a_masked_stop_as_a_repair(self):
        evaluation = {"accepted": True, "full_evaluation": {"accepted": False}}
        result = {"accepted": True, "initially_accepted": True, "initial": evaluation,
                  "final": evaluation, "attempts": [{"accepted": True, "evaluation": evaluation}],
                  "budget": {"calls": 8, "usage": {"total_tokens": 123}}}
        scored = runner.score_result(result, "execution")
        self.assertTrue(scored["controller_accepted"])
        self.assertTrue(scored["initially_accepted_by_available_checks"])
        self.assertFalse(scored["accepted"])
        self.assertFalse(scored["initially_accepted"])
        self.assertFalse(scored["attempts"][0]["accepted"])
        self.assertEqual(scored["budget"]["usage"]["total_tokens"], 123)


if __name__ == "__main__":
    unittest.main()
