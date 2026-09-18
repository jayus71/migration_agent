"""Acceptance regression checks without a model or framework installation."""

import copy
import unittest

from experiments.unified_migration50_20260918.score import compare


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.reference = {'status': 'completed', 'seed': 101,
            'values': {'forward/output': [1., 2.], 'gradient/input': [.2, -.3],
                       'update/weight': [-.01, .02]},
            'schema': {name: {'shape': [2], 'dtype': 'float32'} for name in
                       ('forward/output', 'gradient/input', 'update/weight')}}
        self.target = copy.deepcopy(self.reference)
        self.target['backend'] = {'observed': True}

    def test_healthy_and_stage_errors(self):
        self.assertTrue(compare(self.reference, self.target)['accepted'])
        for name in self.target['values']:
            with self.subTest(name=name):
                modified = copy.deepcopy(self.target)
                modified['values'][name][0] += 1
                self.assertFalse(compare(self.reference, modified)['accepted'])

    def test_missing_nan_and_malformed_are_failures(self):
        for value in (None, [float('nan'), 0], ['not numeric'], [[1, 2], [3]]):
            with self.subTest(value=value):
                modified = copy.deepcopy(self.target)
                modified['values']['gradient/input'] = value
                self.assertFalse(compare(self.reference, modified)['accepted'])

    def test_missing_or_extra_measurements_and_seed(self):
        for change in ('delete', 'extra', 'seed', 'dtype', 'backend'):
            modified = copy.deepcopy(self.target)
            if change == 'delete':
                del modified['values']['gradient/input']
            elif change == 'extra':
                modified['values']['unrequested'] = [0]
            elif change == 'seed':
                modified['seed'] = 202
            elif change == 'dtype':
                modified['schema']['forward/output']['dtype'] = 'float64'
            else:
                modified['backend']['observed'] = False
            self.assertFalse(compare(self.reference, modified)['accepted'], change)

    def test_execution_failure_keeps_measurements_unavailable(self):
        result = compare(self.reference, {'status': 'execution_failed'})
        self.assertFalse(result['accepted'])
        self.assertEqual(set(result['unavailable']), set(self.reference['values']))
        self.assertEqual(result['checks'], {})

    def test_reference_failure_is_not_a_candidate_score(self):
        result = compare({'status': 'execution_failed'}, self.target)
        self.assertIsNone(result['accepted'])


if __name__ == '__main__':
    unittest.main()
