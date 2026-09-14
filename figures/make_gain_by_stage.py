#!/usr/bin/env python3
"""Original Fixed50 acceptance by fault stage, from the archived summary."""
import numpy as np

from paper_data import METHODS, METHOD_LABELS, STAGES, fixed50
from paper_plot_style import BLUE, GREEN, INK, ORANGE, plt, save_figure

COLORS = ["#eeeeee", "#bbbbbb", "#86bfdc", ORANGE, GREEN, BLUE]
HATCHES = ["...", "//", "\\\\", "xx", "--", ""]


def draw_gain_by_stage(ax):
    frame = fixed50()
    x = np.arange(len(STAGES))
    width = 0.13
    for i, (method, label, color, hatch) in enumerate(zip(METHODS, METHOD_LABELS, COLORS, HATCHES)):
        row = frame.loc[method]
        rates = [100 * row[f"{stage}_success"] / row[f"{stage}_instances"] for stage in STAGES]
        ax.bar(x + (i - 2.5) * width, rates, width * 0.92, label=label,
               color=color, hatch=hatch, edgecolor=INK, linewidth=0.4, zorder=3)
    totals = [int(frame.iloc[0][f"{stage}_instances"]) for stage in STAGES]
    labels = ["Execution", "Forward values", "Gradients, updates"]
    ax.set_xticks(x, [f"{label}\n(n = {total})" for label, total in zip(labels, totals)])
    ax.set_ylim(0, 105)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_ylabel("Accepted within four attempts (%)")
    ax.grid(axis="y", linewidth=0.4, color="#dddddd")
    ax.set_axisbelow(True)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.015), ncol=3,
              frameon=False, handlelength=1.3, columnspacing=0.9,
              handletextpad=0.4, borderaxespad=0)


def main():
    fig, ax = plt.subplots(figsize=(3.6, 2.8))
    draw_gain_by_stage(ax)
    fig.subplots_adjust(left=0.15, right=0.99, bottom=0.16, top=0.78)
    save_figure(fig, "gain_by_stage")


if __name__ == "__main__":
    main()
