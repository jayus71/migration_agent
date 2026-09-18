import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from report_autonomous_recovery import report, VERSIONS


class RecoveryReportTests(unittest.TestCase):
    def test_predeclared_replacement_and_all_attempt_costs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def save(path, value):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(value))
            def row(status="completed", accepted=True, unknown=0):
                return {"task": "task_001", "method": "agent", "status": status,
                    "accepted": accepted, "initially_accepted": False, "attempts": [{"attempt": 1, "accepted": accepted}],
                    "budget": {"calls": 1, "usage": {"prompt_tokens": 100, "completion_tokens": 20, "unknown_usage_calls": unknown}}}
            for group in ("autonomous_fixed50_20260917", "autonomous_verifier_20260917"):
                for version in VERSIONS:
                    run = root / "experiments" / group / version
                    save(run / "manifest.json", {"tasks": [{"anonymous_id": "task_001"}], "methods": ["agent"]})
                    save(run / "conditions/task_001/agent/result.json", row())
            original = root / "experiments/autonomous_fixed50_20260917/formal_v3/conditions/task_001/agent/result.json"
            save(original, row("infrastructure_error", True, 1))
            recovery = root / "recovery"
            restarted = recovery / "Fixed50/formal_v3"
            save(restarted / "conditions/task_001/agent/result.json", row(accepted=False))
            save(recovery / "recovery_plan.json", {"policy": "declared retry", "conditions": [{
                "benchmark": "Fixed50", "version": "formal_v3", "task": "task_001", "method": "agent",
                "recovery_run": str(restarted), "original_result_sha256": hashlib.sha256(original.read_bytes()).hexdigest()}]})
            result = report(root, recovery)
            g = result["groups"][0]
            self.assertTrue(result["complete"])
            self.assertEqual(g["accepted"], 0)
            self.assertEqual(g["selected_run_usage"]["known_total_tokens"], 120)
            self.assertEqual(g["all_attempts_usage"]["known_total_tokens"], 240)
            self.assertEqual(g["all_attempts_usage"]["unknown_usage_calls"], 1)
            self.assertIsNone(g["all_attempts_usage"]["total_tokens"])
            self.assertIsNone(result["raw_ledger_problems"])
            save(original, row())
            with self.assertRaisesRegex(ValueError, "Original interrupted result changed"):
                report(root, recovery)


if __name__ == "__main__":
    unittest.main()
