from itertools import combinations
from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "figures"))
try:
    from make_cost_quality import draw_cost_quality
    from make_gradient_drift import build_figure as build_gradient_figure
    from make_repair_comparison import build_figure
    from make_repair_by_budget import draw_repair_by_budget
    from make_unified_results import load_data
    from paper_data import GRADIENT_STEPS, METHOD_LABELS, THRESHOLDS, budget_acceptance
    from paper_plot_style import plt
finally:
    sys.path.pop(0)


class PaperFigureLayoutTests(unittest.TestCase):
    def assert_labels_do_not_overlap(self, fig, ax):
        self.addCleanup(plt.close, fig)
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        for first, second in combinations(ax.texts, 2):
            with self.subTest(first=first.get_text(), second=second.get_text()):
                first_box = (first.get_bbox_patch() or first).get_window_extent(renderer)
                second_box = (second.get_bbox_patch() or second).get_window_extent(renderer)
                self.assertFalse(first_box.overlaps(second_box))

    def test_gradient_labels_and_legends_fit(self):
        fig = build_gradient_figure()
        for ax, panel in zip(fig.axes, ["(a) Incorrect gradients",
                                        "(b) Incorrect parameter updates"]):
            self.assert_labels_do_not_overlap(fig, ax)
            self.assertIn(panel, [label.get_text() for label in ax.texts])
            self.assertEqual(ax.get_ylabel(), "Difference / threshold")
            renderer = fig.canvas.get_renderer()
            legend_box = ax.get_legend().get_window_extent(renderer)
            for label in ax.texts:
                box = (label.get_bbox_patch() or label).get_window_extent(renderer)
                self.assertFalse(box.overlaps(legend_box))
                for x, y in box.get_points():
                    self.assertTrue(fig.bbox.contains(x, y), label.get_text())
            for x, y in legend_box.get_points():
                self.assertTrue(ax.bbox.contains(x, y))

    def test_gradient_curves_and_detection_annotations_match_data(self):
        frame = pd.read_csv(GRADIENT_STEPS)
        fig = build_gradient_figure(frame)
        self.addCleanup(plt.close, fig)
        for ax, fault, metric, check, loss_step in zip(
                fig.axes, ["grad_wrong", "param_wrong"],
                ["grad_norm_abs_diff", "param_update_rel_l2"],
                ["Gradient", "Update"], [31, 18]):
            subset = frame[frame.fault.eq(fault) & frame.coupling.eq("free-running")]
            means = subset.groupby("step")[["loss_abs_diff", metric]].mean()
            lines = {line.get_label(): line for line in ax.lines
                     if not line.get_label().startswith("_")}
            expected = {"Loss difference": "loss_abs_diff", f"{check} difference": metric}
            self.assertEqual(set(lines), set(expected))
            self.assertEqual(len(ax.collections), 2)
            for label, column in expected.items():
                np.testing.assert_array_equal(lines[label].get_xdata(), means.index)
                np.testing.assert_allclose(lines[label].get_ydata(),
                                           (means[column] / THRESHOLDS[column]).clip(lower=1e-7))
            labels = {label.get_text(): label for label in ax.texts}
            first = labels["LaDiM detects at step 1"]
            self.assertEqual(first.xy[0], 1)
            self.assertAlmostEqual(first.xy[1], means.loc[1, metric] / THRESHOLDS[metric])
            loss = labels[f"Loss check detects\nat step {loss_step}"]
            self.assertEqual(loss.xy[0], loss_step)
            self.assertAlmostEqual(loss.xy[1], means.loc[loss_step, "loss_abs_diff"]
                                   / THRESHOLDS["loss_abs_diff"])
            self.assertEqual(labels["Detection threshold"].xy[1], 1)

    def test_gradient_plot_rejects_invalid_or_mixed_detection_data(self):
        frame = pd.read_csv(GRADIENT_STEPS)
        index = frame.index[frame.fault.eq("grad_wrong")
                            & frame.coupling.eq("free-running") & frame.step.eq(1)][0]
        for metric, value, message in [
                ("loss_abs_diff", float("nan"), "finite, nonnegative"),
                ("loss_abs_diff", float("inf"), "finite, nonnegative"),
                ("loss_abs_diff", -1, "finite, nonnegative"),
                ("grad_norm_abs_diff", 0, "same detection step")]:
            with self.subTest(metric=metric, value=value):
                changed = frame.copy()
                changed.loc[index, metric] = value
                try:
                    with self.assertRaisesRegex(ValueError, message):
                        build_gradient_figure(changed)
                finally:
                    plt.close("all")

    def test_composite_cost_labels(self):
        fig = build_figure()
        self.assert_labels_do_not_overlap(fig, fig.axes[0])

    def test_standalone_cost_labels(self):
        fig, ax = plt.subplots(figsize=(3.4, 2.6))
        draw_cost_quality(ax)
        fig.tight_layout(pad=0.4)
        self.assert_labels_do_not_overlap(fig, ax)

    def test_composite_paired_cost_labels_and_data(self):
        fig = build_figure()
        self.addCleanup(plt.close, fig)
        data = load_data()
        a, b = fig.axes
        np.testing.assert_allclose(fig.get_size_inches(), [5.5, 2.65])
        groups = [sorted([p['matchfix_tokens'] - p['ladim_tokens']
                          for p in data['paired_costs'] if p['initially_accepted'] == state])
                  for state in (True, False)]
        self.assertEqual(list(map(len, groups)), [20, 9])
        expected = groups[0] + groups[1]
        self.assertEqual(sum(v < 0 for v in expected), 2)
        self.assertEqual(sum(expected), 6938291)
        self.assertEqual(len(b.patches), 29)
        np.testing.assert_allclose([p.get_height() for p in b.patches], np.array(expected) / 1000)
        for index, method in enumerate(('ladim', 'matchfix', 'swe')):
            self.assertAlmostEqual(sum(p.get_width() for p in a.patches[index*3:index*3+3]),
                                   data['main'][method]['tokens'] / 1e6)
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        for ax in (a, b):
            for x, y in ax.get_legend().get_window_extent(renderer).get_points():
                self.assertTrue(ax.bbox.contains(x, y))
        for ax in fig.axes:
            labels = [*ax.texts, *ax.get_xticklabels(), *ax.get_yticklabels(),
                      ax.xaxis.label, ax.yaxis.label, ax._left_title]
            for label in labels:
                if not label.get_text():
                    continue
                self.assertGreaterEqual(label.get_fontsize(), 8)
                for x, y in label.get_window_extent(renderer).get_points():
                    self.assertTrue(fig.bbox.contains(x, y), label.get_text())

    def test_standalone_budget_labels(self):
        fig, ax = plt.subplots(figsize=(3.6, 2.8))
        draw_repair_by_budget(ax)
        fig.subplots_adjust(left=0.15, right=0.99, bottom=0.16, top=0.78)
        self.assert_labels_do_not_overlap(fig, ax)


if __name__ == "__main__":
    unittest.main()
