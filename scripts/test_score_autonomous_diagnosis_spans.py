"""Offline tests for evaluator v3 exact-span citation transport."""
import copy
import json
from pathlib import Path
import unittest

import score_autonomous_diagnosis as base
import score_autonomous_diagnosis_spans as spans
import test_score_autonomous_diagnosis as fixtures


def selected(public):
    result = {"phase": "public_evidence", "assessment_type": "llm_assisted_exploratory"}
    for channel, prefix in zip(base.CHANNELS, ("p", "a")):
        available = [s for s in public["quotable_statement_spans"] if s["channel"] == channel]
        item = {"claims": [], "reported_mechanisms": [], "ranked_locations": [],
            "uncertainty_observations": [], "evidence_gaps": [], "no_explicit_diagnosis": not available}
        if available:
            item["claims"] = [{"id": prefix + "1", "quote_span_id": available[0]["id"],
                "supporting_evidence_ids": ["e3"], "support": "supported", "reason": "Mock support"}]
            item["reported_mechanisms"] = [{"text": "Detached dependency", "claim_ids": [prefix + "1"]}]
            item["ranked_locations"] = [{"rank": 1, "paths": ["candidate.py"],
                "symbol_or_boundary": "forward", "claim_ids": [prefix + "1"], "reason": "Mock"}]
        result[channel] = item
    return result


class SpanTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.ScoreTests()
        self.f.setUp()
        self.f.case["evidence"][0]["value"] = json.dumps({"summary": 'The "forward" detach\nbreaks gradients.'})
        base.save(self.f.pack / "blind/cases/case1.json", self.f.case)
        self.public = spans.add_spans(base.public_payload(self.f.pack, self.f.case))

    def tearDown(self):
        self.f.tearDown()

    def test_strict_json_leaves_and_exact_contiguous_slices(self):
        leaves = list(spans.string_leaves(self.f.case["evidence"][0]["value"]))
        self.assertEqual(leaves, [('$/@json/summary', 'The "forward" detach\nbreaks gradients.')])
        text = "long line " * 600 + "\nlast line"
        pieces = list(spans.split_spans(text))
        self.assertEqual("".join(x[2] for x in pieces), text)
        self.assertTrue(all(text[a:b] == value and b - a <= 1200 for a, b, value in pieces))
        invalid = '{"broken": "quote}'
        self.assertEqual(list(spans.string_leaves(invalid)), [("$", invalid)])

    def test_original_evidence_preserved_and_all_statement_leaves_included(self):
        original = base.public_payload(self.f.pack, self.f.case)
        for key, value in original.items():
            self.assertEqual(self.public[key], value)
        self.assertEqual({s["parent_evidence_id"] for s in self.public["quotable_statement_spans"]}, {"e1", "e2"})
        self.assertEqual(spans.add_spans(original), self.public)

    def test_resolution_restores_exact_quote_and_parent(self):
        value = selected(self.public)
        spans.validate_and_resolve(value, 1, self.public)
        claim = value["primary_report"]["claims"][0]
        self.assertEqual(claim["quote"], 'The "forward" detach\n')
        self.assertEqual(claim["statement_evidence_id"], "e1")
        self.assertNotIn("quote_span_id", claim)
        spans.validate_canonical(value, 1, self.public)

    def test_unknown_span_cross_channel_and_rewritten_quote_rejected(self):
        for mutation in ("unknown", "cross", "rewritten"):
            value = selected(self.public)
            claim = value["primary_report"]["claims"][0]
            if mutation == "unknown":
                claim["quote_span_id"] = "invented"
            elif mutation == "cross":
                claim["quote_span_id"] = next(s["id"] for s in self.public["quotable_statement_spans"] if s["channel"].startswith("auxiliary"))
            else:
                claim["quote"] = "Paraphrase"
            with self.assertRaises(ValueError):
                spans.validate_and_resolve(value, 1, self.public)

    def test_missing_boolean_and_paraphrased_canonical_quote_rejected(self):
        value = selected(self.public)
        del value["primary_report"]["no_explicit_diagnosis"]
        with self.assertRaises(ValueError):
            spans.validate_and_resolve(value, 1, self.public)
        value = selected(self.public)
        spans.validate_and_resolve(value, 1, self.public)
        value["primary_report"]["claims"][0]["quote"] = "A detach breaks gradient flow."
        with self.assertRaises(ValueError):
            spans.validate_canonical(value, 1, self.public)

    def test_driver_preserves_raw_response_canonicalizes_assessment_and_resumes(self):
        f, calls = self.f, []
        originals = {n: getattr(base, n) for n in ("PHASE1", "PHASE2", "VERSION", "validate", "strings", "public_payload", "config_from_manifest")}
        config_bytes = f.config_path.read_bytes()
        def transport(request, *, timeout):
            self.assertEqual(timeout, 600)
            self.assertEqual(request["max_tokens"], 32768)
            self.assertEqual(request["thinking"], {"type": "enabled"})
            calls.append(request)
            public = json.loads(request["messages"][1]["content"])
            if "phase1_assessment" not in public:
                self.assertNotIn("GOLD_PHASE2_ONLY", json.dumps(public))
                return fixtures.response(selected(public))
            self.assertEqual(request["messages"][0]["content"], originals["PHASE2"])
            return fixtures.response(fixtures.scored(public["public_evidence"], public, public["phase1_assessment"]))
        result = spans.run(f.pack, f.rubric, f.config_path, f.out, execute=True, transport=transport)
        self.assertEqual(result["phase_status_counts"], {"success": 2})
        spans.run(f.pack, f.rubric, f.config_path, f.out, execute=True, transport=transport)
        self.assertEqual(len(calls), 2)
        raw = base.read(f.out / "cases/case1/phase1/response.json")
        self.assertIn("quote_span_id", raw["choices"][0]["message"]["content"])
        canonical = base.read(f.out / "cases/case1/phase1/assessment.json")
        self.assertIn("quote", canonical["primary_report"]["claims"][0])
        self.assertEqual(f.config_path.read_bytes(), config_bytes)
        for name, original in originals.items():
            self.assertEqual(getattr(base, name), original)

    def test_contract_rules_and_missing_primary_report_stay_separate(self):
        public = copy.deepcopy(self.public)
        public["statement_ids"]["primary_report"] = []
        public["quotable_statement_spans"] = [s for s in public["quotable_statement_spans"] if s["channel"] != "primary_report"]
        first = selected(public)
        spans.validate_and_resolve(first, 1, public)
        ref = copy.deepcopy(self.f.reference)
        ref["scorability"].update(specification_status="contract_dependent", primary_mechanism_and_symbol_location_eligible=False)
        final = fixtures.scored(public, ref, first)
        spans.validate_and_resolve(final, 2, public, ref, first)
        self.assertEqual(final["primary_report"]["axis_scores"]["testable_mechanism"]["state"], "not_scorable")
        final["auxiliary_recorded_reasoning"]["axis_scores"]["testable_mechanism"]["state"] = "correct"
        with self.assertRaises(ValueError):
            spans.validate_and_resolve(final, 2, public, ref, first)


if __name__ == "__main__":
    unittest.main(verbosity=2)
