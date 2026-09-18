import importlib.util
from pathlib import Path
import unittest


spec = importlib.util.spec_from_file_location("jax_rerun", Path(__file__).parents[1] / "scripts/run_maintext_jax_autonomous.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class JaxContractTests(unittest.TestCase):
    def test_failure_is_unavailable(self):
        values = module.measurements({"status": "ok"}, {"status": "failed"})
        self.assertTrue(all(value is None for value in values.values()))

    def test_measurement_uses_parameter_names(self):
        left = {"status": "ok", "loss": 1., "grad_norm": 2., "update_by_name": {"b": [2.], "a": [1.]}}
        right = {"status": "ok", "loss": 1., "grad_norm": 2., "update_by_name": {"a": [1.], "b": [2.]}}
        self.assertEqual(module.measurements(left, right)["param_update_rel_l2"], 0.)
        right["update_by_name"]["b"] = [2., 3.]
        self.assertIsNone(module.measurements(left, right)["param_update_rel_l2"])

    def test_nonfinite_is_unavailable(self):
        value = {"status": "ok", "loss": float("nan"), "grad_norm": float("inf"), "update_by_name": {"a": [float("nan")]}}
        self.assertTrue(all(v is None for v in module.measurements(value, value).values()))

    def test_healthy_reference_removed_from_candidate_runtime(self):
        source = "def _reference_model(name):\n    return 'SECRET'\n\ndef run():\n    return 3\n"
        cleaned = module.strip_reference(source)
        self.assertNotIn("SECRET", cleaned)
        self.assertNotIn("def _reference_model", cleaned)
        self.assertIn("def run", cleaned)

    def test_original_grid_preserved(self):
        self.assertEqual(len(module.TASKS), 6)
        self.assertEqual(module.SEEDS, (6701, 6702, 6703))


if __name__ == "__main__":
    unittest.main()
