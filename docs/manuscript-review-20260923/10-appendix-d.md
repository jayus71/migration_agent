# 附录 D 逐句审查报告

本报告审核快照 `d1d6a53` 中的附录 D，仅提出修改方案。未修改论文、脚本、图表、结果或文件，未调用工具、编译或重跑实验。审查依据为本轮提供的 AGENTS.md、意见清单、humanizer 规则、Academic-Writing-DNA 及图表来源说明。

## 1. 范围与覆盖

准确源文件：`sections/supplementary_experiments.tex`，第 129–136 行。

| 对象 | 数量 | 覆盖情况 |
|---|---:|---|
| 章节标题 | 1 | 第 129 行，已审 |
| 交叉引用标签 | 1 | 第 130 行，已审 |
| 正文自然句 | 16 | 全部登记，编号 D01–D16 |
| 句内独立叙述单元 | 17 | D14 含分号连接的两个单元，分别核查 |
| 独立公式、算法、图注、表注 | 0 | 本节快照未包含 |
| 表格引用 | 1 | `tab:natural-repairs`，第 134 行 |
| 正文章节引用 | 1 | `sec:fault-characterization`，第 136 行 |

本节包含三个内容层次：十份初译程序的比较协议、调用与 token 成本、LSTM 支持库修复案例。建议保留这一结构。16 句中，7 句保留，9 句提出局部改写；不建议整句删除或迁移。

表格实体、生成器源码、冻结结果明细及被引用正文未包含在本次源码片段中。下文涉及这些对象时，仅根据传入的来源说明判断同步位置，不将其列为已经逐项复核。

## 2. 逐句台账

| 编号 | 原文短引与位置 | 建议 | 理由及对应意见 |
|---|---|---|---|
| D01 | “The ten supplied translations contain five initially faulty programs and five that already pass the checks.” 第 132 行，第 1 句 | 改写 | `supplied translations` 未直接说明是初次翻译后的程序；`the checks` 未在句内交代首次评估。保留十份、五份失败、五份通过的构成，改为首次评估结果。对应 E08、W03、W07、S13／最新意见 6。 |
| D02 | “Each method receives the same source, candidate, task requirements, and supporting library.” 第 132 行，第 2 句 | 保留 | 具体交代公平比较所需的相同输入，四项各有用途。`candidate` 在 D01 明确初译对象后可自然理解，不必全篇机械替换。对应 E07、W07。 |
| D03 | “The candidate and library may be edited.” 第 132 行，第 3 句 | 保留 | 编辑范围直接决定后文支持库修复是否属于允许操作，是必要实验条件。与 D04 分别规定可变对象和固定对象，信息不重复。对应 M04、B03、W07。 |
| D04 | “The source and acceptance criteria remain fixed.” 第 132 行，第 4 句 | 保留 | 明确修复不修改源程序和验收条件，属于本比较的必要协议，不是新增防御性声明。对应 W07。 |
| D05 | “Target forward computation and differentiation execute in MindSpore through …, followed by PyTorch optimizer updates on its parameters.” 第 132 行，第 5 句 | 改写 | 混合执行机制必须保留；`its parameters` 指代不清，且一个长句压入两个执行阶段。拆句交代 MindSpore 前向／求导和 PyTorch 优化器更新。对应 E10、W01、W03、W07。 |
| D06 | “The comparison uses matching inputs and initial parameters with three-seed confirmation.” 第 132 行，第 6 句 | 改写 | 相同输入、初始参数和三个种子均为实质条件；`three-seed confirmation` 将执行条件压成名词短语。改为直接说明如何确认结果。对应 W01、W04、W07。 |
| D07 | “Loss absolute difference, gradient norm absolute difference, and relative parameter update thresholds are …” 第 132 行，第 7 句 | 改写；检查项定位待核对 | 五个阈值及其对应关系必须完整保留。原句末尾 `the specified layer and parameter checks` 缺少可定位的说明，不能靠读者猜测。对应 M05、E04、W03、W07。 |
| D08 | “Table … counts every call for each input, including failed repairs and investigation of initially accepted programs.” 第 134 行，第 1 句 | 改写 | 费用统计包含失败修复及首次评估通过程序的调查，信息重要。改用“表中的调用数”作主语，并明确覆盖全部十份程序，避免把成本误读为仅覆盖五份错误程序。对应 W06、W07、E08、S13／最新意见 6。 |
| D09 | “LaDiM uses 193 calls, direct repair uses 120, SWE-agent uses 386, and MatchFixAgent uses 265.” 第 134 行，第 2 句 | 保留 | 四个方法的调用数直接可比，句子清楚。附录给出精确成本合理，无须为了减少数字而删除。是否统一写为 `LLM calls`，需核对表头定义。对应 W02、W07。 |
| D10 | “LaDiM uses 13,206,863 tokens.” 第 134 行，第 3 句 | 保留 | 提供新的总成本数值，不是重复结尾。D08 明确统计对象后，本句范围清楚。不得替换为程序组件研究中的 15,547,813。对应 W07、B02、B06。 |
| D11 | “The LSTM repair in Section … follows two errors through the supporting library.” 第 136 行，第 1 句 | 改写 | `follows two errors through` 未清楚说明修复发生在哪里。直接写 LaDiM 修复 LSTM 程序所用支持库中的两个错误，保留案例与主文的联系。对应 R08、W01、W03。 |
| D12 | “The first submission leaves an unregistered recurrent operator unresolved.” 第 136 行，第 2 句 | 保留 | 给出第一次提交仍未解决的具体问题，为后续修改提供因果起点。附录保留提交顺序有助解释修复过程，不属于无用记账。对应 R08、R12、W07。 |
| D13 | “LaDiM reproduces the failure and adds a MindSpore recurrence with its registration.” 第 136 行，第 3 句 | 改写 | 复现、实现递推和注册算子均为实质动作；`with its registration` 表达生硬、指代含混。将实现与注册分别写成动词。对应 R08、W01、W03。 |
| D14a | “The second submission exposes recursive tensor indexing” 第 136 行，第 4 句前半 | 改写，与 D14b 一并处理 | 保留第二次提交暴露张量索引递归的顺序，不推断第二次提交引入了这个错误。对应 R12、W07。 |
| D14b | “a focused test identifies the dispatch cycle, which the third submission corrects.” 第 136 行，第 4 句后半 | 改写，与 D14a 一并处理 | 保留针对性测试定位循环、第三次提交纠正的链条。拆除分号，将 `dispatch cycle` 与前面的张量索引明确连接；不补写未提供的固定诊断路由或具体 API。对应 W03、W04、R12、S13／最新意见 1、7。 |
| D15 | “The final public loss absolute difference is …” 第 136 行，第 5 句 | 改写；`public` 含义待核对 | 三项最终误差必须保留。`public` 的修饰范围和实验含义不明；若仅是记录标签，改成最终评估结果。若区分两类评估，需保留并解释实际区别。对应 W03、W06、W07。 |
| D16 | “The example uses 32 LLM calls.” 第 136 行，第 6 句 | 保留 | 明确单个案例成本。32 次 LLM 调用与三次提交是不同统计量，本句有独立价值，不应合并或互换。对应 W07、R12。 |

### 标题与标签

- 第 129 行 `Natural Translation Repair Protocol`：建议保留。标题能够覆盖自然初译错误的修复协议；当前材料不足以把 `Natural` 改成含义更窄的分类名。
- 第 130 行 `sec:natural-protocol`：保留。它是 LaTeX 交叉引用标识，不是需要清理的读者可见内部术语。
- 本节没有算法，不涉及算法步骤删减，也没有证据支持补入固定诊断顺序或每个工作单元重启 Verifier 的描述。

## 3. 需调整项与具体英文候选

以下均为修改建议，尚未实施。带核对条件的候选不能直接视为已确认事实。

### D01：说明十份程序来自初次翻译及首次评估

原句：

> The ten supplied translations contain five initially faulty programs and five that already pass the checks.

候选：

> Of the ten programs produced by the initial translation, five fail the initial evaluation and five pass.

该句直接交代程序来源及分组依据，不把首次通过夸大为所有可能情形下均正确。后面的 D02 继续说明各方法收到同一份程序，无需在此再重复 `same`。

对应意见：E08、W03、W07、S13／最新意见 6。

### D05：明确执行后端和优化器的分工

原句：

> Target forward computation and differentiation execute in MindSpore through \texttt{torch4ms}, followed by PyTorch optimizer updates on its parameters.

候选：

> Forward computation and differentiation in the target program run in MindSpore through \texttt{torch4ms}. PyTorch then applies optimizer updates to the parameters.

这里保留现有执行机制，不改成“整个训练过程均由 MindSpore 执行”。这段已经位于协议附录，位置合理。

对应意见：E10、W01、W03、W07。

### D06：展开三个种子的确认条件

原句：

> The comparison uses matching inputs and initial parameters with three-seed confirmation.

候选：

> The comparison uses matching inputs and initial parameters, and the results are confirmed with three random seeds.

保留相同输入、初始参数及三个种子，不新增平均方式、逐种子判定方式或种子独立性的主张。

对应意见：W01、W04、W07。

### D07：拆清阈值对应关系，补足检查项引用

原句：

> Loss absolute difference, gradient norm absolute difference, and relative parameter update thresholds are 0.02, 0.05, and 0.03, with an additional gradient vector L2 threshold of 0.05 and the specified layer and parameter checks.

数值部分候选：

> The thresholds are 0.02 for the absolute loss difference, 0.05 for the absolute difference in gradient norms, and 0.03 for the relative parameter update difference. The L2 difference between gradient vectors has an additional threshold of 0.05.

原句还包含层及参数检查，不能在拆句后丢失。可暂写：

> Acceptance also requires the specified layer and parameter checks.

但此句仍需主代理补成可定位的说明：若已有定义，直接引用准确小节或公式；若没有，按冻结协议简述实际检查内容。本快照不足以填写这些检查，也不足以确定是否涉及全部层、参数名称、形状或逐元素数值。

候选保留阈值，不擅自添加 `<`、`≤` 或跨种子聚合规则。

对应意见：M05、E04、W03、W07。

### D08：明确费用覆盖全部十份程序

原句：

> Table~\ref{tab:natural-repairs} counts every call for each input, including failed repairs and investigation of initially accepted programs.

候选：

> The call counts in Table~\ref{tab:natural-repairs} cover all ten programs, including unsuccessful repair attempts and investigation of programs that pass the initial evaluation.

本句解释成本口径，有必要留在附录。若表格指标确认为 LLM 调用，可将 `call counts` 精确改为 `LLM call counts`，并同步 D09；不能据本句自行把工具调用也计入 193 等数字。

对应意见：W06、W07、E08、S13／最新意见 6。

### D11：直接交代案例中的错误位置

原句：

> The LSTM repair in Section~\ref{sec:fault-characterization} follows two errors through the supporting library.

候选：

> In the LSTM example in Section~\ref{sec:fault-characterization}, LaDiM repairs two errors in the supporting library.

保留两个错误、支持库位置及主文引用，使后续过程有明确主语。

对应意见：R08、W01、W03。

### D13：用动作说明递推实现与注册

原句：

> LaDiM reproduces the failure and adds a MindSpore recurrence with its registration.

候选：

> LaDiM reproduces the failure, implements the recurrence in MindSpore, and registers the recurrent operator.

三个动作分别对应复现、递推实现和算子注册，均有原句支持。这是真实动作序列，无须因“三项并列”而机械删项。

对应意见：R08、W01、W03。

### D14：拆开错误暴露、定位和修复

原句：

> The second submission exposes recursive tensor indexing; a focused test identifies the dispatch cycle, which the third submission corrects.

候选：

> The second submission exposes recursive tensor indexing. A focused test identifies a cycle in tensor indexing dispatch, which the third submission corrects.

该候选把 `dispatch cycle` 连接到本句已有的张量索引错误，不补写调用栈、注册表或其他实现细节。主代理需确认原句中的 dispatch cycle 确实指该索引递归；如实现记录另有更准确的机制名称，应据记录命名。

保留 `exposes`，避免改成 `introduces`：当前证据说明第二次提交暴露错误，没有说明它制造了错误。

对应意见：W03、W04、R12、W07、S13／最新意见 7。

### D15：清理未解释的评估标签

原句：

> The final public loss absolute difference is $2.38\times10^{-7}$, gradient vector L2 difference is $4.19\times10^{-7}$, and relative parameter update difference is $8.11\times10^{-7}$.

若 `public` 仅为来源记录中的标签，候选为：

> The final evaluation reports an absolute loss difference of $2.38\times10^{-7}$, an L2 difference between gradient vectors of $4.19\times10^{-7}$, and a relative parameter update difference of $8.11\times10^{-7}$.

若 `public` 区分公开评估与另一套确认评估，应按真实协议说明它修饰哪组结果，再选择措辞。当前材料不支持直接把这些值写成三个种子的均值、最大值或每个种子的共同结果。

对应意见：W03、W06、W07。

## 4. 数值、预算与科学含义核对

下列事实均需原样保留，当前候选未改变其数值或对象。

| 内容 | 快照中的事实 | 修改约束 |
|---|---|---|
| 程序构成 | 共 10 份，5 份首次评估失败，5 份首次评估通过 | 不能写成十个需要修复的错误程序 |
| 比较输入 | 相同源程序、候选程序、任务要求和支持库 | 不删去支持库 |
| 编辑范围 | 可修改候选程序和支持库；源程序与验收条件固定 | 保留支持库修复的合法范围 |
| 执行机制 | MindSpore 经 `torch4ms` 执行前向和求导，随后由 PyTorch 优化器更新参数 | 不简化成全部训练均在 MindSpore 执行 |
| 确认条件 | 相同输入、初始参数，三个种子 | 不补写聚合方式 |
| 阈值 | loss 0.02；梯度范数差 0.05；相对参数更新差 0.03；梯度向量 L2 差 0.05 | 梯度范数差和梯度向量 L2 差是不同指标 |
| 方法调用数 | LaDiM 193；direct repair 120；SWE-agent 386；MatchFixAgent 265 | 核对调用类型，不改数字 |
| LaDiM 总 token | 13,206,863 | 不混入十份初译组件研究的其他配置成本 |
| LSTM 提交顺序 | 第一次仍有未注册算子；第二次暴露索引递归；第三次纠正循环 | 提交序号不能改成 LLM 调用次数 |
| LSTM 最终误差 | $2.38\times10^{-7}$、$4.19\times10^{-7}$、$8.11\times10^{-7}$ | 不补写未提供的种子统计含义 |
| LSTM 调用数 | 32 次 LLM 调用 | 是单案例成本，不能替换全体 193 次 |

本节没有给出整体修复预算。不能根据 LSTM 的三次提交补写“三次预算”，也不能将其他实验的 1／2／4 提交结果嫁接到本节。

## 5. 图表、生成器与来源同步位置

### 自然错误修复表

第 134 行引用 `tab:natural-repairs`。传入来源说明给出的相关位置为：

- 生成器：`figures/make_unified_results.py`。
- 表格资产：`figures/TABLE_natural_repairs.tex`。
- 导出结果：`data/paper_figures/unified_results.json`。
- 来源说明：`data/paper_figures/README.md`。
- 冻结输入：LaDiM 使用 `slim_main.csv`；比较方法使用 `main_comparison.csv` 中选定的 `formal_v3` 行。传入材料没有给出这两个 CSV 的完整目录，不补造路径。

后续若采用 D01、D08 的措辞，应检查表注是否仍用未解释的 `saved translations`、`initially accepted programs` 等表达。若调整调用指标为 `LLM calls`，需同时核对表头和生成器中的相应标签。仅修改本节正文时，无须改变数值输入或重跑实验。

来源说明还明确：自然错误修复与程序组件消融采用不同配置。不能因为两者都使用十份初译程序，就互换 13,206,863 与组件结果中的 token 数。

### LSTM 案例

第 136 行与 `sec:fault-characterization` 对应。主代理整合时，应核对两处是否一致保留以下机制：

1. 支持库中的未注册递归算子；
2. MindSpore 递推实现及算子注册；
3. 第二次提交暴露的张量索引递归；
4. 针对性测试定位分派循环；
5. 第三次提交修复及最终误差。

本快照未提供案例独立图表、资产或生成器，不能指定不存在的同步位置。三次提交的详细过程留在本附录符合 R12，无需重新放回主文。

### 执行后端说明

本节的 `torch4ms` 说明已经位于附录，应保留。最新意见要求迁移的 TorchAX 说明属于 JAX 协议，不能将 TorchAX 填入本节或替换这里的 `torch4ms`。主文与 JAX 附录的具体迁移位置交由对应章节审查整合。

## 6. 最重要发现与主代理裁定项

1. **主要问题是对象与指代不够直接。** 建议明确“初次翻译后的十份程序”和“首次评估通过／失败”，并将混合执行机制拆成两个有明确动作的句子。现有实验范围、支持库编辑权限及结果力度保持。

2. **阈值句存在具体的可复现性缺口。** 四个阈值可以直接清理表达；`specified layer and parameter checks` 需要主代理找到准确协议定义或引用位置，不能凭本轮审查补写检查内容。

3. **费用口径应覆盖全部十份程序。** 保留失败修复和对首次通过程序的调查成本。主代理需确认 193／120／386／265 的调用类型及表头；13,206,863 不得与组件消融配置的成本混用。

4. **LSTM 案例应保留机制链和三次提交。** 建议清理 `follows two errors through`、`with its registration` 及分号句。索引分派循环的准确实现解释留主代理核对，不能扩写固定诊断路由。

5. **`public` 的去留取决于真实评估划分。** 若只是记录标签，可以删除；若区分评估集合或权限范围，应明确其实际含义。最终三个误差的种子统计口径也需据来源确认，不新增均值或最坏值解释。

6. **本节与最新后端迁移意见没有位置冲突。** MindSpore／`torch4ms` 执行说明已在附录；TorchAX 应放入 JAX 协议。上述全部内容均为待整合方案，本轮没有实施任何改动。
