"""Offline invariants for removing explicit work-unit coordination only."""
import ast
import copy
import inspect
import json
from pathlib import Path
import sys
import textwrap
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT))
from unit_adapter import NoWorkUnitTools, NoWorkUnitAgent, REMOVED_TOOLS, NO_UNIT_GUIDANCE
from test_repository_agent_mode import RepositoryTests
from autofix.autonomous.repository import RepositoryTools, RepositoryAgent
from autofix.autonomous.agent import AgentConfig
from autofix.autonomous.tools import ToolError


class AdapterTests(unittest.TestCase):
    def setUp(self):
        RepositoryTests.setUp(self)
        self.full = self.tools
        self.tools = NoWorkUnitTools(self.ws, lambda _: {'accepted': True},
            state_path=self.base / 'without_units.json', validate_syntax=True)

    def tearDown(self):
        self.temp.cleanup()

    def test_exact_original_transaction_minus_declared_coordination(self):
        original = textwrap.dedent(inspect.getsource(RepositoryTools._edit))
        guard = original[original.index('    for edit in edits:'):original.index('    notebooks={};regular=[]')]
        propagation = original[original.index('    stale={key'):original.index('    self.revision+=1;self._persist()')]
        expected = original.replace(guard, '').replace(propagation, '')
        expected = expected.replace("result['invalidated_units']=sorted(stale)", "result['invalidated_units']=[]")
        expected = expected.replace('super()._edit(regular,readonly=readonly)', 'WorkspaceTools._edit(self,regular,readonly=readonly)')
        actual = textwrap.dedent(inspect.getsource(NoWorkUnitTools._edit))
        self.assertEqual(ast.dump(ast.parse(expected)), ast.dump(ast.parse(actual)))

    def test_multifile_edit_needs_no_plan_or_focus(self):
        result = self.tools.execute('edit', {'edits': [
            {'path': 'target/a.py', 'old': 'x = 1', 'new': 'x = 2'},
            {'path': 'target/b.py', 'old': 'x = 1', 'new': 'x = 3'}]})
        self.assertTrue(result['ok'])
        self.assertEqual(self.tools.units, {})
        self.assertIsNone(self.tools.active)
        self.assertEqual(result['invalidated_units'], [])
        self.assertEqual(self.tools.content_revision, 1)
        self.assertEqual((self.ws / 'target/b.py').read_text(), 'x = 3\n')
        with self.assertRaises(ToolError):
            self.full.execute('edit', {'edits': [{'path': 'target/a.py', 'old': 'x = 2', 'new': 'x = 4'}]})

    def test_source_and_task_and_diagnosis_stay_readonly(self):
        for path in ('source/a.py', 'task.json'):
            before = (self.ws / path).read_bytes()
            with self.assertRaises(ToolError):
                self.tools.execute('edit', {'edits': [{'path': path, 'old': '', 'new': 'bad'}]})
            self.assertEqual(before, (self.ws / path).read_bytes())
        with self.assertRaises(ToolError):
            self.tools.execute('edit', {'edits': [{'path': 'target/a.py', 'old': 'x = 1', 'new': 'x = 2'}]}, readonly=True)

    def test_map_retains_exact_automatic_inventory(self):
        self.assertEqual(self.full.inventory()['files'], self.tools.inventory()['files'])
        self.assertTrue(self.tools.inventory()['files']['target/demo.ipynb']['cells'])
        self.assertNotIn('units', self.tools.inventory())

    def test_removed_tools_unavailable_and_no_callback(self):
        names = {s['function']['name'] for s in self.tools.schemas()}
        self.assertFalse(names & REMOVED_TOOLS)
        self.assertTrue({'repository_map', 'repository_evidence', 'edit', 'run_test', 'notebook'} <= names)
        for name in REMOVED_TOOLS:
            with self.assertRaises(ToolError):
                self.tools.execute(name, {})
        self.tools.focus_callback = lambda: self.fail('Unexpected unit context boundary')
        self.tools.execute('edit', {'edits': [{'path': 'target/a.py', 'old': 'x = 1', 'new': 'x = 2'}]})

    def test_notebook_cell_edit_preserves_transaction(self):
        self.tools.execute('edit', {'edits': [{'path': 'target/demo.ipynb', 'cell': 0, 'old': 'x = 1', 'new': 'x = 2'}]})
        value = json.loads((self.ws / 'target/demo.ipynb').read_text())
        self.assertEqual(value['cells'][0]['source'], ['x = 2\n'])
        self.assertTrue(all(c['outputs'] == [] for c in value['cells']))
        before = (self.ws / 'target/a.py').read_bytes()
        with self.assertRaises(ToolError):
            self.tools.execute('edit', {'edits': [
                {'path': 'target/a.py', 'old': 'x = 1', 'new': 'x = 5'},
                {'path': 'target/demo.ipynb', 'cell': 0, 'old': 'x = 2', 'new': 'x = ('}]})
        self.assertEqual(before, (self.ws / 'target/a.py').read_bytes())

    def test_global_working_set_and_test_staleness(self):
        for path in ('target/a.py', 'target/b.py'):
            self.tools.execute('read', {'path': path})
        self.assertEqual({r['path'] for r in self.tools.working_set(120000)['read_results']}, {'target/a.py', 'target/b.py'})
        self.tools.record_test('paired', {'accepted': True})
        self.tools.execute('edit', {'edits': [{'path': 'target/a.py', 'old': 'x = 1', 'new': 'x = 2'}]})
        self.assertFalse(self.tools.evidence_state()['paired']['current'])
        self.assertEqual({r['path'] for r in self.tools.working_set(120000)['read_results']}, {'target/b.py'})

    def test_handoff_guidance_and_original_capacity_rebuild(self):
        agent = NoWorkUnitAgent(self.tools, self.base / 'agent', config=AgentConfig(), client=lambda **kw: self.fail('API'))
        self.assertIn(NO_UNIT_GUIDANCE, agent.history[0]['content'])
        with patch.object(RepositoryAgent, '_stage', return_value='offline'):
            self.assertEqual(agent.repair({'accepted': False}, 1), 'offline')
        self.assertIn(NO_UNIT_GUIDANCE, agent.history[0]['content'])
        self.assertNotIn('Propose semantic work units using plan_units', agent.history[0]['content'])
        self.assertIs(NoWorkUnitAgent._rebuild_context, RepositoryAgent._rebuild_context)
        self.assertIs(NoWorkUnitAgent._prepare_repository_context, RepositoryAgent._prepare_repository_context)
        agent.context_pending = 'context_capacity'
        before = (agent.calls, agent.output_tokens)
        agent._prepare_repository_context(agent.history)
        self.assertEqual(before, (agent.calls, agent.output_tokens))
        self.assertIsNone(agent.context_pending)
        self.assertEqual(self.tools.units, {})


if __name__ == '__main__':
    unittest.main()
