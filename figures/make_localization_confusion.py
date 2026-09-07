#!/usr/bin/env python3
"""Localization confusion matrix from Experiment K.

LADDER's three-layer diagnosis correctly localises 48/50 faults (96% accuracy)
on the full 50-instance pool. The two misclassified instances are both
numerical faults predicted as execution (NU-07-A, NU-07-B).

Source: data/experiments/11_experiment_K_layer_localization/results/
        section65_fault_pool_localization_confusion_matrix.csv
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# From section65_fault_pool_localization_confusion_matrix.csv
LABELS = ["Execution", "Numerical", "Gradient /\nupdate"]
MATRIX = np.array([
    [20,  0,  0],
    [ 2, 12,  0],
    [ 0,  0, 16],
])

INK   = "#1a1a1a"
MUTED = "#5c5c5c"

cmap = LinearSegmentedColormap.from_list(
    "conf", ["#f7fbff", "#2171b5"], N=256)

fig, ax = plt.subplots(figsize=(3.0, 2.6))

im = ax.imshow(MATRIX, cmap=cmap, vmin=0, vmax=20, aspect="auto")

for i in range(3):
    for j in range(3):
        v = MATRIX[i, j]
        color = "white" if v >= 10 else INK
        weight = "bold" if i == j else "normal"
        ax.text(j, i, str(v), ha="center", va="center",
                fontsize=11, fontweight=weight, color=color)

ax.set_xticks(np.arange(3))
ax.set_xticklabels(LABELS, fontsize=7.5, color=INK)
ax.set_yticks(np.arange(3))
ax.set_yticklabels(LABELS, fontsize=7.5, color=INK)
ax.set_xlabel("Predicted layer", fontsize=8, color=INK, labelpad=6)
ax.set_ylabel("True layer", fontsize=8, color=INK, labelpad=6)
ax.tick_params(length=0)
ax.xaxis.set_ticks_position("bottom")

# Accuracy annotation
ax.text(2, -0.65, "96% accuracy\n(48 / 50)", fontsize=7.5, color="#1a6b1a",
        ha="center", va="bottom", fontweight="bold")

# Mark the two misclassifications with a circle around the off-diagonal cell
rect = plt.Rectangle((-.42, 0.58), 0.84, 0.84, linewidth=1.2,
                      edgecolor="#d03b3b", facecolor="none", linestyle="--",
                      zorder=5)
ax.add_patch(rect)
ax.annotate("2 mis-\nclassified", xy=(0.0, 1.0), xytext=(-0.9, 2.2),
            fontsize=5.5, color="#d03b3b", ha="center", va="center",
            fontstyle="italic",
            arrowprops=dict(arrowstyle="-|>", color="#d03b3b",
                            linewidth=0.7, mutation_scale=5))

for spine in ax.spines.values():
    spine.set_visible(False)

fig.tight_layout(pad=0.5)
fig.savefig("figures/localization_confusion.pdf", bbox_inches="tight")
fig.savefig("figures/localization_confusion.png", dpi=200, bbox_inches="tight")
print("wrote figures/localization_confusion.pdf + .png")
