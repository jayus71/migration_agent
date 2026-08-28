#!/usr/bin/env python3
"""Per-step signal divergence under the training fault, normalized by threshold.

Reads the 4800-row per-step result set directly so the figure cannot drift from
the data:
  ascend-torch4ms/experiments/paper_section_65_66/
    results_section65_per_step_divergence/
      section65_per_step_divergence_steps50.csv

The candidate runs a valid forward pass but never applies a parameter update, so
the forward check agrees with the reference while the update check is maximally
violated. Each quantity is divided by its own detection threshold, so y=1 is
exactly where a check fires and all layers share one axis.

Two panels, because the two couplings answer different questions:
  (a) teacher-forced -- candidate parameters are reset to the reference at every
      step, so each step is an independent single-step comparison. Shows that the
      layers cannot be inferred from one another.
  (b) free-running   -- candidate keeps its own parameters. Shows how long a
      forward-only check takes to notice. Only tiny_causal_lm is shown: it is the
      only model whose reference loss travels far enough over 50 steps
      (-0.2125) for the forward difference to be able to cross 0.02 at all. For
      cnn/nlp/transformer the reference moves 0.0025-0.0188, so a frozen
      candidate cannot produce a forward difference above threshold regardless of
      the fault. That is a property of the 50-step horizon, not of the checks.

The gradient quantity does not exist under this fault (no backward pass runs), so
it is drawn in a separate "n/a" band rather than at zero -- plotting it low would
read as "does not fire", the opposite of the truth.

Run with the lzf env (base has no pandas):
    /opt/miniconda3/envs/lzf/bin/python figures/make_divergence_trajectory.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

CSV = os.path.join(
    "ascend-torch4ms/experiments/paper_section_65_66",
    "results_section65_per_step_divergence",
    "section65_per_step_divergence_steps50.csv")

# quantity -> detection threshold (from the run's raw JSON "thresholds")
THRESHOLD = {"loss_abs_diff": 0.02, "grad_norm_abs_diff": 0.05,
             "param_update_rel_l2": 0.03}

# dataviz categorical slots 1/2/3, validated light-mode; marker shape is the
# secondary encoding so the figure survives grayscale print.
STYLE = {
    "loss_abs_diff":       dict(color="#2a78d6", marker="o", label="Forward"),
    "grad_norm_abs_diff":  dict(color="#1baf7a", marker="s", label="Gradient"),
    "param_update_rel_l2": dict(color="#eb6834", marker="^", label="Update"),
}
INK, MUTED, GRID = "#1a1a1a", "#5c5c5c", "#d4d4d4"
FIRE = "#d03b3b"        # status:critical, reserved for the threshold rule
FLOOR = 1e-6            # log axis cannot show exact zeros
ABSENT_Y = 4.0e3        # centre of the "quantity does not exist" band
BAND_LO, BAND_HI = 8.0e2, 2.0e4


def load():
    df = pd.read_csv(CSV)
    return df[df.fault == "training"]


def panel(ax, sub, title, subtitle):
    """Draw Forward / Update trajectories as ratio-to-threshold, plus n/a band."""
    ax.axhspan(BAND_LO, BAND_HI, facecolor="#f2f2f2", zorder=0)
    ax.axhline(BAND_LO, color="#b0b0b0", linewidth=0.6, zorder=1)

    for col in ("loss_abs_diff", "param_update_rel_l2"):
        g = sub.groupby("step")[col]
        mean = g.mean() / THRESHOLD[col]
        lo, hi = g.min() / THRESHOLD[col], g.max() / THRESHOLD[col]
        st = STYLE[col]
        ax.fill_between(mean.index, lo.clip(lower=FLOOR), hi.clip(lower=FLOOR),
                        color=st["color"], alpha=0.16, linewidth=0, zorder=2)
        ax.plot(mean.index, mean.clip(lower=FLOOR), color=st["color"],
                linewidth=2.0, zorder=3)
        # sparse markers: readable without a number on every point
        ticks = [s for s in (1, 10, 20, 30, 40, 50) if s in mean.index]
        ax.plot(ticks, mean.loc[ticks].clip(lower=FLOOR), linestyle="none",
                marker=st["marker"], markersize=4.0, markerfacecolor="white",
                markeredgecolor=st["color"], markeredgewidth=1.3, zorder=4)

    # gradient: unmeasurable under this fault, so it lives in the n/a band
    st = STYLE["grad_norm_abs_diff"]
    steps = sorted(sub.step.unique())
    ax.plot(steps, [ABSENT_Y] * len(steps), color=st["color"], linewidth=1.4,
            linestyle=(0, (4, 2)), zorder=3)
    ax.plot([s for s in (1, 10, 20, 30, 40, 50) if s in steps],
            [ABSENT_Y] * len([s for s in (1, 10, 20, 30, 40, 50) if s in steps]),
            linestyle="none", marker="x", markersize=4.6,
            markeredgecolor=st["color"], markeredgewidth=1.3, zorder=4)

    ax.axhline(1.0, color=FIRE, linewidth=1.0, linestyle="--", zorder=2)
    ax.set_yscale("log")
    ax.set_ylim(3e-6, BAND_HI * 1.6)
    ax.set_xlim(0, 51)
    ax.set_yticks([1e-5, 1e-3, 1e-1, 1, 1e1, 1e2, ABSENT_Y])
    ax.set_yticklabels(["$10^{-5}$", "$10^{-3}$", "$10^{-1}$", "1", "$10^{1}$",
                        "$10^{2}$", "n/a"], fontsize=6.6)
    ax.grid(True, axis="y", which="major", linestyle="-", linewidth=0.5,
            color=GRID, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#9a9a9a")
        ax.spines[side].set_linewidth(0.7)
    ax.tick_params(labelsize=6.6, color="#9a9a9a")
    ax.set_title(title, fontsize=7.6, color=INK, pad=4.0, loc="left")
    # subtitle goes inside the empty mid-band, not on the title baseline
    ax.text(0.985, 0.055, subtitle, transform=ax.transAxes, fontsize=6.2,
            color=MUTED, va="bottom", ha="right")


train = load()
fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.5), sharey=True)

tf = train[train.coupling == "teacher-forced"]
panel(axes[0], tf, "(a) Teacher-forced (each step independent)",
      f"4 models x 3 seeds, n={len(tf)}")

fr = train[(train.coupling == "free-running") & (train.model == "tiny_causal_lm")]
panel(axes[1], fr, "(b) Free-running (fault accumulates)",
      f"tiny causal LM, 3 seeds, n={len(fr)}")

# direct labels: identity is never color-alone, and they satisfy the contrast WARN.
# Each sits ABOVE its line so nothing is cramped against the axis floor.
axes[0].text(50.5, 4.4e-5 * 3.6, "Forward", fontsize=6.6,
             color=STYLE["loss_abs_diff"]["color"], ha="right", va="bottom")
axes[0].text(50.5, 33.3 * 2.2, "Update", fontsize=6.6,
             color=STYLE["param_update_rel_l2"]["color"], ha="right", va="bottom")
axes[0].text(50.5, ABSENT_Y * 2.4, "Gradient (not measurable)", fontsize=6.2,
             color=STYLE["grad_norm_abs_diff"]["color"], ha="right", va="bottom")
axes[0].text(1.2, 1.0 * 1.6, "check fires", fontsize=6.2, color=FIRE,
             ha="left", va="bottom")

# panel (b): mark where the forward check finally notices
cross = fr.groupby("step").loss_abs_diff.mean() / THRESHOLD["loss_abs_diff"]
first = int(cross[cross > 1.0].index.min())
axes[1].axvline(first, color=MUTED, linewidth=0.7, linestyle=":", zorder=2)
axes[1].text(first + 1.4, 3.0e-4, f"forward crosses\nat step {first}",
             fontsize=6.2, color=MUTED, ha="left", va="center")
# arrow stops short of the Update line rather than touching it
axes[1].annotate("", xy=(1, 14.0), xytext=(1, 1.7),
                 arrowprops=dict(arrowstyle="-|>", color=MUTED, linewidth=0.7,
                                 shrinkA=0, shrinkB=0))
axes[1].text(2.6, 4.2, "update fires\nat step 1", fontsize=6.2, color=MUTED,
             ha="left", va="center")

axes[0].set_ylabel("Signal / detection threshold", fontsize=7.4, color=INK)
for ax in axes:
    ax.set_xlabel("Training step", fontsize=7.4, color=INK)

handles = [
    plt.Line2D([], [], color=STYLE[s]["color"], linewidth=2.0,
               marker=STYLE[s]["marker"], markersize=4.0,
               markerfacecolor="white", markeredgecolor=STYLE[s]["color"],
               label=STYLE[s]["label"])
    for s in ("loss_abs_diff", "param_update_rel_l2")
]
handles.append(plt.Line2D([], [], color=STYLE["grad_norm_abs_diff"]["color"],
                          linewidth=1.4, linestyle=(0, (4, 2)), marker="x",
                          markersize=4.6, label="Gradient (absent)"))
handles.append(plt.Line2D([], [], color=FIRE, linewidth=1.0, linestyle="--",
                          label="Detection threshold"))
# shared legend below both panels: inside either one it would sit on the data
fig.legend(handles=handles, fontsize=6.4, loc="lower center", ncol=4,
           frameon=False, handletextpad=0.4, columnspacing=1.4,
           bbox_to_anchor=(0.5, -0.045), labelcolor=INK)

fig.tight_layout(pad=0.4)
fig.subplots_adjust(wspace=0.06, bottom=0.20)
out = "figures/divergence_trajectory.pdf"
fig.savefig(out, bbox_inches="tight")
fig.savefig("figures/divergence_trajectory.png", bbox_inches="tight", dpi=200)
print(f"wrote {out} | teacher-forced rows: {len(tf)} | free-running rows: {len(fr)}")
print(f"  (a) forward mean ratio = {tf.loss_abs_diff.mean()/0.02:.3e}, "
      f"update mean ratio = {tf.param_update_rel_l2.mean()/0.03:.2f}")
print(f"  (b) forward crosses threshold at step {first}")
