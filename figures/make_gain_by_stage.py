#!/usr/bin/env python3
"""Where the gain comes from: methods converge at execution, diverge at gradients.

Data from Table I of the manuscript. Six methods, three fault stages. Hard-coded
to match the table; the figure cannot drift from it.

Source: conference_101719.tex, Table tab:main-results.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Table I, by fault stage.  (repaired, total) per method per stage.
METHODS = [
    ("Execution-only",     [14, 20], [ 7, 14], [12, 16]),
    ("Unordered",          [14, 20], [ 8, 14], [12, 16]),
    ("Direct LLM",         [18, 20], [ 8, 14], [14, 16]),
    ("SWE-agent",          [20, 20], [11, 14], [15, 16]),
    ("MatchFixAgent",      [20, 20], [14, 14], [13, 16]),
    ("LADDER",             [20, 20], [14, 14], [16, 16]),
]

STAGES = ["Execution\n(20)", "Forward values\n(14)", "Gradients, updates\n(16)"]
TOTALS = [20, 14, 16]

INK = "#1a1a1a"
MUTED = "#5c5c5c"
EDGE = "#9a9a9a"

# Colors: reduced = light gray, baselines = medium gray shades, ours = dark
PAL = {
    "Execution-only":  "#c6dbef",
    "Unordered":       "#9ecae1",
    "Direct LLM":      "#6baed6",
    "SWE-agent":       "#4292c6",
    "MatchFixAgent":   "#2171b5",
    "LADDER":          "#08306b",
}

fig, ax = plt.subplots(figsize=(3.4, 2.6))

n_methods = len(METHODS)
n_stages = len(STAGES)
x = np.arange(n_stages)
total_width = 0.78
width = total_width / n_methods

for i, (name, *stages) in enumerate(METHODS):
    rates = [s[0] / s[1] * 100 for s in stages]
    offset = (i - (n_methods - 1) / 2) * width
    bars = ax.bar(x + offset, rates, width * 0.92, color=PAL[name],
                  edgecolor="white", linewidth=0.4, label=name, zorder=3)

ax.set_xticks(x)
ax.set_xticklabels(STAGES, fontsize=7.2, color=INK)
ax.set_ylabel("Repair rate (%)", fontsize=7.5, color=INK)
ax.set_ylim(0, 115)
ax.set_yticks([0, 25, 50, 75, 100])
ax.tick_params(labelsize=7, color=EDGE)
ax.grid(True, axis="y", linestyle="-", linewidth=0.5, color="#e2e2e2", zorder=0)
ax.set_axisbelow(True)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(EDGE)
    ax.spines[side].set_linewidth(0.7)

# Annotation: highlight the gradient/update stage
ax.annotate("gap here", xy=(2 + 0.35, 81.3), xytext=(2 + 0.35, 108),
            fontsize=6.5, color="#d03b3b", ha="center", va="bottom",
            fontweight="bold",
            arrowprops=dict(arrowstyle="-|>", color="#d03b3b",
                            linewidth=0.8, mutation_scale=6))

leg = ax.legend(fontsize=5.6, loc="upper center", bbox_to_anchor=(0.5, 1.22),
                frameon=True, framealpha=0.92, edgecolor="#dcdcdc", ncol=3,
                handlelength=1.0, handletextpad=0.3, borderpad=0.4,
                labelspacing=0.35, columnspacing=0.8)
leg.get_frame().set_linewidth(0.6)

fig.tight_layout(pad=0.3, rect=[0, 0, 1, 0.88])
fig.savefig("figures/gain_by_stage.pdf", bbox_inches="tight")
fig.savefig("figures/gain_by_stage.png", dpi=200, bbox_inches="tight")
print("wrote figures/gain_by_stage.pdf + .png")
