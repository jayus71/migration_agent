import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from report_maintext_recovery import summarize


class ReportTests(unittest.TestCase):
    def row(self, accepted, healthy, unknown=0, status='completed'):
        return {'status': status, 'accepted': accepted, 'initially_accepted': healthy,
                'accepted_at': 0 if healthy else 2 if accepted else None,
                'usage': {'prompt_tokens': 100, 'completion_tokens': 20, 'unknown_usage_calls': unknown},
                'events': {}, 'calls': 1, 'path': 'test', 'ledger_mismatch': False,
                'request_treatment_violations': []}

    def test_failed_episodes_contribute_cost_and_healthy_is_not_repaired(self):
        result = summarize([self.row(True, True), self.row(True, False), self.row(False, False)], 3)
        self.assertEqual(result['known_tokens'], 360)
        self.assertEqual(result['tokens_per_accepted'], 180)
        self.assertEqual(result['actual_faults_repaired'], 1)
        self.assertEqual(result['healthy_retained'], 1)
        self.assertEqual(result['accepted_at'], {'1': 1, '2': 2, '4': 2})

    def test_unknown_usage_or_unfinished_grid_prevents_final_cost_ratio(self):
        self.assertIsNone(summarize([self.row(True, False, unknown=1)], 1)['tokens_per_accepted'])
        result = summarize([self.row(True, False)], 2)
        self.assertFalse(result['complete'])
        self.assertIsNone(result['acceptance_rate'])
        self.assertIsNone(result['tokens_per_accepted'])


if __name__ == '__main__':
    unittest.main()
