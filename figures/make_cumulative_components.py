"""Render the time series component ablation from the completed repository runs."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "output/cumulative-component-ablation-20260922/summary.json"
CONDITIONS = (
    ("repair", "Repair Agent"),
    ("investigation", r"\quad + Verifier investigation"),
    ("handoff", r"\quad + Independent evidence handoff"),
    ("repository_context", r"\quad + Repository context management"),
)


def main():
    payload = SOURCE.read_bytes()
    data = json.loads(payload)
    rows = {(row["repository"], row["condition"]): row for row in data["rows"]}
    assert len(data["rows"]) == len(rows) == 8, "All eight final runs are required"
    for repository, denominator in (("timeseries", 69), ("twotower", 145)):
        for condition, _ in CONDITIONS:
            row = rows[repository, condition]
            assert row["status"] == "completed", "Cannot publish an incomplete run"
            assert row["protocol_checks"]["expected"] == denominator
            assert row["end_to_end_tokens"] == row["repair_tokens"] + row["translation_usage"]["total_tokens"]
            assert row["repair_tokens"] == row["usage"]["total_tokens"]
    lines = [
        "% Source: output/cumulative-component-ablation-20260922/summary.json",
        "% SHA256: " + hashlib.sha256(payload).hexdigest(),
        r"\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}>{\raggedright\arraybackslash}p{6.0cm}rrr@{}}",
        r"\toprule",
        r"\multicolumn{4}{l}{\textit{(b) Agent components: time series repository}} \\",
        r"\midrule",
        r"\textbf{Components} & \thead{Behavior\\checks passed} & \thead{Investigation\\and repair calls} & \thead{Total tokens\\(millions)} \\",
        r"\midrule",
    ]
    for condition, label in CONDITIONS:
        row = rows["timeseries", condition]
        cells = [label, f"{row['protocol_checks']['passed']}/69", str(row["calls"]),
                 f"{row['end_to_end_tokens'] / 1e6:.3f}"]
        lines.append(" & ".join(cells) + r" \\")
    lines.extend((r"\bottomrule", r"\end{tabular*}"))
    (ROOT / "figures/TABLE_cumulative_components.tex").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
