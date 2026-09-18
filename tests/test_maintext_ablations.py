"""Offline checks for isolated component treatments; no provider requests."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

runner = Path(__file__).resolve().parents[1] / "scripts/run_maintext_ablations.py"
if not runner.exists():
    runner = Path(__file__).with_name("run_maintext_ablations.py")
spec = importlib.util.spec_from_file_location("maintext_ablation_runner", runner)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
agent_class, prepare = module.agent_class, module.prepare
try:
    from autofix.autonomous.agent import AgentConfig, AutonomousAgent
    from autofix.autonomous.tools import WorkspaceTools
except ModuleNotFoundError as error:
    if error.name != "autofix":
        raise
    raise unittest.SkipTest(
        "Requires the separate ascend-torch4ms experiment runtime on PYTHONPATH"
    ) from error


class ComponentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        public = self.root / "public"
        public.mkdir()
        (public / "candidate.py").write_text("value = 2\n")
        (public / "task.json").write_text("{}")
        (public / "torch4ms").mkdir()
        self.tools = WorkspaceTools(public, run_test=lambda request: {"execution": "ok"})

    def make(self, variant, client=None):
        cls = agent_class(AutonomousAgent, variant)
        return cls(self.tools, self.root / variant,
                   config=AgentConfig(memory_policy="evidence", workflow_policy="progress_loop"),
                   client=client or (lambda *_: None))

    def test_continuous_role_preserves_actual_conversation(self):
        agent = self.make("continuous_role")
        agent.history.extend([{"role": "user", "content": "observed initial result"},
                              {"role": "assistant", "content": "supported hypothesis",
                               "reasoning_content": "provider reasoning"}])
        before = copy.deepcopy(agent.history)
        agent._handoff_to_fixer()
        self.assertEqual(agent.history, before)
        self.assertEqual(agent.verifier_history, before)
        self.assertEqual(agent.active_role, "continuous_agent")

    def test_history_reset_keeps_handoff_current_code_and_lifetime_budget(self):
        agent = self.make("without_repair_history")
        agent.history.append({"role": "assistant", "content": "initial evidence"})
        agent.last_diagnosis = {"observations": ["initial evidence"]}
        observed = []
        def stage(_stage, observation, *, attempt):
            observed.append(copy.deepcopy(agent.history))
            agent.history.append({"role": "assistant", "content": "failed repair history"})
            agent.calls += 2
            agent.last_diagnosis = {"observations": ["prior repair outcome"]}
        with patch.object(agent, "_stage", side_effect=stage):
            agent.repair({"difference": 1}, 1)
            (self.tools.root / "candidate.py").write_text("value = 3\n")
            agent.repair({"difference": 2}, 2)
        self.assertEqual(observed[0], observed[1])
        self.assertNotIn("failed repair history", json.dumps(observed[1]))
        self.assertIn("initial evidence", json.dumps(observed[1]))
        self.assertNotIn("Your conversation persists across repair attempts.", json.dumps(observed[1]))
        self.assertIn("Earlier repair conversations are not retained", json.dumps(observed[1]))
        self.assertEqual(agent.calls, 4)
        self.assertEqual((self.tools.root / "candidate.py").read_text(), "value = 3\n")

    def test_progress_prompt_absent_from_real_next_request(self):
        requests = []
        def client(request, timeout):
            requests.append(copy.deepcopy(request))
            number = len(requests)
            message = {"role": "assistant", "content": None}
            if number <= 3:
                message["tool_calls"] = [{"id": f"call{number}", "type": "function",
                    "function": {"name": "list", "arguments": "{}"}}]
            else:
                message["content"] = '{"diagnosis":{"observations":["observed"]},"summary":"done"}'
            return {"model": "deepseek-flash", "choices": [{"message": message, "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 10}}
        agent = self.make("without_progress_prompt", client)
        agent.diagnose({"execution": "ok"})
        self.assertEqual(len(requests), 4)
        self.assertNotIn("Stage progress checkpoint:", json.dumps(requests[-1]))
        self.assertEqual(len(list(agent.log_dir.glob("*ablation_progress_prompt_omitted.json"))), 1)

    def test_format_control_preserves_native_schema_and_rejection(self):
        agent = self.make("without_edit_format_feedback")
        self.assertEqual(agent._stage_tool_schemas(readonly=False), self.tools.schemas(readonly=False))
        self.assertIsNone(agent._edit_format_feedback({"path": "candidate.py"}, "invalid edit"))
        self.assertEqual((self.tools.root / "candidate.py").read_text(), "value = 2\n")

    def test_other_controls_retain_format_feedback(self):
        for variant in ("continuous_role", "without_repair_history", "without_progress_prompt"):
            agent = self.make(variant)
            self.assertIn("Argument format", json.dumps(agent._stage_tool_schemas(readonly=False)))
            self.assertIsNotNone(agent._edit_format_feedback({"path": "candidate.py"}, "Unknown or missing tool arguments"))

    def test_transport_blocker_handles_frozen_v4_errors_without_credentials(self):
        path = self.root / "continuous_role/conditions/task_001/autonomous_layered/evidence/agent/call_00001_error.json"
        path.parent.mkdir(parents=True)
        for value in ({"error": "RuntimeError: LLM endpoint returned HTTP 402"}, {"http_status": 403}):
            path.write_text(json.dumps(value))
            blocked = module.transport_blockers(self.root)
            self.assertEqual(len(blocked), 1)
            self.assertIn(blocked[0]["http_status"], (402, 403))
        path.write_text('{"error":"LLM endpoint network request failed"}')
        self.assertEqual(module.transport_blockers(self.root), [])

    def test_frozen_verification_rejects_mutated_input_and_extra_files(self):
        run = self.root / "without_progress_prompt"
        source = run / "private_inputs/task_001/candidate.py"
        source.parent.mkdir(parents=True)
        source.write_text("value = 2\n")
        module.write_json(run / "manifest.json", {"tasks": []})
        module.write_json(run / "frozen_hashes.json", {str(source.relative_to(run)): module.sha(source)})
        module.write_json(self.root / "plan.json", {
            "runner_sha256": module.sha(Path(module.__file__)),
            "variant_manifest_sha256": {run.name: module.sha(run / "manifest.json")}})
        module.verify_frozen(run)
        source.write_text("value = 3\n")
        with self.assertRaisesRegex(RuntimeError, "changed"):
            module.verify_frozen(run)
        source.write_text("value = 2\n")
        source.with_name("extra.py").write_text("extra = 1\n")
        with self.assertRaisesRegex(RuntimeError, "inventory"):
            module.verify_frozen(run)


if __name__ == "__main__":
    unittest.main()
