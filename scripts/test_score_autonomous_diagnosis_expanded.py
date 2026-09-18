"""Verify evaluator-only overrides and unchanged scoring semantics offline."""
import json
import unittest
import score_autonomous_diagnosis as base
import score_autonomous_diagnosis_expanded as expanded
import test_score_autonomous_diagnosis as fixtures


class ExpandedTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.ScoreTests()
        self.fixture.setUp()

    def tearDown(self):
        self.fixture.tearDown()

    def test_overrides_leave_repair_config_and_base_unchanged(self):
        f = self.fixture
        original = f.config_path.read_bytes()
        original_factory, original_version = base.config_from_manifest, base.VERSION
        calls = []

        def valid(request, *, timeout):
            self.assertEqual(timeout, 600)
            self.assertEqual(request["max_tokens"], 32768)
            self.assertEqual(request["thinking"], {"type": "enabled"})
            self.assertEqual(request["reasoning_effort"], "high")
            calls.append(request)
            payload = json.loads(request["messages"][1]["content"])
            if "phase1_assessment" not in payload:
                return fixtures.response(fixtures.extracted(payload))
            return fixtures.response(fixtures.scored(payload["public_evidence"], payload, payload["phase1_assessment"]))

        report = expanded.run(f.pack, f.rubric, f.config_path, f.out, execute=True, transport=valid)
        self.assertEqual(report["phase_status_counts"], {"success": 2})
        expanded.run(f.pack, f.rubric, f.config_path, f.out, execute=True, transport=valid)
        self.assertEqual(len(calls), 2)
        self.assertEqual(f.config_path.read_bytes(), original)
        self.assertIs(base.config_from_manifest, original_factory)
        self.assertEqual(base.VERSION, original_version)
        self.assertEqual(calls[0]["messages"][0]["content"], base.PHASE1)
        self.assertEqual(calls[1]["messages"][0]["content"], base.PHASE2)
        provenance = base.read(f.out / "wrapper_manifest.json")
        self.assertEqual(provenance["original_model_configuration"]["max_tokens"], 16384)
        self.assertFalse(provenance["repair_configuration_changed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
