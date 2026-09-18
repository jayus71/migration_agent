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
            ["Direct LLM", "5/6", r"83.3\%", "15.0K", "177.1"],
            ["Ivy", "0/6", r"0.0\%", "n/a", "n/a"],
            [r"\texttt{torch2jax}", "0/6", r"0.0\%", "n/a", "n/a"],
            ["LaDiM", "6/6", r"100.0\%", "2.9K", "79.8"],
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
                             ("repair_attempts", "4"), ("total_tokens", "0"),
                             ("wall_time_sec", "nan")]:
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

    def test_manuscript_keeps_experiment_pools_separate(self):
        manuscript = (ROOT / "conference_101719.tex").read_text()
        main_table = manuscript.split(r"\label{tab:main-results}", 1)[1].split(r"\end{table}", 1)[0]
        self.assertIn("TABLE_slim_main_rows", main_table)
        self.assertNotIn("TABLE_main_rows", main_table)
        self.assertNotIn("TABLE_jax_rows", main_table)
        generated = (ROOT / "figures/TABLE_main_rows.tex").read_text()
        self.assertIn(table.build_rows().rstrip(), generated)
        self.assertNotIn("MSAdapter", main_table)
        self.assertIn("Fixed50", main_table)
        self.assertIn("Natural10", main_table)
        self.assertIn("(b) JAX: six instances", generated)
        self.assertIn("all accepted repairs finish in the first round", generated)
        jax_section = manuscript.split(r"\label{sec:generalization}", 1)[1].split(
            r"\subsection{", 1)[0]
        self.assertIn("six frozen MLP and CNN faults", jax_section)
        self.assertIn("three-seed training verification", jax_section)
        self.assertIn("up to four submission checkpoints", jax_section)
        self.assertNotIn("TABLE_mindspore_translation_rows", manuscript)
        self.assertNotIn("15 task--seed conditions", main_table)
        self.assertNotIn("Grad./upd.", manuscript)
        self.assertNotIn("optim.", manuscript)

    def test_jax_rows_do_not_pad_unevaluated_categories(self):
        for line in table.build_rows().splitlines():
            if " & " in line:
                cells = line.removesuffix(r" \\").split(" & ")
                self.assertEqual(len(cells), 5)
                self.assertNotIn("-", cells)


if __name__ == "__main__":
    unittest.main()
