#!/usr/bin/env python3
"""Stage-localization counts from the archived 50-instance diagnostic run."""
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

from paper_data import localization
from paper_plot_style import BLUE, INK, plt, save_figure


def draw_localization(ax):
    values = localization()
    cmap = LinearSegmentedColormap.from_list("localization", ["#f1f1f1", BLUE])
    ax.imshow(values, cmap=cmap, vmin=0, vmax=values.max(), aspect="auto")
    for i, j in np.ndindex(values.shape):
        ax.text(j, i, str(int(values[i, j])), ha="center", va="center", fontsize=10,
                color="white" if values[i, j] > values.max() / 2 else INK,
                fontweight="bold" if i == j else "normal")
    labels = ["Execution", "Forward\nvalues", "Gradients,\nupdates"]
    ax.set_xticks(range(3), labels)
    ax.set_yticks(range(3), labels)
    ax.set_xlabel("Predicted stage")
    ax.set_ylabel("True stage")
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)


def main():
    fig, ax = plt.subplots(figsize=(3.4, 2.4))
    draw_localization(ax)
    fig.tight_layout(pad=0.4)
    save_figure(fig, "localization_confusion")


if __name__ == "__main__":
    main()
