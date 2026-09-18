import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('signals', Path(__file__).resolve().parents[1] / 'scripts/run_training_signal_ablations.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def observed():
    checks = dict.fromkeys(['schema', 'backend_attested', 'source_immutable', 'command_execution',
        'reference_execution', 'target_execution', 'training_reported', 'loss_abs_diff',
        'layer_differences_coverage', 'layer_differences_agreement', 'grad_norm_abs_diff',
        'gradient_vector_l2', 'param_update_rel_l2'], True)
    return {'schema_version': 'autonomous-observation-v1', 'execution': {},
        'measurements': {key: {'value': 0, 'status': 'observed'} for key in ('loss_abs_diff', 'grad_norm_abs_diff', 'param_update_rel_l2')},
        'layer_differences': [], 'parameter_updates': [{'update_rel_l2': 999}],
        'gradient_vector_comparison': {'value': 0},
        'acceptance': {'accepted': True, 'checks': checks, 'reasons': [],
                       'thresholds': {'loss_abs': .02, 'grad_norm_abs': .05, 'param_rel_l2': .03}}}


class SignalTests(unittest.TestCase):
    def test_hidden_update_failure_does_not_leak_through_aggregate_or_parameter_rows(self):
        value = observed()
        value['acceptance'].update(accepted=False, reasons=['param_update_rel_l2'])
        value['acceptance']['checks']['param_update_rel_l2'] = False
        before = copy.deepcopy(value)
        for variant in module.VARIANTS[:-1]:
            masked = module.mask(value, variant)
            self.assertTrue(masked['acceptance']['accepted'])
            self.assertEqual(masked['parameter_updates'], [])
            self.assertNotIn('param_update_rel_l2', masked['measurements'])
            self.assertNotIn('param_update_rel_l2', masked['acceptance']['reasons'])
        self.assertFalse(module.mask(value, 'all_observations')['acceptance']['accepted'])
        self.assertEqual(value, before)

    def test_measured_gradient_failure_appears_at_gradient_setting(self):
        value = observed()
        value['acceptance'].update(accepted=False, reasons=['gradient_vector_l2'])
        value['acceptance']['checks']['gradient_vector_l2'] = False
        self.assertTrue(module.expected_signature(value, 'gradient')['valid'])

    def test_missing_execution_check_cannot_pass(self):
        value = observed()
        del value['acceptance']['checks']['target_execution']
        self.assertFalse(module.mask(value, 'execution')['acceptance']['accepted'])

    def test_execution_only_omits_forward_and_gradient_measurements(self):
        value = module.mask(observed(), 'execution')
        self.assertEqual(value['measurements'], {})
        self.assertNotIn('gradient_vector_comparison', value)
        self.assertEqual(value['acceptance']['thresholds'], {})


if __name__ == '__main__':
    unittest.main()
