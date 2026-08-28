#!/usr/bin/env python3
"""Assert every number printed in Table I of the manuscript.

Table I used to be Figure 1, drawn by make_same_loss.py. It was pure text in a
raster, so it is now a LaTeX table and the numbers live in conference_101719.tex
by hand. Hand-copied numbers drift, and the drawing script's verify() was the
only thing standing between the manuscript and a stale value, so that check
survives here without the plotting.

CLAUDE.md states the convention for the other direction: a figure plotting
numbers that also appear in a table hard-codes them with a comment naming the
source table. Table I is the inverse case -- the manuscript holds the numbers,
so this script re-reads the CSV and asserts what the table claims.

Run with the lzf env (base has no pandas):
    /opt/miniconda3/envs/lzf/bin/python figures/verify_table1.py

Exit code is 0 if the table matches the data, 1 if it does not, so it can gate
a commit.
"""
import os
import re
import sys

import pandas as pd

CSV = os.path.join(
    "ascend-torch4ms/experiments/paper_section_65_66",
    "results_section65_per_step_divergence",
    "section65_per_step_divergence_steps50.csv")
TEX = "conference_101719.tex"

# What Table I prints, row by row: (label, runs, loss, grad norm, update, verdict)
# Losses and norms are shown to four decimals. The pipeline's own loss tolerance
# is 0.02, so a difference in the sixth decimal is not one the verdict can see;
# the caption carries the exact values behind the tie.
EXPECTED_ROWS = [
    ("PyTorch source",   "yes", "1.7805", "0.2834", "reference", "---"),
    ("Correct port",     "yes", "1.7805", "0.2834", "matches",   "accept"),
    ("Missing operator", "no",  "---",    "---",    "---",       "reject"),
    ("Wrong reduction",  "yes", "2.5009", "0.6879", "differs",   "reject"),
    ("No backward pass", "yes", "1.7805", "---",    "none",      "accept"),
]


def measured():
    """The single training step Table I reports: CNN, seed 300, step 25."""
    d = pd.read_csv(CSV)
    tf = d[(d.coupling == "teacher-forced") & (d.model == "cnn")
           & (d.seed == 300) & (d.step == 25)]
    return {r.fault: r for _, r in tf.iterrows()}, d


def near(a, b, tol=5e-7):
    return abs(float(a) - float(b)) <= tol


def check_data(g, d):
    """Assert the CSV still says what the table reports."""
    out = []
    src = g["none"]
    tests = [
        ("source loss 1.7805",      near(src.torch_loss, 1.780532)),
        ("source grad 0.2834",       near(src.torch_grad_norm, 0.283368, 5e-6)),
        ("correct port loss 1.7805", near(g["none"].torch4ms_loss, 1.780535)),
        ("correct port grad 0.2834", near(g["none"].torch4ms_grad_norm, 0.283368, 5e-6)),
        ("correct port update matches",
         near(g["none"].param_update_cosine, 1.0, 2e-6)),
        ("missing operator does not run",
         g["execution"].torch4ms_status == "failed"),
        ("wrong reduction loss 2.5009", near(g["numeric"].torch4ms_loss, 2.500882)),
        ("wrong reduction grad 0.6879",
         near(g["numeric"].torch4ms_grad_norm, 0.687914, 5e-6)),
        # the row the table is built on: same loss as the correct port, no
        # gradient at all, and no parameter movement
        ("no-backward loss ties the correct port",
         near(g["training"].torch4ms_loss, g["none"].torch4ms_loss, 1e-9)),
        ("no-backward gradient is absent, not zero",
         bool(pd.isna(g["training"].torch4ms_grad_norm))),
        ("no-backward parameters do not move",
         near(g["training"].param_update_cosine, 0.0, 1e-12)),
    ]
    for name, ok in tests:
        if not ok:
            out.append(f"data disagrees with Table I: {name}")

    # and that the two shaded claims are not a one-seed accident
    all_tf = d[d.coupling == "teacher-forced"]
    tr = all_tf[all_tf.fault == "training"]
    hl = all_tf[all_tf.fault == "none"]
    if not (tr.param_update_cosine == 0).all():
        out.append("training-fault parameter update is not always absent")
    if not tr.torch4ms_grad_norm.isna().all():
        out.append("training-fault gradient is not always absent")
    if hl.param_update_cosine.min() <= 0.999:
        out.append("healthy parameter update dipped below agreement")
    if tr.loss_abs_diff.max() != hl.loss_abs_diff.max():
        out.append("training and healthy loss differences are no longer identical")
    return out, len(tr), len(hl)


def check_tex():
    """Assert the .tex table body still holds the rows this script verifies."""
    if not os.path.exists(TEX):
        return [f"{TEX} not found; run from the repository root"]
    body = open(TEX).read()
    m = re.search(r'\\label\{tab:divergence\}(.*?)\\end\{table\}', body, re.S)
    if not m:
        return ["tab:divergence not found in the manuscript"]
    seg = m.group(1)
    out = []
    for row in EXPECTED_ROWS:
        label = row[0]
        line = next((l for l in seg.split("\\\\") if label in l), None)
        if line is None:
            out.append(f"Table I has no row for {label!r}")
            continue
        for cell in row[1:]:
            if cell == "---":
                continue
            if cell not in line:
                out.append(f"Table I row {label!r} no longer prints {cell!r}")
    return out


def main():
    g, d = measured()
    problems, n_tr, n_hl = check_data(g, d)
    problems += check_tex()
    if problems:
        print("TABLE I DOES NOT MATCH THE DATA:")
        for p in problems:
            print("  " + p)
        return 1
    print("Table I verified against the CSV")
    print(f"  every printed value matches, over {len(EXPECTED_ROWS)} rows")
    print(f"  no-backward parameter update absent on {n_tr} rows, "
          f"healthy agreement on {n_hl} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
