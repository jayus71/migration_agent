#!/usr/bin/env python3
"""Original Fixed50 results: cost and cumulative acceptance by attempt budget."""
from make_cost_quality import draw_cost_quality
from make_repair_by_budget import draw_repair_by_budget
from paper_plot_style import panel_label, plt, save_figure


def build_figure():
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.65))
    draw_cost_quality(axes[0])
    draw_repair_by_budget(axes[1])
    panel_label(axes[0], "(a)")
    axes[1].text(-0.18, 1.04, "(b)", transform=axes[1].transAxes,
                 ha="left", va="bottom", fontsize=9, fontweight="bold")
    fig.subplots_adjust(left=0.07, right=0.99, bottom=0.19, top=0.8, wspace=0.34)
    return fig


def main():
    save_figure(build_figure(), "repair_comparison")


if __name__ == "__main__":
    main()
