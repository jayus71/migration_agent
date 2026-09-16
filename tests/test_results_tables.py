import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "figures"))
spec = importlib.util.spec_from_file_location("make_results_tables", ROOT / "figures/make_results_tables.py")
tables = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tables)


class ResultsTableTests(unittest.TestCase):
    def test_pools_keep_their_recorded_acceptance_and_costs(self):
        main = tables.build_main()
        feedback = tables.build_feedback()
        self.assertIn(r"\textbf{50/50}", main)
        self.assertIn(r"\textbf{84\%}", main)
        self.assertIn(r"MatchFixAgent$^\dagger$ & 47/50 & 74\% & 110.7K & 74.2", main)
        self.assertIn(r"\textbf{LaDiM}$^\ast$ & 48/50 & 72\% & 6.8K & 100.2", feedback)
        self.assertIn(r"Flat feedback & 34/50 & 64\% & 12.7K & 357.2", feedback)
        self.assertIn(r"Pass/fail only & 34/50 & 64\% & 22.0K & 410.7", feedback)
        self.assertNotIn("50/50", feedback)
        self.assertIn("4/12", tables.build_signals())
        self.assertIn("8/12", tables.build_signals())
        self.assertIn("12/12", tables.build_signals())

    def test_missing_controls_do_not_get_an_invented_denominator(self):
        rendered = tables.build_feedback()
        for label in tables.UNMEASURED:
            line = next(line for line in rendered.splitlines() if line.startswith(label))
            self.assertTrue(line.endswith(r" & -- & -- & -- & -- \\"))

    def test_feedback_source_change_requires_provenance_update(self):
        for change in ("passed", "source_run"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                shutil.copy2(tables.J_ROOT / "summary.csv", root / "summary.csv")
                summary = json.loads((tables.J_ROOT / "summary.json").read_text())
                if change == "passed":
                    summary["conditions"][0]["passed"] += 1
                else:
                    summary["metadata"]["condition_provenance"]["r_hier"]["source_run"] = "other_run"
                (root / "summary.json").write_text(json.dumps(summary))
                with self.assertRaises(ValueError):
                    tables.read_feedback(root)

    def test_generated_files_are_current(self):
        for key, builder in (("main", tables.build_main), ("signals", tables.build_signals),
                             ("feedback", tables.build_feedback)):
            self.assertEqual(tables.OUTPUTS[key].read_text(), builder())


if __name__ == "__main__":
    unittest.main()
