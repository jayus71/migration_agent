#!/usr/bin/env python3
"""One verdict collapses three faults that need three different repairs.

Replaces make_divergence_trajectory.py as Figure 1. That figure plotted three
quantities against training step under a single fault, and two of the three were
constant, so it spent a full-width float showing three numbers.

Three panels, each carrying something the others cannot:
  (a) Schematic. Three candidates, three different root causes, one verdict.
      The left half is what prior feedback reports; the right half is the first
      failing stage. Drawn, not measured -- it is the argument, not the evidence.
  (b) Measured fault signatures, from the 4800-row per-step result set. Each
      fault produces a distinct row pattern across the four checks, so the
      pattern identifies the fault while the verdict does not. This is the
      evidence for (a).
  (c) The one genuinely time-varying result: under a free-running training
      fault, the update check fires at step 1 while the forward check needs six
      steps, and only for the model whose reference loss travels far enough.

Data source for (b) and (c):
  data/paper_section_65_66/
    results_section65_per_step_divergence/
      section65_per_step_divergence_steps50.csv

Two conventions that matter for honesty:
  - A quantity that does not exist (candidate aborted, or no backward pass ran)
    is hatched and labelled "n/a", never drawn as a low value. Absent and silent
    are opposite findings.
  - The execution row reports steps 20-50, where its injected fault is live.
    Before step 20 that candidate is healthy by construction.

Run from the repository root after installing requirements-analysis.txt:
    python figures/make_verdict_collapse.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LogNorm, TwoSlopeNorm
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

CSV = (Path(__file__).resolve().parents[1] / "data/paper_section_65_66"
       / "results_section65_per_step_divergence"
       / "section65_per_step_divergence_steps50.csv")

THRESHOLD = {"loss_abs_diff": 0.02, "grad_norm_abs_diff": 0.05,
             "param_update_rel_l2": 0.03}

INK, MUTED, EDGE = "#1a1a1a", "#5c5c5c", "#9a9a9a"
FIRE = "#d03b3b"        # above threshold / fails
CALM = "#2a78d6"        # below threshold / silent
ABSENT_FC = "#e8e8e8"   # quantity does not exist

# The CSV ships the image MLP under the legacy label "nlp" (see PAPER_ISSUES
# item 1); the manuscript calls it MLP.
DISPLAY_MODEL = {"cnn": "CNN", "nlp": "MLP", "transformer": "Transformer",
                 "tiny_causal_lm": "Tiny causal LM"}

# Rows of panel (b). The repair each fault implies is not repeated here: panel
# (a) already maps stage to repair, and putting it on this panel's right edge ran
# it into panel (c)'s axis.
FAULTS = [
    ("none",      "Healthy"),
    ("execution", "Execution"),
    ("numeric",   "Numerical"),
    ("training",  "Training"),
]
# One-line headers only. "Exec.\nstatus" wrapped to two lines and reached up
# into the shared title band; the column is unambiguous from the row labels.
CHECKS = [
    ("status",              "Status"),
    ("loss_abs_diff",       "Forward"),
    ("grad_norm_abs_diff",  "Gradient"),
    ("param_update_rel_l2", "Update"),
]


def signature():
    """Ratio-to-threshold per (fault, check). None means the quantity is absent.

    Returns (values, status_failed) where values[i][j] is a float or None.
    """
    df = pd.read_csv(CSV)
    tf = df[df.coupling == "teacher-forced"]
    vals, failed = [], []
    for key, _ in FAULTS:
        sub = tf[tf.fault == key]
        # The execution fault is injected at step 20; before it the candidate is
        # healthy, so the signature is read from where the fault is live.
        if key == "execution":
            sub = sub[sub.step >= 20]
        failed.append((sub.torch4ms_status == "failed").mean())
        row = []
        for col, _ in CHECKS:
            if col == "status":
                row.append(None)          # handled by the status column itself
                continue
            v = sub[col].dropna()
            row.append(None if len(v) == 0 else float(v.mean() / THRESHOLD[col]))
        vals.append(row)
    return vals, failed


def panel_a(ax):
    """Schematic: three root causes, one verdict on the left, the stage on the right."""
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    rows = [
        (78, "Candidate A", "misses an operator"),
        (54, "Candidate B", "wrong reduction"),
        (30, "Candidate C", "no optimizer step"),
    ]
    for y, name, cause in rows:
        ax.add_patch(FancyBboxPatch((1, y - 8), 30, 16,
                                    boxstyle="round,pad=0,rounding_size=1.6",
                                    facecolor="white", edgecolor=EDGE,
                                    linewidth=0.8, zorder=2))
        ax.text(2.8, y + 3.4, name, fontsize=7.0, color=INK, va="center",
                fontweight="bold", zorder=3)
        ax.text(2.8, y - 3.6, cause, fontsize=6.8, color=MUTED, va="center",
                zorder=3)

    # left: everything funnels into one verdict
    ax.add_patch(FancyBboxPatch((44, 46), 18, 16,
                                boxstyle="round,pad=0,rounding_size=1.6",
                                facecolor="#f0f0f0", edgecolor=EDGE,
                                linewidth=0.8, zorder=2))
    ax.text(53, 57.5, "one verdict", fontsize=7.0, color=INK, ha="center",
            va="center", zorder=3)
    ax.text(53, 50.5, "\"it failed\"", fontsize=7.0, color=MUTED, ha="center",
            va="center", style="italic", zorder=3)
    for y, *_ in rows:
        ax.add_patch(FancyArrowPatch((31, y), (44, 54), arrowstyle="-|>",
                                     mutation_scale=6, color=EDGE,
                                     linewidth=0.8, shrinkA=0, shrinkB=0,
                                     connectionstyle="arc3,rad=0", zorder=4))
    ax.text(37, 9, "same repair signal\nfor all three", fontsize=6.8,
            color=MUTED, ha="center", va="center", style="italic")

    # right: the stage index separates them again
    stages = [(78, "1", "execution"), (54, "2", "forward"),
              (30, "3", "gradient / update")]
    for y, idx, label in stages:
        ax.add_patch(FancyBboxPatch((74, y - 7), 25, 14,
                                    boxstyle="round,pad=0,rounding_size=1.6",
                                    facecolor="white", edgecolor=FIRE,
                                    linewidth=0.9, zorder=2))
        ax.add_patch(FancyBboxPatch((75.4, y - 2.2), 4.2, 4.4,
                                    boxstyle="round,pad=0,rounding_size=0.8",
                                    facecolor=FIRE, edgecolor="none", zorder=3))
        ax.text(77.5, y, idx, fontsize=7.0, color="white", ha="center",
                va="center", fontweight="bold", zorder=4)
        ax.text(81.4, y, label, fontsize=7.0, color=INK, va="center", zorder=3)
        ax.add_patch(FancyArrowPatch((62, 54), (74, y), arrowstyle="-|>",
                                     mutation_scale=6, color=FIRE,
                                     linewidth=0.8, shrinkA=0, shrinkB=0,
                                     zorder=4))
    ax.text(86.5, 9, "first failing stage\nnames the repair", fontsize=6.8,
            color=MUTED, ha="center", va="center", style="italic")


def fmt(r):
    """Compact cell label.

    Sub-threshold values keep one mantissa digit rather than collapsing to a
    bare power of ten: the caption and the introduction both cite 4.4e-5, and a
    cell reading only 10^-5 forces the reader to reconcile the two.
    """
    if r >= 10:
        return f"{r:.0f}$\\times$"
    if r >= 1:
        return f"{r:.1f}$\\times$"
    e = int(np.floor(np.log10(r)))
    m = r / 10 ** e
    return f"${m:.1f}{{\\times}}10^{{{e}}}$"


def panel_b(ax, vals, failed):
    """Measured signature: each fault writes a different row across the checks."""
    nrow, ncol = len(FAULTS), len(CHECKS)
    # Diverging in log space, neutral exactly at the detection threshold.
    norm = TwoSlopeNorm(vmin=-7.0, vcenter=0.0, vmax=2.0)
    cmap = plt.get_cmap("RdBu_r")

    for i in range(nrow):
        for j, (col, _) in enumerate(CHECKS):
            y = nrow - 1 - i
            if col == "status":
                # status is categorical, not a ratio
                ok = failed[i] == 0
                fc = "#ffffff" if ok else cmap(norm(1.6))
                ax.add_patch(Rectangle((j, y), 1, 1, facecolor=fc,
                                       edgecolor="white", linewidth=1.4,
                                       zorder=2))
                ax.text(j + 0.5, y + 0.5, "ok" if ok else "failed",
                        fontsize=7.0, ha="center", va="center", zorder=3,
                        color=INK if ok else "white",
                        fontweight="normal" if ok else "bold")
                continue
            r = vals[i][j]
            if r is None:
                ax.add_patch(Rectangle((j, y), 1, 1, facecolor=ABSENT_FC,
                                       edgecolor="white", linewidth=1.4,
                                       hatch="//", zorder=2))
                ax.text(j + 0.5, y + 0.5, "n/a", fontsize=7.0, color=MUTED,
                        ha="center", va="center", zorder=3)
                continue
            ax.add_patch(Rectangle((j, y), 1, 1,
                                   facecolor=cmap(norm(np.log10(r))),
                                   edgecolor="white", linewidth=1.4, zorder=2))
            fires = r > 1.0
            ax.text(j + 0.5, y + 0.5, fmt(r), fontsize=7.0, zorder=3,
                    ha="center", va="center",
                    color="white" if fires else INK,
                    fontweight="bold" if fires else "normal")

    ax.set_xlim(0, ncol)
    ax.set_ylim(0, nrow)
    ax.set_xticks([j + 0.5 for j in range(ncol)])
    ax.set_xticklabels([lab for _, lab in CHECKS], fontsize=7.2, color=INK)
    ax.xaxis.set_ticks_position("top")
    ax.xaxis.set_label_position("top")
    ax.set_yticks([nrow - 1 - i + 0.5 for i in range(nrow)])
    ax.set_yticklabels([lab for _, lab in FAULTS], fontsize=7.2, color=INK)
    ax.tick_params(length=0)
    for side in ("top", "right", "bottom", "left"):
        ax.spines[side].set_visible(False)


def panel_c(ax):
    """The one result that genuinely varies with step: detection latency."""
    df = pd.read_csv(CSV)
    sub = df[(df.fault == "training") & (df.coupling == "free-running")
             & (df.model == "tiny_causal_lm")]

    for col, color, marker, label in [
            ("param_update_rel_l2", FIRE, "^", "Update"),
            ("loss_abs_diff", CALM, "o", "Forward")]:
        g = sub.groupby("step")[col]
        mean = (g.mean() / THRESHOLD[col]).clip(lower=1e-6)
        lo = (g.min() / THRESHOLD[col]).clip(lower=1e-6)
        hi = (g.max() / THRESHOLD[col]).clip(lower=1e-6)
        ax.fill_between(mean.index, lo, hi, color=color, alpha=0.16,
                        linewidth=0, zorder=2)
        ax.plot(mean.index, mean, color=color, linewidth=1.8, zorder=3)
        ticks = [s for s in (1, 10, 20, 30, 40, 50) if s in mean.index]
        ax.plot(ticks, mean.loc[ticks], linestyle="none", marker=marker,
                markersize=3.8, markerfacecolor="white", markeredgecolor=color,
                markeredgewidth=1.2, zorder=4)

    ax.axhline(1.0, color=INK, linewidth=0.9, linestyle="--", zorder=2)
    ax.text(50.5, 1.35, "threshold", fontsize=6.8, color=INK, ha="right",
            va="bottom")

    r = sub.groupby("step").loss_abs_diff.mean() / THRESHOLD["loss_abs_diff"]
    first = int(r[r > 1.0].index.min())
    ax.axvline(first, color=MUTED, linewidth=0.7, linestyle=":", zorder=2)

    ax.annotate(f"forward needs\n{first} steps",
                xy=(first, 1.0), xytext=(first + 3.5, 2.2e-2),
                fontsize=6.8, color=CALM, ha="left", va="center",
                arrowprops=dict(arrowstyle="-", color=CALM, linewidth=0.6,
                                shrinkA=2, shrinkB=2))
    ax.annotate("update fires\nat step 1",
                xy=(1, float((sub[sub.step == 1].param_update_rel_l2.mean()
                              / THRESHOLD["param_update_rel_l2"]))),
                xytext=(6.0, 220.0),
                fontsize=6.8, color=FIRE, ha="left", va="center",
                arrowprops=dict(arrowstyle="-", color=FIRE, linewidth=0.6,
                                shrinkA=2, shrinkB=2))

    ax.set_yscale("log")
    ax.set_xlim(0, 51)
    ax.set_ylim(3e-3, 2e3)
    ax.set_xlabel("Training step", fontsize=7.2, color=INK)
    ax.set_ylabel("Signal / threshold", fontsize=7.2, color=INK)
    ax.tick_params(labelsize=7.0, color=EDGE)
    ax.grid(True, axis="y", which="major", linestyle="-", linewidth=0.5,
            color="#e2e2e2", zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(EDGE)
        ax.spines[side].set_linewidth(0.7)


vals, failed = signature()

fig = plt.figure(figsize=(7.0, 2.5))
# (b) gets a little more width than its cell count implies, so the four column
# headers do not run together.
gs = fig.add_gridspec(1, 3, width_ratios=[1.38, 1.36, 1.0], wspace=0.46)
ax_a = fig.add_subplot(gs[0, 0])
ax_b = fig.add_subplot(gs[0, 1])
ax_c = fig.add_subplot(gs[0, 2])
panel_a(ax_a)
panel_b(ax_b, vals, failed)
panel_c(ax_c)

# No tight_layout: panel (a) is an axis-off schematic on a fixed 0-100 canvas,
# which tight_layout cannot measure. The gridspec sets the spacing instead.
# top leaves a clear band for the shared titles above panel (b)'s header row
fig.subplots_adjust(left=0.035, right=0.985, top=0.78, bottom=0.165)

# Titles are placed at figure level, on one shared baseline. Per-axes titles put
# panel (b)'s far above the other two, because its x-axis sits on top.
# Titles are kept short enough that (a) and (b) do not touch and (c) does not
# overrun the 7in canvas; measured, not eyeballed. The caption carries the full
# reading of each panel.
TITLE_Y = 0.925
for ax, text in [
        (ax_a, "(a) Three root causes, one verdict"),
        (ax_b, "(b) Measured signatures, ratio to threshold"),
        (ax_c, "(c) Detection latency")]:
    fig.text(ax.get_position().x0, TITLE_Y, text, fontsize=7.6, color=INK,
             ha="left", va="center")
fig.savefig("figures/verdict_collapse.pdf", bbox_inches="tight")
fig.savefig("figures/verdict_collapse.png", bbox_inches="tight", dpi=200)
print("wrote figures/verdict_collapse.pdf")
for (key, lab), row, f in zip(FAULTS, vals, failed):
    shown = ["n/a" if v is None else f"{v:.3e}" for v in row[1:]]
    print(f"  {lab:<10} failed={f:.0%}  fwd={shown[0]} grad={shown[1]} upd={shown[2]}")
