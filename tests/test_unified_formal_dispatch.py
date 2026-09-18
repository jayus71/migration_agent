"""Offline checks for reuse and immutable concurrent-worker inputs."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("unified_dispatch", ROOT / "scripts/dispatch_unified_formal_20260918.py")
dispatch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dispatch)


class DispatchTests(unittest.TestCase):
    def test_every_repair_reuses_the_matching_single_generation(self):
        review = ROOT / "data/audits/unified50-preflight-20260918/final_review"
        jobs = dispatch.plan(review)
        direct = {j["group"]: j for j in jobs if j["lane"] == "main" and j["method"] == "direct"}
        self.assertEqual(len(direct), 29)
        self.assertEqual(len(jobs), 391)
        self.assertEqual(len({dispatch.result_path(j) for j in jobs}), 391)
        for job in jobs:
            if job["kind"] == "repair" and job["lane"] != "cross_language":
                self.assertEqual(job["dependency"], direct[job["group"]]["id"])
                self.assertEqual(job["task"], direct[job["group"]]["task"])
            if job["lane"] == "cross_language":
                self.assertIsNone(job["dependency"])

    def fixture(self, folder):
        review, bundle, references, generations = [folder / name for name in ("review", "bundle", "references", "generations")]
        (review / "analyses/without_repair_history").mkdir(parents=True)
        public = bundle / "public/task_001"
        public.mkdir(parents=True)
        (public / "source.py").write_text("source = 1\n")
        dispatch.save(public / "task.json", {"seed": 101})
        generation = generations / "group_001/direct"
        generation.mkdir(parents=True)
        (generation / "candidate.py").write_text("candidate = 1\n")
        dispatch.save(generation / "generation.json", {"status": "generated", "candidate_sha256": dispatch.digest(generation / "candidate.py")})
        group = {"group": "group_001", "tasks": ["task_001"],
                 "source_sha256": dispatch.digest(public / "source.py"),
                 "contract_sha256": dispatch.digest(public / "task.json")}
        manifest = {"source_bundle": str(bundle), "reference_directory": str(references), "translation_reuse": [group]}
        dispatch.save(review / "manifest.json", manifest)
        dispatch.save(review / "analyses/without_repair_history/manifest.json", manifest)
        for seed in (101, 202, 303):
            dispatch.save(references / "group_001/torch" / str(seed) / "measurement.json", {"status": "completed", "seed": seed})
        return review, generations

    def test_materialization_preserves_active_files_and_rejects_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            review, generations = self.fixture(Path(temporary))
            dispatch.materialize_group(review, generations, "group_001")
            files = [p for p in review.rglob("*") if p.is_file()]
            before = {p: (p.stat().st_mtime_ns, p.read_bytes()) for p in files}
            dispatch.materialize_group(review, generations, "group_001")
            self.assertEqual(before, {p: (p.stat().st_mtime_ns, p.read_bytes()) for p in files})
            path = review / "private_inputs/task_001/candidate.py"
            path.write_text("tampered\n")
            with self.assertRaisesRegex(RuntimeError, "Existing input differs"):
                dispatch.materialize_group(review, generations, "group_001")
            self.assertEqual(path.read_text(), "tampered\n")

    def test_failed_initial_is_not_replaced_or_materialized(self):
        with tempfile.TemporaryDirectory() as temporary:
            review, generations = self.fixture(Path(temporary))
            receipt = generations / "group_001/direct/generation.json"
            dispatch.save(receipt, {"status": "generation_failed"})
            dispatch.materialize_group(review, generations, "group_001")
            self.assertFalse((review / "private_inputs").exists())
            self.assertEqual(json.loads(receipt.read_text())["status"], "generation_failed")

    def test_native_truncation_finishes_without_modifying_or_rerunning_result(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            job = {"id": "cross__task_003__test_repair", "review": str(root / "review"),
                   "task": "task_003", "method": "test_repair", "kind": "ordinary"}
            result = {"status": "generation_error", "accepted": False,
                      "generation_failure": {"status": "generation_error", "failure_category": "output_truncated"}}
            path = dispatch.result_path(job)
            dispatch.save(path, result)
            dispatch.save(path.parent / "repair_3/generation.json", result["generation_failure"])
            self.assertEqual(dispatch.result_state(job, result), "needs_inspection")
            dispatch.save(path.parent / "repair_3/response.json", {"choices": [{"finish_reason": "length"}]})
            self.assertEqual(dispatch.result_state(job, result), "finished")
            before = path.read_bytes()
            receipt = {"job": job["id"], "state": "needs_inspection", "accepted": False}
            revised = dispatch.reconcile_terminal_receipt(root / "control", job, receipt)
            self.assertEqual(revised["state"], "finished")
            self.assertFalse(revised["accepted"])
            self.assertEqual(before, path.read_bytes())
            archive = root / "control/reconciled_native_failures" / job["id"] / "original_dispatch_receipt.json"
            self.assertEqual(dispatch.read(archive), receipt)
            result["generation_failure"]["failure_category"] = "request_or_parse_error"
            self.assertEqual(dispatch.result_state(job, result), "needs_inspection")


if __name__ == "__main__":
    unittest.main()
