# 附录 B 逐句与表格审查报告

审查版本：`d1d6a53`。本报告仅依据本轮提供的完整文本快照，采用所附 AGENTS.md、humanizer 和 Academic-Writing-DNA 的表达要求，并以 2026-09-23 最新用户意见为准。未调用工具、读取其他文件、修改文件、编译论文或运行实验。下文全部修改均为候选方案，尚未实施。

主要问题集中在三处：50 个任务标识与 29 个不同输入之间切换不够清楚；两组组件实验的参照配置容易混淆；接入基线 agent 的结果使用了含糊的 `repair count` 和 `preservation consequences`。现有数字应全部保留，修改重点是让读者看清实验对象、实际改变的组件和结果统计口径。

## 1. 审查范围与覆盖数

| 对象 | 准确源文件与行号 | 覆盖数 |
|---|---|---:|
| 附录 B 标题 | `sections/supplementary_experiments.tex:88` | 1 个标题 |
| 第一组组件实验定义 | 同文件第 91 行 | 5 句 |
| 第一组组件实验分析 | 同文件第 106 行 | 4 句 |
| 十份初译程序的组件实验 | 同文件第 108 行 | 6 句 |
| 基线 agent 接入实验 | 同文件第 120 行 | 8 句 |
| 两张表的 caption | 同文件第 94、111 行 | 4 句 |
| 第一张表的表注 | 同文件第 102 行 | 2 句 |
| 共同 MindSpore 集合组件表 | `figures/TABLE_unified_components.tex:3–12` | 3 个列头、8 个条件行、16 个数值单元 |
| 十份初译程序组件表 | `figures/TABLE_natural_components.tex:3–9` | 5 个列头、5 个条件行、20 个数值单元 |

共覆盖 **23 句正文、4 句图表说明、2 句表注，合计 29 个句子单元**；另覆盖标题、两张表的全部列头和条件行。本节没有公式、图或算法。

LaTeX 的标签、表格引用、输入路径和排版命令已纳入文本范围核对；其余非内容性命令不另计句子。当前快照不包含生成器实现及实验原始记录，涉及实现细节的待核对项单独列在末尾。

本报告使用意见清单已有 ID；“最新意见 6”等指本轮用户列出的九项最新要求，不新增正式意见 ID。

## 2. 逐句台账

### 2.1 标题与实验定义

| 局部编号 | 短引文与位置 | 处理建议 | 理由与对应意见 |
|---|---|---|---|
| B-H01 | “Evidence Handoff and Agent Integration”，第 88 行 | 保留 | 标题覆盖证据交接及向两个基线 agent 接入调查的内容；没有夸大研究范围。 |
| B-S01 | “shares the main collection … cumulative budgets”，第 91 行第 1 句 | 改写 | 明确为主要比较中的 50 个 MindSpore 任务标识；`main collection` 和 `cumulative budgets` 连用过于依赖前文。对应 B04、W03、W07。 |
| B-S02 | “Continuing the original conversation retains its message roles …”，第 91 行第 2 句 | 改写；消息角色细节移来源记录 | 需要解释调查与修复使用同一对话，以及保留历史。`original conversation` 指代不清，消息角色属于实现记录。对应 W03、W06、M14。 |
| B-S03 | “Independent evidence handoff supplies …”，第 91 行第 3 句 | 保留 | 明确交接对象、证据来源及独立修复对话，信息充分，机制准确。对应 B03、W01。 |
| B-S04 | “Removing repair history restarts each subsequent repair attempt …”，第 91 行第 4 句 | 改写 | `restarts` 容易被理解为重启执行或恢复初始文件。应明确重置的是后续修复的上下文，当前文件与累计预算保留。对应 W03、W07、B04。 |
| B-S05 | “Removing progress reminders preserves …”，第 91 行第 5 句 | 改写 | 直接表达关闭提醒后调用和提交上限不变；提醒的实际内容在快照中仍未定义，留主代理核对。对应 B04、W03。 |

### 2.2 第一组结果

| 局部编号 | 短引文与位置 | 处理建议 | 理由与对应意见 |
|---|---|---|---|
| B-S06 | “LaDiM accepts all 50 identifiers … 49”，第 106 行第 1 句 | 改写 | 两个结果均直接写出分母，并把 `continuous conversation` 对应到调查与修复共用对话。对应 W07、B04。 |
| B-S07 | “Removing repair history or progress reminders preserves full acceptance …”，第 106 行第 2 句 | 改写 | 明确是两个分别移除组件的条件，各为 50/50；直接给出接受数并指明 token 比较对象。对应 W02、W07、B04。 |
| B-S08 | “Twenty distinct initial translations … two of the nine failing inputs …”，第 106 行第 3 句 | 改写并拆句 | 当前突然从 50 转为 20 和 9，未就地解释 29 个不同输入与任务别名的关系；`pass the initial checks` 应改为首次评估通过。对应最新意见 6、W03、W07。 |
| B-S09 | “Most cases therefore finish before …”，第 106 行第 4 句 | 保留解释，最小改写 | 该句把实验构成与历史发挥作用的机会联系起来，有解释价值。将 `cases`、`finish` 换成明确的输入和接受状态，不增加历史无效的普遍结论。对应 W02、B06。 |

### 2.3 十份初译程序的组件实验

| 局部编号 | 短引文与位置 | 处理建议 | 理由与对应意见 |
|---|---|---|---|
| B-S10 | “The component study on saved initial translations …”，第 108 行第 1 句 | 改写 | 用初次翻译得到的十份程序解释对象；保留支持库访问范围。已有意见 B03 支持明确允许修改支持库。对应最新意见 6、B02、B03。 |
| B-S11 | “Its reference configuration includes examples …”，第 108 行第 2 句 | 改写 | 内容必须保留；需明确参照配置对应表中 `Independent evidence handoff` 行，避免与第一张表的 LaDiM 配置混淆。对应 B04、W07。 |
| B-S12 | “Each condition changes the named component …”，第 108 行第 3 句 | 保留 | 清楚说明各条件共享程序、访问权限、验收与预算。`named component` 可由表中条件名识别，无需再造分类。对应 B04、W07。 |
| B-S13 | “Removing this format assistance gives … translation error comparison”，第 108 行第 4 句 | 改写 | 用明确的格式辅助内容和现有表引用说明配置关系，替换较宽泛的 `translation error comparison`。对应 W03、B04、B06。 |
| B-S14 | “Table … adds … to the three rows in the main ablation table”，第 108 行第 5 句 | 移来源记录 | 只描述主文与附录选取了哪些行；完整五行已在下表呈现，科学信息没有增加。对应 W06。 |
| B-S15 | “All conditions preserve the five initially passing programs”，第 108 行第 6 句 | 保留 | 五个条件均为 5/5，陈述准确，并交代修复对正确程序的影响。对应 W02、W07、B06。 |

### 2.4 向基线 agent 接入调查

| 局部编号 | 短引文与位置 | 处理建议 | 理由与对应意见 |
|---|---|---|---|
| B-S16 | “The host-integration conditions prepend …”，第 120 行第 1 句 | 改写 | `host-integration`、`prepend` 带有接口描述色彩；直接说明在 SWE-agent 或 MatchFixAgent 修复前加入不修改代码的调查。对应 W03、W04、W06。 |
| B-S17 | “Investigation calls share the host’s total … limits”，第 120 行第 2 句 | 改写 | `share` 未直接说明预算占用；应表达调查计入同一个调用、token 和时间上限。对应 W07、B04。 |
| B-S18 | “The native host retains its own history …”，第 120 行第 3 句 | 改写 | 用基线 agent 替换未定义的 `native host`；保留其历史与修复策略不变这一实质条件。对应 W03、B04。 |
| B-S19 | “MatchFixAgent with investigation retains 50/50 …”，第 120 行第 4 句 | 保留 | 比较明确，保留接受表现与成本上升两项真实结果。对应 W02、W07、B06。 |
| B-S20 | “SWE-agent … 43/50, compared with 44/50 and one interrupted task …”，第 120 行第 5 句 | 改写 | `44/50 and one interrupted task` 容易被读成另有一个任务；中断任务归属及分母处理集中在表注解释。对应 W07。 |
| B-S21 | “increases SWE-agent’s repair count from seven to eight …”，第 120 行第 6 句 | 改写 | `repair count` 容易与修复调用数混淆；这里是九个不同的初始错误输入中成功修复的程序数。对应 W03、W07、最新意见 6。 |
| B-S22 | “It also leaves four initially accepted programs failing …”，第 120 行第 7 句 | 改写 | 明确四个属于 20 个不同的初始通过输入，指的是加入调查后的最终评估结果。对应 W07、最新意见 6。 |
| B-S23 | “records both the repair and preservation consequences …”，第 120 行第 8 句 | 改写 | 将抽象的 `consequences` 改成最终接受数实际包含的两类结果，使该句承担指标解释。对应 W03、B04。 |

### 2.5 表题与表注

| 局部编号 | 短引文与位置 | 处理建议 | 理由与对应意见 |
|---|---|---|---|
| B-C01 | “Complete component and host-integration comparison …”，第 94 行第 1 句 | 改写 | 直接说明比较组件变体以及向基线 agent 加入调查；明确为 50 个任务标识。对应 W03、W04、B04。 |
| B-C02 | “Token totals include initial translation and all subsequent calls”，第 94 行第 2 句 | 保留 | 明确完整迁移成本包含初译与后续调用。对应 W07。 |
| B-N01 | “Includes one task with unavailable final acceptance …”，第 102 行第 1 句 | 改写 | 点明是原生 SWE-agent 条件的中断任务；保持其仍计入分母与实际成本的口径。对应 W07。 |
| B-N02 | “Each condition uses the input reuse described …”，第 102 行第 2 句 | 改写 | `input reuse` 是含糊的来源术语；应简要说明不同输入、任务别名和成本只计一次的关系。对应 W03、W06、W07。 |
| B-C03 | “Complete component results on saved initial translations”，第 111 行第 1 句 | 改写 | 直接写十份初次翻译得到的程序；与 B-S10 一致。对应最新意见 6、B02。 |
| B-C04 | “Repair tokens cover all ten runs, including investigation and failed attempts”，第 111 行第 2 句 | 改写 | 实际成本包括调查和修复，当前列名只写 `Repair tokens`；正文、caption 与列头需要共同澄清。对应 W07、B04。 |

## 3. 需调整项与具体英文候选

以下候选按同段信息关系组织。保留项不因统一文风而强制改写；候选不改变已有主张、数值、预算或实验分组。

### 3.1 明确第一组实验及组件操作

**涉及 B-S01、B-S02；第 91 行。**

原句：

> The component study shares the main collection, initial translations, acceptance checks, and cumulative budgets. Continuing the original conversation retains its message roles and reasoning history when the agent begins editing.

问题：`main collection` 缺少就地识别；`original conversation` 未说明调查与修复的关系；`message roles` 对理解组件作用的贡献较小。

英文候选：

> We evaluate these component variants on the same 50 MindSpore task identifiers, initial translations, acceptance checks, and budgets as the main comparison. The continuous conversation condition keeps investigation and repair in one conversation, retaining the earlier messages and reasoning history.

消息角色的保存细节移至该组件的实现来源记录；不得据此改变实现。对应 B04、W03、W06、W07、M14。

**涉及 B-S04；第 91 行。**

原句：

> Removing repair history restarts each subsequent repair attempt from the initial investigation and latest observation, while retaining the current files and cumulative budget.

问题：`restarts each subsequent repair attempt` 容易引出重新执行调查、恢复文件或重启 Verifier 的误读。快照支持的是后续修复不携带先前修复历史。

英文候选：

> Without repair history, the context for each repair attempt after the first is reset to the initial investigation and latest observation. The current files and cumulative budget are retained.

对应 W03、W07、B04。该候选不增加 Verifier 重启、重新调查或固定诊断路线。实际上下文包含哪些消息，由主代理根据冻结实现核对。

**涉及 B-S05；第 91 行。**

原句：

> Removing progress reminders preserves the call and submission limits.

英文候选：

> Disabling progress reminders leaves the call and submission limits unchanged.

对应 W03、B04。此处可以直接改清“不改变预算”的事实；提醒究竟包含什么内容，现有快照未说明，不补写“剩余预算提醒”等推测。

### 3.2 解释 50 个任务标识与 29 个不同输入

**涉及 B-S06、B-S07；第 106 行。**

原句：

> LaDiM accepts all 50 identifiers, while the continuous conversation accepts 49. Removing repair history or progress reminders preserves full acceptance and uses fewer tokens.

英文候选：

> LaDiM accepts 50/50 task identifiers, compared with 49/50 when investigation and repair share one conversation. The variants without repair history and without progress reminders each accept 50/50 while using fewer tokens than LaDiM.

对应 W02、W07、B04。分别移除两个组件的实验仍保持独立，不改写成同时移除二者。

**涉及 B-S08、B-S09；第 106 行。**

原句：

> Twenty distinct initial translations pass the initial checks, and only two of the nine failing inputs require a second repair submission under the complete method. Most cases therefore finish before a later repair attempt can use earlier repair history.

问题：读者刚看到 50，随即遇到 20 与 9；`initial checks`、`complete method` 和 `cases` 都需要更明确的对象。

英文候选：

> The 50 task identifiers represent 29 distinct migration inputs. Of these, 20 initial translations pass their first evaluation and need no repair. Of the nine that fail, only two require a second repair submission under LaDiM. Most inputs are therefore accepted before a later repair attempt can use earlier repair history.

对应 W03、W07、B04、最新意见 6。

其中 29 来自所附来源说明，20 和 9 来自本节及来源说明。`require a second repair submission` 保留原文的“需要”口径，不能据此补写实际总共执行了多少次提交。最后一句保留原有机制解释，不扩展为修复历史普遍无效。

### 3.3 明确十份初译程序的参照配置

**涉及 B-S10、B-S11；第 108 行。**

原句：

> The component study on saved initial translations uses the same ten candidates as Table~\ref{tab:natural-repairs}, including access to their supporting libraries. Its reference configuration includes examples of the edit format and corrective feedback for malformed edits.

英文候选：

> The second component study uses the same ten programs produced by initial translation as Table~\ref{tab:natural-repairs} and allows edits to their supporting libraries. The reference condition, labeled Independent evidence handoff in Table~\ref{tab:natural-components}, includes examples of the edit format and corrective feedback for malformed edits.

对应 B02、B03、B04、W07、最新意见 6。

“允许修改支持库”得到意见清单 B03 的明确支持；不增加支持库以外的可编辑范围。这里应保留格式示例与格式纠正的配置条件，因为它决定该参照行与自然错误比较中 LaDiM 行的对应关系。

**涉及 B-S13；第 108 行。**

原句：

> Removing this format assistance gives the LaDiM configuration reported in the translation error comparison.

英文候选：

> Removing the edit examples and format correction gives the LaDiM configuration reported in Table~\ref{tab:natural-repairs}.

对应 W03、W07、B04、B06。候选仅展开本段已定义的辅助内容，并给出准确交叉引用。

**涉及 B-S14；第 108 行。**

原句：

> Table~\ref{tab:natural-components} adds the progress reminder and editing assistance conditions to the three rows in the main ablation table.

建议：从论文段落移至来源说明。`data/paper_figures/README.md` 已记载主文组件面板选择前三行，因此不必再重复添加同义记录；只需确认该记录与最终表格选行一致。

对应 W06。完整五行结果继续保留，主文采用十份初译程序组件分组的安排继续保留。

### 3.4 用实际动作说明基线接入实验

**涉及 B-S16–B-S18；第 120 行。**

原句：

> The host-integration conditions prepend the same read-only investigation to SWE-agent or MatchFixAgent. Investigation calls share the host's total call, token, and time limits. The native host retains its own history and repair policy.

英文候选：

> For SWE-agent and MatchFixAgent, we add the same investigation before repair, with code editing disabled during investigation. The investigation counts toward each baseline agent's total call, token, and time limits. Each baseline agent retains its own history and repair policy.

对应 W03、W04、W06、W07、B04。

该候选保留同一调查、调查不可修改代码、占用同一预算以及基线保留自身策略四项事实。若主代理确认这里的调查确实完整复用了 Verifier，可将第二句主语改为 `The Verifier's investigation`；本轮不凭名称推断调用关系。

### 3.5 分清 SWE-agent 的任务数、修复数和保留数

**涉及 B-S20；第 120 行。**

原句：

> SWE-agent with investigation accepts 43/50, compared with 44/50 and one interrupted task for its native condition.

英文候选：

> SWE-agent accepts 43/50 with the added investigation and 44/50 without it.

中断任务归属、最终接受状态缺失及分母处理统一由 B-N01 的表注交代。对应 W07。不得把该任务另加在 50 之外，也不得将其缺失状态改写成确定失败。

**涉及 B-S21、B-S22；第 120 行。**

原句：

> Across distinct inputs, the added investigation increases SWE-agent's repair count from seven to eight among nine initially faulty programs. It also leaves four initially accepted programs failing at the end.

英文候选：

> Among the nine distinct inputs whose initial translations fail evaluation, SWE-agent repairs seven without the added investigation and eight with it. With the added investigation, four of the 20 distinct inputs whose initial translations pass evaluation fail the final evaluation.

对应 W03、W07、最新意见 6。

此处保留真实的修复改善与正确程序退化。九个和二十个均属于不同输入层面的计数，不能用这些数直接重算任务标识层面的 43/50。`repair count` 必须改清，避免与表中其他位置的 repair calls 混淆。

**涉及 B-S23；第 120 行。**

原句：

> Table~\ref{tab:components} records both the repair and preservation consequences in final acceptance.

英文候选：

> Final acceptance in Table~\ref{tab:components} counts both repaired translations and initially passing translations that remain accepted.

对应 W03、B04。该句明确最终接受指标为什么同时反映修复与保留表现，不增加额外评价指标。

### 3.6 两张表的 caption 与表注

**涉及 B-C01、B-C02；第 94 行。**

原文：

> Complete component and host-integration comparison on the common MindSpore collection. Token totals include initial translation and all subsequent calls.

英文候选：

> Component variants and added investigation for baseline agents on the 50 MindSpore task identifiers. Token totals include initial translation and all subsequent calls.

第二句原样保留。对应 W03、W04、W07、B04。

**涉及 B-N01、B-N02；第 102 行。**

原文：

> Includes one task with unavailable final acceptance, which remains in the denominator and cost totals. Each condition uses the input reuse described in Appendix~\ref{sec:task-construction}.

英文候选：

> $\dagger$ The SWE-agent condition includes one interrupted task whose final acceptance is unavailable. This task remains in the denominator, and its incurred costs remain in the totals. For task identifiers that are aliases of the same experimental condition, one execution supplies the results for all aliases and its costs are counted once. Appendix~\ref{sec:task-construction} describes this mapping.

对应 W03、W06、W07。

该表注保留必要的来源口径，同时不把完整的输入判同字段堆进正文。所附 README 明确判同还涉及来源、契约、初译程序、方法及输入；若附录 A 的定义尚不充分，应由负责该节的主代理在原定义处补清，而非在本表再造缩写。

**涉及 B-C03、B-C04；第 111 行。**

原文：

> Complete component results on saved initial translations. Repair tokens cover all ten runs, including investigation and failed attempts.

英文候选：

> Component results on ten programs produced by initial translation. Token totals cover investigation and repair across all ten runs, including failed attempts.

对应最新意见 6、W07、B04。本表的 token 不应因此改成包含初始翻译的完整迁移成本；第一张表与本表继续保留各自统计阶段。

## 4. 表格逐项台账

### 4.1 `figures/TABLE_unified_components.tex`

#### 列头

| 编号 | 位置与内容 | 建议 | 理由 |
|---|---|---|---|
| B-UH01 | 第 3 行：`Setting` | 保留 | 可准确涵盖组件变体与基线接入条件。 |
| B-UH02 | 第 3 行：`Accepted` | 改为 `Final accepted` | 明确按最终候选计分，与加入调查后初始通过程序可能退化的分析一致。 |
| B-UH03 | 第 3 行：`Total tokens (millions)` | 保留 | 单位明确；caption 已定义包括初译及所有后续调用。 |

`Final accepted` 应使用正常换行，不缩小模板字号。该建议对应 W07、B04、F07。

#### 条件行

| 编号 | 行号 | 当前条件与数值 | 建议 | 审查结论 |
|---|---:|---|---|---|
| B-U01 | 5 | LaDiM；50/50；5.159 | 保留 | 接受数与所附统一比较来源一致；完整成本口径明确。 |
| B-U02 | 6 | Continuous investigation and repair conversation；49/50；5.603 | 保留 | 条件名已解释共用对话的对象；配合 B-S02 即可，无需另造简写。 |
| B-U03 | 7 | Without repair history；50/50；4.566 | 保留 | 保留移除历史后本集合仍全部接受且成本更低的真实结果。 |
| B-U04 | 8 | Without progress reminders；50/50；4.562 | 保留数值与行名 | 提醒内容需在实验定义处核实说明，不通过改标签猜测。 |
| B-U05 | 9 | MatchFixAgent；50/50；12.097 | 保留 | 与接入调查条件形成直接比较。 |
| B-U06 | 10 | MatchFixAgent with independent investigation；50/50；19.480 | 保留 | 接受相同、token 增加，应完整保留。 |
| B-U07 | 11 | SWE-agent；44/50†；20.831 | 保留 | † 位置正确；表注需说明未知最终状态及分母处理。 |
| B-U08 | 12 | SWE-agent with independent investigation；43/50；36.547 | 保留 | 最终接受减少与成本增加均不得因优化表述而隐藏。 |

本表无需增添未测量列，也无需为与主文四项组件分组一致而删除这里的历史完整比较。对应 B02、B06、W07。

### 4.2 `figures/TABLE_natural_components.tex`

#### 列头

| 编号 | 位置与当前内容 | 建议候选 | 理由 |
|---|---|---|---|
| B-NH01 | 第 3 行：`Condition` | 保留 | 各行均为实验条件。 |
| B-NH02 | 第 3 行：`Failed programs repaired` | `Initially failing programs repaired` | 指明五份程序在初次评估时失败，避免与修复失败混淆。 |
| B-NH03 | 第 3 行：`Passing programs preserved` | `Initially passing programs preserved` | 与前列成对说明两组程序及各自分母。 |
| B-NH04 | 第 3 行：`Repair tokens (millions)` | `Investigation and repair tokens (millions)` | token 覆盖调查与修复，名称应直接反映统计阶段。 |
| B-NH05 | 第 3 行：`Final accepted` | 保留 | 清楚表示十份程序的最终接受总数。 |

列头调整对应最新意见 6、W07、B04、F07。可使用多行表头；本轮没有渲染证据，不指定行数或压缩字号。

#### 条件行

| 编号 | 行号 | 当前条件与数值 | 建议 | 审查结论 |
|---|---:|---|---|---|
| B-TN01 | 5 | Independent evidence handoff；4/5；5/5；15.548；9/10 | 行名加 `(reference)`；数值保留 | 该行是包含编辑示例及格式纠正的参照，需与第一张表及自然错误主比较中的配置区分。 |
| B-TN02 | 6 | Continuous conversation；3/5；5/5；14.516；8/10 | 保留 | 前文已定义共用调查与修复对话；8/10 与 3+5 一致。 |
| B-TN03 | 7 | Without repair history；0/5；5/5；10.852；5/10 | 保留 | 五份初始错误程序无一修复；正确程序全部保留。该结果不能被第一张表的 50/50 掩盖。 |
| B-TN04 | 8 | Without progress reminders；2/5；5/5；17.325；7/10 | 保留 | 7/10 与 2+5 一致；本组移除提醒后的成本更高，真实差异应保留。 |
| B-TN05 | 9 | Without editing format assistance；4/5；5/5；13.207；9/10 | 保留 | 该条件与自然错误比较中的 LaDiM 配置对应，关系由 B-S13 明确。 |

建议的第一行名称：

> Independent evidence handoff (reference)

正文 B-S11 仍应解释该参照包含什么辅助，不能只依赖 `(reference)` 标签。

五行的最终接受数均等于“已修复的初始错误程序数”加“保留的初始通过程序数”；两个分组的分母均为 5，最终分母为 10。表中数值与给定快照一致，本轮没有独立复核原始实验账本。

## 5. 图表生成与资产同步方案

本节涉及两张生成表，没有独立图形资产或算法。以下均为后续实施位置，本轮未修改或运行。

| 拟调整内容 | 论文位置 | 生成或资产同步位置 | 实施时应保持的事实 |
|---|---|---|---|
| 第一张表 `Accepted` 改为 `Final accepted` | `sections/supplementary_experiments.tex:93–104` | `figures/make_unified_results.py` 中生成 `TABLE_unified_components.tex` 的表头模板；输出 `figures/TABLE_unified_components.tex:3` | 八行结果、50 的分母、token 数值及 † 不变。 |
| 第二张表初始状态列头、token 阶段列头及参照标识 | 同文件第 110–117 行 | 同一生成器中生成 `TABLE_natural_components.tex` 的模板；输出第 3、5 行 | 五行全部数值、十份程序范围、参照配置不变。 |
| 两张表 caption、第一张表注、四段正文 | 同文件第 91、94、102、106、108、111、120 行 | LaTeX 直接文本 | 保持两张表不同的成本统计阶段。 |
| 删除论文中的主文选行说明 | 同文件第 108 行第 5 句 | `data/paper_figures/README.md` 已有主文选取前三行的记录 | 主文与附录选行关系继续可追踪，无须重复添加同义说明。 |
| 如生成器共用第二张表的列头字符串 | 主文对应程序组件表，具体行号未提供 | `TABLE_program_components.tex`、`TABLE_program_components_compact.tex` 的相关生成模板 | 仅在确实共享统计含义或模板时同步；不扩大本节审查范围。 |

所附来源说明明确 `figures/make_unified_results.py` 生成上述表格，`make_repair_comparison.py` 调用同一 exporter。具体函数名和生成器行号未提供，不能据此声称已确认共享模板结构。

这些都是文字或标签修改，不需要改变 `unified_results.json` 中的定量值。后续实施时应核对全部 36 个数值单元保持一致，并检查较长表头的换行及宽度；无需重跑实验。

## 6. 最重要发现与需主代理裁定的事项

1. **50 与 29 的口径必须在本节转换处交代。** 第一张表按 50 个任务标识计分，第 106、120 行的 20、9、7、8、4 均涉及不同输入。建议采用 B-S08 的解释及 B-N02 的别名计费说明。不得直接用不同输入的计数重算 43/50。

2. **修复历史的两组结果应同时保留。** 第一组移除历史后仍为 50/50，第二组为 0/5 修复、5/10 最终接受。当前分组符合用户要求；应明确各自实验对象及参照配置，不合并成一个统一效果判断，也不删去不利结果。

3. **第二张表的参照配置需要显式标明。** `Independent evidence handoff` 行包含编辑格式示例和格式纠正；移除这些辅助才对应自然错误比较中的 LaDiM 配置。建议采用参照标识、正文定义与准确表引用。两张表的 token 还分别覆盖完整迁移与调查修复，不能统一成同一成本口径。

4. **SWE-agent 的 `repair count` 当前容易被读成调用次数。** 应直接写九份初始错误程序中修复七份或八份，并明确加入调查后有四份初始通过程序最终失败。保留最终接受由 44/50 变为 43/50 的事实，中断任务的缺失状态集中放在表注。

5. **两项实现解释需要主代理核对冻结来源。** 一是 progress reminders 的实际内容，二是移除 repair history 后重置的上下文及所保留消息。当前证据足以提出更清楚的表达，尚不足以新增具体提醒内容、Verifier 重启、重新调查或固定诊断路线。

6. **生成器共享范围需要主代理裁定。** 已能确认两张表的生成器和输出资产；无法从快照确认表头是否与主文模板共用。实施时按真实模板关系同步，保持主文十份初译程序组件分组及附录完整结果不变。本轮仅交付审查方案，所有论文、脚本、图表和实验结果均未改动。
