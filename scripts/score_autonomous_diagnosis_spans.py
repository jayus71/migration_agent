#!/usr/bin/env python3
"""Evaluator v3: deterministic citation spans, unchanged diagnosis scoring rules."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import score_autonomous_diagnosis as base

BASE_SHA256 = "d8acb0b0b7c8a037d762bc63cf978f4231c0dfc04e11bf1cd5e4bece14817f26"
VERSION = "autonomous-diagnosis-llm-assessment-v3-citation-spans"
ORIGINAL_VALIDATE = base.validate
ORIGINAL_STRINGS = base.strings
ORIGINAL_PUBLIC = base.public_payload
SPAN_CHARS = 1200


def string_leaves(value, path="$", depth=0):
    """Decode only valid JSON containers; never unescape or fuzzy-match prose."""
    if depth > 20:
        raise ValueError("Statement JSON nesting exceeds deterministic citation limit")
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except (ValueError, TypeError):
            decoded = None
        if isinstance(decoded, (dict, list)):
            yield from string_leaves(decoded, path + "/@json", depth + 1)
        else:
            yield path, value
    elif isinstance(value, dict):
        for key, item in value.items():
            escaped = str(key).replace("~", "~0").replace("/", "~1")
            yield from string_leaves(item, path + "/" + escaped, depth + 1)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from string_leaves(item, path + "/" + str(index), depth + 1)


def strict_strings(value):
    yield from ORIGINAL_STRINGS(value)
    for _, text in string_leaves(value):
        yield text


def split_spans(text):
    """Contiguous exact slices; line boundaries first, bounded long-line slices."""
    offset = 0
    for line in text.splitlines(keepends=True):
        start = 0
        while start < len(line):
            end = min(start + SPAN_CHARS, len(line))
            if end < len(line):
                whitespace = line.rfind(" ", start + SPAN_CHARS // 2, end)
                if whitespace >= 0:
                    end = whitespace + 1
            yield offset + start, offset + end, line[start:end]
            start = end
        offset += len(line)


def add_spans(public):
    result = copy.deepcopy(public)
    spans = []
    statements = {eid: channel for channel, ids in public["statement_ids"].items() for eid in ids}
    for record in public["pre_edit_evidence"]:
        if record["id"] not in statements:
            continue
        index = 0
        for path, leaf in string_leaves(record["value"]):
            for start, end, text in split_spans(leaf):
                if not text.strip():
                    continue
                index += 1
                spans.append({"id": f"{record['id']}.s{index:04d}", "parent_evidence_id": record["id"],
                    "channel": statements[record["id"]], "string_path": path,
                    "start": start, "end": end, "text": text})
    result["quotable_statement_spans"] = spans
    result["citation_span_policy"] = {
        "version": "exact-json-leaves-and-line-slices-v1", "max_span_characters": SPAN_CHARS,
        "selection": "All statement string leaves in both channels, original order; no method or reference filtering.",
        "original_evidence_preserved": True, "json_decoding": "Strict json.loads on complete JSON objects/arrays only.",
        "citation": "Select quote_span_id; the evaluator restores exact original text and parent evidence ID.",
    }
    return result


SPAN_CLAIM_TEMPLATE = copy.deepcopy(base.CLAIM_TEMPLATE)
claim = SPAN_CLAIM_TEMPLATE["claims"][0]
del claim["quote"]
del claim["statement_evidence_id"]
claim["quote_span_id"] = "e00001.s0001"
PHASE1 = base.PHASE1.split("Channel schema:\n")[0] + """
Citation transport for this evaluator version: use quotable_statement_spans.
For each claim, choose exactly one quote_span_id belonging to that claim's
channel. Do not copy, reconstruct, or paraphrase the quote. The evaluator will
restore the span's exact text and parent statement_evidence_id. A long statement
may have several spans; choose the span containing the claim, and use separate
claims if several spans are needed. The original evidence is fully preserved.
Span text is an exact slice of an original string leaf; complete JSON objects or
arrays stored as text are decoded strictly before slicing their string leaves.
Supporting evidence IDs still use parent evidence IDs, never span IDs.
This changes citation transport only: extract actual diagnostic claims, assess
their support, and identify mechanisms/locations yourself. A supplied span is
not a diagnosis, a correct answer, or evidence of causal support by itself.
Return every channel field, including the boolean no_explicit_diagnosis.
Channel schema:
""" + json.dumps(SPAN_CLAIM_TEMPLATE)


def validate_canonical(value, phase, public, reference=None, first=None):
    """Recheck saved canonical scores without weakening strict text matching."""
    original = base.strings
    try:
        base.strings = strict_strings
        ORIGINAL_VALIDATE(value, phase, public, reference, first)
    finally:
        base.strings = original
    if phase == 1:
        available = {(s["channel"], s["parent_evidence_id"], s["text"])
                     for s in public["quotable_statement_spans"]}
        for channel in base.CHANNELS:
            for claim in value[channel]["claims"]:
                if (channel, claim["statement_evidence_id"], claim["quote"]) not in available:
                    raise ValueError("Canonical quote is absent from deterministic citation spans")


def validate_and_resolve(value, phase, public, reference=None, first=None):
    if phase == 1:
        spans = {s["id"]: s for s in public["quotable_statement_spans"]}
        normalized = copy.deepcopy(value)
        for channel in base.CHANNELS:
            claims = normalized[channel]["claims"]
            if not isinstance(claims, list):
                raise ValueError("Expected claims list")
            for claim in claims:
                if set(claim) != set(SPAN_CLAIM_TEMPLATE["claims"][0]):
                    raise ValueError("Invalid span claim schema")
                sid = claim["quote_span_id"]
                if not isinstance(sid, str) or sid not in spans or spans[sid]["channel"] != channel:
                    raise ValueError("Unknown or cross-channel quote_span_id")
                span = spans[sid]
                del claim["quote_span_id"]
                claim["quote"] = span["text"]
                claim["statement_evidence_id"] = span["parent_evidence_id"]
        validate_canonical(normalized, phase, public, reference, first)
        value.clear()
        value.update(normalized)
    else:
        validate_canonical(value, phase, public, reference, first)


def run(pack, rubric, config, output, *, execute=False, case_ids=None, transport=None):
    if base.sha(Path(base.__file__)) != BASE_SHA256:
        raise ValueError("Frozen evaluator driver changed")
    pack, output = Path(pack).resolve(), Path(output).resolve()
    source = Path(base.read(pack / "private/mapping.json")["source_run"]).resolve()
    if output == pack or pack in output.parents or output == source or source in output.parents:
        raise ValueError("Evaluator output must remain outside repair/evidence inputs")
    originals = {name: getattr(base, name) for name in ("config_from_manifest", "VERSION", "PHASE1", "public_payload", "validate")}
    provenance = {"version": VERSION, "base_driver_sha256": BASE_SHA256,
        "wrapper_sha256": base.sha(Path(__file__)), "source_repair_config_sha256": base.sha(Path(config)),
        "original_model_configuration": originals["config_from_manifest"](Path(config)),
        "evaluator_overrides": {"max_tokens": 32768, "transport_timeout_seconds": 600},
        "repair_configuration_changed": False, "scoring_rules_changed": False,
        "citation_transport_changed": True, "automatic_retries": 0,
        "citation_policy": "exact-json-leaves-and-line-slices-v1"}
    base.preserve(output / "wrapper_manifest.json", provenance)
    try:
        base.config_from_manifest = lambda path: {**originals["config_from_manifest"](path), "max_tokens": 32768}
        base.VERSION = VERSION + ":" + provenance["wrapper_sha256"]
        base.PHASE1 = PHASE1
        base.public_payload = lambda p, case: add_spans(ORIGINAL_PUBLIC(p, case))
        base.validate = validate_and_resolve
        def expanded_transport(request, *, timeout):
            return (transport or base.send_once)(request, timeout=600)
        return base.run(pack, Path(rubric), Path(config), output, execute=execute,
                        case_ids=case_ids, transport=expanded_transport)
    finally:
        for name, original in originals.items():
            setattr(base, name, original)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("evidence-export", "rubric", "run-config", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--case-id", action="append")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.execute and not base.os.getenv("AUTOFIX_LLM_API_KEY", "").strip():
        parser.error("--execute requires AUTOFIX_LLM_API_KEY")
    print(json.dumps(run(args.evidence_export, args.rubric, args.run_config, args.output,
        execute=args.execute, case_ids=args.case_id), indent=2))


if __name__ == "__main__":
    main()
