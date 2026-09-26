"""Ensure the anonymous export still evaluates submitted candidate repairs."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from autofix.autonomous import experiment
from autofix.autonomous.agent import StageResult


class ExportControllerTests(unittest.TestCase):
    def test_controller_submits_repairs_and_refuses_to_overwrite(self):
        class Evaluator:
            def __init__(self, workspace):
                self.workspace = workspace
            def paired(self):
                accepted = self.workspace.joinpath('candidate.py').read_text() == 'value = 2\n'
                return {'accepted': accepted, 'observation': {'accepted': accepted}}
            def confirm(self):
                return [self.paired(), self.paired()]
            def tool(self, request):
                return self.paired()['observation']

        def diagnose(agent, observation):
            return StageResult(status='completed', final={}, diagnosis=None, calls=0, usage={}, edited_files=[])

        def repair(agent, observation, attempt=1):
            agent.tools.execute('edit', {'edits': [{'path': 'candidate.py', 'old': '1', 'new': '2'}]})
            return StageResult(status='completed', final={}, diagnosis=None, calls=0, usage={}, edited_files=['candidate.py'])

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            inputs = root / 'private_inputs/example'
            inputs.mkdir(parents=True)
            (inputs / 'candidate.py').write_text('value = 1\n')
            (inputs / 'source.py').write_text('value = 2\n')
            (inputs / 'task.json').write_text('{}')
            config = {'model': 'offline', 'max_calls': 40, 'max_output_tokens': 120000,
                      'max_seconds': 1800, 'per_call_output_tokens': 16384, 'max_repair_attempts': 4}
            (root / 'manifest.json').write_text(json.dumps(config))
            with patch.object(experiment, 'evaluator_for', side_effect=lambda run, task, ws, *args: Evaluator(ws)), \
                 patch('autofix.autonomous.agent.OpenAICompatibleClient'), \
                 patch('autofix.autonomous.agent.AutonomousAgent.diagnose', diagnose), \
                 patch('autofix.autonomous.agent.AutonomousAgent.repair', repair):
                result = experiment.run_condition(root, 'example', 'autonomous_layered', Path('/unused'))
                self.assertEqual(result['status'], 'completed')
                self.assertTrue(result['accepted'])
                self.assertEqual(len(result['attempts']), 1)
                with self.assertRaisesRegex(RuntimeError, 'overwrite'):
                    experiment.run_condition(root, 'example', 'autonomous_layered', Path('/unused'))


if __name__ == '__main__':
    unittest.main()
