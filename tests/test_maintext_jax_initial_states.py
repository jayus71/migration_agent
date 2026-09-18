import importlib.util
from pathlib import Path
import unittest


spec = importlib.util.spec_from_file_location(
    "jax_initial_states", Path(__file__).resolve().parents[1] / "scripts/audit_maintext_jax_initial_states.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class InitialStatesTests(unittest.TestCase):
    def test_unavailable_and_invalid_never_match(self):
        for reference, target in ((None, []), ([], []), ([1], [float("nan")]), ([1], [True])):
            result = module.compare_vectors(reference, target)
            self.assertNotIn("exact_match", result)

    def test_shape_difference_preserved(self):
        self.assertEqual(module.compare_vectors([1, 2], [1])["status"], "shape_mismatch")

    def test_same_norm_different_state_is_detected(self):
        result = module.compare_vectors([1, 0], [0, 1])
        self.assertFalse(result["exact_match"])
        self.assertEqual(result["max_abs_difference"], 1)
        self.assertAlmostEqual(result["relative_l2"], 2 ** 0.5)

    def test_zero_state_exact_match(self):
        result = module.compare_vectors([0, 0], [0, 0])
        self.assertTrue(result["exact_match"])
        self.assertEqual(result["relative_l2"], 0)


if __name__ == "__main__":
    unittest.main()
