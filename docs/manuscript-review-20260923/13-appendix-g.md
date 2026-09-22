# 附录 G 逐句与表格审查报告

本报告审核快照 `d1d6a53` 中附录 G 的全部三个子节、两张表及其表注。主要调整集中在消融条件的说明、对照运行的区分、上下文容量与提交轨迹的表达。现有结果及有证据支持的结论应保留，尤其是时间序列上的成本下降、推荐任务上的成本增加，以及移除规划后的最终检查数下降。

以下均为修改方案，尚未实施。审查仅依据本轮提供的源码、规则和来源说明；没有调用工具、修改文件、编译 PDF 或重跑实验。

## 一、范围、来源与覆盖数

| 审查对象 | 准确来源与原始行号 | 覆盖情况 |
|---|---|---|
| 附录 G 标题及三个子节标题 | `sections/supplementary_experiments.tex:178–219` | 4 个标题 |
| Cumulative Components | 同文件，第 183、194、196 行 | 14 个正文句子 |
| Repository Structural Analysis | 同文件，第 200、211 行 | 10 个正文句子 |
| Repair Dependency Graph Planning | 同文件，第 215、217、219 行 | 18 个正文句子 |
| 两张表的表注 | 同文件，第 186、203 行 | 6 个表注句子 |
| 累计组件表 | `figures/TABLE_cumulative_components.tex:1–14` | 2 组表头单元、4 个数据行、24 个数值单元格 |
| 独立组件消融表 | `figures/TABLE_repository_independent.tex:1–15` | 2 组表头单元、3 个数据行、18 个数值单元格 |
| 表格来源注释 | 两份表文件开头的 Source/SHA256 注释 | 2 组来源记录 |

合计覆盖 **42 个正文句子、6 个表注句子、4 个标题、11 个表头或数据行单元、42 个数值单元格**。本节没有公式、插图或算法。

审查采用本轮提供的 AGENTS.md、humanizer、Academic-Writing-DNA、意见清单及 `data/paper_figures/README.md`。底层 JSON 和实现源码未包含在快照中，因此下文明确区分“源码内部一致”与“需要主代理核对实现或冻结记录”。

意见 ID 沿用现有清单。本报告中的 `G-*` 编号仅为局部审查索引，不表示新增意见已经登记或获批。

## 二、逐句台账

### G.1 Cumulative Components

| 编号 | 原文短引与行号 | 处理方案 | 具体理由与意见 ID |
|---|---|---|---|
| G-S01 | “We add Verifier investigation … on both repositories.” 第 183 行 | 改写 | 首句直接点明时间序列与推荐两个仓库，帮助独立阅读附录；保留三个累计加入的组件及次序。B04、W03 |
| G-S02 | “Each condition runs once with the same source … total budgets.” 第 183 行 | 保留 | 给出单次运行和受控条件，直接支撑消融比较；不因列表较长删去种子、阈值、信号或预算。B04、W07 |
| G-S03 | “The base condition retains the repair prompts … progress reminders.” 第 183 行 | 保留 | 说明基础 Repair Agent 仍具备哪些能力，避免把基础条件误读为无检查、无工具。B03、B04 |
| G-S04 | “Investigation continues in the repair conversation until …” 第 183 行 | 改写 | 明确这是“已有 Verifier investigation、尚无独立证据交接”的条件，避免让读者以为基础行已经包含 Verifier。B03、B04、W03 |
| G-S05 | “All four conditions accept the time series repository …” 第 183 行 | 改写 | 改善施事表达，拆开分号句；保留 69/69、131/145 和每条件 1/2 仓库完全接受。W04、W07、B06 |
| G-S06 | “the complete context mechanism uses … 68.4% fewer …” 第 194 行 | 改写 | `complete context mechanism` 容易让读者把整行结果理解为单个组件成本；明确是包含全部累计组件的条件。B05、B06、W03 |
| G-S07 | “The paired comparison … uses the two conditions …” 第 194 行 | 改写 | 直接说在已含调查和独立交接的条件上加入 repository context management，减少读者对 `paired comparison` 的解码负担。B04、B05、S13 |
| G-S08 | “Investigation and repair input tokens fall from …” 第 194 行 | 保留 | 区分输入 token 与前句总 token，提供不同且有用的信息；数值保持。W07 |
| G-S09 | “The two truncated model responses … remain …” 第 194 行 | 改写 | 明确响应来自 LLM，简化 `remain in its … totals`；保留截断响应计入调用和成本的事实。W06、W07 |
| G-S10 | “On recommendation, adding the components increases token use …” 第 196 行 | 保留 | 清楚报告与时间序列不同的实测结果，同时给出行为检查和原始测试表现；无需降调或删去。W02、B06 |
| G-S11 | “The 14 unresolved checks comprise item embeddings …” 第 196 行 | 改写 | 明确 14 项由 12 个 embedding 检查和 2 个参数更新检查组成，消除“六个路径、两个步骤”需要读者自行相乘的问题。W03、W07 |
| G-S12 | “The first three conditions reach the context capacity …” 第 196 行 | 改写 | `context capacity` 改为明确的 conversation context limit，并注明三组调用数按表格行序对应。W03、B04 |
| G-S13 | “The complete method rebuilds context six times … same final coverage.” 第 196 行 | 改写 | 明确重建的是对话上下文，保留六次和 80 次调用上限；删除与本段首句重复的最终覆盖信息。W01、W06 |
| G-S14 | “Context management sustains further repair … unresolved.” 第 196 行 | 删除 | G-S10 已报告相同最终结果，G-S12–13 已说明提前耗尽上下文与继续至调用上限。这句再次概括同一现象，没有新增机制或结果。W01、W06 |

### G.2 Repository Structural Analysis

| 编号 | 原文短引与行号 | 处理方案 | 具体理由与意见 ID |
|---|---|---|---|
| G-S15 | “The independent structural analysis comparison retains …” 第 200 行 | 改写 | 直接说明同一仓库上“有/无 Repository Structural Analysis”的比较，并列出共同保留的能力。B04、B05、S13 |
| G-S16 | “removes the tool's file, import, symbol … inventory …” 第 200 行 | 改写 | 将“工具的清单”改为具体提供的信息；解释 unassigned files 是尚未分配到修复计划中的文件。保留全部移除项。M12、B03、W03 |
| G-S17 | “Its map tool returns the existing plan state.” 第 200 行 | 移来源记录 | 这是禁用组件后的接口返回细节。正文已经说明规划保留、结构信息移除；返回载荷放消融实现来源说明更合适。M14、W06 |
| G-S18 | “obtains structural information when the agent calls the map tool …” 第 200 行 | 改写 | 保留按需执行、初始化不扫描、上下文重建不扫描三个事实；用组件名称和动作表达，避免把接口名称当作机制解释。M12、M14、S13 |
| G-S19 | “Each condition runs once on each repository …” 第 200 行 | 保留 | 单次运行、相同初译与预算是本比较的必要条件。B04、W07 |
| G-S20 | “reduces time series calls from 42 to 30 …” 第 211 行 | 改写 | 补全 time series repository，并直接写两条件均在两次提交后通过 69/69；保留 19.8% 成本下降。B05、W02、W07 |
| G-S21 | “both finish at 131/145 … third submission instead of the fourth.” 第 211 行 | 改写 | 明确 131/145 是通过检查数，把达到该结果的提交序号与最终结果分开表达。W03、W04、W07 |
| G-S22 | “Its 9,961,503 … are 38.9% higher …” 第 211 行 | 改写 | 去掉可能回指不清的 `Its`，直接报告有无组件的 token 变化；保留成本上升。W02、W03、B06 |
| G-S23 | “The two conditions retain the same final 14 failures …” 第 211 行 | 保留 | 说明相同的是具体失败项，而不仅是总数；这条信息不能由两个 131/145 自动推出。W07、B06 |
| G-S24 | “The complete references … are separate runs …” 第 211 行 | 改写 | `complete references` 易被误解为参考文献或标准答案。明确两项研究分别运行完整方法，各用本研究对照成本。B05、W03、W07 |

### G.3 Repair Dependency Graph Planning

| 编号 | 原文短引与行号 | 处理方案 | 具体理由与意见 ID |
|---|---|---|---|
| G-S25 | “removes the work-unit plan … checkpoint propagation …” 第 215 行 | 改写 | 保留整个组件实际移除的五项能力，并以正式模块名组织句子；`checkpoint propagation` 的具体对象仍需主代理核对，不能擅自解释为重新启动 Verifier。M12、M14、B03、S13 |
| G-S26 | “It retains Repository Structural Analysis … reconstruction …” 第 215 行 | 保留 | 这些共同保留项决定消融含义，尤其是独立交接、与代码版本关联的证据和上下文满时重建；不能为简洁删掉。B03、B04、W07 |
| G-S27 | “The entire permitted target repository remains editable.” 第 215 行 | 保留 | 明确移除规划后的可编辑范围，是判断比较是否改变修复权限的必要条件。B04、W07 |
| G-S28 | “The complete references … use the same source …” 第 215 行 | 改写 | 用“有/无规划的条件”代替抽象 references；保留相同来源、初译、输入、种子、阈值、实现基础和预算。B04、W03 |
| G-S29 | “Each condition runs once; the complete references are shared …” 第 215 行 | 改写 | 拆开分号句，明确每仓库每条件一次，结构分析和规划消融共享完整方法的同一组运行。B05、W04、W07 |
| G-S30 | “Without … time series completes all 69 checks …” 第 217 行 | 保留 | 报告无规划条件的完整结果：一次提交、21 次调用、1,803,551 tokens。信息具体，表达直接。W02、W07 |
| G-S31 | “This is 15.2% fewer tokens than the complete method.” 第 217 行 | 保留 | 指向前句的明确数值，与表中 2,126,900 对照相符；保留无规划条件更省的事实。W02、B06 |
| G-S32 | “removing planning uses 7.5% fewer tokens but finishes at 130/145 …” 第 217 行 | 改写 | 保留成本与检查数的真实比较，只将 `finishes at` 改为具体的 passes；这里的比较关系有实质用途。W02、W03、B06 |
| G-S33 | “the position model's parameter update at step three.” 第 217 行 | 改写，模型名称待核对 | `position model` 在本节未定义，现有证据不能确定其公开名称或结构。先直接说明参数更新检查和训练步骤，不编造模型身份。W03、S13 |
| G-S34 | “Both conditions fully accept one of the two repositories.” 第 217 行 | 保留 | 提供仓库级接受结果，与前文的行为检查级结果不同，不属于无信息总结。W07、B06 |
| G-S35 | “The recommendation trajectories show how this final difference develops.” 第 219 行 | 删除 | 仅预告下一句，没有具体结果；直接进入各次提交的检查数即可。W01、W06 |
| G-S36 | “Without planning, successive submissions pass 128, 103, 133, and 130 checks.” 第 219 行 | 改写 | 明确对应第 1 至第 4 次提交和 145 项协议检查；保留实际轨迹。W07、S13 |
| G-S37 | “The second-stage change … causes the first regression …” 第 219 行 | 改写 | `second-stage` 的阶段划分未定义。用真实计数变化说明两次退化，保留原有共享训练入口的因果陈述，来源需主代理核对。W03、W04、W07 |
| G-S38 | “The complete method's corresponding trajectory is n/a, 122, 131, and 131.” 第 219 行 | 保留 | 与前一句提交顺序对应，下一句解释 n/a。必须保留 n/a，不改为 0。W07 |
| G-S39 | “returns eight execution failure flags outside the 145 protocol checks …” 第 219 行 | 改写 | 拆开表述，说明八个执行失败标记独立于 145 项协议检查记录；不将标记数写成八项协议失败。W03、W07 |
| G-S40 | “each lack one retrieval measurement; both final candidates …” 第 219 行 | 保留 | 分号连接的是直接相关的中间测量缺失与最终完整测量，保留有实际用途；不能把缺失值改为失败或零。W04、W07 |
| G-S41 | “exhausts the 480,000-output-token budget after 69 calls …” 第 219 行 | 改写 | 去掉复杂连字符，明确是输出 token 预算，以及有规划条件实际达到 80 次调用上限。W04、W07 |
| G-S42 | “The final scores retain these later regressions and all associated costs.” 第 219 行 | 改写 | 直接说明评分采用最后提交的候选程序；成本口径已由表注说明，无需再用抽象的 `associated costs` 总结。W06、W07 |

## 三、表注、标题和表格逐项台账

### 3.1 表注的六个句子

| 编号 | 原文与位置 | 处理方案 | 理由 |
|---|---|---|---|
| G-C01 | “Cumulative agent components on both repositories.” 第 186 行 | 保留 | 标题准确，对应两个仓库及累计设计。 |
| G-C02 | “Calls cover investigation and repair; end-to-end tokens also include the shared initial translation.” 第 186 行 | 改写 | 将调用种类说清，并明确每条件只计一次初译。W04、W07 |
| G-C03 | “Each row adds to the preceding row within its repository.” 第 186 行 | 改写 | 同一行已经横向覆盖两个仓库；直接说明每个 `+` 行在上一行基础上增加组件。B06、F07 |
| G-C04 | “Independent repository component ablations.” 第 203 行 | 改写 | `Independent` 未直接说明实验操作。写清每次分别移除一个命名组件。B04、S13 |
| G-C05 | “Both studies share the complete method shown for each repository.” 第 203 行 | 改写 | 明确共享的是每个仓库上完整方法的同一次对照运行，不只是共享方法定义。B05、W07 |
| G-C06 | “Calls cover investigation and repair; end-to-end tokens include initial translation.” 第 203 行 | 改写 | 与累计表统一成本口径，拆开分号句。W04、W07 |

### 3.2 标题

| 编号 | 来源 | 处理方案 | 理由 |
|---|---|---|---|
| G-H01 | 第 178 行：Repository Component Results | 保留 | 覆盖累计结果及两个组件消融，范围准确。 |
| G-H02 | 第 181 行：Cumulative Components | 保留 | 简洁且说明实验设计。 |
| G-H03 | 第 198 行：Repository Structural Analysis | 保留 | 用户确定的正式模块名，不更名、不缩写。M12 |
| G-H04 | 第 213 行：Repair Dependency Graph Planning | 保留 | 用户确定的正式模块名，不更名、不缩写。M12 |

### 3.3 累计组件表

来源：`figures/TABLE_cumulative_components.tex`。

| 编号 | 行号及覆盖内容 | 处理方案与审查结果 |
|---|---|---|
| G-T1-H01 | 第 5 行：Time series / Recommendation | 保留。两组列对应两个仓库，没有把文件、模型路径或检查项当作独立仓库。 |
| G-T1-H02 | 第 7 行：Condition / Behavior checks passed / Calls / End-to-end tokens | `Condition`、`Behavior checks passed` 保留。建议 `Calls` 改为 `LLM calls`，`End-to-end tokens` 改为 `Total tokens`，由表注明确计费阶段。 |
| G-T1-R01 | 第 9 行：Repair Agent；69/69、26、6,128,331；131/145、62、8,335,687 | 行名及全部数值保留。基础条件能力由 G-S03 解释。 |
| G-T1-R02 | 第 10 行：+ Verifier investigation；69/69、18、3,896,158；131/145、59、8,912,546 | 全部保留。`+` 有实际累计含义，不属于装饰性符号。 |
| G-T1-R03 | 第 11 行：+ Independent evidence handoff；69/69、26、6,047,074；131/145、68、9,556,058 | 全部保留。该行是主文 repository context management 比较的无组件对照。 |
| G-T1-R04 | 第 12 行：+ Repository context management；69/69、22、1,936,579；131/145、80、10,191,440 | 全部保留。不得替换为另一研究的完整方法行。 |

24 个数值单元格均已逐项阅读。正文出现的累计研究数值与表格对应，没有发现内部冲突。

### 3.4 独立组件消融表

来源：`figures/TABLE_repository_independent.tex`。

| 编号 | 行号及覆盖内容 | 处理方案与审查结果 |
|---|---|---|
| G-T2-H01 | 第 7 行：Time series / Recommendation | 保留。与累计表使用同一仓库命名。 |
| G-T2-H02 | 第 9 行：Condition / Behavior checks passed / Calls / End-to-end tokens | 与 G-T1-H02 同步调整。不能只改其中一张表。 |
| G-T2-R01 | 第 11 行：Complete method；69/69、30、2,126,900；131/145、80、9,961,503 | 全部保留。两个移除组件的比较共享本行对照。 |
| G-T2-R02 | 第 12 行：Without Repository Structural Analysis；69/69、42、2,651,248；131/145、80、7,172,218 | 全部保留，保留完整正式模块名。推荐任务调用数相同而 token 不同并不矛盾，不能据此更改成本。 |
| G-T2-R03 | 第 13 行：Without Repair Dependency Graph Planning；69/69、21、1,803,551；130/145、69、9,213,723 | 全部保留。推荐任务最终值必须是 130/145，不能用中途的 133/145 代替。 |

18 个数值单元格均已逐项阅读。正文中的 19.8%、38.9%、15.2% 和 7.5% 与各自表内对照值的四舍五入结果一致。

### 3.5 来源注释

- G-P01：累计表第 1–2 行记录 `output/cumulative-component-ablation-20260922/summary.json` 及 SHA256。保留，这是生成资产的来源记录，不属于应清除的论文行文。
- G-P02：独立表第 1–4 行分别记录 structural analysis 和 planning 两份摘要及 SHA256。保留两个来源，不能合并成一个未经验证的新来源。

本轮只核对提供的注释内容，没有重新计算哈希或读取对应 JSON。

## 四、需调整项与具体英文候选

以下候选均保留原始比较、分母和预算含义。涉及实现身份或模型名称的待核对项单独标明。

### 4.1 累计设计的对象、会话关系与结果

对应 G-S01、G-S04、G-S05；原文第 183 行：

> We add Verifier investigation, independent evidence handoff, and repository context management cumulatively to the Repair Agent on both repositories (Table~\ref{tab:repository-cumulative-full}).

候选：

> We cumulatively add Verifier investigation, independent evidence handoff, and repository context management to the Repair Agent on the time series and recommendation repositories (Table~\ref{tab:repository-cumulative-full}).

原文：

> Investigation continues in the repair conversation until independent evidence handoff is added.

候选：

> With Verifier investigation but without independent evidence handoff, investigation and repair use the same conversation.

原文：

> All four conditions accept the time series repository and pass 69/69 checks; all finish at 131/145 on recommendation, giving one fully accepted repository out of two per condition.

候选：

> All four conditions achieve full acceptance on the time series repository, passing 69/69 checks. Each passes 131/145 checks on recommendation, so each condition fully accepts one of the two repositories.

理由：说明实际仓库、具体实验条件及两层结果指标，不引入新的接受标准。对应 B04、B06、W03、W04、W07。

### 4.2 区分 68.4% 与主文组件比较

对应 G-S06、G-S07、G-S09；原文第 194 行：

> On time series, the complete context mechanism uses 1,936,579 end-to-end tokens, 68.4\% fewer than the base Repair Agent.

候选：

> On the time series repository, the condition with all three components uses 1,936,579 total tokens, 68.4\% fewer than the base Repair Agent.

原文：

> The paired comparison of repository context management in the main text uses the two conditions that already include investigation and independent evidence handoff, reducing tokens from 6,047,074 to 1,936,579.

候选：

> The main text compares the conditions with and without repository context management while retaining investigation and independent evidence handoff in both. Adding repository context management reduces total tokens from 6,047,074 to 1,936,579.

原文：

> The two truncated model responses in the condition without repository context remain in its call and token totals.

候选：

> Call and token totals for the condition without repository context management include both truncated LLM responses.

理由：68.4% 比较完整累计条件与基础 Repair Agent；主文 68.0% 比较累计表最后两行。两者都成立，不能为了统一表述改成同一个百分比。对应 B05、B06、W03、W07。

### 4.3 推荐任务未通过项与上下文容量

对应 G-S11–G-S14；原文第 196 行：

> The 14 unresolved checks comprise item embeddings in six model paths at steps two and three, and two parameter updates.

候选：

> The 14 unresolved checks comprise 12 item embedding checks across six model paths at training steps two and three, plus two parameter update checks.

这里的 12 来自原文明确给出的六个路径和两个步骤，与总计 14 及另两项更新检查相符；不新增故障类型。

原文：

> The first three conditions reach the context capacity after 62, 59, and 68 calls.

候选：

> The first three conditions reach the conversation context limit after 62, 59, and 68 calls, respectively, in table order.

原文：

> The complete method rebuilds context six times and continues to the 80-call limit, with the same final coverage.

候选：

> With repository context management, the method rebuilds the conversation context six times and continues to the limit of 80 calls.

原文：

> Context management sustains further repair in this task, while the additional calls leave the remaining training differences unresolved.

建议删除。前述候选已保留“重建上下文使运行继续至调用上限”，G-S10 保留“最终仍为 131/145”。删除该句不会删去组件作用或实际结果。

对应 W01、W03、W06、W07、B06。

### 4.4 结构分析消融：说明移除对象，移出接口返回细节

对应 G-S15–G-S18；原文第 200 行：

> The independent structural analysis comparison retains Repair Dependency Graph Planning, notebook tools, ordinary file inspection, independent evidence handoff, and evidence management in both conditions.

候选：

> For each repository, we compare conditions with and without Repository Structural Analysis while retaining Repair Dependency Graph Planning, notebook tools, ordinary file inspection, independent evidence handoff, and evidence management in both.

原文：

> The condition without Repository Structural Analysis removes the tool's file, import, symbol, and notebook cell inventory, together with the automatic list of unassigned files.

候选：

> Removing Repository Structural Analysis disables its inventory of files, imports, symbols, and notebook cells, together with its automatically generated list of files not assigned in the repair plan.

“未分配”的具体归属应由主代理核对冻结实现：若该列表实际指向另一种分配关系，应按实现修正候选，不能直接采用推测。

原文：

> Its map tool returns the existing plan state.

建议移至 `data/paper_figures/README.md` 中本研究的消融来源说明，保留如下记录：

> When Repository Structural Analysis is disabled, the map tool returns the existing plan state.

原文：

> The complete method obtains structural information when the agent calls the map tool; initialization and context reconstruction do not perform the scan.

候选：

> Repository Structural Analysis runs when the agent requests a repository map. It does not run automatically at initialization or when context is rebuilt.

这两句保留按需调用的实际机制，不新增初始化扫描、固定诊断路由或上下文重建时的自动扫描。

对应 M12、M14、B03、B04、W03、W06、S13。

### 4.5 结构分析结果与各研究的独立对照

对应 G-S20–G-S22、G-S24；原文第 211 行：

> Repository Structural Analysis reduces time series calls from 42 to 30 and end-to-end tokens by 19.8\%, with both conditions completing all 69 checks after two submissions.

候选：

> On the time series repository, Repository Structural Analysis reduces calls from 42 to 30 and total tokens by 19.8\%. Both conditions pass all 69 checks after two submissions.

原文：

> On recommendation, both finish at 131/145, and retaining structural analysis reaches this coverage at the third submission instead of the fourth.

候选：

> On recommendation, both conditions pass 131/145 checks. The condition with Repository Structural Analysis reaches this result on submission three, compared with submission four without it.

原文：

> Its 9,961,503 end-to-end tokens are 38.9\% higher than the 7,172,218 used without structural analysis.

候选：

> Adding Repository Structural Analysis increases total tokens from 7,172,218 to 9,961,503, a 38.9\% increase.

原文：

> The complete references in this independent study and the cumulative study are separate runs, with their costs retained in the corresponding tables.

候选：

> The complete method is run separately in the cumulative study and the structural analysis study. Each comparison uses the complete method's costs from its own study.

理由：明确保留两组不同的完整方法运行，避免把累计研究的 1,936,579 与独立结构分析研究的 2,126,900 互换。对应 B05、B06、W02、W03、W07。

### 4.6 规划消融移除什么、比较什么

对应 G-S25、G-S28、G-S29；原文第 215 行：

> The planning ablation removes the work-unit plan, prerequisite readiness checks, unit file scopes, checkpoint propagation through dependencies, and context reconstruction when the active unit changes.

候选：

> Removing Repair Dependency Graph Planning disables the plan of repair units, checks for completed prerequisites, file scopes for each unit, propagation of checkpoints through dependencies, and context reconstruction when the active repair unit changes.

该候选完整保留五项移除内容。它尚未解决 `checkpoint` 的具体含义；需要主代理从实现确认它记录的是验证结果、完成状态还是其他信息，再作必要的短解释。本轮不能据此补写“逐工作单元重启 Verifier”或“固定依赖调度路线”。

原文：

> The complete references in Table~\ref{tab:repository-independent} use the same source, initial candidate, inputs, seeds, thresholds, method implementation, and budgets as the conditions without planning.

候选：

> For each repository, the conditions with and without Repair Dependency Graph Planning in Table~\ref{tab:repository-independent} use the same source, initial translation, evaluation inputs, seeds, thresholds, underlying implementation, and budgets.

原文：

> Each condition runs once; the complete references are shared with the structural analysis comparison.

候选：

> Each condition runs once per repository. The comparisons of planning and structural analysis share the same complete-method runs.

理由：区分“共享对照运行”和“所有实验都是同一次运行”。完整方法行在两项移除组件的比较中共享，但累计研究使用另一组运行。对应 M12、B04、B05、W03、W04、W07。

### 4.7 规划消融的推荐结果与未定义模型名

对应 G-S32、G-S33；原文第 217 行：

> On recommendation, removing planning uses 7.5\% fewer tokens but finishes at 130/145, one check below the complete method.

候选：

> On recommendation, removing planning reduces total tokens by 7.5\% and passes 130/145 checks, one fewer than the complete method.

原文：

> The additional failure is the position model's parameter update at step three.

在模型身份未核对前，可采用不添加新分类的候选：

> The additional failure concerns a parameter update check at training step three.

处理要求：`position model` 的精确身份应保留在来源记录，并由主代理判断是否有读者可理解的正式模型名可补回论文。此候选保留失败类型和步骤，但暂时省略未解释的模型标签，因此属于待裁定的精简方案，不能直接声称已完整解决命名问题。

对应 W03、W07、B06、S13。

### 4.8 推荐任务的实际提交轨迹

对应 G-S35–G-S37；原文第 219 行：

> The recommendation trajectories show how this final difference develops.

建议删除，直接进入结果。

原文：

> Without planning, successive submissions pass 128, 103, 133, and 130 checks.

候选：

> Without planning, submissions one through four pass 128, 103, 133, and 130 of the 145 protocol checks, respectively.

原文：

> The second-stage change to a shared training entry point causes the first regression, and the final submission regresses from the intermediate 133 checks.

候选：

> A change to a shared training entry point causes the first regression, from 128 to 103 passed checks. The final submission reduces the count from 133 to 130.

理由：用具体检查数说明退化，去掉没有定义的 `second-stage`。候选保留了原稿的因果主张；该因果归因是否由冻结轨迹和代码改动支持，需要主代理核对，不能仅由计数变化推导。

对应 W01、W03、W04、W07。

### 4.9 缺测、输出预算和最终评分

对应 G-S39、G-S41、G-S42；原文第 219 行：

> Its first submission returns eight execution failure flags outside the 145 protocol checks, leaving all protocol measurements unavailable.

候选：

> The complete method's first submission produces eight execution failure flags, recorded separately from the 145 protocol checks. All protocol measurements are unavailable for that submission.

保留 `flags` 的含义，不将其改写为八个模型、八次调用失败或八项协议检查失败。

原文：

> Removing planning exhausts the 480,000-output-token budget after 69 calls, while the complete method uses all 80 calls.

候选：

> Without planning, the method exhausts its budget of 480,000 output tokens after 69 calls. The complete method reaches the limit of 80 calls.

原文：

> The final scores retain these later regressions and all associated costs.

候选：

> Final scores use the last submitted candidate.

完整成本口径保留在两张表的表注中。此处只说明最终评分依据，避免重复成本记账说明。

对应 W04、W06、W07。

### 4.10 两张表的完整表注候选

累计组件表，第 186 行，原文：

> Cumulative agent components on both repositories. Calls cover investigation and repair; end-to-end tokens also include the shared initial translation. Each row adds to the preceding row within its repository.

候选：

> Cumulative agent components on both repositories. Each row marked with \(+\) adds a component to the preceding condition. Calls count LLM calls during investigation and repair. Total tokens include investigation and repair, with the common initial translation counted once for each condition.

独立消融表，第 203 行，原文：

> Independent repository component ablations. Both studies share the complete method shown for each repository. Calls cover investigation and repair; end-to-end tokens include initial translation.

候选：

> Repository component ablations that separately remove Repository Structural Analysis or Repair Dependency Graph Planning. For each repository, both comparisons share the same complete-method run. Calls count LLM calls during investigation and repair. Total tokens include investigation and repair, with the common initial translation counted once for each condition.

配套表头候选：

| 原表头 | 候选 |
|---|---|
| `Calls` | `LLM calls` |
| `End-to-end tokens` | `Total tokens` |

README 将调用与 provider 使用量及调查、修复成本关联，支持上述方向。主代理实施前仍应确认生成器的 `Calls` 字段确实统计 LLM 请求，而非工具操作；若字段含义不同，按实际来源命名，不能仅凭行文偏好改标签。

对应 B04、B05、B06、F07、W03、W04、W07。

## 五、数值与证据关系检查

以下关系由本轮提供的表值与来源说明直接支持，修订时应保持：

| 比较 | 正确对照及结果 | 修订要求 |
|---|---|---|
| 全部累计组件相对基础 Repair Agent，时间序列 | 6,128,331 → 1,936,579，减少 68.4% | 这是整个累计组合的效果，不分摊给单个组件。 |
| Repository context management，时间序列 | 6,047,074 → 1,936,579，减少 68.0% | 对照为累计表最后两行；不同于上一比较。 |
| Repository Structural Analysis，时间序列 | 2,651,248 → 2,126,900，减少 19.8%；调用 42 → 30 | 使用独立消融表自己的完整方法行。 |
| Repository Structural Analysis，推荐 | 7,172,218 → 9,961,503，增加 38.9% | 保留成本增加，同时保留第三次而非第四次提交达到 131/145。 |
| 移除规划，时间序列 | 2,126,900 → 1,803,551，减少 15.2% | 保留无规划一次提交即通过 69 项检查的结果。 |
| 移除规划，推荐 | 9,961,503 → 9,213,723，减少 7.5%；最终 131/145 → 130/145 | 同时报告成本与检查数变化，不把中途 133 项写成最终值。 |
| 推荐提交轨迹，无规划 | 128、103、133、130 | 四个实际提交结果均保留。 |
| 推荐提交轨迹，完整方法 | n/a、122、131、131 | n/a 表示协议测量不可用，不是 0/145。 |

本节的四次提交轨迹是该推荐任务实际记录的轨迹。它与主文按 1/2/4 次提交预算报告的统计不是同一对象，不能相互补值，也不能从这里推断其他任务执行了四次修复。

## 六、生成器与资产同步位置

后续若批准实施，需同步以下位置；本轮均未修改。

| 内容 | 论文或资产位置 | 生成器或来源位置 | 同步要求 |
|---|---|---|---|
| 正文候选与表注 | `sections/supplementary_experiments.tex:183–219` | 手写 LaTeX 正文 | 保持两张表引用标签和三个子节安排。 |
| 累计表表头 | `figures/TABLE_cumulative_components.tex:7` | `figures/make_cumulative_components.py`；输入 `output/cumulative-component-ablation-20260922/summary.json` | 修改导出表头，保留全部数值、来源路径和源数据哈希。 |
| 独立表表头 | `figures/TABLE_repository_independent.tex:9` | 同一生成器；输入 `data/audits/repository-map-ablation-20260922/summary.json` 与 `data/audits/work-unit-planning-ablation-20260922/summary.json` | 与累计表统一调用和 token 标签；保留共享完整方法行。 |
| 接口细节来源记录 | 建议移入 `data/paper_figures/README.md` 的相应来源说明 | structural analysis 消融实现与冻结摘要 | 保存禁用结构分析后 map tool 返回现有计划状态的事实。 |
| 模型身份 | `sections/supplementary_experiments.tex:217` 的 `position model` | 冻结推荐检查结果或模型定义，具体文件未由快照确定 | 核实正式名称后决定补充解释或仅保留来源映射。 |

`figures/make_cumulative_components.py` 还生成主文仓库组件表和其他附录表。调整共享表头逻辑时，应检查影响范围，避免顺带改变主文的任务分组、正式模块名或数值。快照没有提供生成器源码，不能给出准确函数名或行号。

两张表采用横向分组，结构符合已有版式决定。是否出现长模块名拥挤或换行问题，需要后续编译后检查；本轮没有 PDF 视觉证据，不作版面通过判断。

## 七、最重要发现与需主代理裁定之处

1. **必须保留三种不同的成本对照。** 68.4% 是全部累计组件相对基础 Repair Agent；68.0% 是 repository context management 的相邻累计条件比较；19.8% 使用另一项研究的完整方法运行。当前数值相容，主要问题是 `complete context mechanism` 和 `complete references` 容易模糊比较对象。

2. **推荐任务的成本与覆盖结果应完整保留。** 累计组件增加成本而最终检查数不变；结构分析增加成本但更早达到 131/145；移除规划降低成本但最终少通过一项检查。这些均是有信息的结果，不应通过本轮文字审核删去或降调。

3. **消融边界需要清楚，接口载荷可移至来源记录。** 保留结构分析按需调用、规划消融保留上下文满时重建等机制事实。主代理需核对 `unassigned files` 的分配对象和 `checkpoint propagation` 的内容，不能据此新增固定路由或逐工作单元重启 Verifier。

4. **缺测与最终提交评分是本节最重要的统计说明。** 完整方法第一次提交的 n/a、独立记录的八个执行失败标记、两个中间候选各缺一个 retrieval 测量，都不能改成零或混入 145 项分母。最终使用 130，而非无规划条件中途达到的 133。

5. **`position model` 和退化原因需要来源核对。** 快照没有给出该模型的读者可理解名称，也没有提供共享训练入口改动导致退化的底层证据。建议主代理保留原有事实强度，核对后明确名称与因果依据；本轮不自行编造解释。

6. **表头可统一为 `LLM calls` 和 `Total tokens`，但须确认字段含义。** 表注明确调查、修复及一次初译的成本范围后，表头可以更短、更清楚。同步修改应落到 `figures/make_cumulative_components.py`，全部 42 个数值单元格保持不变。
