#!/usr/bin/env python3
"""Aggregate evaluator-only diagnosis scores without model calls or repair feedback."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import score_autonomous_diagnosis as scoring


SCOPES = ("all50", "primary38", "contract12")
CONCORDANCE = ("consistent", "partial", "inconsistent", "undetermined", "not_reported")
TOKEN_FIELDS = ("prompt_tokens", "completion_tokens", "total_tokens")


def counts(values, choices):
    result = dict.fromkeys(choices, 0)
    result.update(Counter(values))
    return result


def coverage(numerator, denominator):
    return {"numerator": numerator, "denominator": denominator,
            "fraction": numerator / denominator if denominator else None}


def load_rubric(path):
    if scoring.sha(path) != scoring.RUBRIC_SHA256:
        raise ValueError("Rubric differs from frozen scoring rules")
    rubric = scoring.read(path)
    tasks = {row["anonymous_id"]: row["scorability"] for row in rubric["tasks"]}
    primary = {task for task, row in tasks.items() if row["primary_mechanism_and_symbol_location_eligible"]}
    contract = {task for task, row in tasks.items() if row["specification_status"] == "contract_dependent"}
    if len(tasks) != 50 or len(primary) != 38 or len(contract) != 12 or primary & contract:
        raise ValueError("Frozen 50/38/12 task scopes are inconsistent")
    return rubric, tasks, {"all50": set(tasks), "primary38": primary, "contract12": contract}


def load_mappings(exports, tasks):
    by_hash, identities, methods = {}, {}, {}
    for pack in sorted({p.resolve() for p in exports}):
        path = pack / "private/mapping.json"
        mapping = scoring.read(path)
        source = mapping["source_run"]
        entries = {}
        for row in mapping["cases"]:
            task, method = row["condition"].split("/", 1)
            if task not in tasks:
                raise ValueError("Mapping contains a task outside Fixed50: " + task)
            identity = (source, task, method)
            cid = row["case_id"]
            if cid in identities and identities[cid] != identity:
                raise ValueError("Anonymous case ID maps to conflicting conditions")
            identities[cid] = identity
            entries[cid] = identity
            methods.setdefault(source, set()).add(method)
        item = {"path": str(path), "source_run": source, "entries": entries}
        by_hash[scoring.sha(path)] = item
    return by_hash, methods


def phase_state(folder):
    path = folder / "state.json"
    if not path.exists():
        return {"status": "not_invoked"}
    state = scoring.read(path)
    usage = state.get("usage")
    if not isinstance(usage, dict) or type(usage.get("attempted")) is not bool:
        raise ValueError("Phase state lacks explicit API-attempt accounting: " + str(path))
    return state


def aggregate_usage(states):
    attempted = [s["usage"] for s in states if s.get("usage", {}).get("attempted")]
    result = {"api_attempts": len(attempted), "measured": {}, "unknown_calls": {}, "totals": {},
              "actual_models": dict(Counter(u.get("actual_model") or "unknown" for u in attempted))}
    for key in TOKEN_FIELDS:
        known = [u.get(key) for u in attempted if type(u.get(key)) is int and u[key] >= 0]
        result["measured"][key] = sum(known)
        result["unknown_calls"][key] = len(attempted) - len(known)
        result["totals"][key] = None if len(known) != len(attempted) else sum(known)
    result["unknown_usage_calls"] = sum(any(type(u.get(k)) is not int or u[k] < 0
                                            for k in TOKEN_FIELDS) for u in attempted)
    result["token_totals_complete"] = result["unknown_usage_calls"] == 0
    result["accounting"] = "Evaluation only, including failed or unfinished calls; unknown usage is not zero cost."
    return result


def verified_assessment(folder, phase1, phase2, reference, pack=None):
    """Verify stored success artifacts; never infer a score from phase 1 alone."""
    if phase1["status"] != "success":
        return None, "phase1_" + phase1["status"], None
    if phase2["status"] != "success":
        return None, "phase2_" + phase2["status"], None
    try:
        for name, state in (("phase1", phase1), ("phase2", phase2)):
            if scoring.sha(folder / name / "assessment.json") != state["assessment_sha256"]:
                raise ValueError("Saved assessment hash changed")
        public = json.loads(scoring.read(folder / "phase1/request.json")["messages"][1]["content"])
        first = scoring.read(folder / "phase1/assessment.json")
        final = scoring.read(folder / "phase2/assessment.json")
        fingerprint = scoring.read(folder / "input_fingerprint.json")
        if fingerprint != {
            "normalized_public_payload_sha256": hashlib.sha256(scoring.encoded(public)).hexdigest(),
            "reference_sha256": hashlib.sha256(scoring.encoded(reference)).hexdigest(),
        }:
            raise ValueError("Saved request/reference differs from the case input fingerprint")
        second_payload = json.loads(scoring.read(folder / "phase2/request.json")["messages"][1]["content"])
        if (second_payload["public_evidence"] != public
                or second_payload["phase1_assessment"] != first
                or any(second_payload[key] != value for key, value in reference.items())):
            raise ValueError("Second-phase input differs from the verified public evidence or reference")
        if "quotable_statement_spans" in public:
            import score_autonomous_diagnosis_spans as span_scoring
            if pack is None:
                raise ValueError("Original evidence export required for citation reconstruction")
            case = scoring.read(pack / "blind/cases" / (folder.name + ".json"))
            # The recorded request sorts dictionary keys; span IDs use export order.
            rebuilt = span_scoring.add_spans(scoring.public_payload(pack, case))
            if rebuilt != public:
                raise ValueError("Citation spans differ from deterministic source reconstruction")
            span_scoring.validate_canonical(first, 1, public)
            span_scoring.validate_canonical(final, 2, public, reference, first)
        else:
            scoring.validate(first, 1, public)
            scoring.validate(final, 2, public, reference, first)
        return final, "assessed", None
    except (OSError, KeyError, TypeError, ValueError, AssertionError, AttributeError) as error:
        return None, "assessment_integrity_error", type(error).__name__ + ": " + str(error)


def summarize_group(group, scopes):
    rows = group.pop("records")
    states = group.pop("phase_states")
    by_task = {row["task"]: row for row in rows}
    assessed = {task for task, row in by_task.items() if row["status"] == "assessed"}
    group["recorded_conditions"] = len(rows)
    group["phase_status_counts"] = dict(Counter(s["status"] for s in states))
    group["usage"] = aggregate_usage(states)
    group["scopes"] = {}
    group["channels"] = {channel: {} for channel in scoring.CHANNELS}
    for name, tasks in scopes.items():
        complete = sorted(tasks & assessed)
        missing = sorted(tasks - assessed)
        group["scopes"][name] = {
            "expected_conditions": len(tasks), "assessed_conditions": len(complete),
            "unassessed_conditions": len(missing), "assessment_coverage": coverage(len(complete), len(tasks)),
            "operational_status_counts": dict(Counter(by_task[t]["status"] if t in by_task else "not_invoked" for t in tasks)),
            "unassessed_tasks": missing,
        }
        for channel in scoring.CHANNELS:
            judgments = [by_task[task]["assessment"][channel] for task in complete]
            group["channels"][channel][name] = {
                "assessed_conditions": len(complete), "unassessed_conditions": len(missing),
                "axis_state_counts": {axis: counts([j["axis_scores"][axis]["state"] for j in judgments], sorted(scoring.STATES))
                                      for axis in scoring.AXES},
                "private_reference_concordance": counts([j["private_reference_concordance"]["state"] for j in judgments], CONCORDANCE),
                "evidence_levels": counts([j["evidence_level"] or "unassigned" for j in judgments],
                    ("unassigned", "observed_failure", "supported_mechanism", "counterfactually_validated")),
            }
            metrics = {}
            for axis in scoring.AXES:
                eligible = tasks & scopes["primary38"] if axis in scoring.MECHANISM_AXES else tasks
                evaluated = sorted(eligible & assessed)
                correct = sum(by_task[task]["assessment"][channel]["axis_scores"][axis]["state"] == "correct"
                              for task in evaluated)
                metrics[axis] = {
                    "eligible_conditions": len(eligible), "assessed_eligible_conditions": len(evaluated),
                    "correct": correct,
                    "correct_fraction_among_assessed": correct / len(evaluated) if evaluated else None,
                    "correct_fraction_frozen_pool": (correct / len(eligible)
                        if eligible and len(evaluated) == len(eligible) else None),
                }
            group["channels"][channel][name]["axis_metrics"] = metrics
    return group


def aggregate(roots, exports, rubric_path):
    rubric, tasks, scopes = load_rubric(rubric_path)
    mappings, methods = load_mappings(exports, tasks)
    references = {r["anonymous_id"]: {"private_reference": r["private_reference"], "scorability": r["scorability"]}
                  for r in rubric["tasks"]}
    groups, records, all_states, sources, seen_conditions = {}, [], [], [], set()
    for root in sorted({p.resolve() for p in roots}):
        manifest = scoring.read(root / "evaluation_manifest.json")
        if manifest["rubric_sha256"] != scoring.RUBRIC_SHA256 or manifest.get("channel_merging") is not False:
            raise ValueError("Assessment manifest conflicts with frozen rubric/channel separation")
        version_id = hashlib.sha256(scoring.encoded(manifest)).hexdigest()
        allowed, packs, run_sources = {}, {}, set()
        for bundle_path in sorted((root / "bundles").glob("*.json")):
            bundle = scoring.read(bundle_path)
            mapping = mappings.get(bundle["pack_mapping_sha256"])
            if mapping is None:
                raise ValueError("Provide the matching evidence export for " + str(bundle_path))
            if bundle["source_run"] != str(Path(mapping["source_run"]).resolve()):
                raise ValueError("Bundle and private mapping source runs differ")
            allowed.update(mapping["entries"])
            packs.update({cid: Path(mapping["path"]).parent.parent for cid in mapping["entries"]})
            run_sources.add(mapping["source_run"])
        if not run_sources:
            raise ValueError("Assessment root has no verified export bundle")
        for source in run_sources:
            for method in methods[source]:
                key = (source, version_id, method)
                if key not in groups:
                    groups[key] = {"source_run": source, "repair_version": Path(source).name,
                        "assessment_version_id": version_id, "assessment_configuration": manifest,
                        "method": method, "records": [], "phase_states": []}
        sources.append({"assessment_root": str(root), "manifest_sha256": scoring.sha(root / "evaluation_manifest.json"),
                        "assessment_version_id": version_id})
        for folder in sorted((root / "cases").iterdir()):
            if not folder.is_dir():
                continue
            cid = folder.name
            if cid not in allowed:
                raise ValueError("Assessment case is absent from verified private mappings: " + cid)
            source, task, method = allowed[cid]
            key = (source, version_id, method)
            unique = (*key, task)
            if unique in seen_conditions:
                raise ValueError("Duplicate condition in the same scoring version; select one output root explicitly: " + "/".join((Path(source).name, task, method)))
            seen_conditions.add(unique)
            p1, p2 = phase_state(folder / "phase1"), phase_state(folder / "phase2")
            assessment, status, error = verified_assessment(folder, p1, p2, references[task], packs[cid])
            cov_path = folder / "coverage.json"
            cov = scoring.read(cov_path) if cov_path.exists() else {}
            if cov.get("status") == "missing_artifact" and p1["status"] == "not_invoked":
                status = "missing_artifact"
            row = {"case_id": cid, "task": task, "method": method, "source_run": source,
                "repair_version": Path(source).name, "assessment_version_id": version_id,
                "assessment_root": str(root), "status": status, "phase_status": {"phase1": p1["status"], "phase2": p2["status"]},
                "primary_mechanism_location_eligible": task in scopes["primary38"],
                "specification_status": tasks[task]["specification_status"],
                "assessment": assessment, "integrity_error": error,
                "usage": aggregate_usage((p1, p2))}
            records.append(row)
            groups[key]["records"].append(row)
            groups[key]["phase_states"].extend((p1, p2))
            all_states.extend((p1, p2))
    return {"schema": "autonomous-diagnosis-aggregation-v1", "label": scoring.LABEL,
            "private_report": True, "repair_feedback": False, "model_calls_made_by_aggregator": 0,
            "rubric_sha256": scoring.sha(rubric_path), "frozen_denominators": {s: len(t) for s, t in scopes.items()},
            "state_policy": "Unassessed conditions have no axis state. partial is a distinct count, never fractional credit.",
            "assessment_sources": sources,
            "mapping_sources": [{"path": v["path"], "sha256": k} for k, v in sorted(mappings.items())],
            "usage": aggregate_usage(all_states),
            "groups": [summarize_group(groups[k], scopes) for k in sorted(groups)],
            "records": records}


def markdown(report):
    lines = ["# 自主诊断评分聚合", "", report["label"], "",
        "每个修复版本、评分配置和方法分别统计。未完成评分的条件保留为未评分；partial 单列，不换算为分数。", "",
        "| 修复版本 | 评分版本 | 方法 | 全部评分覆盖 | 主要机制/位置覆盖 | 契约依赖覆盖 | API尝试 | 总token | 未知用量调用 |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for group in report["groups"]:
        display = [f"{group['scopes'][s]['assessed_conditions']}/{group['scopes'][s]['expected_conditions']}" for s in SCOPES]
        usage = group["usage"]
        total = usage["totals"]["total_tokens"]
        lines.append(f"| {group['repair_version']} | {group['assessment_version_id'][:12]} | {group['method']} | {' | '.join(display)} | {usage['api_attempts']} | {total if total is not None else 'n/a'} | {usage['unknown_usage_calls']} |")
    for group in report["groups"]:
        lines += ["", f"## {group['repair_version']} · {group['method']} · {group['assessment_version_id'][:12]}", ""]
        for channel in scoring.CHANNELS:
            lines += [f"### {channel}", "",
                "| 范围 | 评分轴 | correct | partial | incorrect | undetermined | not_reported | not_scorable | 未评分 |",
                "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
            for scope in SCOPES:
                stats = group["channels"][channel][scope]
                for axis in scoring.AXES:
                    value = stats["axis_state_counts"][axis]
                    values = [str(value[s]) for s in ("correct", "partial", "incorrect", "undetermined", "not_reported", "not_scorable")]
                    lines.append(f"| {scope} | {axis} | {' | '.join(values)} | {stats['unassessed_conditions']} |")
            concordance = group["channels"][channel]["contract12"]["private_reference_concordance"]
            lines += ["", "契约依赖任务的私有参考一致性：" + "，".join(f"{k}={v}" for k, v in concordance.items()) + "。", ""]
        lines += ["运行覆盖状态：" + json.dumps({s: group["scopes"][s]["operational_status_counts"] for s in SCOPES}, ensure_ascii=False) + "。", ""]
    usage = report["usage"]
    lines += ["## 评分调用成本", "", f"全部评分 API 尝试 {usage['api_attempts']} 次；未知用量 {usage['unknown_usage_calls']} 次。",
        "已知 token 合计：" + json.dumps(usage["measured"], ensure_ascii=False) + "。",
        "未知字段按 null/n/a 保留。失败和未完成调用的已知用量也计入评分成本；评分成本与修复成本分开。", ""]
    return "\n".join(lines)


def write_report(report, output, exports):
    targets = [output.with_suffix(suffix).resolve() for suffix in (".json", ".md")]
    protected = [p.resolve() for p in exports] + [Path(g["source_run"]).resolve() for g in report["groups"]]
    for target in targets:
        if any(target == p or p in target.parents for p in protected):
            raise ValueError("Aggregation output must be outside evidence exports and repair runs")
    scoring.save(targets[0], report)
    targets[1].write_text(markdown(report), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assessment-root", action="append", type=Path, default=[])
    parser.add_argument("--assessment-parent", action="append", type=Path, default=[],
                        help="Recursively discover independent scoring roots under this directory")
    parser.add_argument("--evidence-export", action="append", type=Path, required=True)
    parser.add_argument("--rubric", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="Private report prefix; writes .json and .md")
    args = parser.parse_args()
    roots = args.assessment_root + [p.parent for parent in args.assessment_parent for p in parent.rglob("evaluation_manifest.json")]
    if not roots:
        parser.error("No assessment roots supplied or found")
    report = aggregate(roots, args.evidence_export, args.rubric)
    write_report(report, args.output, args.evidence_export)
    print(json.dumps({"assessment_roots": len(report["assessment_sources"]), "groups": len(report["groups"]),
                      "condition_records": len(report["records"]), "usage": report["usage"]}, indent=2))


if __name__ == "__main__":
    main()
