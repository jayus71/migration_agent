#!/usr/bin/env python3
"""Aggregate declared diagnosis selections, retaining every evaluation cost."""
import argparse
from collections import Counter
import json
from pathlib import Path

import aggregate_autonomous_diagnosis as aggregation


def read(path):
    return json.loads(path.read_text())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--continuation", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    root = args.root.resolve()
    rubric_path = root / "code/fixed50-private-diagnosis-rubric-20260917.json"
    if args.continuation:
        continuation = args.continuation.resolve()
        progress = read(continuation / ("dispatch_result.json" if (continuation / "dispatch_result.json").exists() else "progress.json"))
        selections = [r for r in progress["finished"] if r.get("assessment_root")]
        roots = [Path(r["assessment_root"]) for r in selections]
        packs = [Path(r["evidence_export"]) for r in selections]
    else:
        continuation = None
        roots = [p.parent for name in ("assessments", "assessments_expanded", "assessments_spans")
                 for p in (root / name).rglob("evaluation_manifest.json")]
        packs = [p.parent.parent for p in (root / "exports").rglob("private/mapping.json")]
    value = aggregation.aggregate(roots, packs, rubric_path)
    if continuation:
        by_root = {r["assessment_root"]: r for r in selections}
        _, _, scopes = aggregation.load_rubric(rubric_path)
        groups = {}
        for row in value["records"]:
            item = by_root[row["assessment_root"]]
            row["logical_repair_version"] = item["version"]
            key = (item["version"], row["method"])
            group = groups.setdefault(key, {"repair_version": item["version"], "method": row["method"],
                "records": [], "phase_states": []})
            group["records"].append(row)
            folder = Path(row["assessment_root"]) / "cases" / row["case_id"]
            group["phase_states"].extend(aggregation.phase_state(folder / phase) for phase in ("phase1", "phase2"))
        value["logical_groups"] = [aggregation.summarize_group(g, scopes) for g in groups.values()]
        value["declared_selection"] = str(continuation / "plan.json")
        value["planned_conditions"] = len(read(continuation / "plan.json")["jobs"])
    all_states = []
    cost_roots = [root / name for name in ("assessments", "assessments_expanded", "assessments_spans")]
    if continuation:
        cost_roots.append(continuation / "assessments")
    for cost_root in cost_roots:
        for path in cost_root.rglob("state.json"):
            if path.parent.name in {"phase1", "phase2"}:
                all_states.append(aggregation.phase_state(path.parent))
    value["all_evaluator_attempts_usage"] = aggregation.aggregate_usage(all_states)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.with_suffix(".json").write_text(json.dumps(value, indent=2) + "\n")
    lines = ["# 自主诊断评分恢复结果", "",
        "沿用冻结评分规则与 DeepSeek，校验实际引用及首次生产编辑前的证据。原接口中断及开发评分成本单列并保留；格式或长度失败不作为诊断错误，也不自动重试。", "",
        "| 修复版本 | 方法 | 已评分/50 | 主要任务覆盖/38 | 契约依赖覆盖/12 |",
        "| --- | --- | ---: | ---: | ---: |"]
    for group in value.get("logical_groups", value["groups"]):
        coverage = [str(group["scopes"][scope]["assessed_conditions"]) for scope in aggregation.SCOPES]
        lines.append(f"| {group['repair_version']} | {group['method']} | {coverage[0]}/50 | {coverage[1]}/38 | {coverage[2]}/12 |")
    lines += ["", "这是 DeepSeek 辅助探索性评分，正文与已记录推理分别评分。诊断准确率与修复接受率分开；完整轴分布、逐例引用及未评分原因见 JSON。", "",
              "全评估调用成本：" + json.dumps(value["all_evaluator_attempts_usage"], ensure_ascii=False), ""]
    args.output.with_suffix(".md").write_text("\n".join(lines))
    print(json.dumps({"selected_records": len(value["records"]), "statuses": dict(Counter(r["status"] for r in value["records"])),
        "all_usage": value["all_evaluator_attempts_usage"]}))


if __name__ == "__main__":
    main()
