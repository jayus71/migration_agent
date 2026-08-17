# 实验完整性审计（Track A / Track B）

| 项目 | 值 |
|---|---|
| 审计日期 | 2026-07-31 |
| 审计对象 | `/tmp/ascend-torch4ms-track-b-20260801` @ `365652dcf9551bc97fc14464e05e225ccba544ad` |
| 远端位置 | `origin/codex/track-b-repair-baselines`（gitee `feixiao13/ascend-torch4ms`） |
| 对照文档 | `refine-logs/EXPERIMENT_PLAN.md`、`conference_101719.tex` |
| 审计方式 | 只读独立审计（`experiment-audit`），未修改任何文件，未运行测试 |
| 总判定 | **FAIL** |
| 落盘日期 | 2026-08-14（补录） |

> **补录说明**：这份审计原先只存在于 `.mindfs/sessions/1785541058-c888332928e8.jsonl` 会话日志中。
> `.mindfs/` 在 `.gitignore` 内，因此该结论从未进入版本控制，会话清理即永久丢失。
> 2026-08-14 的进度核查发现此问题并补录本文件。原始判定内容按原文保留，
> 每条另附**当前状态**，标注该问题此后是否已被解决。

## 六维判定

| 维度 | 判定 |
|---|---|
| A 真值 / 泄漏 | FAIL |
| B 指标归一化与统一 strict verifier | FAIL |
| C 结果完整性与 provenance | FAIL |
| D 死代码 / 绕过 / mock / 工具真实执行 | WARN–FAIL（外部工具确实真实运行） |
| E 公平性 | FAIL |
| F 范围 / 分类 | WARN–FAIL |

## 关键发现

### 1. Track A 不可复现

`experiments/baselines/track_a/*/{raw,candidates,logs}` 全部只含 `.gitkeep`，没有候选代码、执行日志或 `summary.json`。而 `track_a/overall_results.md:3` 声称结果来自五个 `summary.json`。Track A 的数字无法追溯到模型输出或 verifier 结果。

**当前状态：未解决。** Track A 未进入论文，因此不影响当前论文声明；但若要补进论文必须先补齐 raw artifact。

### 2. Track A strict 口径不可比

- 阈值定义：`T-DIRECT/verify_t_direct_candidate.py:27-29`
- 候选验证硬编码 `lr=1e-3`（`:300-303`），而 reference 用任务特定学习率（`:418-431`）
- MindSpore 验证把 `_grad_norm=None`（`:310-312`），无法做 paired 梯度等价判定
- `verify_section642_candidate.py:195-197` 的 strict 只含 compile + execution + training/update，不比较 loss、梯度或参数更新等价性
- `T-HIER/run_t_hier.py:487-500` 算出了 strict checker 结果，却在 `:497` 用内部 verifier 报告覆盖 `strict_success`

**当前状态：未解决。** 同上，仅在 Track A 补进论文时成为阻塞项。

### 3. Track B 的 strict success 不是统一语义门

- 候选 runner 直接取 `run_probe()` 布尔值：`autofix/faults/runner.py:34-42`
- 归一化只复制 `result["passed"]`：`autofix/faults/oracles.py:58-88`
- 外部方法的 stage 状态由 fault type 与总体 pass 合成，而非实测：`run_external_repair_pilot.py:360-367`
- `full_hier_fixed50/README.md:3-4` 声称六个方法共用同一 strict verifier，代码路径不支持该说法

**当前状态：未解决。** 论文当前措辞为 "fault-specific checks"，比 README 的说法准确，但 6 个方法未共用最终 verifier 这一点仍未在论文披露。

### 4. R-HIER 存在 private-oracle / 绕过路径

- GR-07 有确定性预期修复 payload：`autofix/examples/run_section63_feedback_ablation.py:327-349`
- R-HIER 直接调用 `_validate_candidate()` 并以 `"source": "autograd_optimizer_private_oracle"` 标记成功：`:517-543`
- 校验器自身执行 private preflight / patch 评估：`autofix/faults/core_optimizer_mapping.py:154-200`
- 证据：`full_hier_fixed50/r_hier/raw/GR-07-A.json:55-131`

**当前状态：部分澄清（2026-08-14 复核）。**
- 硬编码 payload（`_core_mock_payload`）只在 `AUTOFIX_FIXER_LLM_ENABLED=0` 分支生效（调用点 `:483`）。论文采用的 6.3 结果包记录 `mode=real_llm`，GR-07 由真实 LLM 修复通过。**该 mock 未污染论文数字。**
- private-oracle 路径在 Fixed50 的 50 个实例中有 14 个涉及。复核 `GR-07-A.json` 显示它是一条 `recommended_validation` 校验命令加 preflight 作用域门控，patch 仍由真实 LLM 生成（该实例 `reasoning_tokens=1400`），并非把答案直接写入。
- 但这仍是外部方法不具备的内部通道，**尚未在论文披露**。

### 5. TorchAX/JAX 迁移声明不被 runner 支撑

旧 Section 6.7 runner `experiments/paper_section_67/run_section67_fixer_torchax.py:25-27,76-121` import 并执行 `torch4ms`、`Torch4msOptimizer`、`torch4ms.default_env`，**从未 import TorchAX 或 JAX**。"故障"只是触发异常、加 loss 偏置或跳过更新的标记位。`autofix/faults/injection.py:114-126` 明确标注为 `torchax_compat` 兼容适配器。判定 C2 **unsupported**。

**当前状态：已解决（本项目最重要的一次修复）。** 2026-08-11 的 Track C 工作重建了该实验：
`experiments/paper_section_67/run_track_c_baselines.py` 真实 import `autofix.backends.torchax_backend`、
`autofix.verifiers.paired_torchax`、`autofix.agents.fixer_torchax`，使用 JAX 自动微分与 Optax，**不再 import torch4ms**。
论文已改用 Track C 结果（`tab:track-c`），旧 6.7 表格已从论文移除。
数据位置：`origin/codex/track-c-torchax-autofix`。

### 6. T-MSA 改变了模型语义

`T-MSA/run_t_msa.py:42-59` 把 `CrossEntropyLoss` 的 reduction 从 mean 改成 sum，超出"仅启用兼容层"的范围，违反计划的统一适配器要求。

**当前状态：未解决。** Track A 未进论文，暂不影响；补进论文前必须移除该改动。

### 7. 公平性与 provenance 不一致

- Fixed50 算术自洽：R-EXEC 33/50、R-FLAT 34/50、R-HIER 50/50、Direct 40/50、SWE 46/50、MatchFix 47/50；每方法 50 行，`instances.csv` 300 行
- Token 预算差异显著（`summary.json:96-173`）：R-HIER 190,588；Direct 1,582,865；MatchFix 5,205,141；SWE 7,635,016
- commit provenance 四处冲突：计划 `f66caf...`、审计 HEAD `365652d...`、summary `3454be4...`、README 复现 `3aaafd...`
- `run_status.tsv` 记录 `r_flat` 与 `r_exec` 非零退出码，summary 仍被采纳

**当前状态：部分解决。** 算术已由 2026-08-14 核查再次确认，论文主表数字与原始 CSV 完全一致。
Token 预算差异与 provenance 冲突**仍未在论文或索引中披露**。

### 8. 外部方法泄漏细节

- MatchFixAgent 直接拿到 healthy 实现片段作为 `source_function`：`run_external_repair_pilot.py:932-934,959-967`
- SWE-agent 的 workspace 被写入 `healthy_probe.py`（`:326-333`，经 `redact_fault_identity` 处理）
- 外部 task/project ID 内嵌 fault ID 与类型：`:281-287`、`:944-967`

**当前状态：未解决，且已产生具体风险。** MatchFixAgent 因此被排除出论文主表，
但**排除理由从未记录在任何版本控制文件中**。artifact 中留有一个 47/50（高于论文采用的 SWE-agent 46/50）
的更强 baseline 而无任何说明。见 `PROJECT_STATUS_CONCLUSION.md` §4.3。

### 9. Trace / artifact 状态

- SWE-agent 有 74 个 `r_swe/tool_runs/**.trace.log` 和 50 个 patch — 真实运行
- MatchFix 有 tool-run 输入输出和 50 个 episode — 真实运行
- Direct LLM 有原始响应 JSON — 真实运行
- Track A 无任何对应 raw trace
- 内部 R-EXEC/R-FLAT/R-HIER 有 raw/candidate JSON，但 pass 语义仍是 probe/oracle 特定的

## 原判定的 claim 影响

| Claim | 原判定 |
|---|---|
| C1 层级 vs flat 的因果改进 | unsupported（private-oracle 路径 + 无统一最终门） |
| 46/50 strict success | 算术支持为 controlled-probe 结果，但不等于文档所述的完整语义 strict success |
| Track A 公开 baseline 对比 | unverifiable / unsupported |
| C2 TorchAX/JAX 迁移 | unsupported（按当时的 6.7 实现） |
| C3 公开方法对比 | 需大幅限定（泄漏、预算不均、provenance 冲突、Track A 证据缺失） |

## 补录时点的状态汇总（2026-08-14）

| 发现 | 状态 |
|---|---|
| 5 TorchAX/JAX 声明无支撑 | **已解决**（Track C 重建实验，论文已改用） |
| 4 GR-07 硬编码 mock 污染论文 | **已澄清不成立**（mock 仅在 LLM 关闭时生效；论文结果为 real_llm） |
| 7 Fixed50 算术 | **已再次确认正确** |
| 1、2、6 Track A 可复现性与口径 | 未解决（Track A 未进论文） |
| 3 无统一 strict verifier | 未解决，未披露 |
| 4 private-oracle 内部通道（14/50） | 未解决，未披露 |
| 7 token 预算差异、provenance 冲突 | 未解决，未披露 |
| 8 MatchFixAgent 泄漏与排除理由 | 排除理由已于本次补录（本文件 + 结论文件） |
