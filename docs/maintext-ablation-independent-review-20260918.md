# 新增消融独立审查，2026-09-18

审查截止时间为 2026-09-17 18:56 UTC（新加坡时间 9 月 18 日 02:56）。本次只读检查代码、冻结输入、已写出的真实请求和事件；没有调用模型 API，没有修改运行代码、输入或论文。运行仍在推进，下面的请求数是审查时快照。

## 发现

### P1：signal12 缺少初始执行正常的梯度错误条件

`scripts/run_signal_ablations.py:27` 选用 EX-01、NU-04、GR-07，各重复四次。冻结 `signal12_v3/plan.json:149` 的 GR-07 faulty 预检记录显示 `execution_passed=false`、空 measurements，异常为把 `[2,4]` 梯度赋给 `[4,3]` 参数。真正触发处是 `signal12_v3/execution/private_inputs/task_003/candidate.py:45`，随后第 46 行执行 `parameter.grad = grad.clone()`。这是候选生产代码抛出的异常，向模型显示它符合 execution-only 的定义。

对冻结预检 observation 实际调用三种纯 masking 函数，得到：

| 初始故障 | Execution | Execution + forward | All observations |
| --- | --- | --- | --- |
| EX-01 | 执行失败，AttributeError | 相同 | 相同 |
| NU-04 | 可用检查通过，无数值 | loss/output 最大差 0.4810836，失败 | 相同 |
| GR-07 | 执行失败，梯度尺寸 RuntimeError | 相同 | 相同 |

因此，最初的三个故障在 execution + forward 与 all observations 下没有额外梯度观测差异。四次重复也没有增加“执行正常但梯度错误”的故障覆盖。这个实验可以报告原始三种 fixture 上的反馈与停止策略效果；其结果无法单独支撑“加入梯度信号发现 execution + forward 漏检的初始故障”。修复后的后续状态仍可能产生不同梯度观测，故不应预先断言两组最终结果必然相同。

建议保留本轮原始 fixture 结果及该预检事实。若论文要估计增加梯度信号的独立作用，应另建有明确执行通过、前向通过、梯度失败预检的条件；不要把现有 GR-07 的生产异常隐藏成执行通过。

### P2：without_repair_history 的系统提示错误宣称历史仍被保留

`scripts/run_maintext_ablations.py:90` 在第二轮起恢复初始 handoff，并在第 92 行恢复初始 diagnosis；这确实删除了先前 repair 会话。冻结 `code_snapshot/autofix/autonomous/agent.py:72` 的 fixer 系统提示却仍写着 `Your conversation persists across repair attempts.`，未被该 treatment 改写。

真实证据为 `natural10_v3/without_repair_history/conditions/task_002/autonomous_layered/evidence/agent/call_0017_request.json:6`：系统提示保留上述声明。该请求第 118 行是 `Repair attempt 2`；它含 29 条消息、没有原生 tool-role 消息，保留初始 verifier handoff，没有第一轮 repair 指令或其工具会话。`fixed50_v3/without_repair_history/conditions/task_003/autonomous_layered/evidence/agent/call_0017_request.json` 有同样情况。

这会让模型被告知存在实际未提供的跨轮会话，混入“错误的记忆承诺”这一提示影响。后续版本应将该句改为准确说明当前提供的初始调查和最新观测；本轮必须按冻结配置保留，并在解释中说明此限制。

### 两项归因范围必须按实现表述

`continuous_role` 同时改变角色交接、消息归属与 provider reasoning 的保留。`scripts/run_maintext_ablations.py:74` 保留整个原会话；标准 handoff 的冻结 `agent.py:578` 将调查转为用户消息中的 verifier records，且第 586 行移除其中的 `reasoning_content`。真实第一次修复请求中，natural10 task_002 的 continuous_role 保留 7 条带 reasoning_content 的 assistant 消息；采用标准 handoff 的相同任务为 0 条。fixed50 task_001 分别为 8 条与 0 条。该条件衡量的是“连续原会话与独立证据交接”的整体差异，不能归因于角色名称或角色独立性这一个窄因素。

`without_edit_format_feedback` 同时移除事前格式示例和事后纠错：`scripts/run_maintext_ablations.py:108` 绕过增强 schema description，第 113 行取消格式错误后的额外反馈；标准增强位于冻结 `agent.py:814`。真实请求中该组 edit schema 没有 `Argument format ...` 示例，其他组保留。可以称为移除“编辑格式辅助”，不能仅解释成移除错误发生后的反馈。底层参数 schema、参数检查与语法事务保护仍在。

## 已排除的具体问题

continuous_role 没有被 verifier 系统提示永久禁止编辑。冻结 `agent.py:49` 的限制明确由 `During diagnosis` 限定；第 854 行仅在 `stage == "diagnose"` 时设置 readonly，第 861 行明确要求 repair。真实 `fixed50_v3/continuous_role/conditions/task_001/autonomous_layered/evidence/agent/call_0009_request.json` 提供允许修改 candidate 和 torch4ms 的 edit schema。`event_00105_tool.json:17` 记录 `ok=true`，第 28 行记录实际修改的 `torch4ms/tensor.py`。这是生产文件编辑的运行证据。

历史重置保留初始 verifier handoff、初始 diagnosis、当前生产文件和 scratch 文件，只撤回之前 repair 会话及其新假设。没有重置 `calls`、token 使用量或 `started`；审查时 natural10 的 6 个 reset 事件和 fixed50 的 1 个 reset 事件均记录 `lifetime_budget_reset=false`。证据上下文压缩器在每个请求内从实际传入 history 构造（冻结 `agent.py:734`），没有独立持久压缩缓存把已删除消息重新注入。保留工作区意味着本条件衡量“会话历史”，而非删除一切历史痕迹。

`without_progress_prompt` 在指定 checkpoint 插入后精确验证并弹出该条用户消息（本地脚本第 99 行），不改变预算、允许工具、final-summary 预留或阶段终止条件。冻结 `agent.py:1017` 至第 1043 行的控制逻辑仍执行。实际 omission 事件已出现，说明该处理已触发。

信号 masking 根据 observation 字段工作，不读取真实 fault ID 或归因。execution 与 execution_forward 重算顶层 `accepted` 及嵌套 `acceptance`（`scripts/run_signal_ablations.py:60`、第 75 行），不会保留隐藏全量验收的 false 标志。GR-07 的异常是合法执行证据，并非隐藏答案泄露。

`full_evaluation` 保存在宿主侧（本地脚本第 211 行），供第 186 行的最终重新计分使用。模型的测试工具只收到 masked observation（第 215 行）；控制器也只把 `current["observation"]` 传入 repair（冻结 `experiment.py:184`）。私有原始验收不作为修复触发器；最终 accepted 再用完整原始 predicate 评分，避免把“可用检查停止”当成真实修复成功。

截至扫描时，signal12 的 46 个实际请求中未发现 `full_evaluation`、`private_fixture`、原始/隔离预检字段或三个真实 fault ID。此时 all_observations 尚无已写出的请求，因此该组的请求级检查尚不可执行；其冻结 masker 和控制器路径已核对。自建 scratch 测试仍可主动测量额外信号（冻结 `fixed50.py:402`），所以信号条件控制的是默认公开测试反馈，不是禁止代理自行调查。

## 可比性与冻结检查

三个 v3 runner、11 个 variant manifest 及所有 `frozen_hashes.json` 登记文件均逐个 SHA-256 匹配：natural10 每组 489 个文件，fixed50 每组 2,329 个文件，signal12 每组 581 个文件。前两个研究的原始 control manifest 及 29 个记录源码哈希也均匹配。四个 component treatment 的 manifest 相对各自 control 只改变 `methods` 和 `ablation` 元数据。

本地 component runner SHA-256 为 `b06fb4d4fe7b8a8a625270330d1573b0cf714d6b2a22798b4b0c03542a86e087`；signal runner 为 `bfb6c1e898d44cae64136101bab1c41654f33a132e69e70a0001d1b658f80146`。本次核对的冻结版本与本地代码一致。

请求参数扫描覆盖当时 natural10 的 291 个、fixed50 的 339 个和 signal12 的 46 个请求。均请求 `deepseek-v4-flash`、thinking enabled、reasoning effort high，并省略 temperature。通常 `max_tokens=16384`；natural10 三个临近输出预算耗尽的请求分别降为 6051、1356、1250，与冻结 `agent.py:746` 的剩余预算裁剪一致。

远端证据根目录为 `/media/main/whj/projects/torch4ms/maintext-ablations-20260918/`。文中 v3 相对路径均基于此目录；引用的 `agent.py`、`experiment.py`、`fixed50.py` 是对应 variant 的 `code_snapshot/autofix/autonomous/` 文件。本记录只给出该次快照的有效性审查，不预判尚未完成条件的成功率。
