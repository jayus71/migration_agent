#!/usr/bin/env python3
"""Teacher-forced signatures and separate fault-pool localization counts."""
from make_fault_signatures import draw_fault_signatures
from make_localization_confusion import draw_localization
from paper_plot_style import panel_label, plt, save_figure


def main():
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.2))
    draw_fault_signatures(axes[0])
    draw_localization(axes[1])
    for ax, label in zip(axes, ["(a)", "(b)"]):
        panel_label(ax, label)
    fig.subplots_adjust(left=0.13, right=0.99, bottom=0.25, top=0.91, wspace=0.47)
    save_figure(fig, "fault_diagnosis")


if __name__ == "__main__":
    main()
