#!/usr/bin/env python3
"""Signal composition on the separate 12-task matched ablation."""
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

from paper_data import signal_ablation
from paper_plot_style import BLUE, INK, plt, save_figure


def main():
    counts, totals = signal_ablation()
    rates = counts / totals
    fig, ax = plt.subplots(figsize=(3.4, 1.6))
    cmap = LinearSegmentedColormap.from_list("acceptance", ["#f1f1f1", BLUE])
    ax.imshow(rates, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    for i, j in np.ndindex(counts.shape):
        ax.text(j, i, f"{int(counts[i, j])}/{int(totals[j])}",
                ha="center", va="center", color="white" if rates[i, j] > 0.5 else INK,
                fontsize=9, fontweight="bold")
    ax.set_xticks(range(3), ["Execution", "Forward\nvalues", "Gradients,\nupdates"])
    ax.set_yticks(range(3), ["Execution", "+ forward values", "+ gradients, updates"])
    ax.set_ylabel("Feedback supplied")
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.subplots_adjust(left=0.39, right=0.99, top=0.98, bottom=0.22)
    save_figure(fig, "staircase_effect")


if __name__ == "__main__":
    main()
