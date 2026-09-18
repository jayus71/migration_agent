import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from compare_autonomous_recovery import compare


def group(version, method, outcomes, tokens=400):
    usage = {"total_tokens": tokens, "known_total_tokens": tokens,
             "unknown_usage_calls": 0, "missing_ledgers": 0}
    return {"benchmark": "Fixed50", "version": version, "method": method,
            "planned": len(outcomes), "completed": len(outcomes), "complete": True,
            "accepted": sum(outcomes), "selected_run_usage": usage,
            "all_attempts_usage": copy.deepcopy(usage),
            "conditions": [{"task": f"task_{i:03d}", "status": "completed", "accepted": v}
                           for i, v in enumerate(outcomes)]}


class RecoveryComparisonTests(unittest.TestCase):
    def report(self):
        return {"complete": True, "raw_verification_requested": True, "raw_ledger_problems": 0,
                "groups": [group("progress_v4", "autonomous_layered", [True, True, False, False]),
                           group("formal_v3", "swe_native_isolated", [True, False, True, False], 800)]}

    def test_pairing_retains_each_outcome_and_unknown_cost(self):
        report = self.report()
        usage = report["groups"][0]["all_attempts_usage"]
        usage.update(unknown_usage_calls=1, total_tokens=None, known_total_tokens=500)
        pair = compare(report)["baseline_pairs"][0]
        self.assertEqual(pair["both"], ["task_000"])
        self.assertEqual(pair["left_only"], ["task_001"])
        self.assertEqual(pair["right_only"], ["task_002"])
        self.assertEqual(pair["neither"], ["task_003"])
        self.assertEqual(pair["acceptance_difference_pp"], 0)
        self.assertEqual(pair["left_over_right_cost"]["selected_run_usage"]["tokens_per_accepted"], 0.5)
        self.assertIsNone(pair["left_over_right_cost"]["all_attempts_usage"]["tokens_per_accepted"])

    def test_rejects_partial_unverified_or_inconsistent_reports(self):
        for field, value in (("complete", False), ("raw_verification_requested", False), ("raw_ledger_problems", 1)):
            report = self.report()
            report[field] = value
            with self.assertRaises(ValueError):
                compare(report)
        report = self.report()
        report["groups"][0]["accepted"] += 1
        with self.assertRaisesRegex(ValueError, "Accepted count"):
            compare(report)

    def test_rejects_duplicate_and_mismatched_tasks(self):
        report = self.report()
        report["groups"][0]["conditions"][0]["task"] = "task_001"
        with self.assertRaisesRegex(ValueError, "Duplicate or missing"):
            compare(report)
        report = self.report()
        report["groups"][0]["conditions"][0]["task"] = "task_999"
        with self.assertRaisesRegex(ValueError, "exact task set"):
            compare(report)

    def test_zero_success_has_no_per_acceptance_ratio(self):
        report = self.report()
        report["groups"][0] = group("progress_v4", "autonomous_layered", [False] * 4)
        pair = compare(report)["baseline_pairs"][0]
        self.assertIsNone(pair["left_over_right_cost"]["selected_run_usage"]["tokens_per_accepted"])


if __name__ == "__main__":
    unittest.main()
