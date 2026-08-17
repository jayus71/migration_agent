# Experiment Tracker

**状态更新：2026-08-14。** 原表（2026-07-23 建立）所有条目仍标记为 `TODO`，已完全过时。
下表按实际结果重建。数据分支见 `paper_experiment_results_index.md`。

## Track A — 迁移赛道

| Run ID | Baseline | 任务 | Status | 结果 | 在论文中 |
|---|---|---|---|---|---|
| `M001` | Direct LLM (`T-DIRECT`) | 5 models x 3 | DONE | strict 0/15 (0.0%)；compile 26.7%、exec 20.0% | 否 |
| `M002` | CodeTransEngine Direct (`T-CTE`) | 5 models x 3 | DONE | strict 0/15 (0.0%)；compile 13.3% | 否 |
| `M003` | X2MindSpore (`T-X2MS`) | 5 models | DONE | strict 0/15 (0.0%)；compile/exec 100% | 否 |
| `M004` | MSAdapter v0.6.0 (`T-MSA`) | 5 models x 3 seeds | DONE | strict 0/15 (0.0%)；compile/exec 100% | 否 |
| `M005` | Full Translator + Fixer (`T-HIER`) | 5 models x 3 | DONE | strict **15/15 (100.0%)** | 否 |

Track A 已跑完但**未进入论文**，2026-08-14 复核后确认当前状态下不可用（不是过度防御，
是结果本身不可辩护）：

1. **T-HIER 与 baseline 不同门**：`run_t_hier.py:487-497` 调用了 strict verifier 并写入
   `final_strict_verification.json`，但 `:497` 用内部诊断报告覆盖了它；四个 baseline 走
   paired metric checker。100% vs 0% 是两套标准的对比。
2. **T-MSA 的 0% 是 harness 改出来的**：`run_t_msa.py:47-56` 强制 `reduction="sum"` 并
   显式拦截 `mean`，而 reference 用 mean，`loss diff <= 0.02` 必然失败。
3. **raw artifact 全缺**：五个目录的 `raw/`、`candidates/`、`logs/` 只有 `.gitkeep`，
   `summary.json` 一个都不存在。

修复路径见 `PROJECT_STATUS_CONCLUSION.md` §6，需重跑，需 MindSpore/CANN 环境。
审计对应条目：`EXPERIMENT_INTEGRITY_AUDIT_20260731.md` §1、§2、§6。

## Track B — 修复赛道 Fixed50

| Run ID | Baseline | 实例 | Status | Verified | R@1 | R@2 | R@4 | Tokens | 在论文中 |
|---|---|---|---|---|---|---|---|---|---|
| `R102`/`R002` | Execution-only (`R-EXEC`) | 50 | DONE | 33/50 (66.0%) | 58.0% | 64.0% | 66.0% | 154,738 | 是 |
| `R102` | Flat Semantic (`R-FLAT`) | 50 | DONE | 34/50 (68.0%) | 66.0% | 66.0% | 68.0% | 180,465 | 是 |
| `R101` | Direct LLM Repair | 50 | DONE | 40/50 (80.0%) | 72.0% | 76.0% | 80.0% | 1,582,865 | 是 |
| `R104` | SWE-agent v1.1.0 | 50 | DONE | 46/50 (92.0%) | 72.0% | 84.0% | 92.0% | 7,635,016 | 是 |
| `R103` | MatchFixAgent `66a52a5` | 50 | DONE | **47/50 (94.0%)** | 74.0% | 86.0% | 94.0% | 5,205,141 | 是（2026-08-14 补入） |
| `R105` | Full Hierarchical (`R-HIER`) | 50 | DONE | **50/50 (100.0%)** | 84.0% | 98.0% | 100.0% | 190,588 | 是 |

MatchFixAgent 是最强外部 baseline（47/50，高于 SWE-agent 的 46/50）。适配器直接把 healthy
实现片段作为 `source_function` 交给它（`run_external_repair_pilot.py:932-934,959-967`），
属 oracle 泄漏。**2026-08-14 已补入论文主表**，并以 dagger 脚注说明该泄漏，其成功率按上界
（upper bound）而非盲修复结果呈现。同时补入 token 列：R-HIER 0.19M 对 MatchFix 5.21M、
SWE-agent 7.64M。

## Track C — PyTorch→JAX

| Run ID | Baseline | 任务 | Status | 结果 | 在论文中 |
|---|---|---|---|---|---|
| `X003` | Full TorchAX (`c_hier`) | MLP/CNN, 6 faults | DONE | **6/6**，均一轮完成 | 是 |
| — | Direct LLM (`c_direct`) | 6 faults | DONE | 5/6（TC-CNN-NU 失败） | 是 |
| `X001` | Ivy (`c_ivy`) | 6 faults | DONE | 0/6 | 是 |
| `X002` | torch2jax (`c_torch2jax`) | 6 faults | DONE | 0/6 | 是 |

Track C 的 runner 真实使用 TorchAX + JAX + Optax，解决了旧 6.7 实现的核心问题
（审计 §5）。这是本项目最重要的一次修复。

## 其他已完成实验（论文 6.3–6.6）

| 实验 | Status | 结果 |
|---|---|---|
| 6.3 反馈粒度消融 | DONE | `4/12 -> 8/12 -> 12/12`，real LLM |
| 6.4.1 多作用域 Fixer-guide | DONE | 24 base tasks / 96 condition runs |
| 6.4.2 Translator-guide | DONE | guide off 0/15 → guide on 15/15 |
| 6.5.1 信号有效性 | DONE | 36 组全部命中预期信号 |
| 6.6 50-step 训练一致性 | DONE | 4 labels x 3 seeds x 50 steps |

## Final Checklist

- [x] 5 个迁移任务均已分配并跑完（Track A）
- [x] 12-task repair pilot 已完成
- [x] Flat Semantic Feedback 已实现并运行（`R-FLAT`）
- [x] pilot 通过的方法已扩展到 Fixed50
- [x] Track B/C 保留候选代码、版本和原始日志
- [ ] **Track A 未保留 raw 日志与候选代码**（只有 `.gitkeep`）
- [x] 未把 unsupported 样本从分母中删除（Ivy/torch2jax 的 0/6 留在分母内）
- [x] 未对单个输出进行人工修复

## 未解决项

1. Track A raw artifact 缺失，无法复现。
2. 六个 Track B 方法未共用同一最终 verifier，论文未披露。
3. R-HIER 在 50 个实例中有 14 个经过 private-oracle 校验路径，论文未披露。
4. Token 预算差异（R-HIER 190k vs SWE 7.6M）未在论文出现。
5. commit provenance 四处不一致（计划 `f66caf`、Track B HEAD `365652d`、summary `3454be4`、README `3aaafd`）。
6. 论文仓 submodule 指针 `f66cafe` 早于 Track A/B/C 数据。
