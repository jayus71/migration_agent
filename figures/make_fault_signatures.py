#!/usr/bin/env python3
"""Observed teacher-forced signatures; unmeasured crash metrics remain missing."""
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle

from paper_data import fault_signatures
from paper_plot_style import BLUE, GRAY, INK, plt, save_figure


def draw_fault_signatures(ax):
    values = fault_signatures()
    ax.imshow(np.ma.masked_invalid(values), cmap=ListedColormap(["#f1f1f1", BLUE]),
              vmin=0, vmax=1, aspect="auto")
    for i, j in np.ndindex(values.shape):
        value = values[i, j]
        missing = np.isnan(value)
        if missing:
            ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1,
                                   facecolor="#e7e7e7", edgecolor="#cccccc",
                                   hatch="///", linewidth=0))
        ax.text(j, i, "n/a" if missing else ("+" if value else "-"),
                ha="center", va="center", fontsize=8 if missing else 11,
                color=GRAY if missing else ("white" if value else INK))
    ax.set_xticks(range(4), ["Execution", "Loss", "Gradient", "Update"])
    ax.set_yticks(range(5), ["Healthy", "Execution", "Forward-value", "Gradient", "Update"])
    ax.set_xlabel("Diagnostic check")
    ax.set_ylabel("Injected fault")
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)


def main():
    fig, ax = plt.subplots(figsize=(3.4, 2.2))
    draw_fault_signatures(ax)
    fig.tight_layout(pad=0.4)
    save_figure(fig, "fault_signatures")


if __name__ == "__main__":
    main()
