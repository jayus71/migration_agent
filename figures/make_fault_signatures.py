#!/usr/bin/env python3
"""Fault signatures: each fault type triggers a distinct subset of detection layers.

Combines existing paper data (execution, numeric faults from
data/paper_section_65_66/) and Experiment C data (grad_wrong, param_wrong from
data/experiments/03_experiment_C_gradient_and_parameter_faults/). All under
teacher-forced coupling, which isolates each fault's signature from feedback-
loop amplification.

Thresholds from the paper: Δloss ≤ 0.02, Δgrad ≤ 0.05, Δparam ≤ 0.03.

Source: conference_101719.tex Section 6.5–6.6; EXPERIMENT_REQUEST_20260820.md
Experiment C.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# Detection matrix under teacher-forced coupling, aggregated across 4 models.
# 1 = threshold crossed for ≥1 model, 0 = never crossed.
# "Exec fail" is 1 if torch4ms_status != ok for any step.
#
# Data sources (teacher-forced, max across 4 models):
# - execution:  exec_fail=93/150, loss=3.8e-6, grad=2.1e-7, param=5.0e-6
# - numeric:    exec_fail=0, loss=1.16, grad=0.72, param=2.96
# - grad_wrong: exec_fail=0, loss=3.8e-6, grad>0.05@step1, param=0.50+
# - param_wrong:exec_fail=0, loss=3.8e-6, grad<0.05, param=0.19-0.99
FAULTS  = ["Execution", "Forward-value\n(numeric)", "Gradient\n(grad_wrong)", "Param. update\n(param_wrong)"]
METRICS = ["Execution\ncheck", "Δ loss\n> 0.02", "Δ gradient\n> 0.05", "Δ param update\n> 0.03"]

# rows = fault types, cols = detection metrics
MATRIX = np.array([
    [1, 0, 0, 0],   # execution: only exec check fires
    [0, 1, 1, 1],   # numeric: loss diverges, cascades to grad and param
    [0, 0, 1, 1],   # grad_wrong: gradient diverges, cascades to param
    [0, 0, 0, 1],   # param_wrong: only param update diverges
], dtype=float)

INK   = "#1a1a1a"
MUTED = "#5c5c5c"

cmap = LinearSegmentedColormap.from_list(
    "sig", ["#f5f5f5", "#2171b5"], N=256)

fig, ax = plt.subplots(figsize=(3.4, 2.4))

im = ax.imshow(MATRIX, cmap=cmap, vmin=0, vmax=1, aspect="auto")

for i in range(len(FAULTS)):
    for j in range(len(METRICS)):
        v = int(MATRIX[i, j])
        label = "\\u2713" if v else "—"
        color = "white" if v else "#c0c0c0"
        weight = "bold" if v else "normal"
        ax.text(j, i, label, ha="center", va="center",
                fontsize=11, fontweight=weight, color=color)

ax.set_xticks(np.arange(len(METRICS)))
ax.set_xticklabels(METRICS, fontsize=6.8, color=INK)
ax.set_yticks(np.arange(len(FAULTS)))
ax.set_yticklabels(FAULTS, fontsize=6.8, color=INK)
ax.tick_params(length=0)
ax.xaxis.set_ticks_position("top")
ax.xaxis.set_label_position("top")

# Remove right-side clutter; the diagonal pattern speaks for itself

for spine in ax.spines.values():
    spine.set_visible(False)

fig.tight_layout(pad=0.5)
fig.savefig("figures/fault_signatures.pdf", bbox_inches="tight")
fig.savefig("figures/fault_signatures.png", dpi=200, bbox_inches="tight")
print("wrote figures/fault_signatures.pdf + .png")
