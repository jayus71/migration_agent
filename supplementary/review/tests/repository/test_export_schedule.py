"""Exercise the exported repository schedule without models or benchmark data."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import orchestration as run
from autofix.autonomous.agent import StageResult


class ExportScheduleTests(unittest.TestCase):
    def test_repair_confirmation_and_shared_translation_accounting(self):
        class Evaluator:
            def __init__(self, workspace):
                self.workspace = workspace
            def final(self):
                accepted = (self.workspace / 'target/module.py').read_text() == 'value = 2\n'
                return {'accepted': accepted, 'observation': {'accepted': accepted}}
            def tool(self, request):
                return self.final()['observation']

        def diagnose(agent, observation):
            return StageResult('completed', {}, None, 0, {}, [])

        def repair(agent, observation, attempt):
            self.assertEqual(attempt, 1)
            self.assertEqual(agent.config.repair_calls_per_stage, 16)
            (agent.tools.root / 'target/module.py').write_text('value = 2\n')
            return StageResult('completed', {}, None, 0, {}, ['target/module.py'])

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'source').mkdir()
            (root / 'source/module.py').write_text('value = 2\n')
            (root / 'translation/target').mkdir(parents=True)
            (root / 'translation/target/module.py').write_text('value = 1\n')
            run.save(root / 'task.json', {})
            run.save(root / 'freeze.json', {})
            run.save(root / 'manifest.json', {'source_hashes': run.hashes(root / 'source'),
                                             'task_sha256': run.digest(root / 'task.json')})
            run.save(root / 'translation/result.json', {'target_hashes': run.hashes(root / 'translation/target'),
                                                        'usage': {'total_tokens': 11}})
            with patch('autofix.autonomous.agent.OpenAICompatibleClient'), \
                 patch.object(run.RepositoryAgent, 'diagnose', diagnose), \
                 patch.object(run.RepositoryAgent, 'repair', repair):
                run.run('timeseries', 'ladim', root, lambda repo, ws, evidence: Evaluator(ws))
            result = run.read(root / 'conditions/ladim/result.json')
            self.assertEqual(result['status'], 'completed')
            self.assertTrue(result['accepted'])
            self.assertTrue(result['source_unchanged'])
            self.assertTrue(result['task_unchanged'])
            self.assertEqual(result['end_to_end_tokens'], 11)
            self.assertEqual(len(result['attempts']), 1)


if __name__ == '__main__':
    unittest.main()
