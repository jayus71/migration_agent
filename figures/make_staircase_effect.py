#!/usr/bin/env python3
"""Staircase effect: each added signal repairs exactly the fault class it measures.

Data from Table II panel (b) of the manuscript. Three feedback conditions on 12
matched tasks (four model families, one fault per stage). Hard-coded to match
the table; the figure cannot drift from it.

Source: conference_101719.tex, Table tab:feedback-ablation panel (b).

Visualised as a heatmap so the lower-triangular staircase pattern is immediately
visible: dark cells (4/4) form a staircase from top-left to bottom-right.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# Table II panel (b): 3 conditions × 3 fault stages, each out of 4.
CONDITIONS = ["Exec. only", "Exec. + forward", "All three (LADDER)"]
STAGES     = ["Execution", "Forward\nvalues", "Gradients,\nupdates"]
MATRIX = np.array([
    [4, 0, 0],
    [4, 4, 0],
    [4, 4, 4],
], dtype=float)

INK   = "#1a1a1a"
MUTED = "#5c5c5c"
EDGE  = "#9a9a9a"

cmap = LinearSegmentedColormap.from_list(
    "stair", ["#f0f0f0", "#6baed6", "#08519c"], N=256)

fig, ax = plt.subplots(figsize=(3.4, 2.2))

im = ax.imshow(MATRIX, cmap=cmap, vmin=0, vmax=4, aspect="auto")

# Cell labels
for i in range(len(CONDITIONS)):
    for j in range(len(STAGES)):
        v = int(MATRIX[i, j])
        color = "white" if v >= 3 else INK
        ax.text(j, i, f"{v}/4", ha="center", va="center",
                fontsize=9, fontweight="bold", color=color)

ax.set_xticks(np.arange(len(STAGES)))
ax.set_xticklabels(STAGES, fontsize=7.5, color=INK)
ax.set_yticks(np.arange(len(CONDITIONS)))
ax.set_yticklabels(CONDITIONS, fontsize=7.5, color=INK)
ax.tick_params(length=0)

# Staircase arrow along the diagonal
arrow_kw = dict(arrowstyle="-|>", color="#d03b3b", linewidth=1.2,
                mutation_scale=8)
ax.annotate("", xy=(2.38, 2.38), xytext=(-0.38, -0.38),
            arrowprops=arrow_kw, zorder=5)
ax.text(2.55, -0.15, "staircase", fontsize=6.5, color="#d03b3b",
        fontweight="bold", ha="left", va="center", rotation=-40)

for spine in ax.spines.values():
    spine.set_visible(False)

fig.tight_layout(pad=0.4)
fig.savefig("figures/staircase_effect.pdf", bbox_inches="tight")
fig.savefig("figures/staircase_effect.png", dpi=200, bbox_inches="tight")
print("wrote figures/staircase_effect.pdf + .png")
