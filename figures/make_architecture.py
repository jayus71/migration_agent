#!/usr/bin/env python3
"""The migration-repair loop: paired execution, the ordered checks, repair.

Vector replacement for figures_to_be_redrawed/hierarchical_feedback_architecture.png,
which was a flattened raster (1691x930, about 243 DPI at full text width) whose
labels no longer match the manuscript. That PNG said "Execution Signal",
"Numerical Signal" and "first failing layer"; the paper says check and first
failing stage. A raster cannot be relabelled, so the figure is redrawn here.

Design notes, since an architecture diagram has no data to constrain it:
  - The three checks are drawn as a numbered ladder, because the ordering IS the
    contribution. Gate arrows carry "holds" downward, so the reader can see that
    a rung is only reachable once the rung above it passes.
  - Exactly one accent colour (FIRE, the same red Figure 1 uses for its
    threshold) marks the failure route out of a rung into the fixer. Everything
    structural stays neutral. The previous figure's gradients, drop shadows and
    clip-art icons are what made it read as a slide rather than a paper figure.
  - Node labels name the repair action each stage implies, which is the reason
    the stage index is useful at all.

Run with the lzf env:
    /opt/miniconda3/envs/lzf/bin/python figures/make_architecture.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# Shared with figures/make_divergence_trajectory.py so the two figures read as
# one system.
INK, MUTED, GRID = "#1a1a1a", "#5c5c5c", "#d4d4d4"
FIRE = "#d03b3b"          # failure route, reserved
SURFACE = "#f4f5f7"       # recessive band fill
# Darker than the hairline grey used for data figures: box borders and dashed
# routes have to survive grayscale printing.
EDGE = "#7f7f7f"

TITLE_FS, BODY_FS, PATH_FS = 8.0, 7.0, 7.0

fig, ax = plt.subplots(figsize=(7.0, 3.4))
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis("off")


def box(x0, y0, x1, y1, *, fc="white", ec=EDGE, lw=0.8, ls="solid", r=1.6, z=2):
    """Rounded node. Coordinates are the corners, not width/height."""
    p = FancyBboxPatch((x0, y0), x1 - x0, y1 - y0,
                       boxstyle=f"round,pad=0,rounding_size={r}",
                       facecolor=fc, edgecolor=ec, linewidth=lw,
                       linestyle=ls, zorder=z)
    ax.add_patch(p)
    return p


def arrow(xy_from, xy_to, *, color=MUTED, lw=0.9, ls="solid", z=4,
          style="-|>", conn="arc3,rad=0", ms=6):
    ax.add_patch(FancyArrowPatch(xy_from, xy_to, arrowstyle=style,
                                 mutation_scale=ms, color=color, linewidth=lw,
                                 linestyle=ls, connectionstyle=conn,
                                 shrinkA=0, shrinkB=0, zorder=z))


def title(x, y, s, *, ha="left", color=INK, fs=TITLE_FS, weight="bold"):
    ax.text(x, y, s, fontsize=fs, color=color, ha=ha, va="center",
            fontweight=weight, zorder=5)


def body(x, y, s, *, ha="left", color=MUTED, fs=BODY_FS, style="normal"):
    ax.text(x, y, s, fontsize=fs, color=color, ha=ha, va="center",
            style=style, zorder=5)


# ---------------------------------------------------------------- paired input
# Left column: the two executions the checks compare. Everything downstream is
# a difference between these two, so they are the entry point.
box(1.5, 42, 21.5, 78, fc=SURFACE, ec=EDGE)
title(2.8, 74.5, "Paired execution")
body(2.8, 70.4, "same inputs, seeds,", fs=6.6)
body(2.8, 66.8, "optimizer settings", fs=6.6)

box(3.0, 57.5, 20.0, 64.5)
title(4.2, 61.0, "Source $P$", fs=7.4)
body(13.2, 61.0, "PyTorch", fs=6.6)

box(3.0, 45.5, 20.0, 52.5)
title(4.2, 49.0, "Candidate $\\hat{P}$", fs=7.4)
body(15.0, 49.0, "target", fs=6.6)

# translator produces the first candidate
arrow((11.5, 57.5), (11.5, 52.5), color=EDGE, lw=0.8)
body(12.3, 55.0, "translate", fs=6.4)

# -------------------------------------------------------------------- the ladder
# Three rungs, numbered, top to bottom. The gate arrows between them are the
# whole point: a rung is reachable only once the one above it holds.
RUNG_X0, RUNG_X1 = 27.0, 63.0
RUNGS = [
    (70.0, 78.0, "1", "Execution",
     "runs to completion", "compatibility, lowering"),
    (54.0, 62.0, "2", "Forward value",
     "$\\Delta_{\\mathrm{loss}}$, module diff", "operator semantics"),
    (38.0, 46.0, "3", "Gradient / update",
     "$\\Delta_{\\mathrm{grad}}$, $\\Delta_{\\mathrm{param}}$", "autodiff, optimizer"),
]

for y0, y1, idx, name, quantity, implies in RUNGS:
    box(RUNG_X0, y0, RUNG_X1, y1)
    ymid = (y0 + y1) / 2
    # index badge, so identity is never position-alone
    ax.add_patch(FancyBboxPatch((RUNG_X0 + 1.1, ymid - 2.2), 4.0, 4.4,
                                boxstyle="round,pad=0,rounding_size=0.8",
                                facecolor=INK, edgecolor="none", zorder=3))
    ax.text(RUNG_X0 + 3.1, ymid, idx, fontsize=7.2, color="white",
            ha="center", va="center", fontweight="bold", zorder=4)
    title(RUNG_X0 + 6.6, ymid + 1.9, name, fs=7.6)
    body(RUNG_X0 + 6.6, ymid - 2.0, quantity, fs=6.6)
    body(RUNG_X1 - 1.2, ymid, implies, ha="right", fs=6.4, style="italic")

# gates between rungs
for (y_upper, y_lower) in [(70.0, 62.0), (54.0, 46.0)]:
    arrow((45.0, y_upper), (45.0, y_lower), color=EDGE, lw=1.1)
    body(46.0, (y_upper + y_lower) / 2, "if holds", fs=6.4)

# the two executions feed the ladder
arrow((21.5, 60.0), (RUNG_X0, 74.0), color=EDGE, lw=0.8,
      conn="angle3,angleA=0,angleB=90")

title(RUNG_X0 - 0.3, 84.0, "Ordered checks", fs=8.0)

# ------------------------------------------------------- failure route to fixer
# One accent colour, used only here. Each rung's failure exits right and joins a
# collector, so "whichever fails first" is a single visible path.
COLLECT_X = 68.0
for y0, y1, *_ in RUNGS:
    ymid = (y0 + y1) / 2
    arrow((RUNG_X1, ymid), (COLLECT_X, ymid), color=FIRE, lw=0.9)
ax.plot([COLLECT_X, COLLECT_X], [42.0, 74.0], color=FIRE, linewidth=0.9,
        zorder=3)
body(RUNG_X1 + 0.8, 79.6, "fails", color=FIRE, fs=6.6)

# fixer
box(72.0, 62.0, 98.0, 78.0)
title(73.4, 74.0, "Fixer")
body(73.4, 70.0, "edits at the reported stage", fs=6.6)
body(73.4, 66.4, "bounded scope, rollback", fs=6.6)
arrow((COLLECT_X, 70.0), (72.0, 70.0), color=FIRE, lw=0.9)

# Orchestrator sits between the fixer and acceptance, which is where it acts.
# It was previously loose text in the top band, where the loop route crossed it.
box(72.0, 55.0, 98.0, 61.5, ls=(0, (3, 2)))
title(73.4, 58.25, "Orchestrator", fs=7.4)
body(96.6, 58.25, "rounds, rollback", ha="right", fs=6.4)

# accepted candidate: the only exit that is not a failure
box(72.0, 42.0, 98.0, 54.0, ls=(0, (3, 2)))
title(73.4, 50.0, "Accepted")
body(73.4, 46.0, "all three checks hold", fs=6.6)
arrow((45.0, 38.0), (45.0, 33.0), color=EDGE, lw=0.9)
arrow((45.0, 33.0), (85.0, 33.0), color=EDGE, lw=0.9, style="-")
arrow((85.0, 33.0), (85.0, 42.0), color=EDGE, lw=0.9)
body(46.2, 34.6, "all hold", fs=6.4)

# ------------------------------------------------------------- the repair loop
# Routed above the ladder so it crosses nothing. This is what makes the figure a
# loop rather than a pipeline.
LOOP_Y = 90.5
ax.plot([85.0, 85.0], [78.0, LOOP_Y], color=MUTED, linewidth=0.9, zorder=3)
ax.plot([11.5, 85.0], [LOOP_Y, LOOP_Y], color=MUTED, linewidth=0.9, zorder=3)
arrow((11.5, LOOP_Y), (11.5, 78.0), color=MUTED, lw=0.9)
body(48.0, LOOP_Y + 2.2, "targeted patch, then re-verify from check 1",
     ha="center", fs=6.8)

# ------------------------------------------------------------- adapter boundary
# The checks are backend-independent; only this band changes per framework.
box(1.5, 8.0, 98.0, 24.0, fc=SURFACE, ec=EDGE, ls=(0, (3, 2)))
title(3.0, 20.0, "Common adapter interface", fs=7.6)
body(3.0, 15.8, "normalizes phase status, forward values, gradients, and "
                "parameter deltas into one report", fs=6.6)
body(3.0, 11.6, "torch4ms / MindSpore", fs=6.6, color=INK)
body(28.0, 11.6, "TorchAX / JAX", fs=6.6, color=INK)
body(52.0, 11.6, "the checks and their order are unchanged across both",
     fs=6.4, style="italic")
# Ties from the band to what it serves. The second one previously started at
# x=24, left of the ladder's left edge, so it read as an unfinished stroke.
arrow((33.0, 24.0), (33.0, 38.0), color=EDGE, lw=0.8, ls=(0, (2, 2)),
      style="-")
arrow((11.5, 42.0), (11.5, 24.0), color=EDGE, lw=0.8, ls=(0, (2, 2)),
      style="-")

fig.tight_layout(pad=0.2)
fig.savefig("figures/architecture.pdf", bbox_inches="tight")
fig.savefig("figures/architecture.png", bbox_inches="tight", dpi=200)
print("wrote figures/architecture.pdf")
