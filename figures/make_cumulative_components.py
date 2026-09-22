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


def table_start(width="6.8cm"):
    return [r"\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}>{\raggedright\arraybackslash}p{" + width + r"}rrr@{}}",
            r"\toprule",
            r"\textbf{Condition} & \thead{Behavior\\checks passed} & \thead{Investigation\\and repair calls} & \thead{End-to-end\\tokens} \\"]


def row_text(label, row):
    checks = row["protocol_checks"]
    return (f"{label} & {checks['passed']}/{checks['expected']} & {row['calls']} & "
            f"{row['end_to_end_tokens']:,}" + r" \\")


def main():
    cumulative = load_rows(SOURCE)
    structure = load_rows(STRUCTURE)
    planning = load_rows(PLANNING)
    assert len(cumulative) == 8 and len(structure) == len(planning) == 4
    for repository in ("timeseries", "twotower"):
        for field in ("calls", "repair_tokens", "end_to_end_tokens", "protocol_checks"):
            assert structure[repository, "full"][field] == planning[repository, "full"][field]

    lines = table_start()
    for repository, title in (("timeseries", "Time series repository"), ("twotower", "Recommendation repository")):
        lines += [r"\midrule", r"\multicolumn{4}{l}{\textit{" + title + r"}} \\"]
        lines += [row_text(label, cumulative[repository, condition]) for condition, label in CONDITIONS]
    lines += [r"\bottomrule", r"\end{tabular*}"]
    write_table("TABLE_cumulative_components.tex", lines, [SOURCE])

    lines = [r"\textit{(c) Repository context management and Repository Structural Analysis on the time series repository}\par\smallskip"] + table_start()
    for title, pairs in [
            ("Repository context management", [
                ("Without repository context", cumulative["timeseries", "handoff"]),
                ("With repository context", cumulative["timeseries", "repository_context"])]),
            ("Repository Structural Analysis", [
                ("Without Repository Structural Analysis", structure["timeseries", "no_automatic_map"]),
                ("With Repository Structural Analysis", structure["timeseries", "full"])])]:
        lines += [r"\midrule", r"\multicolumn{4}{l}{\textit{" + title + r"}} \\"]
        lines += [row_text(label, row) for label, row in pairs]
    lines += [r"\bottomrule", r"\end{tabular*}"]
    write_table("TABLE_repository_components.tex", lines, [SOURCE, STRUCTURE])

    lines = table_start()
    for repository, title in (("timeseries", "Time series repository"), ("twotower", "Recommendation repository")):
        lines += [r"\midrule", r"\multicolumn{4}{l}{\textit{" + title + r"}} \\"]
        for label, row in [
                ("Complete method", structure[repository, "full"]),
                ("Without Repository Structural Analysis", structure[repository, "no_automatic_map"]),
                ("Without Repair Dependency Graph Planning", planning[repository, "no_work_unit_planning"])]:
            lines.append(row_text(label, row))
    lines += [r"\bottomrule", r"\end{tabular*}"]
    write_table("TABLE_repository_independent.tex", lines, [STRUCTURE, PLANNING])

    native = json.loads(NATIVE_JAX.read_text())
    assert (native["source_pool_tasks"], native["generated_candidates"], native["initial_passes"]) == (12, 10, 8)
    lines = [r"\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}lrrrr@{}}", r"\toprule",
             r"\textbf{Method} & \thead{Repair\\calls} & \thead{Repair\\tokens} & \thead{Two repair tasks\\end-to-end tokens} & \thead{All twelve sources\\end-to-end tokens} \\", r"\midrule"]
    for row in native["methods"]:
        assert row["repair_accepted"] == 1 and row["repair_denominator"] == 2
        assert row["shared_translation_then_repair_accepted"] == 9
        assert row["selected_task_end_to_end_tokens"] == row["repair_total_tokens"] + 31427
        assert row["shared_translation_then_repair_total_tokens"] == row["repair_total_tokens"] + native["source_pool_translation_usage"]["total_tokens"]
        label = "Direct repair" if row["method"] == "direct_shared_tools" else row["label"]
        lines.append(f"{label} & {row['repair_calls']} & {row['repair_total_tokens']:,} & "
                     f"{row['selected_task_end_to_end_tokens']:,} & {row['shared_translation_then_repair_total_tokens']:,}" + r" \\")
    lines += [r"\bottomrule", r"\end{tabular*}"]
    write_table("TABLE_native_jax.tex", lines, [NATIVE_JAX])


if __name__ == "__main__":
    main()
