#!/usr/bin/env python3
"""Staircase effect: each added signal repairs exactly the fault class it measures.

Data from Table II panel (b) of the manuscript. Three feedback conditions on 12
matched tasks (four model families, one fault per stage). Hard-coded to match
the table; the figure cannot drift from it.

Source: conference_101719.tex, Table tab:feedback-ablation panel (b).
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Table II panel (b): rows are feedback conditions, columns are fault stages.
# Each cell is (repaired, total).
DATA = {
    "Execution only":           {"Execution": 4, "Forward\nvalues": 0, "Gradients,\nupdates": 0},
    "Execution +\nforward":     {"Execution": 4, "Forward\nvalues": 4, "Gradients,\nupdates": 0},
    "All three\n(LADDER)":      {"Execution": 4, "Forward\nvalues": 4, "Gradients,\nupdates": 4},
}

TOTAL = 4
CONDITIONS = list(DATA.keys())
STAGES = ["Execution", "Forward\nvalues", "Gradients,\nupdates"]

INK = "#1a1a1a"
MUTED = "#5c5c5c"
EDGE = "#9a9a9a"

COLORS = ["#6baed6", "#3182bd", "#08519c"]

fig, ax = plt.subplots(figsize=(3.4, 2.4))

x = np.arange(len(STAGES))
width = 0.24
offsets = [-width, 0, width]

for i, cond in enumerate(CONDITIONS):
    vals = [DATA[cond][s] for s in STAGES]
    bars = ax.bar(x + offsets[i], vals, width, color=COLORS[i],
                  edgecolor="white", linewidth=0.6, label=cond, zorder=3)
    for bar, v in zip(bars, vals):
        if v > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.12,
                    str(v), ha="center", va="bottom", fontsize=7.0, color=INK,
                    fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels(STAGES, fontsize=7.5, color=INK)
ax.set_ylabel("Faults repaired (out of 4)", fontsize=7.5, color=INK)
ax.set_ylim(0, 5.2)
ax.set_yticks([0, 1, 2, 3, 4])
ax.tick_params(labelsize=7, color=EDGE)
ax.grid(True, axis="y", linestyle="-", linewidth=0.5, color="#e2e2e2", zorder=0)
ax.set_axisbelow(True)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(EDGE)
    ax.spines[side].set_linewidth(0.7)

# Arrows showing "adding this signal repairs this fault class"
arrow_kw = dict(arrowstyle="-|>", mutation_scale=7, linewidth=0.9, zorder=5)
# Arrow 1: execution signal → execution faults
ax.annotate("", xy=(0 - width, 4.55), xytext=(0 - width, 5.05),
            arrowprops=dict(color=COLORS[0], **arrow_kw))
# Arrow 2: adding forward → forward faults
ax.annotate("", xy=(1, 4.55), xytext=(1, 5.05),
            arrowprops=dict(color=COLORS[1], **arrow_kw))
# Arrow 3: adding gradient → gradient faults
ax.annotate("", xy=(2 + width, 4.55), xytext=(2 + width, 5.05),
            arrowprops=dict(color=COLORS[2], **arrow_kw))

leg = ax.legend(fontsize=6.2, loc="upper left", frameon=True, framealpha=0.9,
                edgecolor="#dcdcdc", ncol=1, handlelength=1.2, handletextpad=0.4,
                borderpad=0.4, labelspacing=0.5)
leg.get_frame().set_linewidth(0.6)

fig.tight_layout(pad=0.3)
fig.savefig("figures/staircase_effect.pdf", bbox_inches="tight")
print("wrote figures/staircase_effect.pdf")
