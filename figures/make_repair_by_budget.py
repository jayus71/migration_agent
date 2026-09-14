#!/usr/bin/env python3
"""Original Fixed50 cumulative acceptance at the recorded attempt budgets."""
from paper_data import METHODS, METHOD_LABELS, budget_acceptance
from paper_plot_style import BLUE, GRAY, GREEN, INK, ORANGE, plt, save_figure

STYLES = [
    (GRAY, "o", ":"),
    (GRAY, "D", "--"),
    (INK, "s", "-"),
    (ORANGE, "+", "--"),
    (GREEN, "^", "-."),
    (BLUE, "*", "-"),
]


def draw_repair_by_budget(ax):
    rates = budget_acceptance()
    budgets = rates.columns.to_numpy()
    for method, label, (color, marker, linestyle) in zip(METHODS, METHOD_LABELS, STYLES):
        ours = method == "r_hier"
        ax.plot(budgets, rates.loc[method].to_numpy() * 100, label=label,
                color=color, marker=marker, linestyle=linestyle,
                linewidth=1.5 if ours else 1.0,
                markersize=7 if ours else (5.5 if marker == "s" else 4.5),
                markerfacecolor=color if ours else "white",
                markeredgewidth=0.9, zorder=4 if ours else 3)
    for budget, rate in rates.loc["r_hier"].items():
        ax.annotate(f"{rate:.0%}", (budget, rate * 100), xytext=(0, 6),
                    textcoords="offset points", ha="center", va="bottom",
                    fontsize=7, color=BLUE)
    ax.set_xticks(budgets)
    ax.set_xlim(0.8, 4.3)
    ax.set_ylim(50, 109)
    ax.set_yticks([50, 60, 70, 80, 90, 100])
    ax.set_xlabel("Maximum repair attempts")
    ax.set_ylabel("Cumulative acceptance (%)")
    ax.grid(which="major", linewidth=0.4, color="#dddddd")
    ax.set_axisbelow(True)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.015), ncol=3,
              frameon=False, handlelength=2, columnspacing=0.8,
              handletextpad=0.4, borderaxespad=0)


def main():
    fig, ax = plt.subplots(figsize=(3.6, 2.8))
    draw_repair_by_budget(ax)
    fig.subplots_adjust(left=0.15, right=0.99, bottom=0.16, top=0.78)
    save_figure(fig, "repair_by_budget")


if __name__ == "__main__":
    main()
