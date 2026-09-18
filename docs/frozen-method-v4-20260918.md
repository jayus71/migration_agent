# 统一主方法：精简 v4 独立证据交接

用户于 2026-09-18 最终确认统一使用精简 v4，即组件实验中的 `without_edit_format_feedback`。它从冻结的 `progress_v4/autonomous_layered` 去掉事前编辑格式示例和事后格式纠错反馈，保留独立调查、证据交接、跨轮历史、进展提醒、语法检查和全部预算。结果为 Fixed50 45/50、Natural10 9/10，其中真实故障修复 4/5。原 v4 仍是既有组件实验的参照；JAX 和训练信号研究仍标明原 v4。v3、v5、v6、v7 保留为开发记录。

精简 v4 已以 `694f692` 合入实现仓库 `origin/main`，集成分支为 `codex/slim-v4-main-20260918`，远端工作树为 `/media/main/whj/projects/torch4ms/ascend-torch4ms-slim-v4-main-20260918`。`python -m autofix.autonomous` 和 `AgentConfig()` 默认采用当前配置。Linux 服务器运行 151 项测试通过，其中 2 项因前置条件跳过；11 次模拟模型请求与冻结组件配置逐项相同，涵盖诊断、交接、编辑拒绝和跨轮修复，没有调用 API。

## 冻结来源

以下路径位于历史实验目录 `/media/main/whj/projects/torch4ms/ascend-torch4ms-autonomous-verifier-20260917`，标识精简版所基于的原 v4 快照。实际已测精简配置由 `scripts/run_maintext_ablations.py::agent_class` 的两项覆盖定义，完整选定轨迹见 `output/maintext-ablations-20260918/recovery_final.json`。

| 任务组 | manifest 路径（相对实现目录） | SHA-256 |
| --- | --- | --- |
| Fixed50 | `experiments/autonomous_fixed50_20260917/progress_v4/manifest.json` | `d3c901416d98a465b341b0cece99c30902505339644ca1f0bd5ca7cf6870adec` |
| Natural10 | `experiments/autonomous_verifier_20260917/progress_v4/manifest.json` | `a1a01207eeb68b8754fd3daf4df9bafe5d7ee95978bca8f5bc95e27330c07ea0` |

共同设置为 `memory_policy=evidence`、`diagnosis_policy=evidence`、`workflow_policy=progress_loop`、语法检查开启。Verifier 自主读取代码和执行测试，Fixer 接收实际证据与诊断；故障真值、健康目标实现和评估方答案保持私有，不要求控制器根据预设类别选路。

模型请求固定 `deepseek-v4-flash`，现有响应标识为 `deepseek-flash`，thinking enabled、reasoning effort high。每条件最多 40 次调用、120,000 输出 token、1,800 秒和四次外部提交；每调用最多 16,384 输出 token，初诊与各修复阶段分别最多八次调用。请求 temperature 为 0，但推理模式下该参数无效，不能将运行视为确定性。

当前 610 条轨迹中工具证据压缩没有实际触发；v4 的机制名称使用“独立证据交接”，不把它的结果称为已验证的工具压缩收益。

## 版本与实验成本

v3 是首次完整自主比较；v4 增加预算内进展提醒和编辑格式辅助；v5 延长单次修复阶段；v6 允许修复阶段末次调用继续使用工具；v7 修正 v6 遗留的末次调用提示。版本名对应不同实现，不是多种后端模型。

v6、v7 各重新执行了 50+10 条完整条件。仅 v7 的选定完整运行就产生 1,197 次调用、51,242,146 tokens；两版含中断共有 2,575 次请求，已知至少 109,290,075 tokens，另有 54 次未知 usage。大部分 token 来自反复携带的输入上下文，不能按输出 token 或版本间差额估算新增消耗。没有账单单价和完整缓存计费信息时，不把 token 直接换算成人民币。

在 v6 全量启动前检查真实 checkpoint 请求，本可发现提示与工具行为冲突。该问题导致的重跑属于可避免的实施返工。后续提示或控制器改动先完成离线行为检查，再在固定小样本检查实际请求与流程；明确待验证主张和预算后才安排完整矩阵。已通过有效性核对的 baseline、源程序、首次候选和私有评分证据按实际变更范围复用。

本次 E/M/N 任务先审查分支 `codex/experiments-emn-integration` 的实现和已有结果，不因共享框架更新而自动启动全部实验。该分支的审查 commit 为 `c21dadcf6e5e82665fa163b90c9dccb1ea15c4ef`，独立 worktree 为 `/media/main/whj/projects/torch4ms/ascend-torch4ms-emn-audit-20260918`。

完整组件结果与成本来源见 [独立审查](component-final-version-cost-review-20260918.md)，结果表见 [实验汇总](maintext-results-20260918.md)。用户最新授权已包含论文正文与图表更新，以及 InterTrans 和有效 MatchFix 输入的补充比较。
