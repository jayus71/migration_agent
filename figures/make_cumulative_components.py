"""Render repository component and native JAX tables from completed evidence."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "output/cumulative-component-ablation-20260922/summary.json"
STRUCTURE = ROOT / "data/audits/repository-map-ablation-20260922/summary.json"
PLANNING = ROOT / "data/audits/work-unit-planning-ablation-20260922/summary.json"
NATIVE_JAX = ROOT / "output/jax-expansion-20260922/formal/formal_report.json"
CONDITIONS = (
    ("repair", "Repair Agent"),
    ("investigation", r"\quad + Verifier investigation"),
    ("handoff", r"\quad + Independent evidence handoff"),
    ("repository_context", r"\quad + Repository context management"),
)


def load_rows(path):
    data = json.loads(path.read_text())
    rows = {(row["repository"], row["condition"]): row for row in data["rows"]}
    assert len(data["rows"]) == len(rows), "Duplicate conditions"
    for (repository, _), row in rows.items():
        assert row["status"] == "completed", "Cannot publish an incomplete run"
        assert row["protocol_checks"]["expected"] == (69 if repository == "timeseries" else 145)
        assert row["end_to_end_tokens"] == row["repair_tokens"] + row["translation_usage"]["total_tokens"]
        assert row["repair_tokens"] == row["usage"]["total_tokens"]
    return rows


def write_table(name, lines, sources):
    provenance = []
    for path in sources:
        provenance += ["% Source: " + str(path.relative_to(ROOT)),
                       "% SHA256: " + hashlib.sha256(path.read_bytes()).hexdigest()]
    (ROOT / "figures" / name).write_text("\n".join(provenance + lines) + "\n")


def table_start():
    return [r"\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}>{\raggedright\arraybackslash}p{5.4cm}rrrrrr@{}}",
            r"\toprule",
            r"& \multicolumn{3}{c}{\textbf{Time series}} & \multicolumn{3}{c}{\textbf{Recommendation}} \\",
            r"\cmidrule(lr){2-4}\cmidrule(l){5-7}",
            r"\textbf{Condition} & \textbf{Checks} & \textbf{Calls} & \textbf{Tokens} & \textbf{Checks} & \textbf{Calls} & \textbf{Tokens} \\",
            r"\midrule"]


def row_text(label, rows):
    cells = [label]
    for row in rows:
        checks = row["protocol_checks"]
        cells += [f"{checks['passed']}/{checks['expected']}", str(row["calls"]), f"{row['end_to_end_tokens']/1e6:.3f}"]
    return " & ".join(cells) + r" \\"


def main():
    cumulative = load_rows(SOURCE)
    structure = load_rows(STRUCTURE)
    planning = load_rows(PLANNING)
    assert len(cumulative) == 8 and len(structure) == len(planning) == 4
    for repository in ("timeseries", "twotower"):
        for field in ("calls", "repair_tokens", "end_to_end_tokens", "protocol_checks"):
            assert structure[repository, "full"][field] == planning[repository, "full"][field]

    lines = table_start()
    for condition, label in CONDITIONS:
        lines.append(row_text(label, [cumulative[repository, condition] for repository in ("timeseries", "twotower")]))
    lines += [r"\bottomrule", r"\end{tabular*}"]
    write_table("TABLE_cumulative_components.tex", lines, [SOURCE])

    lines = [r"\raggedright\textit{(c) Components on the time series repository}\par\smallskip",
             r"\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}>{\raggedright\arraybackslash}p{4.8cm}rrrrr@{}}", r"\toprule",
             r"& \multicolumn{2}{c}{\textbf{Without component}} & \multicolumn{2}{c}{\textbf{With component}} & \\",
             r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}",
             r"\textbf{Component} & \textbf{Calls} & \textbf{Tokens} & \textbf{Calls} & \textbf{Tokens} & \textbf{Saved} \\", r"\midrule"]
    for label, without, with_component in [
            ("Repository context management", cumulative["timeseries", "handoff"], cumulative["timeseries", "repository_context"]),
            ("Repository Structural Analysis", structure["timeseries", "no_automatic_map"], structure["timeseries", "full"])]:
        reduction = 100 * (1 - with_component["end_to_end_tokens"] / without["end_to_end_tokens"])
        lines.append(f"{label} & {without['calls']} & {without['end_to_end_tokens']/1e6:.3f} & "
                     f"{with_component['calls']} & {with_component['end_to_end_tokens']/1e6:.3f} & "
                     + r"\textbf{" + f"{reduction:.1f}" + r"\%}" + r" \\")
    lines += [r"\bottomrule", r"\end{tabular*}"]
    write_table("TABLE_repository_components.tex", lines, [SOURCE, STRUCTURE])

    lines = table_start()
    for label, data, condition in [
            ("LaDiM", structure, "full"),
            ("Without Repository Structural Analysis", structure, "no_automatic_map"),
            ("Without Repair Dependency Graph Planning", planning, "no_work_unit_planning")]:
        lines.append(row_text(label, [data[repository, condition] for repository in ("timeseries", "twotower")]))
    lines += [r"\bottomrule", r"\end{tabular*}"]
    write_table("TABLE_repository_independent.tex", lines, [STRUCTURE, PLANNING])

    native = json.loads(NATIVE_JAX.read_text())
    assert (native["source_pool_tasks"], native["generated_candidates"], native["initial_passes"]) == (12, 10, 8)
    lines = [r"\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}lrrrr@{}}", r"\toprule",
             r"\textbf{Method} & \textbf{Calls} & \textbf{Tokens} & \textbf{Two tasks} & \textbf{All sources} \\", r"\midrule"]
    for row in native["methods"]:
        assert row["repair_accepted"] == 1 and row["repair_denominator"] == 2
        assert row["shared_translation_then_repair_accepted"] == 9
        assert row["selected_task_end_to_end_tokens"] == row["repair_total_tokens"] + 31427
        assert row["shared_translation_then_repair_total_tokens"] == row["repair_total_tokens"] + native["source_pool_translation_usage"]["total_tokens"]
        label = "Direct repair" if row["method"] == "direct_shared_tools" else row["label"]
        lines.append(f"{label} & {row['repair_calls']} & {row['repair_total_tokens']/1e6:.3f} & "
                     f"{row['selected_task_end_to_end_tokens']/1e6:.3f} & {row['shared_translation_then_repair_total_tokens']/1e6:.3f}" + r" \\")
    lines += [r"\bottomrule", r"\end{tabular*}"]
    write_table("TABLE_native_jax.tex", lines, [NATIVE_JAX])


if __name__ == "__main__":
    main()
