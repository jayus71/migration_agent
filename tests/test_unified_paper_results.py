"""Check reporting units, interrupted outcomes, and archived usage accounting."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'figures'))
from make_unified_results import AUDIT, load_data
sys.path.pop(0)


class UnifiedPaperResultsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_data()
        cls.audit = json.loads(AUDIT.read_text(encoding='utf-8-sig'))

    def test_all_methods_report_the_same_fifty_identifiers(self):
        rows = self.audit['rows']
        reference = {a for r in rows if r['variant'] == 'main' and r['method'] == 'direct'
                     for a in r['aliases']}
        self.assertEqual(len(reference), 50)
        for key in self.audit['aggregates']:
            if key.startswith('cross_language/'):
                continue
            subset = [r for r in rows if r['variant'] + '/' + r['method'] == key]
            self.assertEqual(len(subset), 29, key)
            aliases = [a for r in subset for a in r['aliases']]
            self.assertEqual(len(aliases), 50, key)
            self.assertEqual(set(aliases), reference, key)

    def test_token_totals_count_calls_once_per_executed_group(self):
        totals = {'ladim': 5159134, 'matchfix': 12097425, 'swe': 20831495,
                  'direct': 429109, 'cte': 279536, 'msadapter': 0}
        for method, expected in totals.items():
            row = self.data['main'][method]
            self.assertEqual(row['tokens'], expected, method)
            self.assertEqual(row['groups'], 29)
            self.assertEqual(row['denominator'], 50)
        self.assertAlmostEqual(100 * (1 - totals['ladim'] / totals['matchfix']),
                               57.3534492, places=5)

    def test_interrupted_swe_final_does_not_inherit_an_initial_pass(self):
        rows = [r for r in self.audit['rows'] if r['interrupted']]
        self.assertEqual(len(rows), 1)
        self.assertIsNone(rows[0]['accepted'])
        swe = self.data['main']['swe']
        self.assertEqual(swe['missing'], 1)
        self.assertEqual(swe['accepted'], 44)
        self.assertEqual(swe['at_budget'], {'1': 44, '2': 44, '4': 44})

    def test_signal_results_score_full_final_checks(self):
        signals = self.data['training_signals']
        self.assertEqual([r['accepted'] for r in signals], [4, 8, 12, 16])
        self.assertEqual([r['controller_accepted'] for r in signals], [16] * 4)
        self.assertEqual([r['initially_accepted_by_visible_checks'] for r in signals],
                         [12, 8, 4, 0])
        self.assertEqual(sum(r['calls'] for r in signals), 690)
        self.assertEqual(sum(r['unknown_usage_calls'] for r in signals), 0)

    def test_generated_export_matches_its_frozen_inputs(self):
        saved = json.loads((ROOT / 'data/paper_figures/unified_results.json').read_text())
        self.assertEqual(saved, self.data)

    def test_paired_costs_cover_all_inputs_without_alias_weighting(self):
        pairs = self.data['paired_costs']
        self.assertEqual(len(pairs), 29)
        self.assertEqual(len({p['group'] for p in pairs}), 29)
        self.assertEqual(sum(p['initially_accepted'] for p in pairs), 20)
        for method in ('ladim', 'matchfix'):
            self.assertEqual(sum(p[method + '_tokens'] for p in pairs),
                             self.data['main'][method]['tokens'])
        # Includes each shared initial translation and all subsequent calls.
        first = next(p for p in pairs if p['group'] == 'group_001')
        self.assertEqual((first['ladim_tokens'], first['matchfix_tokens']), (303940, 173863))
        for initial, expected in [(True, 19), (False, 8)]:
            self.assertEqual(sum(p['ladim_tokens'] < p['matchfix_tokens']
                                 for p in pairs if p['initially_accepted'] == initial), expected)


if __name__ == '__main__':
    unittest.main()
