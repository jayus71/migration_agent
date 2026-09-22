#!/usr/bin/env python3
"""Current migration comparison, with the historical plot retained as a helper."""
from make_cost_quality import draw_cost_quality
from make_repair_by_budget import draw_repair_by_budget
from paper_plot_style import panel_label, plt, save_figure
from make_unified_results import build_figure as build_unified_figure, export_tables, export_figure, load_data


def build_historical_figure():
    # Match ICLR's 5.5-inch text width so labels retain their intended size.
    fig, axes = plt.subplots(1, 2, figsize=(5.5, 2.8))
    draw_cost_quality(axes[0])
    draw_repair_by_budget(axes[1])
    for label in axes[0].texts:
        if "lower token cost than" in label.get_text():
            label.set_text(label.get_text().replace(" than ", "\nthan "))
    axes[0].set_xlabel("Tokens per accepted repair\n(K, log scale)")
    axes[1].legend(loc="lower center", bbox_to_anchor=(0.5, 1.015), ncol=2,
                   frameon=False, handlelength=2, columnspacing=0.8,
                   handletextpad=0.4, borderaxespad=0)
    panel_label(axes[0], "(a)")
    axes[1].text(-0.18, 1.04, "(b)", transform=axes[1].transAxes,
                 ha="left", va="bottom", fontsize=9, fontweight="bold")
    fig.subplots_adjust(left=0.09, right=0.99, bottom=0.22, top=0.76, wspace=0.5)
    return fig


def build_figure():
    return build_unified_figure()


def main():
    export_tables(load_data())
    export_figure()


if __name__ == "__main__":
    main()
