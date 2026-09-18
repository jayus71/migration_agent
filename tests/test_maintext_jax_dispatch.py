import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


spec = importlib.util.spec_from_file_location(
    "jax_dispatch", Path(__file__).resolve().parents[1] / "scripts/dispatch_maintext_jax_autonomous.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DispatchTests(unittest.TestCase):
    def test_structured_and_frozen_client_errors_stop_dispatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            error = root / "conditions/task_001/autonomous_layered/evidence/agent/call_001_error.json"
            error.parent.mkdir(parents=True)
            self.assertFalse(module.transport_blocked(root))
            for value in ({"http_status": 402}, {"error": "LLM endpoint returned HTTP 402"},
                          {"error": "HTTP 401: Unauthorized"}, {"http_status": 403}):
                error.write_text(json.dumps(value))
                self.assertTrue(module.transport_blocked(root))
            error.write_text(json.dumps({"error": "ConnectionResetError"}))
            self.assertFalse(module.transport_blocked(root))


if __name__ == "__main__":
    unittest.main()
