#!/usr/bin/env python3
"""Measure text collisions and overflow in a matplotlib figure script.

Written because looking at renders does not work. A vision model cleared this
figure twice while text was in fact overlapping, and the author cleared it by
eye as well. Text position is computable, so it should be computed.

Usage:
    /opt/miniconda3/envs/lzf/bin/python figures/check_collisions.py <script.py>

The target script must build its figure at import time (all of the make_*.py
scripts do). This module imports it with a stubbed savefig, then walks every
Text artist on every axes and reports:

  OVERLAP   two text bounding boxes intersect
  OVERFLOW  a text bbox extends outside its own axes' bounds
  OFFCANVAS a text bbox extends outside the figure canvas

Exit code is 1 if anything is found, so it can gate a commit.
"""
import importlib.util
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load(path):
    """Import a figure script without letting it write files."""
    real_savefig = matplotlib.figure.Figure.savefig
    matplotlib.figure.Figure.savefig = lambda self, *a, **k: None
    try:
        spec = importlib.util.spec_from_file_location("_fig", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        matplotlib.figure.Figure.savefig = real_savefig
    return [plt.figure(n) for n in plt.get_fignums()]


def texts_of(ax):
    """Every Text artist on an axes that actually renders something.

    Tick labels are skipped when the axis is off: they still exist as artists on
    a hidden axis and would be reported as phantom collisions.
    """
    out = list(ax.texts)
    for t in (ax.title, ax.xaxis.label, ax.yaxis.label):
        out.append(t)
    if ax.axison:
        out += ax.get_xticklabels() + ax.get_yticklabels()
    return [t for t in out
            if t.get_text().strip() and t.get_visible()]


def overlap(a, b):
    """Intersection area of two bboxes, 0 if disjoint."""
    dx = min(a.x1, b.x1) - max(a.x0, b.x0)
    dy = min(a.y1, b.y1) - max(a.y0, b.y0)
    return dx * dy if dx > 0 and dy > 0 else 0.0


def label(t, ax_name):
    s = t.get_text().replace("\n", " / ")
    return f"[{ax_name}] {s[:44]!r}"


def check(fig, fig_name):
    """Return a list of finding strings for one figure."""
    r = fig.canvas.get_renderer()
    dpi = fig.dpi
    findings = []

    # Collect every text with its bbox in pixels, tagged by its axes.
    entries = []
    for i, ax in enumerate(fig.axes):
        name = f"ax{i}"
        for t in texts_of(ax):
            try:
                bb = t.get_window_extent(renderer=r)
            except Exception:
                continue
            if bb.width <= 0 or bb.height <= 0:
                continue
            entries.append((t, bb, name, ax))
    # figure-level texts (fig.text / suptitle) belong to no axes
    for t in fig.texts:
        if not t.get_text().strip():
            continue
        bb = t.get_window_extent(renderer=r)
        entries.append((t, bb, "fig", None))

    # 1. text-on-text overlap. Tolerance is deliberately tiny: the defect that
    #    shipped past two visual reviews was a 0.007in overlap.
    TOL_IN = 0.004
    tol_px2 = (TOL_IN * dpi) ** 2
    for i in range(len(entries)):
        for j in range(i + 1, len(entries)):
            t1, b1, n1, _ = entries[i]
            t2, b2, n2, _ = entries[j]
            a = overlap(b1, b2)
            if a > tol_px2:
                dx = (min(b1.x1, b2.x1) - max(b1.x0, b2.x0)) / dpi
                dy = (min(b1.y1, b2.y1) - max(b1.y0, b2.y0)) / dpi
                findings.append(
                    f"OVERLAP   {label(t1,n1)} x {label(t2,n2)}  "
                    f"({dx:.3f} x {dy:.3f} in)")

    # 2. text outside its own axes. Tick labels and axis labels live outside by
    #    design, so only in-axes texts (ax.texts) are checked.
    for t, bb, name, ax in entries:
        if ax is None or t not in ax.texts:
            continue
        ab = ax.get_window_extent(renderer=r)
        for side, amount in (("left", ab.x0 - bb.x0), ("right", bb.x1 - ab.x1),
                             ("bottom", ab.y0 - bb.y0), ("top", bb.y1 - ab.y1)):
            if amount / dpi > TOL_IN:
                findings.append(
                    f"OVERFLOW  {label(t,name)} exits {side} of its axes "
                    f"by {amount/dpi:.3f} in")

    # 3. text outside the canvas
    fw, fh = fig.get_size_inches()
    for t, bb, name, _ in entries:
        for side, amount in (("left", -bb.x0), ("right", bb.x1 - fw * dpi),
                             ("bottom", -bb.y0), ("top", bb.y1 - fh * dpi)):
            if amount / dpi > TOL_IN:
                findings.append(
                    f"OFFCANVAS {label(t,name)} exits {side} of the "
                    f"{fw}x{fh}in canvas by {amount/dpi:.3f} in")
    return findings


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    bad = 0
    for path in sys.argv[1:]:
        for k, fig in enumerate(load(path)):
            name = f"{path}#{k}"
            found = check(fig, name)
            print(f"=== {name}  ({fig.get_size_inches()[0]}x"
                  f"{fig.get_size_inches()[1]}in, {len(fig.axes)} axes) ===")
            if not found:
                print("  clean")
            for f in found:
                print("  " + f)
            bad += len(found)
        plt.close("all")
    print(f"\n{bad} finding(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
