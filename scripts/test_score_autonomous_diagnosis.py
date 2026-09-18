"""Offline behavioral tests. No real provider request is made."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import score_autonomous_diagnosis as scorer


def extracted(public):
    value = {"phase": "public_evidence", "assessment_type": "llm_assisted_exploratory"}
    records = {r["id"]: r for r in public["pre_edit_evidence"]}
    for channel, prefix in zip(scorer.CHANNELS, ("p", "a")):
        ids = public["statement_ids"][channel]
        item = {"claims": [], "reported_mechanisms": [], "ranked_locations": [],
                "uncertainty_observations": [], "evidence_gaps": [], "no_explicit_diagnosis": not ids}
        if ids:
            claim_id = prefix + "1"
            item["claims"] = [{"id": claim_id, "quote": records[ids[0]]["value"],
                "statement_evidence_id": ids[0], "supporting_evidence_ids": ["e3"],
                "support": "supported", "reason": "Mock evidence explanation"}]
            item["reported_mechanisms"] = [{"text": "Detached dependency", "claim_ids": [claim_id]}]
            item["ranked_locations"] = [{"rank": 1, "paths": ["candidate.py"],
                "symbol_or_boundary": "forward", "claim_ids": [claim_id], "reason": "Mock location"}]
        value[channel] = item
    return value


def scored(public, reference, first):
    sc = reference["scorability"]
    value = {"phase": "reference_assessment", "assessment_type": "llm_assisted_exploratory",
             "specification_status": sc["specification_status"],
             "primary_mechanism_location_eligible": sc["primary_mechanism_and_symbol_location_eligible"],
             "category_missing_penalized": False, "needs_human_review": True}
    for channel in scorer.CHANNELS:
        item = copy.deepcopy(scorer.SCORE_TEMPLATE)
        claims = [c["id"] for c in first[channel]["claims"]]
        for axis, score in item["axis_scores"].items():
            state = "correct" if claims else "not_reported"
            if axis in scorer.MECHANISM_AXES and sc["specification_status"] == "contract_dependent":
                state = "not_scorable"
            score.update(state=state, evidence_ids=["e3"], claim_ids=claims, reason="Mock judgment")
        value[channel] = item
    return value


def response(value, usage=True):
    result = {"model": "deepseek-flash", "choices": [{"message": {"content": json.dumps(value)}, "finish_reason": "stop"}]}
    if usage:
        result["usage"] = {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
    return result


class ScoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.pack = self.root / "pack"
        source = self.pack / "blind/inputs/input1/candidate.py"
        source.parent.mkdir(parents=True)
        source.write_text("def forward(x):\n    return x.detach()\n")
        self.case = {"case_id": "case1", "input_bundle": "inputs/input1",
                     "public_input_hashes": {"candidate.py": scorer.sha(source)},
                     "boundary": {"status": "recorded_production_edit"}, "gaps": [],
                     "final": "FINAL_OUTCOME_MUST_NOT_BE_SENT", "evidence": [
            {"id": "e1", "kind": "assistant_statement", "value": "Detach in forward removes the gradient edge."},
            {"id": "e2", "kind": "recorded_reasoning", "value": "The forward detach breaks upstream gradients."},
            {"id": "e3", "kind": "tool_exchange", "value": {"error": "gradient missing"}}]}
        scorer.save(self.pack / "blind/cases/case1.json", self.case)
        scorer.save(self.pack / "private/mapping.json", {"source_run": str(self.root / "repair_run"),
            "cases": [{"case_id": "case1", "condition": "task_001/autonomous_layered"}]})
        self.reference = {"private_reference": {"mechanism": "GOLD_PHASE2_ONLY", "locations": []},
                          "scorability": {"specification_status": "publicly_investigable",
                              "primary_mechanism_and_symbol_location_eligible": True}}
        self.rubric = self.root / "rubric.json"
        scorer.save(self.rubric, {"tasks": [{"anonymous_id": "task_001", **self.reference}],
                                 "scoring_rules": {"category_missing_is_error": False}})
        self.config_path = self.root / "config.json"
        scorer.save(self.config_path, {"model": "deepseek-v4-flash", "thinking_mode": "enabled",
            "reasoning_effort": "high", "per_call_output_tokens": 16384, "max_context_chars": 1000000})
        self.config = scorer.config_from_manifest(self.config_path)
        self.out = self.root / "assessment"
        self.patch = patch.object(scorer, "RUBRIC_SHA256", scorer.sha(self.rubric))
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def run_driver(self, **kwargs):
        return scorer.run(self.pack, self.rubric, self.config_path, self.out, **kwargs)

    def test_dry_run_has_two_phase_separation_and_zero_network(self):
        def forbidden(*args, **kwargs):
            self.fail("Dry-run called a provider")
        report = self.run_driver(transport=forbidden)
        self.assertEqual(report["api_attempts"], 0)
        first = (self.out / "cases/case1/phase1/request.json").read_text()
        second = (self.out / "cases/case1/phase2/request.template.json").read_text()
        self.assertNotIn("GOLD_PHASE2_ONLY", first)
        self.assertIn("GOLD_PHASE2_ONLY", second)
        for text in (first, second):
            self.assertNotIn("autonomous_layered", text)
            self.assertNotIn("FINAL_OUTCOME_MUST_NOT_BE_SENT", text)
        self.assertIn("recorded_reasoning", first)

    def test_channels_cannot_backfill_each_other(self):
        public = scorer.public_payload(self.pack, self.case)
        first = extracted(public)
        first["primary_report"]["claims"][0]["statement_evidence_id"] = "e2"
        with self.assertRaises(ValueError):
            scorer.validate(first, 1, public)

    def test_no_json_requirement_and_not_reported_is_not_incorrect(self):
        case = copy.deepcopy(self.case)
        case["evidence"] = case["evidence"][1:]
        public = scorer.public_payload(self.pack, case)
        first = extracted(public)
        scorer.validate(first, 1, public)
        final = scored(public, self.reference, first)
        scorer.validate(final, 2, public, self.reference, first)
        self.assertEqual(final["primary_report"]["axis_scores"]["testable_mechanism"]["state"], "not_reported")
        self.assertEqual(final["auxiliary_recorded_reasoning"]["axis_scores"]["testable_mechanism"]["state"], "correct")
        final["primary_report"]["axis_scores"]["testable_mechanism"]["state"] = "incorrect"
        with self.assertRaises(ValueError):
            scorer.validate(final, 2, public, self.reference, first)

    def test_contract_dependent_stays_separate(self):
        public = scorer.public_payload(self.pack, self.case)
        first = extracted(public)
        ref = copy.deepcopy(self.reference)
        ref["scorability"].update(specification_status="contract_dependent", primary_mechanism_and_symbol_location_eligible=False)
        final = scored(public, ref, first)
        scorer.validate(final, 2, public, ref, first)
        final["auxiliary_recorded_reasoning"]["axis_scores"]["causal_symbol_top1"]["state"] = "correct"
        with self.assertRaises(ValueError):
            scorer.validate(final, 2, public, ref, first)

    def test_unreported_location_cannot_be_filled_from_mechanism(self):
        public = scorer.public_payload(self.pack, self.case)
        first = extracted(public)
        first["primary_report"]["ranked_locations"] = []
        final = scored(public, self.reference, first)
        with self.assertRaises(ValueError):
            scorer.validate(final, 2, public, self.reference, first)
        for axis in ("causal_symbol_top1", "causal_symbol_top3"):
            final["primary_report"]["axis_scores"][axis].update(state="not_reported", claim_ids=[])
        scorer.validate(final, 2, public, self.reference, first)
        first["primary_report"]["reported_mechanisms"] = []
        with self.assertRaises(ValueError):
            scorer.validate(final, 2, public, self.reference, first)
        final["primary_report"]["axis_scores"]["testable_mechanism"].update(state="not_reported", claim_ids=[])
        scorer.validate(final, 2, public, self.reference, first)

    def test_schema_failure_and_unknown_usage_are_preserved_without_retry(self):
        calls = []
        def invalid(request, **kwargs):
            calls.append(request)
            return response({"wrong_schema": True}, usage=False)
        result = self.run_driver(execute=True, transport=invalid)
        self.run_driver(execute=True, transport=invalid)
        self.assertEqual(len(calls), 1)
        self.assertEqual(result["unknown_usage_calls"], 1)
        self.assertFalse(result["token_totals_complete"])
        self.assertTrue((self.out / "cases/case1/phase1/response.json").exists())
        self.assertFalse((self.out / "cases/case1/phase2/request.json").exists())

    def test_resume_and_incremental_bundle_reuse(self):
        calls = []
        def valid(request, **kwargs):
            calls.append(request)
            payload = json.loads(request["messages"][1]["content"])
            if "phase1_assessment" not in payload:
                return response(extracted(payload))
            return response(scored(payload["public_evidence"], payload, payload["phase1_assessment"]))
        result = self.run_driver(execute=True, transport=valid)
        self.assertEqual(result["api_attempts"], 2)
        other = self.root / "new_export"
        shutil.copytree(self.pack, other)
        scorer.run(other, self.rubric, self.config_path, self.out, execute=True, transport=valid)
        self.assertEqual(len(calls), 2)
        case = scorer.read(other / "blind/cases/case1.json")
        case["evidence"][0]["value"] = "Changed diagnosis"
        scorer.save(other / "blind/cases/case1.json", case)
        with self.assertRaises(ValueError):
            scorer.run(other, self.rubric, self.config_path, self.out, execute=True, transport=valid)
        self.assertEqual(len(calls), 2)

    def test_inflight_call_is_not_reissued(self):
        self.run_driver()
        state_path = self.out / "cases/case1/phase1/state.json"
        scorer.save(state_path, {"status": "started", "usage": scorer.usage_of(None, attempted=True)})
        def forbidden(*args, **kwargs):
            self.fail("Uncertain prior request was retried")
        result = self.run_driver(execute=True, transport=forbidden)
        self.assertIn("outcome_unknown_no_automatic_retry", result["phase_status_counts"])

    def test_truncated_provider_response_does_not_become_success(self):
        def truncated(request, **kwargs):
            raw = response({})
            raw["choices"][0]["finish_reason"] = "length"
            return raw
        result = self.run_driver(execute=True, transport=truncated)
        self.assertEqual(result["phase_status_counts"], {"provider_truncated": 1})


if __name__ == "__main__":
    unittest.main(verbosity=2)
