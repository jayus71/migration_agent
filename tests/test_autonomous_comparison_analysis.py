"""Guard the reporting denominators and failure-cost accounting."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    "autonomous_analysis", Path(__file__).resolve().parents[1] / "scripts/analyze_autonomous_comparison.py")
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


class ComparisonAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name)
        self.methods = ["autonomous_layered", "direct_shared_tools"]
        self.write("manifest.json", {"tasks": [{"anonymous_id": f"task_{i:03}"} for i in (1, 2)], "methods": self.methods})

    def write(self, name, obj):
        path = self.run / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj))

    def row(self, task, method, *, accepted=False, healthy=False, status="completed", unknown=0):
        row = {"task": task, "method": method, "status": status, "accepted": accepted,
               "initially_accepted": healthy, "attempts": [{"attempt": 2, "accepted": accepted}],
               "budget": {"calls": 1, "usage": {"prompt_tokens": 100, "completion_tokens": 20,
                                                "unknown_usage_calls": unknown}}, "wall_time_sec": 3}
        self.write(f"conditions/{task}/{method}/result.json", row)
        return row

    def test_full_failure_costs_and_initial_health_are_separate(self):
        for method in self.methods:
            self.row("task_001", method, accepted=True)
            self.row("task_002", method, healthy=True)
        result = analysis.analyze(self.run)
        self.assertTrue(result["complete"])
        s = result["methods"][self.methods[0]]
        self.assertEqual(s["acceptance_rate"], 0.5)
        self.assertEqual(s["tokens_per_accepted"], 240)
        self.assertEqual(s["accepted_by_attempt"], {"1": 0, "2": 1, "4": 1})
        self.assertEqual((s["repaired_initially_failed"], s["initially_failed"]), (1, 1))
        self.assertEqual((s["retained_healthy"], s["initially_healthy"]), (0, 1))

    def test_partial_grid_does_not_become_complete_rate(self):
        self.row("task_001", self.methods[0], accepted=True)
        report = analysis.analyze(self.run)
        s = report["methods"][self.methods[0]]
        self.assertFalse(report["complete"])
        self.assertIsNone(s["acceptance_rate"])
        self.assertIsNone(s["tokens_per_accepted"])
        self.assertEqual(s["pending"], ["task_002"])

    def test_infrastructure_failure_costs_remain_and_unknown_usage_blocks_ratio(self):
        self.row("task_001", self.methods[0], accepted=True)
        self.row("task_002", self.methods[0], status="infrastructure_error", unknown=1)
        s = analysis.analyze(self.run)["methods"][self.methods[0]]
        self.assertEqual(s["total_tokens"], 240)
        self.assertEqual(s["unknown_usage_calls"], 1)
        self.assertIsNone(s["tokens_per_accepted"])
        self.assertEqual(s["noncompleted_terminal"], {"task_002": "infrastructure_error"})

    def test_raw_audit_detects_unrecorded_failed_request(self):
        method = self.methods[0]
        row = self.row("task_001", method, accepted=True)
        folder = f"conditions/task_001/{method}/evidence/agent"
        self.write(f"{folder}/call_0001_request.json", {})
        self.write(f"{folder}/call_0001_response.json", {"model": "deepseek-flash", "usage": {"prompt_tokens": 100, "completion_tokens": 20}})
        self.write(f"{folder}/call_0002_request.json", {})
        audit = analysis.audit_ledger(self.run / f"conditions/task_001/{method}", row)
        self.assertEqual(audit["mismatches"]["calls"], {"raw": 2, "recorded": 1})
        self.assertEqual(audit["mismatches"]["unknown_usage_calls"], {"raw": 1, "recorded": 0})


if __name__ == "__main__":
    unittest.main()
