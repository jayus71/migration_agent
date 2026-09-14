"""Shared typography and export settings for the manuscript's data plots."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

FIG_DIR = Path(__file__).resolve().parent
INK = "#202020"
GRAY = "#686868"
BLUE = "#0072b2"
GREEN = "#007c61"
ORANGE = "#d55e00"

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["STIXGeneral"],
    "mathtext.fontset": "stix",
    "font.size": 8,
    "axes.labelsize": 8,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "legend.fontsize": 7,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.dpi": 300,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.6,
    "axes.edgecolor": GRAY,
    "text.color": INK,
    "axes.labelcolor": INK,
})


def save_figure(fig, name):
    for extension in ("pdf", "png"):
        fig.savefig(FIG_DIR / f"{name}.{extension}", bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    print(f"Wrote figures/{name}.pdf and .png")


def panel_label(ax, label):
    ax.text(0, 1.04, label, transform=ax.transAxes, ha="left", va="bottom",
            fontsize=9, fontweight="bold")
