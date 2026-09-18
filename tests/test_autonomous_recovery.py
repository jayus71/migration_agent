import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


spec = importlib.util.spec_from_file_location("recovery", Path(__file__).resolve().parents[1] / "scripts/run_autonomous_recovery.py")
recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recovery)


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.original = self.root / "experiments/formal_v3"
        recovery.save(self.original / "manifest.json", {"model": "frozen-model"})
        recovery.save(self.original / "code_snapshot/code.json", {"prompt": "frozen-prompt"})
        recovery.save(self.original / "private_inputs/task_001/task.json", {"input": "original"})
        recovery.save(self.original / "conditions/task_001/agent/result.json", {"status": "infrastructure_error"})
        self.item = {"benchmark": "Fixed50", "version": "formal_v3", "task": "task_001", "method": "agent",
                     "original_status": "infrastructure_error", "original_run": "experiments/formal_v3",
                     "manifest_sha256": recovery.sha(self.original / "manifest.json")}
        self.inventory = self.root / "inventory.json"

    def prepare(self):
        recovery.save(self.inventory, {"conditions": [self.item]})
        return recovery.prepare(self.root, self.inventory, self.root / "new")

    def test_restart_retains_manifest_code_inputs_and_original_failure(self):
        plan = self.prepare()
        run = Path(plan["conditions"][0]["recovery_run"])
        for relative in ("manifest.json", "code_snapshot/code.json", "private_inputs/task_001/task.json"):
            self.assertEqual((run / relative).read_bytes(), (self.original / relative).read_bytes())
        self.assertFalse((run / "conditions").exists())
        self.assertEqual(recovery.read(self.original / "conditions/task_001/agent/result.json")["status"], "infrastructure_error")
        with self.assertRaises(ValueError):
            self.prepare()

    def test_completed_failure_is_never_restarted(self):
        recovery.save(self.original / "conditions/task_001/agent/result.json", {"status": "completed", "accepted": False})
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse((self.root / "new").exists())

    def test_pending_with_artifacts_is_not_silently_restarted(self):
        self.item["original_status"] = "not_started"
        with self.assertRaises(ValueError):
            self.prepare()

    def test_changed_manifest_is_rejected(self):
        recovery.save(self.original / "manifest.json", {"model": "changed"})
        with self.assertRaises(ValueError):
            self.prepare()


if __name__ == "__main__":
    unittest.main()
