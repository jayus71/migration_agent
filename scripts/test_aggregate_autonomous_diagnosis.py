"""Behavioral aggregation checks using synthetic provider responses only."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import aggregate_autonomous_diagnosis as aggregation
import score_autonomous_diagnosis as scorer
from test_score_autonomous_diagnosis import extracted, response, scored


class AggregationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.rubric = Path(__file__).resolve().parents[1] / "data/audits/fixed50-private-diagnosis-rubric-20260917.json"
        self.rows = scorer.read(self.rubric)["tasks"]
        self.primary = next(r for r in self.rows if r["scorability"]["primary_mechanism_and_symbol_location_eligible"])
        self.contract = next(r for r in self.rows if r["scorability"]["specification_status"] == "contract_dependent")
        self.pack = self.root / "pack"
        source = self.pack / "blind/inputs/input1/candidate.py"
        source.parent.mkdir(parents=True)
        source.write_text("def forward(x):\n    return x.detach()\n")
        self.case = {"case_id": "case1", "input_bundle": "inputs/input1",
            "public_input_hashes": {"candidate.py": scorer.sha(source)},
            "boundary": {"status": "recorded_production_edit"}, "gaps": [], "evidence": [
                {"id": "e2", "kind": "recorded_reasoning", "value": "Detach removes the gradient edge."},
                {"id": "e3", "kind": "tool_exchange", "value": {"error": "gradient missing"}}]}
        scorer.save(self.pack / "blind/cases/case1.json", self.case)
        scorer.save(self.pack / "private/mapping.json", {"source_run": str(self.root / "formal_v3"),
            "cases": [{"case_id": "case1", "condition": self.primary["anonymous_id"] + "/autonomous_layered"}]})
        self.config = self.root / "config.json"
        scorer.save(self.config, {"model": "deepseek-v4-flash", "thinking_mode": "enabled",
            "reasoning_effort": "high", "per_call_output_tokens": 16384, "max_context_chars": 1000000})
        self.out = self.root / "assessments/formal_v3/case1"

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def transport(request, **kwargs):
        payload = json.loads(request["messages"][1]["content"])
        if "phase1_assessment" not in payload:
            return response(extracted(payload))
        return response(scored(payload["public_evidence"], payload, payload["phase1_assessment"]))

    def run_driver(self, **kwargs):
        options = {"execute": True, "transport": self.transport}
        options.update(kwargs)
        return scorer.run(self.pack, self.rubric, self.config, self.out, **options)

    def aggregate(self, roots=None, packs=None):
        return aggregation.aggregate(roots or [self.out], packs or [self.pack], self.rubric)

    def test_frozen_denominators_missing_coverage_and_channel_separation(self):
        self.run_driver()
        report = self.aggregate()
        self.assertEqual(report["frozen_denominators"], {"all50": 50, "primary38": 38, "contract12": 12})
        group = report["groups"][0]
        self.assertEqual(group["scopes"]["all50"]["operational_status_counts"], {"assessed": 1, "not_invoked": 49})
        primary = group["channels"]["primary_report"]["primary38"]
        auxiliary = group["channels"]["auxiliary_recorded_reasoning"]["primary38"]
        self.assertEqual(primary["axis_state_counts"]["testable_mechanism"]["not_reported"], 1)
        self.assertEqual(auxiliary["axis_state_counts"]["testable_mechanism"]["correct"], 1)
        self.assertIsNone(auxiliary["axis_metrics"]["testable_mechanism"]["correct_fraction_frozen_pool"])
        self.assertEqual(auxiliary["axis_metrics"]["testable_mechanism"]["correct_fraction_among_assessed"], 1)
        self.assertEqual(report["usage"]["totals"]["total_tokens"], 60)
        self.assertEqual(report["usage"]["api_attempts"], 2)

    def test_contract_cases_are_excluded_from_mechanism_denominator(self):
        mapping = scorer.read(self.pack / "private/mapping.json")
        mapping["cases"][0]["condition"] = self.contract["anonymous_id"] + "/autonomous_layered"
        scorer.save(self.pack / "private/mapping.json", mapping)
        self.run_driver()
        group = self.aggregate()["groups"][0]
        contract = group["channels"]["auxiliary_recorded_reasoning"]["contract12"]
        self.assertEqual(contract["axis_state_counts"]["testable_mechanism"]["not_scorable"], 1)
        self.assertEqual(contract["axis_metrics"]["testable_mechanism"]["eligible_conditions"], 0)
        self.assertIsNone(contract["axis_metrics"]["testable_mechanism"]["correct_fraction_frozen_pool"])
        self.assertEqual(group["scopes"]["primary38"]["assessed_conditions"], 0)

    def test_schema_failure_unknown_usage_remains_unassessed(self):
        self.run_driver(transport=lambda *a, **k: response({"invalid": True}, usage=False))
        report = self.aggregate()
        self.assertEqual(report["records"][0]["status"], "phase1_schema_error")
        self.assertIsNone(report["records"][0]["assessment"])
        self.assertEqual(report["usage"]["api_attempts"], 1)
        self.assertEqual(report["usage"]["unknown_usage_calls"], 1)
        self.assertIsNone(report["usage"]["totals"]["total_tokens"])
        self.assertEqual(report["groups"][0]["scopes"]["all50"]["assessed_conditions"], 0)

    def test_missing_total_is_unknown_even_when_prompt_and_completion_known(self):
        usage = aggregation.aggregate_usage([{"status": "schema_error", "usage": {
            "attempted": True, "prompt_tokens": 5, "completion_tokens": 7, "total_tokens": None}}])
        self.assertEqual(usage["measured"]["prompt_tokens"], 5)
        self.assertEqual(usage["totals"]["completion_tokens"], 7)
        self.assertIsNone(usage["totals"]["total_tokens"])
        self.assertFalse(usage["token_totals_complete"])

    def test_tampered_success_is_unassessed_but_usage_counted(self):
        self.run_driver()
        path = self.out / "cases/case1/phase2/assessment.json"
        final = scorer.read(path)
        final["primary_report"]["axis_scores"]["failure_evidence"]["reason"] = "changed"
        scorer.save(path, final)
        report = self.aggregate()
        self.assertEqual(report["records"][0]["status"], "assessment_integrity_error")
        self.assertEqual(report["usage"]["totals"]["total_tokens"], 60)

    def test_second_phase_must_use_frozen_reference(self):
        self.run_driver()
        path = self.out / "cases/case1/phase2/request.json"
        request = scorer.read(path)
        payload = json.loads(request["messages"][1]["content"])
        payload["private_reference"] = {"changed": True}
        request["messages"][1]["content"] = json.dumps(payload)
        scorer.save(path, request)
        self.assertEqual(self.aggregate()["records"][0]["status"], "assessment_integrity_error")

    def test_duplicate_roots_rejected_without_double_counting(self):
        self.run_driver()
        clone = self.root / "duplicate"
        shutil.copytree(self.out, clone)
        with self.assertRaisesRegex(ValueError, "Duplicate condition"):
            self.aggregate([self.out, clone])
        self.assertEqual(self.aggregate([self.out, self.out])["usage"]["api_attempts"], 2)

    def test_changed_scoring_configuration_is_separate_group(self):
        self.run_driver()
        clone = self.root / "other_scoring_version"
        shutil.copytree(self.out, clone)
        manifest = scorer.read(clone / "evaluation_manifest.json")
        manifest["version"] = "different_assessment_version"
        scorer.save(clone / "evaluation_manifest.json", manifest)
        report = self.aggregate([self.out, clone])
        self.assertEqual(len(report["groups"]), 2)
        self.assertEqual(report["usage"]["api_attempts"], 4)

    def test_independent_case_outputs_merge_without_changing_fixed_pool(self):
        mapping = scorer.read(self.pack / "private/mapping.json")
        other_task = next(r for r in self.rows if r["scorability"]["primary_mechanism_and_symbol_location_eligible"]
                          and r["anonymous_id"] != self.primary["anonymous_id"])
        mapping["cases"].append({"case_id": "case2", "condition": other_task["anonymous_id"] + "/autonomous_layered"})
        scorer.save(self.pack / "private/mapping.json", mapping)
        case2 = copy.deepcopy(self.case)
        case2["case_id"] = "case2"
        scorer.save(self.pack / "blind/cases/case2.json", case2)
        self.run_driver(case_ids=["case1"])
        output2 = self.out.parent / "case2"
        scorer.run(self.pack, self.rubric, self.config, output2, execute=True,
                   case_ids=["case2"], transport=self.transport)
        report = self.aggregate([self.out, output2])
        self.assertEqual(len(report["groups"]), 1)
        self.assertEqual(report["groups"][0]["scopes"]["primary38"]["assessment_coverage"],
                         {"numerator": 2, "denominator": 38, "fraction": 2 / 38})
        self.assertEqual(report["usage"]["totals"]["total_tokens"], 120)

    def test_partial_credit_is_not_converted_to_correct(self):
        def partial_transport(request, **kwargs):
            raw = self.transport(request, **kwargs)
            value = json.loads(raw["choices"][0]["message"]["content"])
            if value["phase"] == "reference_assessment":
                value["auxiliary_recorded_reasoning"]["axis_scores"]["testable_mechanism"]["state"] = "partial"
            return response(value)
        self.run_driver(transport=partial_transport)
        stats = self.aggregate()["groups"][0]["channels"]["auxiliary_recorded_reasoning"]["primary38"]
        self.assertEqual(stats["axis_state_counts"]["testable_mechanism"]["partial"], 1)
        self.assertEqual(stats["axis_metrics"]["testable_mechanism"]["correct"], 0)

    def test_v3_canonical_quotes_are_verified_against_rebuilt_spans(self):
        import score_autonomous_diagnosis_spans as span_scorer
        from test_score_autonomous_diagnosis_spans import selected
        def span_transport(request, **kwargs):
            payload = json.loads(request["messages"][1]["content"])
            if "phase1_assessment" not in payload:
                return response(selected(payload))
            return response(scored(payload["public_evidence"], payload, payload["phase1_assessment"]))
        span_scorer.run(self.pack, self.rubric, self.config, self.out, execute=True, transport=span_transport)
        report = self.aggregate()
        self.assertEqual(report["records"][0]["status"], "assessed")
        self.assertEqual(report["usage"]["api_attempts"], 2)

    def test_v3_span_ids_reconstructed_from_export_order_and_tampering_rejected(self):
        import score_autonomous_diagnosis_spans as span_scorer
        from test_score_autonomous_diagnosis_spans import selected
        self.case["evidence"][0]["value"] = {"z_location": "forward", "a_mechanism": "Detached dependency"}
        scorer.save(self.pack / "blind/cases/case1.json", self.case)
        def transport(request, **kwargs):
            payload = json.loads(request["messages"][1]["content"])
            if "phase1_assessment" not in payload:
                return response(selected(payload))
            return response(scored(payload["public_evidence"], payload, payload["phase1_assessment"]))
        span_scorer.run(self.pack, self.rubric, self.config, self.out, execute=True, transport=transport)
        public = json.loads(scorer.read(self.out / "cases/case1/phase1/request.json")["messages"][1]["content"])
        rebuilt_from_sorted_request = span_scorer.add_spans({k: v for k, v in public.items()
            if k not in {"quotable_statement_spans", "citation_span_policy"}})
        self.assertNotEqual(rebuilt_from_sorted_request, public)
        self.assertEqual(self.aggregate()["records"][0]["status"], "assessed")
        self.case["evidence"][0]["value"]["z_location"] = "different symbol"
        scorer.save(self.pack / "blind/cases/case1.json", self.case)
        self.assertEqual(self.aggregate()["records"][0]["status"], "assessment_integrity_error")

    def test_dryrun_and_missing_artifacts_have_no_model_cost(self):
        self.run_driver(execute=False)
        report = self.aggregate()
        self.assertEqual(report["records"][0]["status"], "phase1_dry_run")
        self.assertEqual(report["usage"]["api_attempts"], 0)
        shutil.rmtree(self.out)
        self.case["boundary"]["status"] = "missing"
        scorer.save(self.pack / "blind/cases/case1.json", self.case)
        self.run_driver(execute=False)
        report = self.aggregate()
        self.assertEqual(report["records"][0]["status"], "missing_artifact")
        self.assertEqual(report["usage"]["api_attempts"], 0)

    def test_report_must_not_modify_repair_or_evidence_directories(self):
        self.run_driver()
        report = self.aggregate()
        for destination in (self.pack / "report", self.root / "formal_v3/report"):
            with self.assertRaises(ValueError):
                aggregation.write_report(report, destination, [self.pack])
        output = self.root / "reports/summary"
        aggregation.write_report(report, output, [self.pack])
        self.assertTrue(output.with_suffix(".json").exists())
        self.assertIn("评分成本与修复成本分开", output.with_suffix(".md").read_text())


if __name__ == "__main__":
    unittest.main(verbosity=2)
