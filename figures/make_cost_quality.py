#!/usr/bin/env python3
"""Token cost against first-attempt repair rate on the 50-instance MindSpore pool.

All values are taken from Table I of the manuscript; this script only plots
them, so the figure cannot drift from the table.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# name, tokens (millions), verified rate (%), family
# Row labels match Table I exactly; "All checks, unordered" was renamed there.
POINTS = [
    ("Execution-only",        0.15,  58.0, "reduced"),
    ("All checks, unordered", 0.18,  66.0, "reduced"),
    ("Direct LLM",            1.58,  72.0, "baseline"),
    ("SWE-agent",             7.64,  72.0, "baseline"),
    ("MatchFixAgent",         5.21,  74.0, "baseline"),
    ("LADDER (ours)",         0.19,  84.0, "ours"),
]

STYLE = {
    "reduced":  dict(marker="o", s=46, facecolor="white", edgecolor="#666666", zorder=3),
    "baseline": dict(marker="s", s=46, facecolor="#bdbdbd", edgecolor="#444444", zorder=3),
    "ours":     dict(marker="*", s=210, facecolor="#1a1a1a", edgecolor="#1a1a1a", zorder=4),
}
# Label placement in typographic offsets from the marker, not data coordinates.
# The three cheapest methods sit against the left spine, so their labels are
# left-aligned and grow rightwards into empty space; centring them there pushed
# the text outside the axes.
OFFSET = {
    # name:                  (dx_pt, dy_pt, horizontal align, vertical align)
    "Execution-only":        (6.0,  -7.0, "left",   "center"),
    "All checks, unordered": (6.0,   4.0, "left",   "center"),
    "Direct LLM":            (0.0,   5.0, "center", "bottom"),
    "SWE-agent":             (0.0,  -5.0, "center", "top"),
    "MatchFixAgent":         (-1.0,  5.0, "right",  "bottom"),
    "LADDER (ours)":         (7.0,  -3.0, "left",   "center"),
}

fig, ax = plt.subplots(figsize=(3.4, 2.5))

for name, tok, rate, fam in POINTS:
    st = dict(STYLE[fam])
    ax.scatter(tok, rate, facecolors=st.pop("facecolor"),
               edgecolors=st.pop("edgecolor"), linewidths=0.9, **st)
    dx, dy, ha, va = OFFSET[name]
    weight = "bold" if fam == "ours" else "normal"
    # A surface-coloured halo keeps a label legible where it crosses a gridline
    # (SWE-agent sits on the 70% line). Padding is minimal so the box reads as
    # breathing room rather than as a drawn container.
    ax.annotate(name, (tok, rate), xytext=(dx, dy),
                textcoords="offset points", fontsize=6.2, ha=ha, va=va,
                fontweight=weight, zorder=5,
                bbox=dict(boxstyle="square,pad=0.12", facecolor="white",
                          edgecolor="none", alpha=0.72))

ax.set_xscale("log")
ax.set_xlabel("Tokens consumed over the pool (M, log scale)", fontsize=7.5)
ax.set_ylabel("First-attempt repair rate (\\%)", fontsize=7.5)
ax.set_xlim(0.10, 14)
# Headroom above the star for the annotation, which used to sit mid-plot and
# collide with the MatchFixAgent label.
ax.set_ylim(50, 93)
ax.set_xticks([0.1, 0.3, 1, 3, 10])
ax.set_xticklabels(["0.1", "0.3", "1", "3", "10"])
ax.tick_params(labelsize=7)
# Solid hairline grid: dashing reads as a threshold or projection when it is
# only a grid.
ax.grid(True, which="major", linestyle="-", linewidth=0.5, color="#dcdcdc", zorder=0)
ax.set_axisbelow(True)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)

# Connector between the two endpoints the annotation compares. The annotation
# itself sits in the empty space above the star rather than at the midpoint,
# where it previously overlapped the MatchFixAgent label and was crossed by this
# line.
ax.annotate("", xy=(0.19, 84.0), xytext=(5.21, 74.0),
            arrowprops=dict(arrowstyle="-", linestyle="--", linewidth=0.6,
                            color="#9a9a9a", shrinkA=10, shrinkB=8))
ax.text(0.205, 86.4, "$27\\times$ fewer tokens,\nhigher rate", fontsize=6.2,
        color="#555555", ha="left", va="bottom", style="italic")

fig.tight_layout(pad=0.25)
fig.savefig("figures/cost_quality.pdf", bbox_inches="tight")
print("wrote figures/cost_quality.pdf")
