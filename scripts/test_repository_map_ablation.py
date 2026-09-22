"""Preserved dependency behavior and absence of automatically extracted maps."""
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiments/repository_map_ablation_20260922'))
from map_adapter import NoAutomaticMapTools
from test_repository_agent_mode import RepositoryTests


class MapRemovalTests(RepositoryTests):
    def setUp(self):
        super().setUp()
        self.tools = NoAutomaticMapTools(self.ws, lambda _: {'accepted': True},
            state_path=self.base / 'no_map.json', validate_syntax=True)

    def test_symbol_inventory_records_parse_failures_without_guessing(self):
        # Parent inventory test is replaced: ordinary reads remain available,
        # while the automatic scanner must not run even when map is requested.
        with patch.object(self.tools, '_files', side_effect=AssertionError('automatic scan')):
            result = self.tools.execute('repository_map', {})
        self.assertNotIn('files', result)
        self.assertNotIn('unassigned_target_code_files', result)
        self.assertEqual(result['units'], {})
        self.assertIn('lines', self.tools.execute('read', {'path': 'target/a.py'}))


if __name__ == '__main__':
    unittest.main()
