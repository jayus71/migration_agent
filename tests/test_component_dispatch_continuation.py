import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location("continuation", Path(__file__).resolve().parents[1] / "scripts/continue_component_dispatch.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class InventoryTests(unittest.TestCase):
    def test_keeps_success_and_failure_and_only_starts_absent_directories(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for task, accepted in (("task_001", True), ("task_002", False)):
                result = root / "variant/conditions" / task / "autonomous_layered/result.json"
                result.parent.mkdir(parents=True)
                result.write_text(json.dumps({"status": "completed", "accepted": accepted}))
            complete, pending = module.inventory(root, [(f"task_00{i}", "variant") for i in (1, 2, 3)])
            self.assertEqual([row["accepted"] for row in complete], [True, False])
            self.assertEqual(pending, [("task_003", "variant")])

    def test_infrastructure_error_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            result = root / "variant/conditions/task_001/autonomous_layered/result.json"
            result.parent.mkdir(parents=True)
            result.write_text(json.dumps({"status": "infrastructure_error", "accepted": None}))
            complete, pending = module.inventory(root, [("task_001", "variant")])
            self.assertEqual(complete[0]["status"], "infrastructure_error")
            self.assertEqual(pending, [])

    def test_existing_nonterminal_directory_is_not_restarted(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "variant/conditions/task_001").mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, "terminal result"):
                module.inventory(root, [("task_001", "variant")])

    def test_drain_waits_for_real_worker_before_terminating_only_dispatcher(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = root / "run_maintext_ablations.py"
            script.write_text(
                "import json, subprocess, sys, time\n"
                "from pathlib import Path\n"
                "root = Path(__file__).parent\n"
                "if sys.argv[1] == 'worker':\n"
                "    time.sleep(1)\n"
                "    p = root / 'variant/conditions/task_001/autonomous_layered/result.json'\n"
                "    p.parent.mkdir(parents=True)\n"
                "    p.write_text(json.dumps({'status':'completed','accepted':False}))\n"
                "else:\n"
                "    child = subprocess.Popen([sys.executable, __file__, 'worker'])\n"
                "    (root / 'child_pid').write_text(str(child.pid))\n"
                "    child.wait()\n"
                "    time.sleep(60)\n")
            record = root / "records"
            record.mkdir()
            dispatcher = subprocess.Popen([sys.executable, str(script), "dispatch", "--output", str(root)])
            try:
                deadline = time.monotonic() + 10
                while not (root / "child_pid").exists():
                    if time.monotonic() > deadline:
                        self.fail("Fixture dispatcher did not start its worker")
                    time.sleep(0.01)
                with patch.object(module, "load_runner", return_value=None), patch.object(
                        module, "grid", return_value=[("task_001", "variant")]):
                    module.drain(root, dispatcher.pid, record)
                self.assertEqual(dispatcher.wait(timeout=10), -signal.SIGKILL)
                inventory = json.loads((record / "drained_inventory.json").read_text())
                self.assertEqual(inventory["completed"][0]["accepted"], False)
                self.assertEqual(inventory["pending"], [])
            finally:
                if dispatcher.poll() is None:
                    os.kill(dispatcher.pid, signal.SIGCONT)
                    dispatcher.kill()
                    dispatcher.wait(timeout=10)


if __name__ == "__main__":
    unittest.main()
