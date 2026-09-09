import hashlib
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("paper_data", ROOT / "figures/paper_data.py")
data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data)


class PaperFigureTests(unittest.TestCase):
    def test_original_snapshots_are_unchanged(self):
        hashes = {
            data.FIXED50: "db4dd52fa1892ee53ec377ff3c5907779611689692d59b75e9c3c01f0f2ddd0e",
            data.SIGNAL_ABLATION: "ca2ba5a14e00716bdd35977b8b30e41096b4932f9e968c8e7f5bc72e4657c0f1",
        }
        for path, expected in hashes.items():
            with self.subTest(path=path):
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected)

    def test_fixed50_acceptance_and_cost_denominator(self):
        frame = data.fixed50()
        self.assertEqual(frame.strict_success.tolist(), [33, 34, 40, 46, 47, 50])
        self.assertEqual(frame.loc["r_hier", "repair_at_1"], 0.84)
        ladder = frame.loc["r_hier", "tokens_per_accepted_repair"]
        match = frame.loc["r_matchfix", "tokens_per_accepted_repair"]
        self.assertAlmostEqual(ladder, 190588 / 50)
        self.assertAlmostEqual(match, 5205141 / 47)
        self.assertEqual(round(match / ladder), 29)
        for stage in data.STAGES:
            self.assertEqual(frame[f"{stage}_instances"].nunique(), 1)

    def test_signal_ablation_keeps_separate_task_pool(self):
        counts, totals = data.signal_ablation()
        np.testing.assert_array_equal(totals, [4, 4, 4])
        np.testing.assert_array_equal(counts, [[4, 0, 0], [4, 4, 0], [4, 4, 4]])
        np.testing.assert_array_equal(counts.sum(axis=1), [4, 8, 12])

    def test_budget_acceptance_uses_recorded_checkpoints(self):
        rates = data.budget_acceptance()
        self.assertEqual(rates.columns.tolist(), [1, 2, 4])
        self.assertEqual(rates.index.tolist(), data.METHODS)
        counts = rates.mul(data.fixed50().instances, axis=0).round().astype(int)
        np.testing.assert_array_equal(counts, [[29, 32, 33], [33, 33, 34],
                                                [36, 38, 40], [36, 42, 46],
                                                [37, 43, 47], [42, 49, 50]])

    def test_budget_acceptance_rejects_inconsistent_checkpoints(self):
        for column, value in [("repair_at_2", 0.8), ("repair_at_2", 0.99),
                              ("repair_at_4", 0.98), ("repair_at_1", float("nan"))]:
            with self.subTest(column=column, value=value):
                frame = data.fixed50()
                frame.loc["r_hier", column] = value
                with patch.object(data, "fixed50", return_value=frame):
                    with self.assertRaises(ValueError):
                        data.budget_acceptance()

    def test_crash_metrics_are_missing_not_passes(self):
        signatures = data.fault_signatures()
        np.testing.assert_array_equal(signatures[0], [0, 0, 0, 0])
        self.assertEqual(signatures[1, 0], 1)
        self.assertTrue(np.isnan(signatures[1, 1:]).all())
        self.assertEqual(np.isnan(signatures).sum(), 3)
        np.testing.assert_array_equal(signatures[2:], [[0, 1, 1, 1],
                                                      [0, 0, 1, 1],
                                                      [0, 0, 0, 1]])

    def test_localization_is_counted_separately(self):
        matrix = data.localization()
        np.testing.assert_array_equal(matrix, [[20, 0, 0], [2, 12, 0], [0, 0, 16]])
        self.assertEqual(matrix.sum(), 50)
        self.assertEqual(matrix.trace(), 48)

    def test_gradient_plot_caption_matches_trajectories(self):
        frame = pd.read_csv(data.GRADIENT_STEPS)
        for fault, metric, mean_loss_crossing in [
            ("grad_wrong", "grad_norm_abs_diff", 31),
            ("param_wrong", "param_update_rel_l2", 18),
        ]:
            with self.subTest(fault=fault):
                subset = frame[frame.fault.eq(fault) & frame.coupling.eq("free-running")]
                self.assertEqual(subset.groupby(["model", "seed"]).ngroups, 12)
                self.assertTrue(subset.groupby(["model", "seed"]).step.nunique().eq(50).all())
                first = subset[subset.step.eq(1)]
                self.assertTrue(first[metric].gt(data.THRESHOLDS[metric]).all())
                mean = subset.groupby("step").loss_abs_diff.mean()
                crossing = mean[mean.gt(data.THRESHOLDS["loss_abs_diff"])].index.min()
                self.assertEqual(crossing, mean_loss_crossing)


if __name__ == "__main__":
    unittest.main()
