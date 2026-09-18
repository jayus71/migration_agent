#!/usr/bin/env python3
"""Export read-only, pre-production-edit evidence; never score or call a model.

Only blind/ is for reviewers. private/ maps opaque IDs to original conditions
and immutable evidence hashes. No rubric, private probe, healthy implementation,
final patch, or final acceptance decision is loaded into a review packet.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import hmac
import json
from pathlib import Path
import re
import secrets
import shutil
import sys
import tempfile
import unittest


VERSION = "autonomous-pre-edit-export-v1"
PROTOCOL_SHA256 = "5f8624058e18a09da987c0e9758bdb397260aeab6623357a21520026bc98499c"
METHODS = (
    "autonomous_layered", "autonomous_layered_native", "autonomous_category_ablation",
    "direct_shared_tools", "swe_native_isolated", "swe_style_shared_tools",
    "matchfix_shared_tools", "matchfix_full_orchestration",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def production(path: str) -> bool:
    return path == "candidate.py" or (path.startswith("torch4ms/") and path.endswith(".py"))


def hashes(root: Path) -> dict[str, str] | None:
    if not root.is_dir():
        return None
    return {p.relative_to(root).as_posix(): digest(p) for p in sorted(root.rglob("*.py"))
            if p.is_file() and not p.is_symlink() and production(p.relative_to(root).as_posix())}


def content_text(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(x.get("text", "") for x in value if isinstance(x, dict))
    return "" if value is None else json.dumps(value, ensure_ascii=False)


def provider_message(response: dict) -> tuple[dict, str | None]:
    choices = response.get("choices") or []
    if not choices or not isinstance(choices[0], dict):
        return {}, None
    return choices[0].get("message") or {}, choices[0].get("finish_reason")


def changed_files(result: dict) -> list[dict]:
    return [x for x in (result.get("files") or []) if isinstance(x, dict)
            and production(x.get("path", "")) and "before_sha256" in x
            and "after_sha256" in x and x["before_sha256"] != x["after_sha256"]]


def source_limits(value, pointer="") -> list[dict]:
    """Describe upstream pagination/truncation without pretending to recover it."""
    limits = []
    if isinstance(value, dict):
        for name in ("next_line", "next_offset"):
            if value.get(name) is not None:
                limits.append({"pointer": pointer + "/" + name, "kind": "pagination",
                               "next": value[name], "total": value.get("total_lines", value.get("total"))})
        if isinstance(value.get("lines"), list) and value["lines"]:
            lines = [x.get("line") for x in value["lines"] if isinstance(x, dict)]
            limits.append({"pointer": pointer + "/lines", "kind": "line_window",
                           "first": lines[0] if lines else None, "last": lines[-1] if lines else None,
                           "total": value.get("total_lines")})
        for key, item in value.items():
            if key == "stdout" and isinstance(item, str) and len(item) == 16000:
                limits.append({"pointer": pointer + "/stdout", "kind": "at_known_16000_character_cap",
                               "omitted_length": "unknown"})
            limits.extend(source_limits(item, pointer + "/" + str(key)))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            limits.extend(source_limits(item, pointer + "/" + str(index)))
    elif isinstance(value, str) and re.search(r"\[.{0,60}(?:truncated|omitted).{0,60}\]|output.{0,30}truncated", value, re.I):
        limits.append({"pointer": pointer, "kind": "text_truncation_marker", "omitted_length": "unknown"})
    return limits


class Packet:
    def __init__(self, run: Path, condition: Path, *, max_chars: int = 0):
        self.run, self.condition, self.max_chars = run, condition, max_chars
        self.agent = condition / "evidence/agent"
        self.records: list[dict] = []
        self.sources: list[dict] = []
        self.gaps: list[str] = []
        self.source_ids: dict[str, str] = {}
        self.boundary: dict = {}
        self.contexts: list[dict] = []
        self.task = condition.parent.name
        self.initial_hashes = hashes(condition / "evidence/initial_code")

    def source(self, path: Path, pointer: str = "") -> dict:
        key = path.relative_to(self.run).as_posix()
        if key not in self.source_ids:
            sid = f"source_{len(self.sources) + 1:05d}"
            self.source_ids[key] = sid
            self.sources.append({"id": sid, "path": key, "sha256": digest(path), "bytes": path.stat().st_size})
        return {"source": self.source_ids[key], "json_pointer": pointer}

    def sanitize(self, value):
        if isinstance(value, dict):
            return {str(k): self.sanitize(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self.sanitize(x) for x in value]
        if not isinstance(value, str):
            return value
        value = value.replace(str(self.condition / "workspace"), "<workspace>")
        # Export also works from a copied archive whose path differs from the host.
        value = re.sub(r"/(?:[^\s\"'<>/]+/)*conditions/task_\d+/[A-Za-z0-9_]+/workspace", "<workspace>", value)
        value = re.sub(r"/(?:[^\s\"'<>/]+/)*conditions/task_\d+/[A-Za-z0-9_]+", "<condition>", value)
        value = value.replace(str(self.run), "<run>")
        for name in sorted(METHODS, key=len, reverse=True):
            value = value.replace(name, "<method>")
        value = re.sub(r"\btask_\d+\b", "<task>", value)
        value = re.sub(r"SWE[- ]agent|MatchFixAgent|Direct LLM|LaDiM", "<method>", value, flags=re.I)
        return value

    def clip(self, value, pointer="") -> tuple[object, list[dict]]:
        if isinstance(value, str) and self.max_chars and len(value) > self.max_chars:
            return value[:self.max_chars] + "\n[EXPORT TRUNCATED]", [{
                "pointer": pointer, "original_characters": len(value),
                "retained_range": [0, self.max_chars], "range_convention": "half-open Unicode characters",
                "untruncated_sanitized_sha256": hashlib.sha256(value.encode()).hexdigest()}]
        notes = []
        if isinstance(value, (dict, list)):
            output = {} if isinstance(value, dict) else []
            items = value.items() if isinstance(value, dict) else enumerate(value)
            for key, item in items:
                clipped, more = self.clip(item, pointer + "/" + str(key))
                if isinstance(output, dict):
                    output[key] = clipped
                else:
                    output.append(clipped)
                notes.extend(more)
            return output, notes
        return value, notes

    def add(self, kind: str, value, path: Path, pointer="", **metadata) -> None:
        if value is None or value == "":
            return
        cleaned, truncation = self.clip(self.sanitize(value))
        self.records.append({"id": f"e{len(self.records) + 1:05d}", "kind": kind,
                             "value": cleaned, "origin": self.source(path, pointer),
                             "source_limits": source_limits(value), "export_truncation": truncation,
                             **metadata})

    def assistant(self, response: dict, path: Path, pointer="", *, triggering=False) -> None:
        message, finish = provider_message(response)
        # Tool-call arguments, proposed diffs, and the triggering step observation
        # are not diagnostic prose and are deliberately not copied here.
        for field, kind in (("content", "assistant_statement"), ("reasoning_content", "recorded_reasoning")):
            self.add(kind, content_text(message.get(field)), path,
                     pointer + "/choices/0/message/" + field,
                     finish_reason=finish, provider_truncated=finish == "length",
                     triggering_response=triggering,
                     scoring_use="Explicit claims only; do not infer diagnosis from proposed code.")
        if not message:
            self.gaps.append("provider_response_has_no_message")

    def context(self, call: int) -> None:
        path = self.agent / f"call_{call:04d}_metadata.json"
        if path.exists():
            data = read_json(path)
            self.contexts.append({"origin": self.source(path), **{k: data.get(k) for k in (
                "original_chars", "prepared_chars", "compression_applied", "request_sha256")}})

    def shared(self, result: dict) -> None:
        events = []
        for path in sorted(self.agent.glob("event_*.json")):
            if not re.search(r"_(tool|api_start|stage_start|stage_end|output_truncated|observation)\.json$", path.name):
                continue
            events.append((path, read_json(path)))
        if not events:
            self.boundary = {"status": "missing_artifact"}
            self.gaps.append("event_timeline_missing")
            return
        stop = None
        uncertain = None
        for i, (path, event) in enumerate(events):
            data = event.get("data", {})
            if event.get("kind") == "tool" and data.get("name") == "edit":
                value = data.get("result", {})
                changed = changed_files(value)
                if value.get("ok") is True and changed:
                    stop = i
                    self.boundary = {"status": "recorded_production_edit", "origin": self.source(path),
                                     "call": data.get("call"), "tool_call_id": data.get("tool_call_id"),
                                     "changed_file_count": len(changed),
                                     "initial_hash_match": bool(self.initial_hashes) and all(
                                         self.initial_hashes.get(x["path"]) == x["before_sha256"] for x in changed),
                                     "granularity": "completed edit-tool transaction; triggering result excluded"}
                    break
                edits = data.get("arguments")
                edits = edits if isinstance(edits, dict) else {}
                requested = any(production(x.get("path", "")) for x in edits.get("edits", []) if isinstance(x, dict))
                if value.get("ok") is True and requested and not value.get("files"):
                    uncertain = i
                    self.gaps.append("successful_production_edit_missing_file_hashes")
                    break
        if uncertain is not None:
            stop = uncertain
            self.boundary = {"status": "missing_artifact", "granularity": "stopped before unverified edit result"}
        if stop is None:
            final = hashes(self.condition / "evidence/final_code")
            unchanged = self.initial_hashes is not None and final == self.initial_hashes
            self.boundary = {"status": "no_recorded_production_edit" if unchanged else "missing_artifact",
                             "snapshot_endpoints_equal": unchanged,
                             "granularity": "completed episode; no recorded edit and equal endpoint snapshots"}
            if not unchanged:
                self.gaps.append("production_change_without_recoverable_edit_event")
                # Keep only the independently checked read-only diagnosis phase.
                stop = next((i for i, (_, e) in enumerate(events) if e.get("kind") == "stage_start"
                             and e.get("data", {}).get("stage") != "diagnose"), 0)
        if self.boundary.get("initial_hash_match") is False:
            self.gaps.append("first_recorded_edit_before_hash_differs_from_initial")
            self.boundary["status"] = "missing_artifact"
            stop = next((i for i, (_, e) in enumerate(events) if e.get("kind") == "stage_start"
                         and e.get("data", {}).get("stage") != "diagnose"), 0)
        after_diagnosis = hashes(self.condition / "evidence/after_diagnosis")
        if after_diagnosis is not None and after_diagnosis != self.initial_hashes:
            self.gaps.append("diagnostic_snapshot_changed_production")
            self.boundary["status"] = "missing_artifact"
            stop = 0
        self.gaps.append("shared_tools_have_no_full_tree_hash_after_every_tool; transient_unlogged_writes_unresolved")
        limit = len(events) if stop is None else stop
        seen_calls = set()
        for path, event in events[:limit]:
            data, kind = event.get("data", {}), event.get("kind")
            if kind == "api_start":
                call = data.get("call")
                if not isinstance(call, int) or call in seen_calls:
                    continue
                seen_calls.add(call)
                response = self.agent / f"call_{call:04d}_response.json"
                if response.exists():
                    self.assistant(read_json(response), response, triggering=call == self.boundary.get("call"))
                else:
                    self.gaps.append(f"missing_provider_response_call_{call}")
                self.context(call)
            elif kind == "tool":
                value = {k: data.get(k) for k in ("name", "arguments", "result")}
                if data.get("name") == "edit":
                    arguments = data.get("arguments")
                    edits = arguments.get("edits", []) if isinstance(arguments, dict) else []
                    if any(production(x.get("path", "")) for x in edits if isinstance(x, dict)):
                        value = {"name": "edit", "production_proposal_withheld": True,
                                 "applied": data.get("result", {}).get("ok") is True,
                                 "error": data.get("result", {}).get("error")}
                self.add("tool_exchange", value, path, "/data")
            elif kind == "stage_end":
                self.add("explicit_report", data.get("final"), path, "/data/final")
            elif kind == "output_truncated":
                self.add("provider_output_limit", {k: data.get(k) for k in (
                    "finish_reason", "tools_executed")}, path, "/data")
            elif kind == "observation":
                self.add("controller_observation", data, path, "/data")

    def native(self, result: dict) -> None:
        paths = sorted(self.agent.glob("swe_event_*_first_edit.json"))
        if paths:
            path = paths[0]
            data = read_json(path)
            pointer = ""
        else:
            data = result.get("initial_diagnosis", {}).get("first_production_edit")
            path = self.condition / "result.json"
            pointer = "/initial_diagnosis/first_production_edit"
        if data:
            before, after = data.get("before_hashes"), data.get("after_hashes")
            if not isinstance(before, dict) or not isinstance(after, dict) or before == after:
                self.gaps.append("native_first_edit_missing_or_equal_hashes")
            self.boundary = {"status": "recorded_production_edit" if before != after and before else "missing_artifact",
                             "origin": self.source(path, pointer),
                             "initial_hash_match": before == self.initial_hashes,
                             "granularity": "one native step; triggering command and its output excluded"}
            if before != self.initial_hashes:
                self.gaps.append("native_before_hashes_differ_from_initial")
                self.boundary["status"] = "missing_artifact"
                return
            history = data.get("history_before", [])
            for index, message in enumerate(history):
                self.native_message(message, path, pointer + f"/history_before/{index}")
            response = data.get("triggering_provider_response")
            if isinstance(response, dict):
                self.assistant(response, path, pointer + "/triggering_provider_response", triggering=True)
            else:
                self.add("assistant_statement", data.get("triggering_step", {}).get("thought"),
                         path, pointer + "/triggering_step/thought", triggering_response=True)
                self.gaps.append("native_triggering_provider_response_missing")
            trigger_id = response.get("id") if isinstance(response, dict) else None
            self.native_auxiliary(history, trigger_id, allow_statement_match=False)
            self.gaps.append("native_step_boundary_excludes_internal_timing_of_multiple_shell_commands")
        else:
            unchanged = self.initial_hashes is not None and hashes(self.condition / "evidence/final_code") == self.initial_hashes
            self.boundary = {"status": "no_recorded_production_edit" if unchanged else "missing_artifact",
                             "snapshot_endpoints_equal": unchanged,
                             "granularity": "submitted native history; no recorded edit and equal endpoint snapshots"}
            if not unchanged:
                self.gaps.append("native_production_change_without_first_edit_artifact")
                return
            checkpoints = sorted(self.agent.glob("swe_event_*_checkpoint.json"))
            if checkpoints:
                path = checkpoints[-1]
                history = read_json(path).get("history", [])
                for index, message in enumerate(history):
                    self.native_message(message, path, f"/history/{index}")
                self.native_auxiliary(history)
            else:
                self.gaps.append("native_no_edit_episode_has_no_checkpoint_history")

    def native_auxiliary(self, history: list[dict], trigger_id: str | None = None,
                         *, allow_statement_match: bool = True) -> None:
        # Native history need not retain reasoning_content. Match actual provider
        # replies to frozen history by tool IDs or an exact nonempty statement.
        allowed_ids = {tc.get("id"): i for i, m in enumerate(history) for tc in (m.get("tool_calls") or [])}
        statements = {content_text(m.get("content")): i for i, m in enumerate(history)
                      if m.get("role") == "assistant" and content_text(m.get("content"))}
        unmatched = 0
        for path in sorted(self.agent.glob("call_*_response.json")):
            raw = read_json(path)
            if trigger_id is not None and raw.get("id") == trigger_id:
                self.context(int(path.name.split("_")[1]))
                break
            message, finish = provider_message(raw)
            ids = {x.get("id") for x in (message.get("tool_calls") or [])}
            indices = sorted({allowed_ids[x] for x in ids}) if ids and ids <= allowed_ids.keys() else []
            text = content_text(message.get("content"))
            if allow_statement_match and not ids and text and text in statements:
                indices = [statements[text]]
            if indices:
                self.add("recorded_reasoning_auxiliary", message.get("reasoning_content"), path,
                         "/choices/0/message/reasoning_content", finish_reason=finish,
                         provider_truncated=finish == "length", native_history_indices=indices,
                         scoring_use="Matched to frozen native history; auxiliary records are not appended chronology.")
                self.context(int(path.name.split("_")[1]))
            elif message.get("reasoning_content"):
                unmatched += 1
        if unmatched:
            self.gaps.append(f"native_reasoning_responses_without_frozen_history_match_not_exported:{unmatched}")

    def native_message(self, message: dict, path: Path, pointer: str) -> None:
        role = message.get("role")
        if role == "assistant":
            self.add("assistant_statement", content_text(message.get("content")), path, pointer + "/content")
            for index, call in enumerate(message.get("tool_calls") or []):
                self.add("tool_request", call.get("function"), path, pointer + f"/tool_calls/{index}/function")
        elif role == "tool":
            self.add("tool_result", content_text(message.get("content")), path, pointer + "/content")
        elif role == "user" and message.get("message_type") == "external_verifier_feedback":
            self.add("controller_observation", content_text(message.get("content")), path, pointer + "/content")
        # System prompts and method-specific workflow instructions are withheld.

    def build(self, result: dict) -> dict:
        initial = result.get("initial", {}).get("observation")
        self.add("initial_observation", initial, self.condition / "result.json", "/initial/observation")
        if self.condition.name == "swe_native_isolated":
            self.native(result)
        elif self.condition.name.startswith("matchfix"):
            self.boundary = {"status": "unsupported_export_format"}
            self.gaps.append("MatchFix trajectory export is outside this Fixed50 exporter")
        else:
            self.shared(result)
        return {"schema": VERSION, "boundary": self.boundary, "evidence": self.records,
                "context_windows": self.contexts, "gaps": sorted(set(self.gaps)),
                "export_character_limit_per_string": self.max_chars or None,
                "diagnosis_assessment": "unscored; read explicit pre-edit claims, never infer from patch actions",
                "category_required": False,
                "blinding_limit": "Explicit method names, paths and system prompts are removed. Interaction style and tool names may still suggest a framework."}


def export(run: Path, output: Path, *, conditions: list[str] | None = None, max_chars: int = 0,
           key: str | None = None) -> dict:
    run, output = run.resolve(), output.resolve()
    if not (run / "conditions").is_dir():
        raise ValueError("Source run has no conditions directory")
    if output.exists() or output == run or run in output.parents or output in run.parents:
        raise ValueError("Use a fresh output directory outside the source run")
    if max_chars < 0:
        raise ValueError("max_chars must be nonnegative")
    secret = bytes.fromhex(key) if key else secrets.token_bytes(32)
    if len(secret) < 16:
        raise ValueError("The private blinding key must contain at least sixteen bytes")
    opaque = lambda kind, name: hmac.new(secret, (kind + ":" + name).encode(), hashlib.sha256).hexdigest()[:20]
    selected = sorted(run.glob("conditions/*/*"))
    if conditions:
        requested = set(conditions)
        selected = [p for p in selected if p.relative_to(run / "conditions").as_posix() in requested]
        found = {p.relative_to(run / "conditions").as_posix() for p in selected}
        if found != requested:
            raise ValueError("Unknown condition selectors: " + ", ".join(sorted(requested - found)))
    output.mkdir(parents=True)
    mapping, skipped, cases, input_bundles = [], [], [], {}
    for condition in selected:
        if not condition.is_dir() or condition.is_symlink():
            continue
        relative = condition.relative_to(run / "conditions").as_posix()
        result_path = condition / "result.json"
        if not result_path.exists():
            skipped.append({"condition": relative, "reason": "missing_result"})
            continue
        result = read_json(result_path)
        if result.get("status") not in {"completed", "infrastructure_error"}:
            skipped.append({"condition": relative, "reason": "not_completed", "status": result.get("status")})
            continue
        packet = Packet(run, condition, max_chars=max_chars)
        data = packet.build(result)
        cid, iid = opaque("case", relative), opaque("input", condition.parent.name)
        inputs = run / "private_inputs" / condition.parent.name
        if iid not in input_bundles:
            inventory = {}
            if inputs.is_dir():
                for path in sorted(inputs.rglob("*")):
                    if path.is_symlink():
                        raise ValueError("Linked public input is forbidden: " + str(path))
                    if not path.is_file():
                        continue
                    rel = path.relative_to(inputs).as_posix()
                    if not (production(rel) or rel in {"task.json", "source.py"}):
                        continue
                    dest = output / "blind/inputs" / iid / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, dest)
                    inventory[rel] = digest(path)
            else:
                data["gaps"].append("frozen_public_input_bundle_missing")
            input_bundles[iid] = inventory
        data.update({"case_id": cid, "input_bundle": "inputs/" + iid,
                     "public_input_hashes": input_bundles[iid]})
        public_production = {k: v for k, v in input_bundles[iid].items() if production(k)}
        if packet.initial_hashes != public_production:
            data["gaps"].append("public_bundle_does_not_match_initial_snapshot")
        encoded = json.dumps(data, ensure_ascii=False)
        if any(name in encoded for name in METHODS):
            raise ValueError("Explicit method identity remains in blinded packet")
        write_json(output / "blind/cases" / (cid + ".json"), data)
        mapping.append({"case_id": cid, "condition": relative, "input_id": iid,
                        "source_condition_status": result.get("status"), "sources": packet.sources,
                        "boundary": packet.boundary, "gaps": data["gaps"]})
        cases.append({"case_id": cid, "input_bundle": data["input_bundle"],
                      "boundary_status": data["boundary"].get("status"),
                      "evidence_records": len(data["evidence"]), "gap_count": len(data["gaps"])})
    summary = {"exported": len(cases), "skipped": len(skipped),
               "boundaries": dict(Counter(x["boundary_status"] for x in cases)),
               "evidence_records": sum(x["evidence_records"] for x in cases)}
    write_json(output / "blind/index.json", {"schema": VERSION, "cases": sorted(cases, key=lambda x: x["case_id"])})
    write_json(output / "private/mapping.json", {"schema": VERSION, "source_run": str(run),
        "private_blinding_key": secret.hex(), "script_sha256": digest(Path(__file__)),
        "frozen_protocol_sha256": PROTOCOL_SHA256,
        "summary": summary, "cases": mapping, "skipped": skipped})
    (output / "blind/README.txt").write_text(
        "Unscored pre-production-edit evidence. Use index.json and cases/*.json.\n"
        "Do not distribute the sibling private directory to blind reviewers.\n"
        "The input bundle is the frozen faulty public code, never the final patch.\n"
        "recorded_reasoning is logged provider reasoning, distinct from an explicit final report.\n"
        "No diagnosis is inferred from code proposals. Review explicit claims and their evidence.\n"
        "Missing categories carry no penalty. Gaps and upstream/export limits are recorded.\n"
        "Method names are masked, but tool vocabulary and interaction style can remain recognizable.\n",
        encoding="utf-8")
    return summary


def main() -> None:
    if "--self-test" in sys.argv:
        self_test()
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--condition", action="append", help="task_001/method_name; repeat to select a subset")
    parser.add_argument("--max-chars", type=int, default=0, help="Per-string export cap; 0 preserves full content")
    parser.add_argument("--key", help="Optional private hex key for reproducible opaque IDs; kept only in private/")
    args = parser.parse_args()
    print(json.dumps(export(args.run, args.output, conditions=args.condition, max_chars=args.max_chars, key=args.key), indent=2))


def self_test() -> None:
    """Small behavioral checks for evidence leakage and uncertain boundaries."""
    class ExportTests(unittest.TestCase):
        def setUp(self):
            self.tmp = tempfile.TemporaryDirectory()
            self.root = Path(self.tmp.name)
            self.run = self.root / "run"

        def tearDown(self):
            self.tmp.cleanup()

        def condition(self, method="autonomous_layered"):
            condition = self.run / "conditions/task_001" / method
            for folder in [self.run / "private_inputs/task_001", condition / "evidence/initial_code",
                           condition / "evidence/after_diagnosis", condition / "evidence/final_code"]:
                folder.mkdir(parents=True)
                (folder / "candidate.py").write_text("VALUE = 1\n")
            result = {"status": "completed", "accepted": "PRIVATE_FINAL_SENTINEL",
                      "initial": {"observation": {"accepted": False, "error": "initial"}}}
            write_json(condition / "result.json", result)
            return condition, result

        def event(self, condition, number, kind, data):
            path = condition / "evidence/agent" / f"event_{number:05d}_{kind}.json"
            write_json(path, {"kind": kind, "data": data})
            return path

        def response(self, condition, call, text, reasoning="", tool_id="call_a"):
            data = {"id": f"response_{call}", "choices": [{"message": {
                "content": text, "reasoning_content": reasoning,
                "tool_calls": [{"id": tool_id, "function": {"name": "edit", "arguments": "PRIVATE_PATCH_SENTINEL"}}]},
                "finish_reason": "tool_calls"}]}
            write_json(condition / "evidence/agent" / f"call_{call:04d}_response.json", data)
            return data

        def edit(self, condition, number, *, before=None, after="changed"):
            return self.event(condition, number, "tool", {"call": 1, "tool_call_id": "call_a", "name": "edit",
                "arguments": {"edits": [{"path": "candidate.py", "new": "PRIVATE_PATCH_SENTINEL"}]},
                "result": {"ok": True, "files": [{"path": "candidate.py",
                    "before_sha256": before or digest(condition / "evidence/initial_code/candidate.py"),
                    "after_sha256": after}]}})

        def test_trigger_statement_included_post_edit_result_excluded(self):
            condition, _ = self.condition()
            self.event(condition, 1, "api_start", {"call": 1})
            self.response(condition, 1, "Explicit cause in autonomous_layered before changing code")
            self.event(condition, 2, "tool", {"name": "read", "result": {"value": "before"}})
            self.edit(condition, 3)
            self.event(condition, 4, "observation", {"post_edit": "PRIVATE_AFTER_SENTINEL"})
            export(self.run, self.root / "out")
            blind = next((self.root / "out/blind/cases").glob("*.json")).read_text()
            self.assertIn("Explicit cause", blind)
            for marker in ("PRIVATE_PATCH_SENTINEL", "PRIVATE_AFTER_SENTINEL", "PRIVATE_FINAL_SENTINEL", "autonomous_layered"):
                self.assertNotIn(marker, blind)
            self.assertIn("recorded_production_edit", blind)

        def test_noop_edit_does_not_freeze(self):
            condition, result = self.condition()
            same = digest(condition / "evidence/initial_code/candidate.py")
            self.edit(condition, 1, after=same)
            self.event(condition, 2, "observation", {"value": "after_noop_before_real_edit"})
            self.edit(condition, 3)
            data = Packet(self.run, condition).build(result)
            self.assertIn("after_noop_before_real_edit", json.dumps(data))

        def test_unlogged_change_fails_closed(self):
            condition, result = self.condition()
            self.event(condition, 1, "stage_start", {"stage": "repair"})
            self.event(condition, 2, "observation", {"secret": "PRIVATE_UNBOUNDED_SENTINEL"})
            self.edit(condition, 3, before="unlogged_change")
            data = Packet(self.run, condition).build(result)
            self.assertEqual(data["boundary"]["status"], "missing_artifact")
            self.assertNotIn("PRIVATE_UNBOUNDED_SENTINEL", json.dumps(data))

        def test_native_trigger_observation_and_patch_excluded(self):
            condition, result = self.condition("swe_native_isolated")
            before = hashes(condition / "evidence/initial_code")
            response = self.response(condition, 2, "Explicit native cause", "Hypothesis before edit")
            write_json(condition / "evidence/agent/swe_event_0001_first_edit.json", {
                "before_hashes": before, "after_hashes": {"candidate.py": "changed"},
                "history_before": [{"role": "assistant", "content": "Earlier hypothesis"}],
                "triggering_provider_response": response,
                "triggering_step": {"observation": "PRIVATE_AFTER_SENTINEL", "action": "PRIVATE_PATCH_SENTINEL"}})
            data = Packet(self.run, condition).build(result)
            self.assertIn("Explicit native cause", json.dumps(data))
            self.assertNotIn("PRIVATE_AFTER_SENTINEL", json.dumps(data))
            self.assertNotIn("PRIVATE_PATCH_SENTINEL", json.dumps(data))

        def test_native_no_edit_keeps_matched_reasoning_and_null_tools(self):
            condition, result = self.condition("swe_native_isolated")
            response = self.response(condition, 1, "Diagnostic statement", "Reasoned mechanism")
            response["choices"][0]["message"]["tool_calls"] = None
            write_json(condition / "evidence/agent/call_0001_response.json", response)
            write_json(condition / "evidence/agent/swe_event_0001_checkpoint.json", {
                "history": [{"role": "assistant", "content": "Diagnostic statement", "tool_calls": None}]})
            data = Packet(self.run, condition).build(result)
            self.assertEqual(data["boundary"]["status"], "no_recorded_production_edit")
            self.assertIn("Reasoned mechanism", json.dumps(data))

        def test_truncation_boundaries_and_pagination_recorded(self):
            condition, result = self.condition()
            self.event(condition, 1, "tool", {"name": "read", "result": {
                "lines": [{"line": 7, "text": "abcdefghijklmnop"}], "total_lines": 100, "next_line": 8}})
            data = Packet(self.run, condition, max_chars=8).build(result)
            record = next(x for x in data["evidence"] if x["kind"] == "tool_exchange")
            self.assertTrue(record["export_truncation"])
            self.assertTrue(any(x["kind"] == "pagination" for x in record["source_limits"]))

        def test_output_cannot_modify_source_run(self):
            self.condition()
            with self.assertRaises(ValueError):
                export(self.run, self.run / "output")

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ExportTests)
    if not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
