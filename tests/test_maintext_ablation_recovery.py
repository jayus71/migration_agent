import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

spec = importlib.util.spec_from_file_location('recovery', Path(__file__).resolve().parents[1] / 'scripts/recover_maintext_ablations.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RecoveryTests(unittest.TestCase):
    def test_only_infrastructure_failure_is_selected(self):
        with tempfile.TemporaryDirectory() as folder:
            run = Path(folder)
            module.save(run / 'variant/manifest.json', {'tasks': [{'anonymous_id': str(i)} for i in range(3)]})
            for i, (status, accepted) in enumerate([('completed', True), ('completed', False), ('infrastructure_error', False)]):
                module.save(run / 'variant/conditions' / str(i) / 'autonomous_layered/result.json',
                            {'status': status, 'accepted': accepted})
            self.assertEqual([row['task'] for row in module.eligible(run, 'variant')], ['2'])
            self.assertEqual(module.eligible(run, 'without_repair_history'), [])

    def test_numeric_status_survives_frozen_client_without_body_or_credentials(self):
        with tempfile.TemporaryDirectory() as folder:
            run = Path(folder)
            def old_worker(*args):
                return urllib.request.urlopen('https://example.invalid')
            error = urllib.error.HTTPError('https://example.invalid', 402, 'secret-body', {}, None)
            with patch.object(urllib.request, 'urlopen', side_effect=error), patch.object(
                    module, 'load', return_value=SimpleNamespace(worker=old_worker)):
                with self.assertRaises(urllib.error.HTTPError):
                    module.worker(run, Path('unused'), 'task_001')
            data = (run / 'conditions/task_001/autonomous_layered/transport_failures.json').read_text()
            self.assertEqual(json.loads(data)[0]['http_status'], 402)
            self.assertNotIn('secret', data)
            self.assertNotIn('example.invalid', data)

    def test_existing_recovery_condition_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            run = Path(folder)
            (run / 'conditions/task_001/autonomous_layered').mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, 'already exists'):
                module.worker(run, Path('unused'), 'task_001')


if __name__ == '__main__':
    unittest.main()
