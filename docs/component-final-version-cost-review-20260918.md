# 组件最终结果、版本选择与新增成本审查

2026-09-18 05:19 UTC 只读核对完成。依据远端 `maintext-ablations-20260918/reports/recovery_final.json`（生成时间 05:18:38 UTC）、143 条 recovery plan 及其原始 result/request/event，以及本地 `output/autonomous-verifier-20260917/autonomous_recovery_comparison_final.json`。未启动实验、API、汇总器或修改运行目录与论文。

## 四项组件结果

四项条件均以冻结的 progress_v4/autonomous_layered 为对照，模型固定 DeepSeek。Fixed50 的 50 条全部初始失败；Natural10 有五条初始健康、五条初始失败，表中自然修复数只计算后者。

| 条件 | Fixed50 接受 | Natural10 接受 | 自然初始失败修复 | 两组所选运行 tokens |
| --- | ---: | ---: | ---: | ---: |
| v4 对照 | 41/50 | 9/10 | 4/5 | 53,576,201 |
| 连续原会话 | 44/50 | 8/10 | 3/5 | 53,756,911 |
| 无 repair 会话历史，修正提示版 | 37/50 | 5/10 | 0/5 | 42,728,083 |
| 无进展提示 | 46/50 | 7/10 | 2/5 | 62,462,551 |
| 无编辑格式辅助 | 45/50 | 9/10 | 4/5 | 53,189,707 |

全部自然组保留了五条健康候选。自然任务直接复用原 Experiment I 的现成初始翻译：manifest 记录 `no_fault_injection=true`、`translation_reused=true`，任务来源指向 `runs_real_core_v3/tasks/I-xx/translation`。没有为本次自然任务人工注入故障，也没有重新调用翻译模型。

结果支持会话历史在本轮任务上的作用；其余机制表现随数据集变化。无进展提示在 Fixed50 多接受五例、自然故障少修复两例。无格式辅助在 Fixed50 多接受四例，自然结果相同。不能据此写成每项组件都提高成功率。这些是开发任务上的单次比较，没有独立测试集或显著性结论。

各条件的固定差异为：连续原会话取消独立证据交接，同时保留原消息归属和 provider reasoning；无历史在每轮修复前恢复初始 verifier handoff，保留当前工作区、最新观测和累计预算；无进展提示仅删除连续读取后的软提醒；无格式辅助同时移除事前格式示例与事后 schema 纠错，保留底层 schema 和语法事务保护。后三者与前者都不应被重新命名成更窄的因果因素。

## 历史修正与最终恢复

恢复批次 143/143 完成，合并原有效结果后为 276/276：200 个 Fixed50 组件条件、40 个 Natural10 组件条件、36 个旧 signal12 条件。最终报告 `ledger_mismatches=0`、`treatment_violations=0`，所有所选运行 unknown usage 为 0。

143 条包含 83 条基础设施错误恢复（Fixed50 71、Natural10 1、旧 signal12 11）和 60 条历史提示修正后的完整条件重跑（50+10）。逐一读取 83 条对应原 result，全部确为 infrastructure_error，没有将 completed 的功能失败选入恢复。因此恢复没有全量重跑所有组件或只挑功能失败追加机会。

历史条件的 60 条属于实际全量补跑。原实现删去历史，却在系统提示宣称历史跨轮保留；修正后必须整组采用一致协议，不能拼接旧、新提示下的任务成绩。该组新增成本为 42,728,083 tokens。此前结果与费用均保留在 all-attempts 账本中。

代表性真实第二轮请求：

- `recovery_round1/fixed50_history_v4/without_repair_history/conditions/task_003/autonomous_layered/evidence/agent/call_0017_request.json`。
- `recovery_round1/natural10_history_v4/without_repair_history/conditions/task_002/autonomous_layered/evidence/agent/call_0017_request.json`。

两者已移除 `Your conversation persists across repair attempts.`，系统提示明确每轮从初始调查和最新观测开始，不保留早期 repair 会话但保留工作区。请求只含本轮 `Repair attempt 2` 指令，没有先前 repair 指令。Fixed50 的 51 个、Natural10 的 15 个 history-reset 事件全部记录 lifetime_budget_reset=false。

143 条本次实际新增调用为 3,158 次，prompt 112,639,008、completion 5,133,265，共 117,772,273 tokens，未知 usage 为 0。合并报告的 276 个所选条件合计 223,330,971 tokens；包含被替换旧 episode 后已知为 252,885,419 tokens，另有 108 个未知 usage 调用。因此后者只是实际总成本的已知下界，未知值不能当作零。

旧 signal12 最终为 8/12、12/12、12/12，仍是三 fixture 各四次重复；它不具备初始执行通过的梯度专属故障。新增训练信号研究另有 64 条及独立审查，不并入这里的 276 条组件恢复统计。

## v6 与 v7 的真实新增成本

本地最终比较 JSON 的 Fixed50 与 Natural10 账本相加，与父代理提供数值一致：

| 版本 | 新条件数 | 所选调用 | 所选 tokens | 中断调用 | 中断已知 tokens | 中断未知 usage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| productive_v6 | 60 | 1,149 | 50,364,246 | 103 | 2,897,030 | 24 |
| productive_v7 | 60 | 1,197 | 51,242,146 | 126 | 4,786,653 | 30 |

两版合计真实新增 120 个完整条件、2,346 次所选调用、101,606,392 个所选 tokens。再计中断 episode，共 2,575 次请求、至少 109,290,075 tokens，54 次 usage 未知。v7 相对 v6 的完整所选运行多 877,900 tokens，但 v7 本身新增消耗为 51,242,146 tokens，不能只把差额当作成本。

v4→v6 的固定变化是修复阶段最后一次调用继续开放工具，不再强制无工具总结；初诊仍预留最后报告，修复阶段八次调用、总 40 次调用、四次尝试、120,000 输出 token 和 evidence memory 等设置不变。v6 的进展提示遗留“最后调用用于总结”，与其工具供给冲突。

直接比较冻结 `productive_v6/code_snapshot/autofix/autonomous/agent.py` 与 v7，差异仅为第 1043 行附近新增的四行提示替换。真实 v6 `task_027/.../call_0014_request.json` 仍说最后调用留给总结；v7 `task_001/.../call_0014_request.json` 改为最后调用可应用或测试修复。

| 版本 | Fixed50 | Natural10 | 自然故障实际修复 |
| --- | ---: | ---: | ---: |
| v4 | 41/50 | 9/10 | 4/5 |
| v6 | 45/50 | 9/10 | 4/5 |
| v7 | 44/50 | 7/10 | 2/5 |

v6/v7 确实各全量运行了 50+10 条，不是只补中断，也不是复用 v4 结果。v6 有提示实施缺陷，v7 的完整重跑是为了获得统一修正协议的数据；该返工成本由缺陷造成，应明确承认。现有证据不能把它描述成“没有重复开销”。在启动完整 v6 前核对真实 repair checkpoint 请求，本可先发现冲突，减少这次返工。

若选择 productive-loop 协议，应采用提示与工具一致的 v7，并保留 v6 为开发与成本记录。不能因 v6 分数较高而替换 v7，也不能拼接各版本逐任务最佳结果。四项组件实验的对照仍固定 v4，因为它们从 v4 输入和实现构造；不能直接把它们当作针对 v7 的消融。当前整理任务无需再次运行任何版本。
