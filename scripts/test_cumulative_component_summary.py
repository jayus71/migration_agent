"""Checks that incomplete evaluations and failed API calls stay visible."""
import json
from pathlib import Path
import tempfile
import unittest

from summarize_cumulative_component_ablations import CONDITIONS, expected_checks, summarize


class SummaryTests(unittest.TestCase):
    def test_fixed_denominators_and_unknown_usage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            training, retrieval, status, behavior, ts = expected_checks()
            for condition in CONDITIONS:
                for repository in ('timeseries', 'twotower'):
                    folder = root / repository / 'conditions' / condition
                    agent = folder / 'evidence/agent'
                    agent.mkdir(parents=True)
                    checks = {key: True for key in (ts if repository == 'timeseries' else training + status + behavior)}
                    if repository == 'twotower':
                        checks[training[0]] = False
                    result = {'status': 'completed', 'accepted': False, 'calls': 2,
                              'usage': {'total_tokens': 100, 'completion_tokens': 30, 'unknown_usage_calls': 1},
                              'final': {'public': {'numeric': {'checks': checks}}, 'confirmations': []}}
                    (folder / 'result.json').write_text(json.dumps(result))
                    (agent / 'call_0001_response.json').write_text(json.dumps({'usage': {'total_tokens': 100}}))
                    for call in (1, 2):
                        (agent / f'call_{call:04d}_request.json').write_text('{}')
            result = summarize(root)
            self.assertTrue(result['all_conditions_terminal'])
            timeseries, twotower = result['rows'][:2]
            self.assertEqual(timeseries['protocol_checks']['expected'], 69)
            self.assertEqual(timeseries['protocol_checks']['passed'], 23)
            self.assertEqual(len(timeseries['protocol_checks']['not_measured']), 46)
            self.assertEqual(twotower['protocol_checks']['expected'], 145)
            self.assertEqual(twotower['protocol_checks']['passed'], 138)
            self.assertEqual(len(twotower['protocol_checks']['failed']), 1)
            self.assertEqual(len(twotower['protocol_checks']['not_measured']), 6)
            self.assertEqual(twotower['original_tests']['passed'], None)
            self.assertEqual(result['physical_ledger']['new_model_calls'], 16)
            self.assertEqual(result['physical_ledger']['unknown_usage_calls'], 8)
            self.assertEqual(result['physical_ledger']['new_measured_tokens'], 800)

    def test_undispatched_conditions_remain_pending(self):
        with tempfile.TemporaryDirectory() as directory:
            result = summarize(Path(directory))
            self.assertEqual(len(result['rows']), 8)
            self.assertFalse(result['all_conditions_terminal'])
            self.assertTrue(all(row['status'] == 'not_run' for row in result['rows']))

    def test_execution_failure_is_not_zero_accuracy(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / 'timeseries/conditions/repair'
            folder.mkdir(parents=True)
            (folder / 'result.json').write_text(json.dumps({'status': 'infrastructure_error',
                'accepted': False, 'calls': 0, 'usage': None}))
            row = summarize(Path(directory))['rows'][0]
            self.assertIsNone(row['protocol_checks']['passed'])
            self.assertIsNone(row['protocol_checks']['passed_fraction'])
            self.assertEqual(row['protocol_checks']['expected'], 69)
            self.assertEqual(row['protocol_checks']['measured'], 0)


if __name__ == '__main__':
    unittest.main()
