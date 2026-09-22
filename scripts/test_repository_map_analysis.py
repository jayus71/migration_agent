"""Missing confirmation seeds must remain unmeasured in budget progress."""
import unittest
import json
from pathlib import Path
import tempfile
from analyze_repository_map_ablation import checks, analyze
from summarize_cumulative_component_ablations import expected_checks


class ProgressTests(unittest.TestCase):
    def test_unexecuted_confirmations_are_not_failures_or_passes(self):
        ts = expected_checks()[-1]
        result = checks('timeseries', {'public': {'numeric': {'checks': dict.fromkeys(ts, True)}}})
        self.assertEqual(result['passed'], 23)
        self.assertEqual(result['expected'], 69)
        self.assertEqual(result['measured'], 23)
        self.assertEqual(len(result['not_measured']), 46)
        self.assertEqual(result['failed'], [])

    def test_execution_failure_has_no_zero_accuracy(self):
        result = checks('twotower', {})
        self.assertEqual(result['expected'], 145)
        self.assertIsNone(result['passed'])
        self.assertEqual(result['measured'], 0)

    def test_partial_snapshot_does_not_claim_zero_call_usage(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / 'timeseries/conditions/full'
            folder.mkdir(parents=True)
            (folder / 'result.json').write_text(json.dumps({'repository': 'timeseries',
                'condition': 'full', 'status': 'completed', 'calls': 30, 'usage': {'total_tokens': 1000}}))
            row = analyze(root, ['full'])['rows'][0]
            self.assertEqual(row['evidence_scope'], 'summary_and_tool_events_only')
            self.assertEqual(row['calls'], 30)
            self.assertIsNone(row['observed_requests'])
            self.assertIsNone(row['measured_response_tokens'])


if __name__ == '__main__':
    unittest.main()
