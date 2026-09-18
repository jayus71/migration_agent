from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "analyze_autonomous_process.py"
spec = importlib.util.spec_from_file_location("process_analysis", SCRIPT)
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


class Trace:
    def __init__(self, root, task="task_001", *, status="completed"):
        self.condition = Path(root) / "conditions" / task / "autonomous_layered"
        self.folder = self.condition / "evidence" / "agent"
        self.folder.mkdir(parents=True)
        self.index = 0
        self.result(status)

    def result(self, status):
        # Acceptance is deliberately unrelated to the process evidence.
        (self.condition / "result.json").write_text(json.dumps({"status": status, "accepted": True}))

    def event(self, kind, **data):
        self.index += 1
        path = self.folder / f"event_{self.index:05d}_{kind}.json"
        path.write_text(json.dumps({"kind": kind, "time": "2026-09-17T10:00:00Z", "data": data}))
        return path

    def start(self, attempt=1):
        self.event("stage_start", stage="repair", attempt=attempt)

    def call(self, number):
        self.event("api_start", call=number, stage="repair", attempt=1)

    def tool(self, number, name, result, arguments=None):
        return self.event("tool", call=number, name=name, arguments=arguments or {}, result=result)

    def end(self, calls, status="completed"):
        self.event("stage_end", calls=calls, status=status)

    def analyze(self):
        return analysis.analyze_condition(self.condition, suite="test", version="formal_v3")


def edit(path, *, before="a" * 64, after="b" * 64):
    return {"ok": True, "files": [{"path": path, "before_sha256": before, "after_sha256": after}]}


class ProcessAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_counts_require_byte_change_and_read_recurrence_has_explicit_epoch(self):
        trace = Trace(self.root)
        trace.start()
        read = {"path": "candidate.py", "lines": [{"line": 1, "text": "x = 1"}]}
        for number in (1, 2):
            trace.call(number)
            trace.tool(number, "read", read, {"path": "candidate.py"})
        trace.call(3)
        trace.tool(3, "edit", edit("candidate.py"))
        trace.tool(3, "edit", edit("scratch_tests/check.py", before=None))
        trace.call(4)
        trace.tool(4, "read", read, {"path": "candidate.py"})
        trace.call(5)
        trace.tool(5, "edit", edit("candidate.py", before="b" * 64))
        trace.tool(5, "edit", {"ok": True, "files": [{"path": "candidate.py"}]})
        trace.call(6)
        trace.tool(6, "edit", {"ok": False, "error_type": "ToolError", "error": "Unknown or missing tool arguments"})
        trace.call(7)
        trace.tool(7, "run_test", {"execution": {"status": "failed"}})
        trace.call(8)
        trace.end(8, "unvalidated_repair")
        row = trace.analyze()
        metrics = row["metrics"]
        self.assertTrue(row["eligible_completed"])
        self.assertEqual(metrics["llm_calls_started"], 8)
        self.assertEqual(metrics["successful_production_edit_operations"], 1)
        self.assertEqual(metrics["successful_scratch_edit_operations"], 1)
        self.assertEqual(metrics["successful_edits_without_byte_change"], 1)
        self.assertEqual(metrics["unverifiable_edit_file_records"], 1)
        self.assertEqual(metrics["repeated_identical_reads"], 2)
        self.assertEqual(metrics["repeated_identical_reads_without_file_change"], 1)
        self.assertEqual(metrics["peak_inspection_only_rounds"], 2)
        self.assertEqual(metrics["run_test_observations"], 1)
        self.assertEqual(metrics["edit_structure_errors"], 1)
        self.assertEqual(metrics["unvalidated_repair_stages"], 1)
        self.assertNotIn("accepted", row)

    def test_feedback_excludes_same_batch_and_distinguishes_pending_next_stage(self):
        trace = Trace(self.root, status="running")
        trace.start()
        trace.call(1)
        trace.tool(1, "edit", {"ok": False, "error_type": "ToolError", "error": "Every edit requires only path, old and new", "schema_feedback": {}})
        trace.tool(1, "run_test", {"measured": True})  # Already selected before feedback.
        trace.call(2)
        trace.tool(2, "run_test", {"ok": False, "error_type": "ToolError", "error": "Unknown test"})
        trace.end(2, "investigation_only")
        row = trace.analyze()
        follow = row["feedback_follow_through"][0]["follow_through"]
        self.assertFalse(follow["next_call"]["test_or_edit"])
        self.assertFalse(follow["remaining_current_stage"]["test_or_edit"])
        self.assertIsNone(follow["next_stage"]["test_or_edit"])
        trace.start(2)
        trace.call(3)
        trace.tool(3, "run_test", {"execution": "failed"})
        trace.tool(3, "edit", edit("candidate.py"))
        trace.call(4)
        trace.end(2)
        trace.result("completed")
        row = trace.analyze()
        follow = row["feedback_follow_through"][0]["follow_through"]
        self.assertTrue(follow["next_stage"]["observed"]["test_observation"])
        self.assertTrue(follow["next_stage"]["observed"]["production_edit"])
        self.assertEqual(follow["next_stage"]["status"], "closed")

    def test_live_last_call_cannot_prematurely_count_as_pure_inspection(self):
        trace = Trace(self.root, status="running")
        trace.start()
        for number in (1, 2, 3):
            trace.call(number)
            trace.tool(number, "list", {"files": []})
        trace.event("stage_progress_checkpoint", call=3, stage="repair", attempt=1)
        row = trace.analyze()
        self.assertEqual(row["metrics"]["peak_inspection_only_rounds"], 2)
        self.assertEqual(row["open_call_numbers"], [3])
        self.assertFalse(row["eligible_completed"])
        self.assertIsNone(row["feedback_follow_through"][0]["follow_through"]["next_call"]["test_or_edit"])
        trace.call(4)
        trace.end(4, "call_budget_exhausted")
        trace.result("completed")
        row = trace.analyze()
        self.assertEqual(row["metrics"]["peak_inspection_only_rounds"], 3)
        self.assertTrue(row["eligible_completed"])
        self.assertEqual(row["metrics"]["successful_production_edit_operations"], 0)

    def test_zero_call_budget_exit_is_complete_with_zero_edits(self):
        trace = Trace(self.root)
        trace.start()
        trace.end(0, "call_budget_exhausted")
        row = trace.analyze()
        self.assertTrue(row["eligible_completed"])
        self.assertEqual(row["metrics"]["llm_calls_started"], 0)
        self.assertEqual(row["changed_edits"], [])

    def test_pairing_uses_only_common_complete_tasks(self):
        for version, counts in (("formal_v3", (2, 8, 3)), ("progress_v4", (4, 1, 9))):
            for task, count in enumerate(counts, 1):
                status = "running" if (version, task) in {("progress_v4", 2), ("formal_v3", 3)} else "completed"
                trace = Trace(self.root / version, f"task_{task:03d}", status=status)
                trace.start()
                for number in range(1, count + 1):
                    trace.call(number)
                if status == "completed":
                    trace.end(count)
        report = analysis.build_report([("test", v, self.root / v) for v in ("formal_v3", "progress_v4")])
        paired = report["paired_comparisons"][0]
        self.assertEqual(paired["paired_tasks"], ["task_001"])
        self.assertEqual(paired["mean_difference_right_minus_left"]["llm_calls_started"], 2)
        self.assertEqual(paired["completed_but_unmatched"], {"formal_v3": ["task_002"], "progress_v4": ["task_003"]})

    def test_incomplete_or_corrupt_logs_do_not_enter_completed_pairs(self):
        trace = Trace(self.root)
        trace.start()
        trace.call(1)
        trace.end(1)
        (trace.folder / "event_00099_tool.json").write_text('{"unfinished":')
        row = trace.analyze()
        self.assertFalse(row["eligible_completed"])
        self.assertEqual(row["observation_state"], "terminal_incomplete_log")
        self.assertTrue(row["read_issues"])

    def test_cli_refuses_to_write_inside_input_run(self):
        Trace(self.root)
        output = self.root / "new-analysis.json"
        result = subprocess.run([sys.executable, str(SCRIPT), "--run", "test", "formal_v3", str(self.root),
                                 "--output", str(output)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("outside every input run", result.stderr)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
