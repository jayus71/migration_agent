"""Reused complete-method observations must not become new API expenses."""
from pathlib import Path
import unittest
from unittest.mock import patch
import audit_work_unit_planning_ablation as module


class AccountingTests(unittest.TestCase):
    def test_reused_calls_and_costs_are_separate(self):
        rows = [
            {'condition': 'full', 'status': 'completed', 'calls': 30, 'repair_tokens': 1000},
            {'condition': 'full', 'status': 'completed', 'calls': 80, 'repair_tokens': 2000},
            {'condition': 'no_work_unit_planning', 'status': 'completed', 'calls': 20,
             'repair_tokens': 500, 'usage': {'completion_tokens': 40}},
            {'condition': 'no_work_unit_planning', 'status': 'completed', 'calls': 50,
             'repair_tokens': 800, 'usage': {'completion_tokens': 80}, 'unknown_usage_calls': 1}]
        before = module.common.CONDITIONS
        with patch.object(module.common, 'summarize', return_value={'rows': rows}):
            result = module.summarize(Path('unused'))
        self.assertEqual(module.common.CONDITIONS, before)
        ledger = result['physical_ledger']
        self.assertEqual(ledger['new_model_calls'], 70)
        self.assertEqual(ledger['new_measured_tokens'], 1300)
        self.assertEqual(ledger['new_full_method_calls'], 0)
        self.assertEqual(ledger['reused_full_reference_calls'], 110)
        self.assertEqual(ledger['reused_full_reference_repair_tokens'], 3000)
        self.assertEqual(ledger['unknown_usage_calls'], 1)


if __name__ == '__main__':
    unittest.main()
