import copy
import csv
import hashlib
import importlib.util
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("make_jax_table", ROOT / "figures/make_jax_table.py")
table = importlib.util.module_from_spec(spec)
spec.loader.exec_module(table)


class JaxTableTests(unittest.TestCase):
    def test_original_snapshot_is_unchanged(self):
        self.assertEqual(hashlib.sha256(table.SOURCE.read_bytes()).hexdigest(),
                         "de2a165be2f9cf4409a92ff4a23c3711a356e8fe4e5787d3be705857c4800a8d")

    def test_generated_rows_match_original_results(self):
        rendered = re.sub(r"\\textbf\{([^{}]+)\}", r"\1", table.build_rows())
        rows = [line.removesuffix(r" \\").split(" & ")
                for line in rendered.splitlines() if " & " in line]
        expected = [
            ["Direct LLM", "2/2", "1/2", "2/2", "2/3", "3/3",
             r"83.3\%", r"83.3\%", "15.0K"],
            ["Ivy", "0/2", "0/2", "0/2", "0/3", "0/3",
             r"0\%", r"0\%", r"$\mathrm{n/a}$"],
            [r"\texttt{torch2jax}", "0/2", "0/2", "0/2", "0/3", "0/3",
             r"0\%", r"0\%", r"$\mathrm{n/a}$"],
            ["LADDER", "2/2", "2/2", "2/2", "3/3", "3/3",
             r"100\%", r"100\%", "2.9K"],
        ]
        self.assertEqual(rows, expected)

    def test_cost_includes_failed_attempts(self):
        rows = [row for row in table.read_results() if row["baseline_id"] == "c_direct"]
        self.assertEqual(sum(int(row["total_tokens"]) for row in rows), 74841)
        self.assertEqual(sum(int(row["total_tokens"]) for row in rows
                             if row["strict_success"] == "False"), 24582)
        self.assertEqual(table.accepted_count(rows), 5)

    def test_generated_file_is_current(self):
        self.assertEqual(table.OUTPUT.read_text(), table.build_rows())

    def test_unrun_budget_columns_are_not_used(self):
        rows = table.read_results()
        for row in rows:
            row["repair_at_2"] = "unused"
            row["repair_at_4"] = "unused"
        self.assertEqual(table.build_rows(rows), table.build_rows())

    def test_rejects_invalid_snapshot_rows(self):
        original = table.read_results()
        for field, value in [("model", "transformer"), ("strict_success", ""),
                             ("repair_attempts", "4"), ("total_tokens", "0")]:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                changed = copy.deepcopy(original)
                changed[0][field] = value
                path = Path(directory) / "instances.csv"
                with path.open("w", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=changed[0].keys())
                    writer.writeheader()
                    writer.writerows(changed)
                with self.assertRaises(ValueError):
                    table.read_results(path)

    def test_manuscript_uses_compact_panels_and_single_line_headers(self):
        manuscript = (ROOT / "conference_101719.tex").read_text()
        self.assertNotIn("tab:jax-transfer", manuscript)
        self.assertIn(r"\input{figures/TABLE_jax_rows.tex}", manuscript)
        self.assertIn(r"Table~\ref{tab:main-results}(a)", manuscript)
        self.assertIn(r"Table~\ref{tab:main-results}(b)", manuscript)
        main_table = manuscript.split(r"\label{tab:main-results}", 1)[1].split(r"\end{table*}", 1)[0]
        self.assertNotIn(r"\hdr", main_table)
        self.assertNotIn("Tokens per repair", main_table)
        self.assertEqual(main_table.count(r"\multirow{2}{*}{\textbf{Tokens}}"), 2)
        self.assertEqual(main_table.count(r"\begin{tabular*}"), 2)
        jax = main_table.split(r"\textit{(b) JAX", 1)[1]
        self.assertNotIn(r"\textbf{Program}", jax)
        self.assertNotIn(r"\textbf{Transformer}", jax)

    def test_jax_rows_do_not_pad_unevaluated_categories(self):
        for line in table.build_rows().splitlines():
            if " & " in line:
                cells = line.removesuffix(r" \\").split(" & ")
                self.assertEqual(len(cells), 9)
                self.assertNotIn("-", cells)


if __name__ == "__main__":
    unittest.main()
