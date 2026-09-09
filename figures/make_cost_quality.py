#!/usr/bin/env python3
"""Original Fixed50 acceptance against tokens per accepted repair."""
from paper_data import METHODS, METHOD_LABELS, fixed50
from paper_plot_style import BLUE, GRAY, INK, plt, save_figure

OFFSETS = [(6, -5, "left", "top"), (6, 4, "left", "bottom"),
           (0, -6, "center", "top"), (0, -6, "center", "top"),
           (-2, 6, "right", "bottom"), (8, -2, "left", "center")]


def draw_cost_quality(ax):
    frame = fixed50()
    for method, label, (dx, dy, ha, va) in zip(METHODS, METHOD_LABELS, OFFSETS):
        row = frame.loc[method]
        x, y = row.tokens_per_accepted_repair / 1000, row.repair_at_1 * 100
        ours = method == "r_hier"
        ax.scatter(x, y, marker="*" if ours else ("o" if method in METHODS[:2] else "s"),
                   s=105 if ours else 30, facecolor=BLUE if ours else "white",
                   edgecolor=BLUE if ours else GRAY, linewidth=0.8, zorder=3)
        ax.annotate(label, (x, y), xytext=(dx, dy), textcoords="offset points",
                    fontsize=7, ha=ha, va=va, fontweight="bold" if ours else "normal",
                    bbox=dict(facecolor="white", edgecolor="none", pad=0.7))
    ratio = (frame.loc["r_matchfix", "tokens_per_accepted_repair"]
             / frame.loc["r_hier", "tokens_per_accepted_repair"])
    ax.text(0.04, 0.95, f"{ratio:.0f}x lower token cost than MatchFixAgent",
            transform=ax.transAxes, va="top", fontsize=7, color=INK)
    ax.set_xscale("log")
    ax.set_xlim(2.8, 300)
    ax.set_ylim(50, 94)
    ax.set_xticks([3, 10, 30, 100, 300], ["3", "10", "30", "100", "300"])
    ax.set_yticks([50, 60, 70, 80, 90])
    ax.set_xlabel("Tokens per accepted repair (K, log scale)")
    ax.set_ylabel("Acceptance on first attempt (%)")
    ax.grid(which="major", linewidth=0.4, color="#dddddd")
    ax.set_axisbelow(True)


def main():
    fig, ax = plt.subplots(figsize=(3.4, 2.6))
    draw_cost_quality(ax)
    fig.tight_layout(pad=0.4)
    save_figure(fig, "cost_quality")


if __name__ == "__main__":
    main()
