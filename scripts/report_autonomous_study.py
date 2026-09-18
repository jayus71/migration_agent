#!/usr/bin/env python3
"""Combine complete/provisional grids; preserve versions and all denominators."""
import argparse
import json
from pathlib import Path

from analyze_autonomous_comparison import analyze


LABELS = {
    "autonomous_layered": "我们：证据记忆，无类别要求",
    "autonomous_layered_native": "我们：完整历史，无类别要求",
    "autonomous_category_ablation": "我们：证据记忆，类别要求消融",
    "swe_native_isolated": "SWE-agent 1.1.0 原生流程",
    "direct_shared_tools": "Direct 共享工具控制",
    "matchfix_full_orchestration": "MatchFix 完整编排＋共享工具后端",
}


def compare(left, right):
    """Compare only completed matched records and explicitly mark partial sets."""
    by_left = {r["task"]: r for r in left if r["status"] == "completed"}
    by_right = {r["task"]: r for r in right if r["status"] == "completed"}
    result = {"left_only": [], "right_only": [], "both": [], "neither": []}
    for task in sorted(by_left.keys() & by_right.keys()):
        a, b = by_left[task]["accepted"], by_right[task]["accepted"]
        key = ("both" if b else "left_only") if a else ("right_only" if b else "neither")
        result[key].append(task)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="Implementation checkout containing experiments/")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-raw", action="store_true")
    args = parser.parse_args()
    study = {}
    for benchmark, group in (("Fixed50", "autonomous_fixed50_20260917"), ("Natural10", "autonomous_verifier_20260917")):
        study[benchmark] = {}
        for version in ("formal_v3", "progress_v4", "repair_window_v5", "productive_v6", "productive_v7"):
            run = args.root / "experiments" / group / version
            if (run / "manifest.json").exists():
                study[benchmark][version] = analyze(run, verify_raw=args.verify_raw)
    complete = all(r["complete"] for versions in study.values() for r in versions.values())
    all_terminal = all(r["all_terminal"] for versions in study.values() for r in versions.values())
    block_path = args.root / "output/transport_block_402.json"
    block = json.loads(block_path.read_text()) if block_path.exists() else None
    lines = ["# 去除答案提示后的自主修复实验", "",
        "状态：" + ("DeepSeek 接口返回 HTTP 402，已停止新请求派发；保留完整结果、基础设施错误及尚未执行条件，等待接口恢复。" if block else "全部计划条件已完成。" if complete else "全部计划条件已结束；存在基础设施或其他缺失结果，相关统计保留 n/a。" if all_terminal else "仍有条件运行中；以下为临时统计，分母固定，暂不作最终排名。"), "",
        "全部方法沿用配置的 DeepSeek。Fixed50 保留原故障单元验收与四次尝试；Natural10 使用相同初态和输入下的数值配对验收及两个额外确认种子。两组任务独立统计。", "",
        "v3 比较冻结后的完整方法及类别、记忆消融。v4 仅改进我们的方法，增加阶段进展检查点和编辑参数格式反馈，预算与验收不变；两个版本完整保留。v4 设计参考了 v3 公开轨迹，这些任务属于开发评估。", "",
        "v5 在 v4 完整历史配置上，仅把每个修复阶段调用上限从 8 改为 32；初诊仍最多 8 次，全局仍最多 40 次调用、12 万输出 token、四次外部提交。下表的 1/2/4 次表示外部提交，不表示单次模型调用；比较最终接受率和全调用成本时沿用同一总预算。", "",
        "v6 在 v4 证据记忆配置上保留每阶段 8 次调用，使修复阶段最后一次调用仍可使用工具；初诊仍保留报告调用。其他工作流、预算和验收不变。v5/v6 都由已观察的开发轨迹提出。", "",
        "v6 的进展提示遗留了最后调用留给总结的相反表述；v7 修正该提示，工具行为和预算不变。v6 保留为开发记录，最终选择使用提示一致的版本。", "",
        "Native SWE 使用其原生提示、工具、历史、解析、重试与提交。MatchFix 保留完整上游编排，编码后端适配共同 DeepSeek 和文件工具；Fixed50 没有源／目标程序对，所以该组不含 MatchFix。Direct 是明确配置的共享工具控制。", ""]
    version_pairs = {}
    window_pairs = {}
    productive_pairs = {}
    corrected_pairs = {}
    for benchmark, versions in study.items():
        lines += [f"## {benchmark}", "",
                  "| 版本 | 方法 | 完成/计划 | 接受 | 第1/2/4次提交内 | 初始失败修复 | token总量 | token/接受 |",
                  "| --- | --- | ---: | ---: | --- | --- | ---: | ---: |"]
        for version, report in versions.items():
            for method, s in report["methods"].items():
                checkpoint = "/".join(str(s["accepted_by_attempt"][str(n)]) for n in (1, 2, 4))
                ratio = f"{s['tokens_per_accepted']:,.1f}" if s["tokens_per_accepted"] is not None else "n/a"
                lines.append(f"| {version} | {LABELS.get(method, method)} | {s['completed']}/{s['planned']} | {s['accepted']} | {checkpoint} | {s['repaired_initially_failed']}/{s['initially_failed']} | {s['total_tokens']:,} | {ratio} |")
        lines += ["", "token 总量包括已结束的失败条件；运行中调用尚未计入此表。未知 usage 或尚未完成时，每次接受成本为 n/a。健康保持及逐例结果见配套 JSON。", ""]
        for version, report in versions.items():
            for method, s in report["methods"].items():
                if s["noncompleted_terminal"]:
                    lines += [f"{version} / {method} 的终止缺失：" + json.dumps(s["noncompleted_terminal"], ensure_ascii=False)
                              + f"；未知 usage 调用 {s['unknown_usage_calls']} 次。", ""]
        if all(v in versions for v in ("formal_v3", "progress_v4")):
            original, improved = versions["formal_v3"], versions["progress_v4"]
            version_pairs[benchmark] = {}
            for method in ("autonomous_layered", "autonomous_layered_native"):
                a = [r for r in improved["records"] if r["method"] == method]
                b = [r for r in original["records"] if r["method"] == method]
                version_pairs[benchmark][method] = {"left": "progress_v4", "right": "formal_v3",
                    "complete": improved["methods"][method]["complete"] and original["methods"][method]["complete"],
                    **compare(a, b)}
        if all(v in versions for v in ("progress_v4", "repair_window_v5")):
            method = "autonomous_layered_native"
            original, improved = versions["progress_v4"], versions["repair_window_v5"]
            a = [r for r in improved["records"] if r["method"] == method]
            b = [r for r in original["records"] if r["method"] == method]
            window_pairs[benchmark] = {"method": method, "left": "repair_window_v5", "right": "progress_v4",
                "complete": improved["methods"][method]["complete"] and original["methods"][method]["complete"],
                **compare(a, b)}
        if all(v in versions for v in ("progress_v4", "productive_v6")):
            method = "autonomous_layered"
            original, improved = versions["progress_v4"], versions["productive_v6"]
            a = [r for r in improved["records"] if r["method"] == method]
            b = [r for r in original["records"] if r["method"] == method]
            productive_pairs[benchmark] = {"method": method, "left": "productive_v6", "right": "progress_v4",
                "complete": improved["methods"][method]["complete"] and original["methods"][method]["complete"],
                **compare(a, b)}
        if all(v in versions for v in ("progress_v4", "productive_v7")):
            method = "autonomous_layered"
            original, improved = versions["progress_v4"], versions["productive_v7"]
            a = [r for r in improved["records"] if r["method"] == method]
            b = [r for r in original["records"] if r["method"] == method]
            corrected_pairs[benchmark] = {"method": method, "left": "productive_v7", "right": "progress_v4",
                "complete": improved["methods"][method]["complete"] and original["methods"][method]["complete"],
                **compare(a, b)}
    lines += ["## 结果解释", "",
        "分类只在我们的一项消融中要求自由文本输出，任何配置都不提供正确类别、责任位置、修复路线或健康目标代码。诊断能力依据首次生产编辑之前的明确解释与工具证据另行评分；修复接受率不替代定位准确率。", "",
        "Natural10 的后端核查证明模型损失对应 MindSpore 求导；冻结候选通过 torch4ms 调用 PyTorch 优化器更新参数。配对验收覆盖该混合执行路径的数值一致性，不能描述为全部训练 kernel 均由 MindSpore 执行。", "",
        "全部结果、失败调用、未知 usage、固定输入哈希和各版本代码快照随运行保留。最终正文和图表尚未用这些新结果替换。", ""]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.with_suffix(".md").write_text("\n".join(lines), encoding="utf-8")
    args.output.with_suffix(".json").write_text(json.dumps({"complete": complete, "all_terminal": all_terminal, "transport_block": block, "studies": study,
        "version_comparisons": version_pairs, "repair_window_comparisons": window_pairs,
        "productive_comparisons": productive_pairs, "corrected_productive_comparisons": corrected_pairs}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"complete": complete, "all_terminal": all_terminal, "conditions_completed": sum(s["completed"] for vs in study.values() for r in vs.values() for s in r["methods"].values()),
                      "planned": sum(s["planned"] for vs in study.values() for r in vs.values() for s in r["methods"].values()),
                      "noncompleted_terminal": sum(len(s["noncompleted_terminal"]) for vs in study.values() for r in vs.values() for s in r["methods"].values()),
                      "raw_ledger_problems": sum(not a.get("available") or bool(a.get("mismatches")) for vs in study.values() for r in vs.values() for a in r["raw_ledger_audits"].values())}))


if __name__ == "__main__":
    main()
