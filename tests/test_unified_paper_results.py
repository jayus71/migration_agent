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

    def test_repository_checks_keep_missing_measurements_in_denominator(self):
        rows = self.data['repository']
        self.assertEqual(len(rows), 6)
        expected_tokens = {
            ('timeseries', 'ladim'): 2614230, ('timeseries', 'swe'): 8199825,
            ('timeseries', 'matchfix'): 13597778, ('twotower', 'ladim'): 8811246,
            ('twotower', 'swe'): 8316552, ('twotower', 'matchfix'): 8679080}
        for row in rows:
            key = row['repository'], row['method']
            self.assertEqual(row['tokens'], expected_tokens[key])
            self.assertEqual(row['tokens'], row['translation_tokens'] +
                             row['repair_prompt_tokens'] + row['repair_completion_tokens'])
            self.assertEqual(row['accepted'], row['repository'] == 'timeseries')
            paired = row['paired_checks']
            self.assertEqual(paired['expected'], 69 if row['repository'] == 'timeseries' else 145)
            if row['repository'] == 'twotower':
                numerical = row['details']['numerical_checks']
                self.assertEqual(numerical['expected'], 114)
                missing = 0 if row['method'] == 'ladim' else 1
                self.assertEqual(len(paired['not_measured']), missing)
                self.assertEqual(len(numerical['not_measured']), missing)
                self.assertEqual(paired['passed'] + len(paired['failed']) + missing, 145)
                self.assertEqual(numerical['passed'] + len(numerical['failed']) + missing, 114)

    def test_natural_repairs_use_selected_method_and_preserve_initial_acceptance(self):
        rows = self.data['natural_repairs']
        self.assertEqual({r['method'] for r in rows}, {'ladim', 'swe', 'matchfix', 'direct'})
        for row in rows:
            self.assertEqual(row['retained'], 5)
            self.assertEqual(row['denominator'], 10)
            self.assertEqual(row['accepted'], row['repaired'] + row['retained'])
            self.assertEqual(row['repaired'], 4 if row['method'] == 'ladim' else 0)
        ladim = next(r for r in rows if r['method'] == 'ladim')
        self.assertEqual((ladim['tokens'], ladim['calls']), (13206863, 193))

    def test_natural_components_keep_same_program_denominators(self):
        rows = self.data['natural_components']
        self.assertEqual(len(rows), 5)
        self.assertEqual([r['repaired'] for r in rows], [4, 3, 0, 2, 4])
        self.assertEqual([r['tokens'] for r in rows],
                         [15547813, 14516463, 10851537, 17325026, 13206863])
        for row in rows:
            self.assertEqual(row['retained'], 5)
            self.assertEqual(row['accepted'], row['repaired'] + row['retained'])
        selected = next(r for r in self.data['natural_repairs'] if r['method'] == 'ladim')
        self.assertEqual(rows[-1]['tokens'], selected['tokens'])

    def test_main_table_cost_breakdowns_and_repository_signal_counts(self):
        for row in [*self.data['main'].values(), *self.data['cross_language']]:
            self.assertEqual(row['input_tokens'] + row['output_tokens'], row['tokens'])
        for row in self.data['repository']:
            signals = row['main_table_signals']
            if row['repository'] == 'timeseries':
                for key in ('loss', 'gradient', 'update'):
                    self.assertEqual(signals[key], {'passed': 9, 'expected': 9})
                self.assertEqual(signals['entry_points'], {'passed': 3, 'expected': 3})
            elif row['method'] == 'matchfix':
                self.assertEqual(signals['entry_points'], {'passed': 0, 'expected': 10})
                tests = row['details']['original_tests']
                self.assertEqual(tests['status'], 'collection_failed')
                self.assertEqual(tests['exit_code'], 2)
                self.assertEqual(tests['observed_outcomes'], [])
        table = (ROOT / 'figures/TABLE_main_comparison.tex').read_text()
        self.assertNotIn('Passed', table)
        self.assertNotIn('Failed', table)
        setup = (ROOT / 'sections/experiments.tex').read_text().split(r'\subsection{Main Results}')[0]
        for key in ('macedo2025codetransengine', 'openi2025msadapter',
                    'yang2024sweagent', 'ibrahimzada2025matchfixagent', 'macedo2024intertrans'):
            self.assertEqual(setup.count(r'\citep{' + key + '}'), 1)
        self.assertNotIn(r'\citep', table)
        costs = (ROOT / 'figures/TABLE_repository_costs.tex').read_text()
        self.assertEqual(costs.count('9/9 & 9/9'), 3)
        for expected in ('LaDiM & 18/18 & 15/18', 'SWE-agent & 17/18 & 12/18',
                         'MatchFixAgent & 18/18 & 16/18'):
            self.assertIn(expected, costs)

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
