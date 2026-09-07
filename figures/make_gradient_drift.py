#!/usr/bin/env python3
"""Gradient drift under free-running coupling from Experiment C.

Two panels show per-step divergence for grad_wrong and param_wrong faults.
Under free-running coupling, errors accumulate across steps, revealing how
long each metric takes to cross its detection threshold.

Key insight for the introduction: a forward-only check ("loss matched")
misses gradient and parameter faults for tens of steps, while LADDER's
multi-stage checks catch them at step 1.

Data source: data/experiments/03_experiment_C_gradient_and_parameter_faults/
             results_per_step/section65_per_step_divergence_steps50.csv
Thresholds from the paper: Δloss ≤ 0.02, Δgrad ≤ 0.05, Δparam ≤ 0.03.
Source: EXPERIMENT_REQUEST_20260820.md Experiment C.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CSV = (Path(__file__).resolve().parents[1] / "data/experiments"
       / "03_experiment_C_gradient_and_parameter_faults"
       / "results_per_step" / "section65_per_step_divergence_steps50.csv")

THRESHOLD = {"loss_abs_diff": 0.02, "grad_norm_abs_diff": 0.05,
             "param_update_rel_l2": 0.03}

INK   = "#1a1a1a"
MUTED = "#5c5c5c"
EDGE  = "#9a9a9a"

METRICS = [
    ("loss_abs_diff",       "Δ loss (forward)",  "#2a78d6", "o"),
    ("grad_norm_abs_diff",  "Δ grad. norm",      "#d03b3b", "^"),
    ("param_update_rel_l2", "Δ param. update",   "#1a6b1a", "s"),
]

PANELS = [
    ("grad_wrong",  "(a) Gradient fault (grad_wrong)"),
    ("param_wrong", "(b) Parameter fault (param_wrong)"),
]

df = pd.read_csv(CSV)

fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.5), sharey=True)

for ax, (fault, title) in zip(axes, PANELS):
    sub = df[(df.fault == fault) & (df.coupling == "free-running")]

    for col, label, color, marker in METRICS:
        g = sub.groupby("step")[col]
        mean = (g.mean() / THRESHOLD[col]).clip(lower=1e-7)
        lo   = (g.min()  / THRESHOLD[col]).clip(lower=1e-7)
        hi   = (g.max()  / THRESHOLD[col]).clip(lower=1e-7)
        ax.fill_between(mean.index, lo, hi, color=color, alpha=0.12,
                        linewidth=0, zorder=2)
        ax.plot(mean.index, mean, color=color, linewidth=1.6, zorder=3,
                label=label)
        ticks = [s for s in (1, 10, 20, 30, 40, 50) if s in mean.index]
        ax.plot(ticks, mean.loc[ticks], linestyle="none", marker=marker,
                markersize=3.5, markerfacecolor="white",
                markeredgecolor=color, markeredgewidth=1.0, zorder=4)

    # Threshold line
    ax.axhline(1.0, color=INK, linewidth=0.8, linestyle="--", zorder=2)

    # Find where loss first crosses threshold
    loss_g = sub.groupby("step")["loss_abs_diff"]
    loss_ratio = loss_g.mean() / THRESHOLD["loss_abs_diff"]
    crossed = loss_ratio[loss_ratio > 1.0]
    if len(crossed) > 0:
        first_step = int(crossed.index.min())
        ax.axvline(first_step, color=MUTED, linewidth=0.6, linestyle=":",
                   zorder=2)
        ax.annotate(f"loss crosses\nat step {first_step}",
                    xy=(first_step, 1.0),
                    xytext=(first_step + 4, 3e-3),
                    fontsize=6.5, color="#2a78d6", ha="left", va="center",
                    arrowprops=dict(arrowstyle="-", color="#2a78d6",
                                    linewidth=0.6, shrinkA=2, shrinkB=2))

    ax.set_title(title, fontsize=7.8, color=INK, pad=6)
    ax.set_yscale("log")
    ax.set_xlim(0, 51)
    ax.set_ylim(1e-6, 1e3)
    ax.set_xlabel("Training step", fontsize=7.2, color=INK)
    ax.tick_params(labelsize=7.0, color=EDGE)
    ax.grid(True, axis="y", which="major", linestyle="-", linewidth=0.5,
            color="#e2e2e2", zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(EDGE)
        ax.spines[side].set_linewidth(0.7)

axes[0].set_ylabel("Signal / threshold", fontsize=7.2, color=INK)
axes[0].text(50.5, 1.35, "threshold", fontsize=6.5, color=INK, ha="right",
             va="bottom")

# Shared legend above panels
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, fontsize=6.5, loc="upper center",
           bbox_to_anchor=(0.5, 1.02), ncol=3, frameon=True, framealpha=0.92,
           edgecolor="#dcdcdc", handlelength=1.5, handletextpad=0.4,
           borderpad=0.4, columnspacing=1.2)

fig.tight_layout(pad=0.5, rect=[0, 0, 1, 0.88])
fig.savefig("figures/gradient_drift.pdf", bbox_inches="tight")
fig.savefig("figures/gradient_drift.png", dpi=200, bbox_inches="tight")
print("wrote figures/gradient_drift.pdf + .png")
