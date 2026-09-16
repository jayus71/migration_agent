#!/usr/bin/env python3
"""Build tables without pooling original repair, signal, and Experiment J runs."""
import csv
import json
from pathlib import Path

from make_jax_table import build_rows as build_jax_rows
from paper_data import fixed50, signal_ablation

ROOT = Path(__file__).resolve().parents[1]
J_ROOT = ROOT / "data/experiments/10_experiment_J_feedback_ablation/formal_run_2d6bd3d"
OUTPUTS = {
    "main": ROOT / "figures/TABLE_main_rows.tex",
    "signals": ROOT / "figures/TABLE_signal_rows.tex",
    "feedback": ROOT / "figures/TABLE_feedback_rows.tex",
}
MAIN_METHODS = {"r_direct": "Direct LLM", "r_swe": "SWE-agent",
                "r_matchfix": r"MatchFixAgent$^\dagger$", "r_hier": "LaDiM"}
CONDITIONS = {
    "r_hier": r"\textbf{LaDiM}$^\ast$",
    "r_exec": "Execution only",
    "r_binary": "Pass/fail only",
    "r_stage": "Stage label only",
    "r_flat": "Flat feedback",
    "r_reverse": "Reverse presentation",
}
# Presentation order is evaluated separately in the appendix.
FEEDBACK_METHODS = ("r_hier", "r_exec", "r_binary", "r_stage", "r_flat")
UNMEASURED = (
    "Without targeted guidance",
    "Without repair history",
    "Without rollback",
)


def latex_row(cells, bold=False):
    if bold:
        cells = [rf"\textbf{{{cell}}}" for cell in cells]
    return " & ".join(cells) + r" \\"


def build_main():
    frame = fixed50()
    lines = ["% Generated from the original Fixed50 summary."]
    for method, label in MAIN_METHODS.items():
        row = frame.loc[method]
        accepted = int(row.strict_success)
        cells = [label, f"{accepted}/{int(row.instances)}",
                 f"{100 * row.repair_at_1:.0f}\\%",
                 f"{row.total_tokens / accepted / 1000:.1f}K",
                 f"{row.wall_time_sec / accepted:.1f}"]
        lines.append(latex_row(cells, bold=method == "r_hier"))
    lines.append(r"\midrule")
    lines.append(r"\multicolumn{5}{l}{\textit{(b) JAX: six instances, all accepted repairs finish in the first round}} \\")
    lines.append(build_jax_rows().rstrip())
    return "\n".join(lines) + "\n"


def build_signals():
    counts, totals = signal_ablation()
    conditions = ["Execution only", "Execution and forward values",
                  r"\shortstack[l]{Execution, forward values,\\gradients and parameter updates}"]
    lines = ["% Generated from the separate 12-task signal study."]
    for label, values in zip(conditions, counts):
        cells = [label, *(f"{int(n)}/{int(d)}" for n, d in zip(values, totals)),
                 f"{int(values.sum())}/{int(totals.sum())}"]
        lines.append(latex_row(cells))
    lines.append(r"\bottomrule")
    return "\n".join(lines) + "\n"


def read_feedback(root=J_ROOT):
    summary = json.loads((root / "summary.json").read_text())
    with (root / "summary.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    metadata = summary["metadata"]
    if metadata["repair_attempts"] != 4 or float(metadata["temperature"]) != 0:
        raise ValueError("Unexpected Experiment J protocol")
    if len(rows) != 6 or {r["condition"] for r in rows} != set(CONDITIONS):
        raise ValueError("Expected six Experiment J conditions")
    indexed = {r["condition"]: r for r in summary["conditions"]}
    for row in rows:
        reference = indexed[row["condition"]]
        if any(float(row[key]) != reference[key] for key in
               ("total", "passed", "repair_at_1", "repair_at_2", "repair_at_4",
                "prompt_tokens", "completion_tokens", "total_tokens", "wall_time_sec")):
            raise ValueError("Experiment J CSV and JSON disagree")
        total, passed = int(row["total"]), int(row["passed"])
        checkpoints = [float(row[f"repair_at_{budget}"]) for budget in (1, 2, 4)]
        if (total != 50 or not 0 <= passed <= total
                or checkpoints != sorted(checkpoints)
                or any(not 0 <= rate <= 1 or abs(rate * total - round(rate * total)) > 1e-8
                       for rate in checkpoints)
                or abs(checkpoints[-1] * total - passed) > 1e-8):
            raise ValueError("Invalid Experiment J acceptance counts")
        if int(row["total_tokens"]) != int(row["prompt_tokens"]) + int(row["completion_tokens"]):
            raise ValueError("Invalid Experiment J token totals")
    for method in ("r_hier", "r_reverse"):
        if metadata["condition_provenance"][method]["source_run"] != "confirmatory_repeat3_hier_first":
            raise ValueError("Update the manuscript provenance note for a changed source run")
    return {r["condition"]: r for r in rows}


def build_feedback():
    rows = read_feedback()
    lines = ["% Generated from the feedback-ablation results."]
    for method in FEEDBACK_METHODS:
        row = rows[method]
        accepted = int(row["passed"])
        cells = [CONDITIONS[method], f"{accepted}/{row['total']}",
                 f"{100 * float(row['repair_at_1']):.0f}\\%",
                 f"{int(row['total_tokens']) / accepted / 1000:.1f}K" if accepted else "n/a",
                 f"{float(row['wall_time_sec']) / accepted:.1f}" if accepted else "n/a"]
        lines.append(latex_row(cells))
        if method == "r_hier":
            lines.append(r"\midrule")
    lines.append(r"\midrule")
    for label in UNMEASURED:
        lines.append(latex_row([label, "--", "--", "--", "--"]))
    lines.append(r"\bottomrule")
    return "\n".join(lines) + "\n"


def main():
    for key, builder in (("main", build_main), ("signals", build_signals),
                         ("feedback", build_feedback)):
        OUTPUTS[key].write_text(builder(), encoding="utf-8")
        print(f"Saved: {OUTPUTS[key].relative_to(ROOT)}")


if __name__ == "__main__":
    main()
