import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    "resume_maintext_dispatch", Path(__file__).parents[1] / "scripts/resume_maintext_dispatch.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plan = {"variants": ["a", "b"]}
        for variant in self.plan["variants"]:
            run = self.root / variant
            run.mkdir()
            (run / "manifest.json").write_text(json.dumps({"tasks": [{"anonymous_id": "t1"}]}))

    def test_retains_functional_failure_and_only_schedules_absent(self):
        path = self.root / "a/conditions/t1/autonomous_layered"
        path.mkdir(parents=True)
        (path / "result.json").write_text(json.dumps({"status": "completed", "accepted": False}))
        pending, retained = module.inventory(self.root, self.plan)
        self.assertEqual(pending, [("t1", "b")])
        self.assertEqual(len(retained), 1)
        self.assertFalse(retained[0]["accepted"])

    def test_rejects_unfinished_existing_condition(self):
        (self.root / "a/conditions/t1").mkdir(parents=True)
        with self.assertRaisesRegex(RuntimeError, "no terminal result"):
            module.inventory(self.root, self.plan)

    def test_rejects_unknown_condition(self):
        (self.root / "a/conditions/unknown").mkdir(parents=True)
        with self.assertRaisesRegex(RuntimeError, "Unknown condition"):
            module.inventory(self.root, self.plan)


if __name__ == "__main__":
    unittest.main()
