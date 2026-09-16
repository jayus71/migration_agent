import importlib.util
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "mindspore_table", ROOT / "figures/make_mindspore_translation_table.py")
table = importlib.util.module_from_spec(spec)
spec.loader.exec_module(table)


class MindSporeTranslationTableTests(unittest.TestCase):
    def test_current_archived_results_and_generated_rows(self):
        results = table.read_results()
        # Training completion and paired acceptance are different measurements.
        self.assertTrue(all(row["training_success"] for row in results["T-MSA"]))
        self.assertFalse(any(row["strict_success"] for row in results["T-MSA"]))
        self.assertTrue(all(row["fixer_calls"] == 0 for row in results["T-HIER"]))
        rendered = re.sub(r"\\textbf\{([^{}]+)\}", r"\1", table.build_rows(results))
        cells = [line.removesuffix(r" \\").split(" & ")
                 for line in rendered.splitlines() if " & " in line]
        self.assertEqual(cells, [["Direct LLM", "13/15", "7/15"],
                                 ["CodeTransEngine", "12/15", "8/15"],
                                 ["MSAdapter", "15/15", "0/15"],
                                 ["LaDiM", "15/15", "15/15"]])
        self.assertNotIn("T-X2MS", results)

    def test_generated_file_is_current(self):
        self.assertEqual(table.OUTPUT.read_text(), table.build_rows())


if __name__ == "__main__":
    unittest.main()
