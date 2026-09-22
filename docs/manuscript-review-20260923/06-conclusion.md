# 结论逐句审查报告

## 1. 审查范围与状态

审查对象为快照 `d1d6a53` 中 `conference_101719.tex` 的结论：第 89 行章节标题，以及第 91 行的全部正文。正文共 1 段、6 句，以下按出现顺序编号为 `CON-01` 至 `CON-06`。

本次依据传入的 AGENTS.md、humanizer 规则、Academic-Writing-DNA、论文意见清单和图表来源说明审核。覆盖情况如下：

| 对象 | 覆盖数 | 处理建议 |
|---|---:|---|
| 结论正文 | 6/6 句 | 保留 3 句，局部改写 3 句 |
| 章节标题 | 1/1 | 保留 |
| 本节公式、图表、图注、表注、算法 | 0 | 本节未包含 |
| 相关结果证据 | MindSpore 主比较、自然翻译错误修复、JAX 修复比较 | 用于核对结论，不重复审查其他章节 |

下文均为修改方案，未实施任何改动。没有读取外部文件、调用工具、重跑实验或修改论文及其资产。

## 2. 逐句台账

所有正文句子的原文件行号均为第 91 行；局部编号用于区分同一源码行中的六个句子。

| 编号 | 短引文与位置 | 建议 | 具体理由 | 对应意见 |
|---|---|---|---|---|
| CON-01 | “We introduced LaDiM, a framework with multiple agents…”；`conference_101719.tex:91` | 保留 | 直接交代方法、组织形式和研究目标。`preserving training behavior` 与全文核心主张一致；`with multiple agents` 清楚且没有不必要的连字符。无须为了句式更短而改动。 | W01、W02、A09 |
| CON-02 | “Layered Diagnosis uses dependencies among execution, forward values, gradients, and parameter updates…”；同上 | 保留 | 明确命名创新机制，并说明其利用什么关系指导调查。四项分别对应真实诊断内容，属于必要列举。此句概括机制，没有重复四种 discrepancy 的公式或逐类解释，也没有虚构固定诊断路由。 | A08、M03、W02；最新意见 1 |
| CON-03 | “Independent evidence handoff and repair history connect the resulting evidence…”；同上 | 改写 | `connect ... to ...` 把证据交接、修复历史和验证结果笼统串联，读者难以看出这些信息如何参与修改。建议以 Repair Agent 为动作主体，说明其使用诊断证据和已有验证结果指导修改。保留两个组件，不添加新的调度或验证步骤。 | W01、W03、M13、M14；最新意见 6、7 |
| CON-04 | “Repository context management carries this process across shared implementations and multiple entry points.”；同上 | 保留 | 已给出机制的实际作用范围：共享实现和多个入口。`this process` 承接前面的诊断与修复，指代可辨认。结论无需再次罗列五部分机制，也无需为列齐名称而加入两个正式子模块名。 | A04、M12、M13、A09 |
| CON-05 | “LaDiM completes all 50 MindSpore migrations with 57.4\% fewer tokens…”；同上 | 改写，拆为两句 | 数值及基线对应有来源支持，应完整保留。建议把 `completes` 改为实际评价术语 `achieves 50/50 acceptance`，把 `tokens` 明确为 `total tokens`。后半句转入另一项研究，拆句可清楚区分比较集合；同时把 `translation error study demonstrates repairs` 改为方法直接修复初次翻译中的错误。 | A06、A09、W07、E08、R08；最新意见 6、7、8 |
| CON-06 | “Results across framework, language, and repository migration establish…preserving training behavior and reducing repair costs.”；同上 | 改写 | 句首将三个迁移范围共同覆盖到末尾两个效果，容易把成本降低读成这些比较的一致结果。传入证据明确显示，六例 JAX 中 LaDiM 与 Direct repair 均接受 6/6，但 LaDiM 的 token 更多。建议保留跨范围的训练行为保持结论，将成本优势由前句的明确比较承载。`establish` 可保留，无须改成 `may` 或 `potentially`。 | W02、W07、A07、R14；最新意见 8 |

标题 `\section{Conclusion}` 位于第 89 行，名称准确，建议保留。

## 3. 需调整项与具体英文候选

### CON-03：把组件的信息作用写成实际动作

原句：

> Independent evidence handoff and repair history connect the resulting evidence to corrective edits and their verification results.

问题在于 `connect` 没有说明联系如何用于修复；`their verification results` 也需要读者回读才能确认指向 edits。这里需要改善机制表达，不宜仅用 `link` 替换 `connect`。

建议候选：

> The Repair Agent uses diagnostic evidence from the independent handoff and previous verification results from the repair history to guide corrective edits.

该候选保留独立证据交接、修复历史、诊断证据、修改和验证结果五项信息，并明确它们服务于修复决策。没有添加固定诊断顺序、每个工作单元重启 Verifier 或新的验证调用。

需要主代理核对的具体事项：本快照没有提供 Repair Agent 的方法正文或实际历史内容定义。采用候选前，应确认 `previous verification results` 确实由 repair history 提供，并供 Repair Agent 使用。当前原句和意见清单支持这一解释，但不足以独立确认实现细节。

若现有定义不足以支持上述职责拆分，可采用只澄清指代的最小候选：

> Independent evidence handoff and repair history connect diagnostic evidence to corrective edits and the results of verifying those edits.

对应意见：W01、W03、M13、M14，最新意见 6、7。两项均为方案，未实施。

### CON-05：明确验收指标和总 token，并分开两项研究

原句：

> LaDiM completes all 50 MindSpore migrations with 57.4\% fewer tokens than MatchFixAgent, and the translation error study demonstrates repairs that all three repair baselines leave unresolved.

建议候选：

> LaDiM achieves 50/50 acceptance on the MindSpore migration tasks while using 57.4\% fewer total tokens than MatchFixAgent. In the translation error study, LaDiM repairs errors in the initial translations that all three repair baselines leave unresolved.

该调整保留原句的两项结果及其力度：

- MindSpore 比较仍为 50/50 接受，较 MatchFixAgent 节省 57.4% 总 token。
- 自然翻译错误研究仍明确表述 LaDiM 修复了三种修复基线未解决的错误。

`50/50 acceptance` 与当前主比较的评价口径一致，也避免将“完成迁移”与“通过验收”混用。`total tokens` 对应完整迁移用量，包含初译及失败尝试。来源说明中的 LaDiM 5,159,134 和 MatchFixAgent 12,097,425 总 token 与 57.4% 的报告值一致。

50 是该比较的任务标识数。候选没有将其改称 50 个独立源程序，也不在结论中增加别名映射和去重细账。初次翻译中的错误采用直接表述，不增加 `saved translations` 等内部记录用语。

本句没有提交预算，无须补入 1/2/4 次预算结果，也不应写成四次修复均已执行。依据 A09，保留主要定量比较即可，无须在结论再加入自然错误研究的全部分母和结果数字。

对应意见：A06、A09、W07、E08、R08，最新意见 6、7、8。候选为方案，未实施。

### CON-06：将成本优势绑定到已有明确比较

原句：

> Results across framework, language, and repository migration establish the effectiveness of this approach in preserving training behavior and reducing repair costs.

建议候选：

> Results across framework, language, and repository migration establish the effectiveness of this approach in preserving training behavior.

原句需要调整的是两个结论共享同一个范围修饰语。所给六例 JAX 证据为：

| 方法 | 接受数 | 总 token |
|---|---:|---:|
| LaDiM | 6/6 | 674,009 |
| Direct repair | 6/6 | 353,311 |

因此，跨框架有效性与各项比较中的成本变化应分别表达。候选完整保留跨框架、语言和仓库迁移的效果主张，也保留 `establish` 的表达力度；成本贡献已由 CON-05 的 57.4% 比较直接呈现。

这项调整不需要在结论追加 JAX 成本解释或防御性尾句。JAX 的具体成本差异继续由对应实验段承载。结论末句承担跨研究范围的综合判断，与前句的具体比较层级不同，可以保留。

对应意见：W02、W07、A07、R14，最新意见 8。候选为方案，未实施。

## 4. 整段候选

以下版本保留 CON-01、CON-02 和 CON-04，采用上述三处调整。CON-03 的机制职责仍须按前述事项核对。原文 6 句因 CON-05 拆分而成为 7 句，仍保持一个连贯段落。

> We introduced LaDiM, a framework with multiple agents for preserving training behavior during code migration. Layered Diagnosis uses dependencies among execution, forward values, gradients, and parameter updates to guide investigation. The Repair Agent uses diagnostic evidence from the independent handoff and previous verification results from the repair history to guide corrective edits. Repository context management carries this process across shared implementations and multiple entry points. LaDiM achieves 50/50 acceptance on the MindSpore migration tasks while using 57.4\% fewer total tokens than MatchFixAgent. In the translation error study, LaDiM repairs errors in the initial translations that all three repair baselines leave unresolved. Results across framework, language, and repository migration establish the effectiveness of this approach in preserving training behavior.

在 LaTeX 中保留 `57.4\%`。该段为待审候选，未写入论文。

## 5. 图表、生成器及来源同步位置

本方案只调整结论表述，不改变数值、图表标签、方法名称或评价协议，因此不要求重新生成图表。后续实施时，需要核对的对应位置如下：

| 结论内容 | 对应生成器或资产 | 本方案的同步要求 |
|---|---|---|
| MindSpore 50/50、57.4% 总 token 节省 | `figures/make_unified_results.py`；其生成的 `TABLE_main_comparison.tex`、`TABLE_program_costs.tex`；`data/paper_figures/unified_results.json` | 核对接受数、基线和完整迁移成本口径一致；无需改动生成器或资产。 |
| 引言中展示的相同总 token 比较 | `figures/make_migration_motivation.py` 及其图形输出 | 数值与结论保持一致；无需重新生成。 |
| 初次翻译错误的修复结果 | `figures/make_unified_results.py`；其生成的 `TABLE_natural_repairs.tex` | 保留正文对研究对象及三种修复基线的定义；本结论候选不引入新的分母或分类。 |
| JAX 成本差异对末句范围的约束 | `TABLE_jax_repairs.tex`；冻结来源 `output/maintext-jax-autonomous-20260918/final_analysis/summary.json` | 保留既有接受数和成本。用于决定结论措辞，无需将这些数值新增到结论。 |
| 独立交接与修复历史的职责 | `sections/methods.tex` 中相关定义 | 核对 CON-03 候选的信息来源和使用主体；快照未提供对应行号，不补造定位。 |

用户维护的方法图不在本方案修改范围内。本文没有提出任何图表重绘或生成标签调整。

## 6. 最重要发现与主代理待裁定项

1. 结论的推进顺序已经完整：方法目标、诊断机制、修复机制、仓库协调、具体结果、综合效果。建议保留这一结构，只处理三处局部表达。

2. 50/50 接受和 57.4% 总 token 节省均有传入证据支持，应保留。A09 的后续决定允许结论使用必要定量证据，不能按早期“不重复精确数字”的意见删除。

3. CON-03 是主要机制表达问题。优先候选能说明两个组件如何服务于修改；主代理需核对 repair history 的实际内容及 Repair Agent 的使用方式，再决定采用职责明确版还是最小指代修正版。

4. CON-06 存在成本结论范围不清的问题。六例 JAX 的成本比较支持将成本优势绑定到具体对手和任务。建议保留前句明确的节省结果，末句集中概括跨范围的训练行为保持效果，不追加降调说明。

5. 本节没有四类 discrepancy 的重复定义、固定诊断路由、TorchAX 后端说明、四次修复均执行等问题。无需为覆盖其他章节的批注向结论添加内容，也无需追加两个仓库子模块名称或实验结果清单。

以上均为待整合的审查方案；本轮已完成六句逐句审核，未实施论文、脚本、图表或结果修改。
