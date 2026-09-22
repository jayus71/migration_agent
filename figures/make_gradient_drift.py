#!/usr/bin/env python3
"""Threshold-normalized free-running trajectories from the archived step CSV."""
import numpy as np
import pandas as pd

from paper_data import GRADIENT_STEPS, THRESHOLDS
from paper_plot_style import BLUE, GREEN, GRAY, INK, ORANGE, plt, save_figure

METRICS = {
    "loss_abs_diff": ("Loss difference", BLUE, "o"),
    "grad_norm_abs_diff": ("Gradient difference", ORANGE, "^"),
    "param_update_rel_l2": ("Update difference", GREEN, "s"),
}
PANELS = [
    ("grad_wrong", "grad_norm_abs_diff", "(a) Incorrect gradients", "Gradient"),
    ("param_wrong", "param_update_rel_l2", "(b) Incorrect parameter updates", "Update"),
]


def build_figure(frame=None):
    if frame is None:
        frame = pd.read_csv(GRADIENT_STEPS)
    # Two panels across the ICLR text width, with labels at their printed size.
    fig, axes = plt.subplots(1, 2, figsize=(5.5, 2.0), sharex=True, sharey=True)
    for ax, (fault, diagnostic, panel, check) in zip(axes, PANELS):
        subset = frame[frame.fault.eq(fault) & frame.coupling.eq("free-running")]
        runs = subset.groupby(["model", "seed"])
        if runs.ngroups != 12 or subset.duplicated(["model", "seed", "step"]).any():
            raise ValueError(f"Expected 12 distinct free-running trajectories: {fault}")
        if any(set(run.step) != set(range(1, 51)) for _, run in runs):
            raise ValueError(f"Expected steps 1-50 in every trajectory: {fault}")
        metrics = ["loss_abs_diff", diagnostic]
        if not np.isfinite(subset[metrics]).all().all() or subset[metrics].lt(0).any().any():
            raise ValueError(f"Expected finite, nonnegative differences: {fault}")
        means = {}
        for metric in metrics:
            label, color, marker = METRICS[metric]
            grouped = subset.groupby("step")[metric]
            mean = grouped.mean() / THRESHOLDS[metric]
            means[metric] = mean
            low = (grouped.min() / THRESHOLDS[metric]).clip(lower=1e-7)
            high = (grouped.max() / THRESHOLDS[metric]).clip(lower=1e-7)
            ax.fill_between(mean.index, low, high, color=color, alpha=0.10, linewidth=0)
            ax.plot(mean.index, mean.clip(lower=1e-7), color=color, label=label,
                    linewidth=1.2, marker=marker, markevery=[0, 9, 19, 29, 39, 49],
                    markersize=3, markerfacecolor="white", markeredgewidth=0.7)

        # A single detection label must describe every run, not only the mean.
        detected = subset[subset[diagnostic].gt(THRESHOLDS[diagnostic])]
        first_steps = detected.groupby(["model", "seed"]).step.min()
        if len(first_steps) != runs.ngroups or first_steps.nunique() != 1:
            raise ValueError(f"Expected the same detection step in every run: {fault}")
        first_detection = int(first_steps.iloc[0])
        loss_crossings = means["loss_abs_diff"][means["loss_abs_diff"].gt(1)]
        if loss_crossings.empty:
            raise ValueError(f"Mean loss difference never exceeds its threshold: {fault}")
        first_loss = int(loss_crossings.index.min())

        diagnostic_color = METRICS[diagnostic][1]
        ax.annotate(f"LaDiM detects at step {first_detection}",
                    xy=(first_detection, means[diagnostic].loc[first_detection]),
                    xytext=(0.08, 0.80), textcoords="axes fraction",
                    ha="left", va="top", color=diagnostic_color, fontsize=7.5,
                    arrowprops=dict(arrowstyle="->", color=diagnostic_color,
                                    linewidth=0.8, shrinkA=3, shrinkB=3),
                    bbox=dict(facecolor="white", edgecolor="none", pad=1))
        ax.axvline(first_loss, color=GRAY, linewidth=0.6, linestyle=":")
        ax.annotate(f"Loss check detects\nat step {first_loss}",
                    xy=(first_loss, means["loss_abs_diff"].loc[first_loss]),
                    xytext=(0.96, 0.26), textcoords="axes fraction",
                    ha="right", va="bottom", color=BLUE, fontsize=7.5,
                    arrowprops=dict(arrowstyle="->", color=BLUE,
                                    linewidth=0.8, shrinkA=3, shrinkB=3),
                    bbox=dict(facecolor="white", edgecolor="none", pad=1))
        ax.axhline(1, color=INK, linewidth=0.7, linestyle="--")
        ax.annotate("Detection threshold", xy=(50, 1), xytext=(0, -4),
                    textcoords="offset points", ha="right", va="top", fontsize=7,
                    color=GRAY, bbox=dict(facecolor="white", edgecolor="none", pad=1))
        ax.text(0.98, 0.98, panel, transform=ax.transAxes,
                ha="right", va="top", fontsize=8,
                bbox=dict(facecolor="white", edgecolor="none", pad=0.5))
        ax.set_yscale("log")
        ax.set_ylim(1e-6, 1e4)
        ax.set_yticks([1e-6, 1e-3, 1, 1e4])
        ax.set_xlim(0, 51)
        ax.set_ylabel("Difference / threshold")
        ax.grid(axis="y", linewidth=0.4, color="#dddddd")
        ax.set_axisbelow(True)
        ax.legend(loc="lower left", bbox_to_anchor=(0.02, 0.00),
                  frameon=False, fontsize=7, handlelength=1.6,
                  borderaxespad=0.5, labelspacing=0.4)
        ax.set_xlabel("Training step")
        ax.set_xticks([1, 10, 20, 30, 40, 50])
    fig.subplots_adjust(left=0.105, right=0.99, bottom=0.24, top=0.98, wspace=0.20)
    return fig


def main():
    save_figure(build_figure(), "gradient_drift")


if __name__ == "__main__":
    main()
