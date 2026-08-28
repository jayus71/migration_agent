#!/usr/bin/env python3
"""Signal magnitude under controlled faults, normalized by detection threshold.

NOT CURRENTLY IN THE MANUSCRIPT. This figure was added in 635ecd5 and dropped
again in 9da362f; no \\includegraphics in conference_101719.tex refers to
signal_magnitude.pdf. The magnitude-separation argument it made is now carried
by Figure 1 (figures/make_divergence_trajectory.py), which shows the same
separation over training steps rather than at a single step. Kept because it
reads the fault-injection CSV that Table III also reports, so it is the quickest
way to re-check that table visually. Delete both this script and its PDF if that
stops being useful.

Reads the two measured result sets directly so the figure cannot drift from the
data:
  - oracle negative control : results_realdata_66/...steps_steps50.csv (600 rows)
  - fault injection         : results_section65_signal_sanity_current/
                              section65_signal_effectiveness_table.csv (36 rows)

Each quantity is divided by its own detection threshold, so y=1 is exactly where
a signal fires and all three signals share one axis. Quantities that do not
exist (run aborted, gradient missing) are drawn as crosses in a separate band at
the top, because plotting them low would read as "does not fire" -- the opposite
of the truth.
"""
import csv
import os
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = "ascend-torch4ms/experiments/paper_section_65_66"
ORACLE_CSV = os.path.join(
    BASE, "results_realdata_66",
    "section66_realdata_training_consistency_steps_steps50.csv")
FAULT_CSV = os.path.join(
    BASE, "results_section65_signal_sanity_current",
    "section65_signal_effectiveness_table.csv")

# quantity -> detection threshold (from section65 raw JSON "thresholds")
THRESHOLD = {
    "loss_abs_diff": 0.02,
    "grad_norm_abs_diff": 0.05,
    "param_update_rel_l2": 0.03,
}
SIGNALS = ["loss_abs_diff", "grad_norm_abs_diff", "param_update_rel_l2"]
SIGNAL_LABEL = {
    "loss_abs_diff": "Forward",
    "grad_norm_abs_diff": "Gradient",
    "param_update_rel_l2": "Update",
}
MARKER = {
    "loss_abs_diff": dict(marker="o", facecolor="white", edgecolor="#333333"),
    "grad_norm_abs_diff": dict(marker="s", facecolor="#bdbdbd", edgecolor="#333333"),
    "param_update_rel_l2": dict(marker="^", facecolor="#1a1a1a", edgecolor="#1a1a1a"),
}

FLOOR = 1e-6      # log axis cannot show exact zeros; clipped here, noted in caption
ABSENT_Y = 6.0e3  # centre of the "no magnitude" band


def num(v):
    """Absolute value, or None when the field is empty (quantity absent)."""
    if v is None or v in ("", "None", "nan"):
        return None
    return abs(float(v))


def stats(values):
    """(median, min, max) over present values, or None if none are present."""
    present = [v for v in values if v is not None]
    if not present:
        return None
    return statistics.median(present), min(present), max(present)


def load():
    """Return group label -> {signal: (median, min, max) | None}, normalized."""
    with open(ORACLE_CSV) as fh:
        oracle_rows = list(csv.DictReader(fh))
    with open(FAULT_CSV) as fh:
        fault_rows = list(csv.DictReader(fh))

    groups = {}

    label = "Oracle\n(no fault)"
    groups[label] = {}
    for sig in SIGNALS:
        vals = [num(r[sig]) for r in oracle_rows]
        st = stats(vals)
        groups[label][sig] = None if st is None else tuple(
            v / THRESHOLD[sig] for v in st)

    for fault, label in [("execution", "Execution\nfault"),
                         ("numeric", "Numerical\nfault"),
                         ("training", "Training\nfault")]:
        sub = [r for r in fault_rows if r["fault"] == fault]
        groups[label] = {}
        for sig in SIGNALS:
            st = stats([num(r[sig]) for r in sub])
            groups[label][sig] = None if st is None else tuple(
                v / THRESHOLD[sig] for v in st)
    return groups, len(oracle_rows), len(fault_rows)


groups, n_oracle, n_fault = load()

fig, ax = plt.subplots(figsize=(3.4, 2.6))
labels = list(groups)
offsets = {"loss_abs_diff": -0.24, "grad_norm_abs_diff": 0.0,
           "param_update_rel_l2": 0.24}

# band for quantities that do not exist, visually separated from the data area
ax.axhspan(1.2e3, 3.0e4, facecolor="#f2f2f2", zorder=0)
ax.axhline(1.2e3, color="#999999", linewidth=0.6, linestyle="-", zorder=1)

for gi, label in enumerate(labels):
    for sig in SIGNALS:
        x = gi + offsets[sig]
        st = groups[label][sig]
        style = dict(MARKER[sig])
        if st is None:
            ax.scatter(x, ABSENT_Y, marker="x", s=30, linewidths=1.2,
                       color="#333333", zorder=4)
            continue
        med, lo, hi = st
        lo_p, hi_p = max(lo, FLOOR), max(hi, FLOOR)
        ax.plot([x, x], [lo_p, hi_p], color="#777777", linewidth=0.8, zorder=2)
        ax.scatter(x, max(med, FLOOR), s=30, linewidths=0.9, zorder=3,
                   marker=style["marker"], facecolors=style["facecolor"],
                   edgecolors=style["edgecolor"])

ax.axhline(1.0, color="#c0392b", linewidth=0.9, linestyle="--", zorder=2)
ax.text(3.42, 1.5, "fires", fontsize=6.0, color="#c0392b", ha="right")

ax.set_yscale("log")
ax.set_ylim(3e-7, 3.0e4)
ax.set_xlim(-0.55, 3.55)
ax.set_xticks(range(len(labels)))
ax.set_xticklabels(labels, fontsize=6.6)
ax.set_yticks([1e-6, 1e-4, 1e-2, 1, 1e2, ABSENT_Y])
ax.set_yticklabels(["$10^{-6}$", "$10^{-4}$", "$10^{-2}$", "1", "$10^{2}$",
                    "n/a"], fontsize=7)
ax.set_ylabel("Signal / detection threshold", fontsize=7.5)
ax.tick_params(axis="x", length=0)
ax.grid(True, axis="y", which="major", linestyle=":", linewidth=0.5,
        color="#cccccc", zorder=0)
ax.set_axisbelow(True)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)

handles = [
    plt.Line2D([], [], linestyle="none", marker=MARKER[s]["marker"],
               markerfacecolor=MARKER[s]["facecolor"],
               markeredgecolor=MARKER[s]["edgecolor"], markersize=4.2,
               label=SIGNAL_LABEL[s])
    for s in SIGNALS
]
handles.append(plt.Line2D([], [], linestyle="none", marker="x", color="#333333",
                          markersize=4.6, label="absent"))
ax.legend(handles=handles, fontsize=6.0, loc="lower left", ncol=4,
          frameon=False, handletextpad=0.25, columnspacing=0.7,
          borderaxespad=0.1, bbox_to_anchor=(-0.02, -0.02))

fig.tight_layout(pad=0.25)
out = "figures/signal_magnitude.pdf"
fig.savefig(out, bbox_inches="tight")
print("wrote", out, "| oracle rows:", n_oracle, "| fault rows:", n_fault)
