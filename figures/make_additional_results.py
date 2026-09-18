"""Generate the E table from the audited four-method export."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS = {
    "MSAdapter 0.6.0 CPU": "MSAdapter 0.6.0 (CPU)",
    "CodeTransEngine translation-only": "CodeTransEngine (translation only)",
    "Direct": "Direct translation",
    "Frozen Translator": "Frozen Translator",
}


def main():
    source = ROOT / "output/maintext-results-20260918/end_to_end_e.csv"
    with source.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 4 and {r["method"] for r in rows} == LABELS.keys()
    lines = []
    for row in rows:
        assert int(row["conditions"]) == 15 and int(row["new_api_calls"]) == 0
        values = [f"{row[k]}/15" for k in
                  ("forward_completed", "training_completed", "strict_accepted")]
        lines.append(" & ".join([LABELS[row["method"]]] + values) + r" \\")
    lines.append(r"\bottomrule")
    (ROOT / "figures/TABLE_end_to_end_e_rows.tex").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
