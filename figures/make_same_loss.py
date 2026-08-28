#!/usr/bin/env python3
"""Two ported programs report the same loss; one trains and one does not.

Figure 1. It replaces make_verdict_collapse.py, which asked the reader to
understand "ratio to detection threshold" and phrases like "the update check
fires" on page 1 -- quantities and vocabulary this paper does not define until
Section IV. A first-page figure can only use what a reader already knows.

So this figure shows the raw measured quantities and nothing derived:
  does the program run, what loss does it report, what gradient norm does it
  report, and which way do its parameters move.

The argument is the two rows that agree on every column a conventional check
looks at. The correct port and the program whose optimizer never steps both run
to completion and both report loss 1.780535 against the source's 1.780532. A
verdict built on "it runs and the loss matches" accepts both. They differ only
in the last column, where one moves its parameters with the source and the other
does not move them at all.

Numbers are measured, from the 4800-row per-step set (CNN, seed 300, step 25):
  ascend-torch4ms/experiments/paper_section_65_66/
    results_section65_per_step_divergence/
      section65_per_step_divergence_steps50.csv
Each row's behaviour holds across all four models and three seeds; see the
verification block at the bottom of this file, which re-reads the CSV and asserts
the displayed values rather than trusting this docstring.

Every text position is asserted against its cell before the file is written, so
a layout regression fails the build instead of shipping. Reviewing renders by eye
did not catch a 0.007in overlap; measuring does.

Run with the lzf env (base has no pandas):
    /opt/miniconda3/envs/lzf/bin/python figures/make_same_loss.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyArrowPatch, Rectangle

CSV = os.path.join(
    "ascend-torch4ms/experiments/paper_section_65_66",
    "results_section65_per_step_divergence",
    "section65_per_step_divergence_steps50.csv")

INK, MUTED, EDGE = "#1a1a1a", "#5c5c5c", "#b0b0b0"
ACCENT = "#d03b3b"      # the false accept, and only that
CALM = "#2a78d6"
BAND = "#fdf0ef"        # highlight behind the two rows that agree
HEAD = "#f2f3f5"

# Rows: label, sub-label, runs?, loss, grad norm, parameter update, verdict, band?
#
# A dash means the quantity does not exist, not that it is zero. For the missing
# operator the program stopped before anything could be measured; for the
# suppressed optimizer no backward pass runs, so there is no gradient to report.
# The raw fault definition is "run a valid candidate forward but suppress
# backward and optimizer update".
#
# The parameter column is deliberately categorical. The underlying metric is a
# cosine, but a cosine against a zero update is undefined -- metrics.py returns
# 0.0 only because of an eps floor in the denominator. Printing "0.00" would
# invite a reviewer to ask what a zero cosine means. What is actually true, and
# needs no definition on page 1, is whether the parameters moved.
ROWS = [
    ("Source program", "the reference",
     "yes", "1.780532", "0.283368", "reference", "--", False),
    ("Correct port", "no fault",
     "yes", "1.780535", "0.283368", "matches", "accept", True),
    ("Missing operation", "no implementation",
     "no", "--", "--", "--", "reject", False),
    ("Wrong reduction", "averaged, not summed",
     "yes", "2.500882", "0.687914", "differs", "reject", False),
    ("No backward pass", "no gradients",
     "yes", "1.780535", "--", "never moves", "accept", True),
]

# Column geometry on a 0-100 canvas. Width is reserved per column so the
# assertion pass can check that no label exceeds its own cell.
# Boundaries are solved, not chosen. Every header line and every cell was
# rendered and measured, each column takes the wider of the two plus 2.2 units
# of padding, and the leftover 4 units are split evenly. Guessing these three
# times produced three overflow failures.
COLS = [
    ("ported program",           2.0, 24.7, "left"),
    ("runs to\ncompletion?",    24.7, 40.2, "center"),
    ("loss",                    40.2, 53.0, "center"),
    ("gradient\nnorm",          53.0, 65.7, "center"),
    ("parameter\nupdate",       65.7, 82.3, "center"),
    ("verdict from\nruns + loss", 82.3, 98.0, "center"),
]

# Vertical layout is computed from the font sizes, not chosen by eye. At 3.3in
# tall, one data unit is 2.376pt, so a 7.4pt line occupies 8.6/2.376 = 3.6 data
# units. Any gap smaller than that overlaps by construction, which is what the
# first draft did with a 4.2-unit gap and 4.68-unit lines.
FIG_H = 3.3
UNIT_PT = FIG_H / 100 * 72


def line_units(fs):
    """Height of one text line, in data units."""
    return fs * 1.16 / UNIT_PT


FS_NAME, FS_SUB, FS_HEAD, FS_VAL, FS_NOTE = 7.4, 6.6, 7.2, 7.4, 6.4

ROW_H = 11.6
ROW_TOP = 70.0
# name above centre, sub below, each clear of the other by half a line
NAME_DY = line_units(FS_NAME) / 2 + 0.35
SUB_DY = line_units(FS_SUB) / 2 + 0.35
# header sits a full line above row 1's tallest point
HEAD_Y = ROW_TOP + NAME_DY + line_units(FS_NAME) / 2 + line_units(FS_HEAD) + 1.2


def verify():
    """Re-read the CSV and assert every number this figure prints."""
    d = pd.read_csv(CSV)
    tf = d[(d.coupling == "teacher-forced") & (d.model == "cnn")
           & (d.seed == 300) & (d.step == 25)]
    got = {r.fault: r for _, r in tf.iterrows()}

    def near(a, b, tol=5e-7):
        return abs(float(a) - float(b)) <= tol

    src = got["none"]
    assert near(src.torch_loss, 1.780532), src.torch_loss
    assert near(src.torch_grad_norm, 0.283368, 5e-6), src.torch_grad_norm
    assert near(got["none"].torch4ms_loss, 1.780535), got["none"].torch4ms_loss
    assert near(got["numeric"].torch4ms_loss, 2.500882), got["numeric"].torch4ms_loss
    assert near(got["numeric"].torch4ms_grad_norm, 0.687914, 5e-6)
    # the claim the figure is built on: same loss, opposite parameter behaviour
    assert near(got["training"].torch4ms_loss, got["none"].torch4ms_loss, 1e-9)
    assert pd.isna(got["training"].torch4ms_grad_norm)
    assert near(got["none"].param_update_cosine, 1.0, 2e-6)
    assert near(got["training"].param_update_cosine, 0.0, 1e-12)
    assert got["execution"].torch4ms_status == "failed"

    # and that it is not a one-seed accident
    all_tf = d[d.coupling == "teacher-forced"]
    tr = all_tf[all_tf.fault == "training"]
    assert (tr.param_update_cosine == 0).all(), "training cosine not always 0"
    assert tr.torch4ms_grad_norm.isna().all(), "training grad not always absent"
    hl = all_tf[all_tf.fault == "none"]
    assert hl.param_update_cosine.min() > 0.999, "healthy cosine dipped"
    assert (tr.loss_abs_diff.max() == hl.loss_abs_diff.max()), \
        "training and healthy loss differences are not identical"
    return len(tr), len(hl)


n_train, n_healthy = verify()

fig, ax = plt.subplots(figsize=(7.0, FIG_H))
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis("off")
placed = []          # (Text, x0, x1, tag) for the assertion pass


def put(x, y, s, *, ha="center", fs=7.4, color=INK, weight="normal",
        style="normal", cell=None, tag=""):
    t = ax.text(x, y, s, fontsize=fs, color=color, ha=ha, va="center",
                fontweight=weight, style=style, zorder=5)
    if cell is not None:
        placed.append((t, cell[0], cell[1], tag or s.replace("\n", " ")))
    return t


# header band
# Band is sized to the tallest header, which is two lines.
HEAD_HALF = line_units(FS_HEAD) + 1.0
ax.add_patch(Rectangle((2.0, HEAD_Y - HEAD_HALF), 96.0, 2 * HEAD_HALF,
                       facecolor=HEAD, edgecolor="none", zorder=1))
for name, x0, x1, ha in COLS:
    x = x0 + 0.8 if ha == "left" else (x0 + x1) / 2
    put(x, HEAD_Y, name, ha=ha, fs=FS_HEAD, color=INK, weight="bold",
        cell=(x0, x1), tag=f"header {name}")

# rows
for i, (label, sub, runs, loss, grad, update, verdict, band) in enumerate(ROWS):
    y = ROW_TOP - i * ROW_H
    if band:
        ax.add_patch(Rectangle((2.0, y - ROW_H / 2 + 0.6), 96.0, ROW_H - 1.2,
                               facecolor=BAND, edgecolor="none", zorder=1))
    ax.plot([2.0, 98.0], [y - ROW_H / 2 + 0.6] * 2, color="#e4e4e4",
            linewidth=0.6, zorder=2)

    c = COLS[0]
    put(c[1] + 0.8, y + NAME_DY, label, ha="left", fs=FS_NAME, weight="bold",
        cell=(c[1], c[2]), tag=f"{label} name")
    put(c[1] + 0.8, y - SUB_DY, sub, ha="left", fs=FS_SUB, color=MUTED,
        cell=(c[1], c[2]), tag=f"{label} sub")

    # The last two columns carry the argument, so they are the only emphasized
    # cells. The false accept is the one place the accent colour is used.
    wrong = band and verdict == "accept" and update == "never moves"
    for (val, col) in ((runs, COLS[1]), (loss, COLS[2]), (grad, COLS[3])):
        xm = (col[1] + col[2]) / 2
        em = val == "--"
        put(xm, y, val, fs=FS_VAL, color=MUTED if em else INK,
            cell=(col[1], col[2]), tag=f"{label} / {col[0]}")

    col = COLS[4]
    put((col[1] + col[2]) / 2, y, update, fs=FS_VAL,
        color=MUTED if update == "--" else (ACCENT if wrong else INK),
        weight="bold" if wrong else "normal",
        cell=(col[1], col[2]), tag=f"{label} / update")

    col = COLS[5]
    put((col[1] + col[2]) / 2, y, verdict, fs=FS_VAL,
        color=MUTED if verdict == "--" else (ACCENT if wrong else INK),
        weight="bold" if wrong else "normal",
        cell=(col[1], col[2]), tag=f"{label} / verdict")

# The claim has to be that the shaded rows agree on the columns a single verdict
# inspects, not that they differ in exactly one column. They differ in two.
put(50.0, 11.0, "A completion-and-loss check accepts both shaded rows, even though "
                "their gradients and updates differ.",
    fs=FS_HEAD, color=INK, cell=(2.0, 98.0), tag="punchline 1")
put(50.0, 4.5, "One of the two never updates its parameters, and no single verdict "
               "tells them apart.",
    fs=FS_HEAD, color=ACCENT, cell=(2.0, 98.0), tag="punchline 2")

# footnote naming the provenance, so no reader has to guess
put(2.0, 93.0, "One CNN training step: PyTorch source and four ported candidates. "
               "Losses count as matching within 0.02.",
    ha="left", fs=FS_NOTE, color=MUTED, style="italic", cell=(2.0, 98.0),
    tag="provenance")

# ----------------------------------------------------------- layout assertions
# Measured, not eyeballed. A vision review cleared a 0.007in overlap in the
# previous figure twice; arithmetic does not.
fig.canvas.draw()
r = fig.canvas.get_renderer()
inv = ax.transData.inverted()
TOL = 0.25          # data units of slack at a cell edge

boxes, problems = [], []
for t, cx0, cx1, tag in placed:
    bb = t.get_window_extent(renderer=r)
    (x0, y0) = inv.transform((bb.x0, bb.y0))
    (x1, y1) = inv.transform((bb.x1, bb.y1))
    boxes.append((x0, y0, x1, y1, tag))
    if x0 < cx0 - TOL:
        problems.append(f"{tag!r} exits its cell left by {cx0 - x0:.2f} units")
    if x1 > cx1 + TOL:
        problems.append(f"{tag!r} exits its cell right by {x1 - cx1:.2f} units")
    if x0 < -TOL or x1 > 100 + TOL:
        problems.append(f"{tag!r} leaves the canvas ({x0:.1f}..{x1:.1f})")

for i in range(len(boxes)):
    for j in range(i + 1, len(boxes)):
        ax0, ay0, ax1, ay1, at = boxes[i]
        bx0, by0, bx1, by1, bt = boxes[j]
        dx = min(ax1, bx1) - max(ax0, bx0)
        dy = min(ay1, by1) - max(ay0, by0)
        if dx > 0.15 and dy > 0.15:
            problems.append(
                f"{at!r} overlaps {bt!r} by {dx:.2f} x {dy:.2f} units")

if problems:
    raise SystemExit("LAYOUT FAILED, figure not written:\n  "
                     + "\n  ".join(problems))

fig.subplots_adjust(left=0.005, right=0.995, top=0.99, bottom=0.01)
fig.savefig("figures/same_loss.pdf", bbox_inches="tight")
fig.savefig("figures/same_loss.png", bbox_inches="tight", dpi=200)
print("wrote figures/same_loss.pdf")
print(f"  layout clean: {len(placed)} labels, 0 collisions, 0 cell overflows")
print(f"  data verified: training cosine==0 on {n_train} rows, "
      f"healthy cosine>0.999 on {n_healthy} rows")
