# 论文修改方案：论证结构、实验安排与表达

本方案围绕训练行为保持组织论文，纳入 [仓库迁移最新结果](repository-migration-run-20260921.md) 的六组正式结果，并采用图 3 方案 B 的简洁柱状图。结论参考用户提供的 MOST 段落，按方法目标、具体设计、设计作用和实验结论展开。方案依据 2026 年 9 月 21 日的论文、指定对话「移除答案泄露并优化自主定位 (3)」、实验账本和实现代码，结合相关方法原文、写作样例及图表资料制定。

## 1. 全文的论证主线

训练代码迁移后，程序可以运行，损失也可以暂时接近源程序，但求导或更新已经发生偏差。前向计算、梯度和参数更新相互依赖，某一阶段的错误可能暂时隐藏，也可能传播到后续计算。LaDiM 利用这些依赖调查偏差的来源，将支持原因假设的测量和代码证据交给 Repair Agent，再根据修改后的训练结果继续修复。图 1 呈现这种偏差，方法章节解释如何据此诊断和修改，主实验比较完整迁移的效果与成本。自然故障和消融实验进一步检验修复能力及组件作用，仓库实验则考察这套过程如何处理跨文件依赖和多个入口。

摘要从迁移需求引出静默语义偏差，随后说明只检查执行或损失会遗漏哪些训练错误。`prevailing pipelines check only whether the migrated code runs` 对已有方法的概括过宽。MatchFixAgent 会生成语义测试，MindSpore 官方迁移指南也要求梯度及优化器对齐，项目自然案例中的两个 agent 基线还主动发现过梯度问题。因此，论文应将问题落在执行和损失一致仍可能遗漏训练偏差，以及如何利用训练观测持续诊断和修复。[MatchFixAgent §3](https://arxiv.org/html/2509.16187v1)、[MindSpore 迁移指南](https://www.mindspore.cn/docs/en/r2.4.1/migration_guide/overview.html)、[项目自然案例追踪](natural-baseline-probe-20260917.md)

`semantic drift` 在首次出现时解释为迁移造成的训练行为偏差，后文沿用该含义。解释机制时使用具体的 forward values、gradients 和 parameter updates。引言交代随机数处理、数值精度和算子语义等差异如何影响训练，图 1 的图注则说明实验实际施加的梯度缩放和部分更新抑制。

## 2. 章节与段落安排

| 位置 | 组织方式 | 本节完成的论证 |
| --- | --- | --- |
| Abstract | 一个完整段落 | 迁移中的训练偏差、LaDiM 的处理思路、最关键的效果与 token 结果、跨框架和跨语言有效性 |
| 1 Introduction | 按背景、问题和设计展开，最后概括贡献 | 需求与研究位置；图 1 揭示的困难；由困难推导设计；评估与贡献 |
| 2 Related Work | 按研究问题组织主题段落 | 翻译和迁移；训练行为验证；agent 验证与修复 |
| 3 LaDiM | 任务与观测；自主分层诊断；证据交接与修复；仓库协调 | 把设计目的、输入、动作和输出讲完整 |
| 4 Experiments | Experimental Setup；Main Experiments；Analysis Experiments；Ablation Studies | 效果与成本、泛化、机制和组件证据各有位置 |
| 5 Conclusion | 参考 MOST 的完整段落 | We introduced 交代目标，Specifically 解释设计，随后说明作用与总体实验结论 |
| Appendix | 任务构成、运行接入、完整协议、附加结果和轨迹 | 保存复现所需细节与完整结果 |

相关工作移到引言后面。引言只保留理解问题所需的代表性工作，相关工作负责具体比较，避免两处重复列方法。当前第 3 节实验随之成为第 4 节，交叉引用使用已有 LaTeX 标签更新。

段落按推理的完整性划分。一次观测、其解释、相应设计和必要例子可以在同一较长段落中展开。方法中分别讲工具、调查记录和记录用途的三个短段应合并，修复中的反馈、保留状态和终止条件也应连贯说明。实验设置将任务与验证放在一起，方法与预算、指标与成本各自集中交代。段落在问题或论证重点发生变化时拆分，长度随内容调整。

实验主体保留主实验、分析实验和消融的层级。`Repository Migration` 位于主实验，与单程序框架迁移、跨语言迁移并列。`Generalization Across Frameworks` 保留原题，在分析实验中介绍 JAX。自然故障增加为分析实验中的一段完整讨论和一张紧凑表。成本解释与图 3 相邻，避免主实验与分析实验分别重述同一组总数。

方法篇幅重点用于解释诊断、证据交接和仓库状态管理的设计目的及工作过程。任务定义和普通工具清单适当压缩，种子、容差、预算和底层接入集中放入实验设置或附录。结果章节围绕数据支持的判断展开，表格承担完整数值比较。[方法指南](https://mitcommlab.mit.edu/eecs/commkit/journal-article-methods-cs/)、[结果指南](https://mitcommlab.mit.edu/eecs/commkit/journal-article-results/)

## 3. 方法设计与作用

### 3.1 Task Definition and Training Observations

先定义迁移目标，再解释可比较性。源程序定义预期训练行为，迁移指定目标语言与框架。测试给两端相同输入和对应初始参数，通过参数映射比较训练计算。模型任务比较连续训练步骤，算子任务采用其适用的前向及梯度检查。具体任务范围在设置中集中说明。

删除反复出现的 `public training contract`、`task contract`。MatchFixAgent 和 InterTrans 使用 translation pair、source/target program、test suite、functional equivalence 等与具体对象对应的表达。论文中的 task specification 用于说明任务要求，evaluation protocol 描述比较过程，acceptance criteria 指通过条件，可编辑范围直接说明哪些文件允许修改。首次使用时交代各自内容，后文保持这一分工。代码中的 `contract` 字段留在实现说明中。[MatchFixAgent](https://arxiv.org/html/2509.16187v1)、[InterTrans](https://arxiv.org/html/2411.01063v1)

保留观测向量公式，用它统一表示各训练阶段的观测，公式后解释这些量之间的依赖。删除 `leaving unmeasured quantities missing`，其实际含义在报告格式附录中说明一次，即执行失败后未获得的测量记为 n/a。正文交代此时返回异常信息和已经取得的观测。

### 3.2 Autonomous Layered Diagnosis

本节解释如何利用训练计算的依赖关系缩小调查范围。前向计算发生偏差时，需要检查它是否造成了后续差异。前向值一致而梯度不同时，调查转向求导过程。如果梯度也一致，参数更新的差异则提示检查优化器行为。随后用缺失梯度的例子展开实际调查，说明 Verifier 如何检查参数注册和计算图，并用测试判断假设是否成立。

Verifier 只读候选代码，并可编写临时测试来核查假设。调查记录说明哪些测量和代码位置支持某个可能原因，同时保留尚未解决的问题，供后续修复会话复查。故障类别和修复位置由调查得出，任务输入不提供这些答案。当前 `D = {observations, hypotheses, locations, uncertainty}` 仅列出记录字段，可用上述调查实例替代。若保留形式化描述，应进一步说明记录如何被下一阶段读取和更新。

### 3.3 Evidence Handoff and Verified Repair

本节解释独立修复会话如何接收和使用调查证据。Verifier 完成初诊后，将支持假设的代码观察和测试结果交给 Repair Agent，使其能够复查依据并选择修改。Orchestrator 对提交的候选执行验收，新的测量随后用于检验修改是否解决问题，并指导下一次尝试。当前文件与修复历史随尝试保留，整个任务受累计预算约束。将角色分工与证据交接放在同一段中展开，可以直接对应连续会话的实验对照。进展提醒在预算管理中交代其作用。

统一使用 `Translator`、`Verifier`、`Repair Agent` 和 `Orchestrator`。前面三者是 LLM 角色，Orchestrator 是调度和外部验收组件。代码内部类名不必跟着改，论文正文、图 2 和图注统一。介绍外部方法时沿用其自身组件名，避免把 SWE-agent 的 controller 也误改为 LaDiM 的专有角色。

### 3.4 Repository Coordination

仓库扩展单设一节，先说明如何处理跨文件依赖和检查状态，再解释完整证据的检索及上下文管理。各机制对应的困难如下。

| 仓库中的困难 | 已实现的机制 | 应解释的技术作用 |
| --- | --- | --- |
| 模型、训练器和入口分散在多个文件 | Agent 依据公开代码提出工作单元及依赖，聚焦具备前置条件的单元 | 让相关接口的调查和修改能够一起推进 |
| 修改共享实现后，旧检查可能失效 | 候选代码变化使旧测量失效，并使相关单元及下游局部检查失效，保存检查对应的代码版本 | 用当前候选上的证据判断进度 |
| 多文件输出和 notebook 内容使会话增长 | 独立角色交接、实际切换工作单元或接近上下文容量时重建上下文，保留计划、完整假设与下一步、最新测量及仍与文件哈希匹配的已读代码 | 为当前编辑保留需要的信息，减少重复读取 |
| 摘要省略了大数组或长日志 | 完整观察归档在可编辑工作区之外，通过只读工具按记录和片段检索 | 支持进一步核查原始证据 |
| 局部检查通过，其他入口仍可能失败 | Orchestrator 最后执行整个声明范围的入口与训练验证 | 把局部进展连接到仓库最终验收 |

以上来自 [仓库机制说明](repository-agent-mechanism-20260920.md)、[当前运行协议](repository-migration-run-20260921.md)和 [实现](../scripts/repository_agent_mode.py)。归档检索和上下文重建属于仓库扩展；统一 50 项结果来自较早冻结的小程序配置。57.4% 的节省由那组实测账本支持，其原因分析不能追溯归给后来新增的仓库压缩机制。

方法描述采用最终仓库运行中的行为。首次选择工作单元和普通修复阶段续接保留完整对话，实际单元切换才触发相应的上下文重建。规划状态与候选代码版本分开管理，单纯调整计划不会使未改变代码的实际测量过期。完整假设、下一步建议和可检索证据指针随交接保留。容量阈值、代码缓存大小与阶段调用额度放附录。时间序列的成本优势支持整套仓库流程的效率分析，现有开发前后两次运行用于解释发现并修正的交接问题，各项修正的独立收益仍需对应消融测量。

图 2 保留用户此前决定的简单占位方案，先统一角色名和关键连接，为后续自行绘制提供内容规格。图中出现 Translator、独立调查、证据交接、Repair Agent、Orchestrator，以及 MindSpore/JAX 两个目标框架。仓库协调作为围绕工作区的组件，画出依赖状态、证据检索和检查失效。框架图中的 TorchAX、torch4ms 和桥接细节移到附录。正式更新时 PowerPoint、SVG 和供 LaTeX 使用的矢量 PDF 从同一内容生成。

## 4. 实验如何形成论证

### 4.1 主比较与成本

主表继续采用各集合自己的共同输入和验收。表中保留完整方法、接受结果、token 和调用数，正文重点解释下列关系。

LaDiM 在 MindSpore 集合上达到与 MatchFixAgent 相同的完整验收结果，并减少一半以上 token。Direct LLM、CodeTransEngine 和 MSAdapter 的 token 更少，但仍有部分任务未通过验收。SWE-agent 的 token 更多，验收通过率也低于 LaDiM。正文据此分析各方法在迁移完成度和成本上的差异。

图 3 进一步分析节省发生在哪些输入。LaDiM 在修复初始故障和确认初始已通过的程序时都减少了 token。下表由原始调用 ID 去重累加得到，每个 agent 的总量包含共同初译费用。

| 成本阶段 | LaDiM | MatchFixAgent | LaDiM 减少比例 |
| --- | ---: | ---: | ---: |
| 初始翻译 | 429,109 | 429,109 | 相同 |
| 初始已通过输入上的后续调查与确认 | 1,409,686 | 5,135,863 | 72.6% |
| 初始故障输入上的后续诊断与修复 | 3,320,339 | 6,532,453 | 49.2% |
| 总 token | 5,159,134 | 12,097,425 | 57.4% |

LaDiM 在 27/29 个不同输入上使用更少 token，其中初译已通过组为 19/20，初译故障组为 8/9。这说明总量优势覆盖了大多数输入。逐输入成本比的中位数 0.588 留在附录，正文结合总量和节省量柱状图分析。

MatchFixAgent 需要初译程序的事实在相关工作说明，成本口径在设置说明一次。原始调用账本已经把相同的 429,109 token 归入 LaDiM、SWE-agent 和 MatchFixAgent，总量无需再次加收。每个方法成本包含一份初译，物理账本中共享的生成只执行一次。复算脚本逐输入检查了共同初译调用 ID 属于各方法端到端调用集合，并与图表导出值逐项核对。

LaDiM 的 1、2、4 次提交结果保留为 46/50、50/50、50/50。MatchFixAgent 首次外部提交完成的事实放在预算解释中，连同各方法一次提交包含的内部操作一起说明。效率比较采用完整 token 和模型调用数，使不同原生编排的资源消耗可以直接比较。

跨语言结果重点分析修复增加了哪些成功任务。LaDiM 完成全部八个教材示例及一个应用程序，其通过集合包含 MatchFixAgent 的全部成功输入，并多完成一个循环网络示例，token 比两个 agent 对照更少。正文结合这一覆盖关系和成本比较展开，完整数量保留在主表。教材示例具有可比较的训练接口，应用程序还涉及依赖与集成工作，具体失败原因结合逐任务轨迹说明。

### 4.2 仓库迁移放进主实验

新增 `Repository Migration`，放在主实验中。六个正式条件已经完成，采用两个仓库一致的最终 LaDiM 实现及有效原生基线。三种方法对每个仓库获得相同源程序、共同初译、完整公开反馈和验收，修复上限均为 80 次调用、480,000 输出 token、3,600 秒和四次外部提交。双塔的训练 CLI 与数值验证调用候选提供的同一优化器工厂。具体预算、初始化、三步训练及确认种子写入设置，正文分析完整验收、成本和剩余偏差。[最终运行记录](repository-migration-run-20260921.md)

主表增加仓库面板，按仓库分组保留全部六行。下面给出建议展示的核心数据，模型调用及完整分项检查可放附录。

| 仓库 | 方法 | 完整验收 | 配对检查已通过 | 端到端 token |
| --- | --- | --- | ---: | ---: |
| 时间序列 | LaDiM | 通过 | 69/69 | 2,614,230 |
| 时间序列 | SWE-agent | 通过 | 69/69 | 8,199,825 |
| 时间序列 | MatchFixAgent | 通过 | 69/69 | 13,597,778 |
| 双塔 | LaDiM | 未通过 | 130/145 | 8,811,246 |
| 双塔 | SWE-agent | 未通过 | 104/145 | 8,316,552 |
| 双塔 | MatchFixAgent | 未通过 | 129/145 | 8,679,080 |

表注一次说明统计对象。时间序列为三个种子各 23 项检查，主脚本、notebook、教学片段及文档依赖均通过。双塔为公开种子上的 145 项声明检查，尚未触发确认种子；两个基线各有一项未测，保留在分母中并记为 n/a。配对检查包括数值、执行和源行为检查，具体数值子集在分析中说明。完整仓库接受数三个方法均为 1/2，检查通过比例描述每个仓库内部的完成程度。

仓库结果按两个问题展开。时间序列实验比较完成相同迁移所需的成本。LaDiM 用 35 次修复调用完成任务，相比 SWE-agent 的 80 次和 MatchFixAgent 的 69 次更少，端到端 token 分别减少 68.1% 和 80.8%。这组结果把小程序上的效率优势扩展到包含脚本、notebook 和教学入口的真实仓库。成本含各方法的全部修复调用和同一份初译，效率结果对应整套仓库流程。

双塔实验分析功能完成程度及连续训练中的剩余偏差。LaDiM 完成全部十个原测试，并通过训练 CLI、文件覆盖和文档依赖检查。它通过 99/114 项数值检查，比 SWE-agent 的 74/114 高 21.9 个百分点，与 MatchFixAgent 相同。两者通过的检查存在差异。LaDiM 完成了 MatchFixAgent 缺失的奖励模型推理检索及原测试、文件和文档工作，MatchFixAgent 则多通过一项参数更新检查。三个方法均未通过完整验收，正文结合这些差异说明各自完成的工作与剩余问题。

双塔中保留下来的偏差也呼应图 1 的问题。LaDiM 的 18 项前向损失和 18 项梯度检查全部通过，参数更新通过 15/18，物品表示通过 6/18。六条路径的物品表示均在第二、第三步发生偏差，合计 12 项，构成 LaDiM 的 15 项数值失败中的主要部分。损失、梯度和原测试通过后，连续训练中的更新及表示仍需要直接比较。后续调查可沿跨步状态和优化器行为检查原因。

完整分项检查、确认过程与费用统计放附录。旧试点及上下文开发记录保留在实验来源文档，正文主比较采用最终六组结果。来源为 [最终汇总](../output/repository-migration-20260921/final/summary.json)、[完整性核查](../output/repository-migration-20260921/final/final_integrity_audit.json)和 [共同检查统计](../output/repository-migration-20260921/partial_results.json)。

### 4.3 自然故障提升到正文分析

在 `Analysis Experiments` 中加入 `Repairing Natural Translation Faults`，考察实际初译中的错误能否被修复，以及初始已通过验收的程序是否继续通过。下表呈现全部对照。

| 方法 | 修复初始故障 / 5 | 保留初始已通过程序 / 5 | 最终通过 / 10 |
| --- | ---: | ---: | ---: |
| Direct repair with shared tools | 0/5 | 5/5 | 5/10 |
| SWE-agent | 0/5 | 5/5 | 5/10 |
| MatchFixAgent | 0/5 | 5/5 | 5/10 |
| LaDiM | 4/5 | 5/5 | 9/10 |

这一段重点分析调查能否产生有效修改。自然案例追踪显示基线也能主动发现梯度异常，因此最终修复和保留结果更能体现方法差异。选择当前配置下的一个成功案例，结合最终候选和对应轨迹说明最初发现了什么、怎样检查实现，以及修改后哪些测量恢复一致。历史 I-08/I-09 的归因材料仅用于对应历史运行的说明。

这组实验从给定目标候选开始，修复范围还包括支持它执行的库实现。正文说明这一范围，底层 bridge 名称与配置放附录。采用独立分析表报告自然故障修复，使这组修复 token 与主表从源程序开始的端到端 token 各自对应清楚的任务。来源为 [最终方法 CSV](../output/maintext-results-20260918/slim_main.csv)、[完整对照 CSV](../output/maintext-results-20260918/main_comparison.csv)和 [实验记录](maintext-results-20260918.md)。

### 4.4 检测与消融各回答自己的问题

`controlled signal studies` 改为具体的 `fault detection experiments` 和 `training signal ablation`。`controlled` 本身是正常实验用语，在介绍“固定其他条件、注入一种变化”时可以用 `controlled fault injection`。现稿将检测轨迹、反馈消融和修复效果笼统装进这个词组，读者看不出变量是什么。

检测实验解释观测时机。保留每步同步与连续保留状态这两种设置的区别，图 1 使用后者。图中梯度/更新在每个面板的 12 次运行中都于第 1 步发现故障，31 和 18 是均值损失曲线越过阈值的时间。单次运行中的损失检出数量是 3/12 和 4/12，平均曲线与个体检测时间各自说明。

训练信号消融解释所选检查如何触发和终止修复。4/16、8/16、12/16、16/16 是完整检测与修复流程的结果，正文分析缺少某类观测时，哪些错误会通过检查并使流程提前停止。实验名称和解释都围绕检查范围对整个修复过程的影响展开。

证据交接和上下文消融对应方法中的角色分工及信息保留。统一迁移集合里连续会话通过 49/50，独立交接通过 50/50，去掉历史或提醒也达到 50/50 且费用较低。自然故障对照进一步检验修复是否依赖先前的调查与修改。在带编辑格式辅助的参照配置中，保留历史时修复 4/5，去掉历史后为 0/5，两者都保留 5/5 正确程序。论文保留这一配置与最终精简配置的差别及完整对照矩阵，结合任务差异讨论历史的作用。

`Generalization Across Frameworks` 保留六个 JAX 修复的事实和三种子验证，说明共同观测接口如何支持另一目标框架。TorchAX 和 torch4ms 只在附录介绍；正文保留 JAX、MindSpore 和 PyTorch 等源/目标框架的名称。

## 5. 图表方案

### 图 1：摘要问题的直接证据

现有图 1 已具备所需的两个面板、阈值和检测箭头，主要调整正文与图注的衔接。正文先说明损失接近时求导或更新仍可能有偏差，再结合曲线解释各类观测何时显出错误。保留 `(a)` 的 loss/gradient 和 `(b)` 的 loss/update 内容，名称放图内。箭头标出第 1 步直接检测，以及均值损失差异在第 31 和 18 步越过阈值的位置，统一使用 `Loss difference`。

图注说明轨迹来自施加梯度缩放或部分更新抑制的实验，并区分均值曲线越过阈值与各次运行的检测时间。故障注入和跨步状态处理的详细配置放附录。

### 图 3：从总量比较推进到节省发生在哪里

现图左侧仅重复总 token，右侧的双对数散点需要读者同时判断横纵坐标与对角线。图内图例和注解占比较大。重画优先改善数据组织、留白、文字层级和颜色用途。

采用原方案 B 的紧凑双面板布局，图形小样已由子 agent 完成。图例位于左面板内部的上方空白处，计算方式和结果解释放入 caption。PNG 和可编辑文本的 SVG 位于 `output/paper-revision-plan-20260921/figure3-proposal-b-refined.*`，供正式替换论文图时使用。方案 A 的成本比点图保留作比较记录。

| 方案 | 左面板 | 右面板 | 用途 |
| --- | --- | --- | --- |
| B，采用 | 总成本分成初译、初始已通过输入上的后续调用、初始故障输入上的后续调用 | 每根柱表示一个输入比 MatchFixAgent 节省的 token，按初译状态分组并排序 | 从柱子的方向和高度直接读取节省量，并看出优势覆盖哪些输入 |
| A，保留作比较 | 与 B 相同 | 每个输入的 LaDiM/MatchFixAgent token 比及分组中位数 | 可用于补充分析，正文优先采用更直观的节省量 |

![图 3 方案 B 优化版](../output/paper-revision-plan-20260921/figure3-proposal-b-refined.png)

右面板标题为 `Savings on each input`，纵轴为 `Tokens saved (thousands)`。每根柱对应同一输入的一对完整迁移结果，组内按节省量排序，两个初译状态组以虚线分隔。绿色柱表示正节省，橙色柱表示 LaDiM 用量更高的两个输入。图内文字限于标题、轴标签和分组名，差值定义、排序方式及 19/20、8/9 的结果由 caption 说明。

左面板回答总量差异及成本构成，右面板回答优势覆盖范围及各输入的绝对贡献。正文引用“27/29 个输入更省”，构造细节及输入映射放附录。三种 agent 的总量都包含初译，初始错误输入上的后续成本包括失败尝试。右侧所有柱子的差额相加为 6,938,291 token，与两方法总量之差一致。共享初译在每一对成本中同时计入，并在求差时抵消。图 3 保持原 MindSpore 集合，仓库成本在主表的独立面板中呈现。

图注候选为：`Token use on the common MindSpore collection. (a) Totals include the shared initial translation and all subsequent calls, with subsequent costs grouped by whether the initial candidate passes the acceptance checks. (b) Each bar shows MatchFixAgent tokens minus LaDiM tokens for one migration input. Bars are sorted within each group, and positive values indicate lower token use by LaDiM. LaDiM uses fewer tokens on 19 of 20 initially accepted inputs and 8 of 9 initially faulty inputs.`

配色参考 Okabe–Ito，使用蓝 `#0072B2`、绿 `#009E73`、橙 `#D55E00` 及中性灰，颜色只承担明确含义，并以形状、位置和直接文字辅助辨认。[Color Universal Design](https://jfly.uni-koeln.de/color/)

此前调研涵盖山峦图、雨云图、箱线/小提琴图及成对数据呈现。山峦图适合多组分布随时间或条件的变化；雨云图结合原始观测、分布和统计摘要。当前两个组仅有 20 和 9 个配对输入，逐输入节省量能够保留全部实际比较，并直观呈现差额的方向和大小。因此图 3 采用节省量柱状图。山峦图可用于以后多组、足够样本的训练误差分布展示。[ggridges 官方介绍](https://wilkelab.org/ggridges/)、[Raincloud plots 原论文](https://pmc.ncbi.nlm.nih.gov/articles/6480976/)、[Wilke 的分布图说明](https://clauswilke.com/dataviz/boxplots-violins.html)

### 其他数据的作图价值

| 数据 | 合适的呈现 | 要回答的问题 | 当前安排 |
| --- | --- | --- | --- |
| 12 次运行的检测时机 | 累积检出比例的阶梯图，50 步仍未检出的轨迹保留为未检出 | 平均损失曲线之外，多少运行实际发现了错误 | 图 1 附录补图，正文已有时机解释 |
| 四类故障 × 四种反馈 | 状态矩阵，区分未触发修复、修复未通过、最终通过 | 缺少哪种观测会漏掉哪类故障 | 可以替换现信号表的一部分，逐例核对后绘制 |
| 自然翻译的十个输入 | 方法 × 输入的状态矩阵，标出原本正确与修复成功 | 各方法的成功集合如何重叠 | 正文紧凑表足够，矩阵可放附录 |
| 仓库入口、测试与训练检查 | 分仓库的覆盖矩阵，区分通过、失败、n/a；双塔再按训练步数排列各信号 | 功能完成与训练数值保持如何相互补充 | 采用最终六条件及共同检查统计，主文先用综合表，分项矩阵放附录 |
| 现有每调用用量与阶段记录 | 分阶段累计 token 曲线并标记实际验收事件 | 成本在哪个活动累积，何时形成有效修改 | 先核对阶段字段及完整账本，不按调用位置猜阶段 |
| 后续连续训练轨迹 | 误差随训练步数的曲线，按实际独立运行显示区间 | 完成迁移后是否出现累积漂移 | 当前补充方案中的待测量内容，未使用预测数据 |

最终按图表承担的分析任务取舍，保留提供新信息的图。正式图按 LaTeX 中的实际宽度检查，图中文字以 7.5 至 8 pt 为最低目标，并导出矢量 PDF。核对文字重叠、边缘裁切和图例位置，同时检查灰度下能否区分数据。小样的字体与尺寸随正式排版统一。

## 6. 术语与句法的全局修改规则

| 当前表达 | 全文统一处理 |
| --- | --- |
| public training contract / task contract | 任务要求用 task specification，比较过程用 evaluation protocol，通过条件用 acceptance criteria，可编辑范围直接说明哪些文件允许修改 |
| controller / acceptance controller | LaDiM 的组件统一为 Orchestrator，在首次出现处定义 |
| translator / verifier / repair agent | 作为角色名称统一为 Translator、Verifier、Repair Agent，普通动作保持小写 |
| controlled signal studies | 按具体实验写 fault detection experiments 或 training signal ablation |
| loss / forward 混用 | loss 是所测 forward values 的一部分；图 1 专门使用 Loss difference |
| update / optimizer state 混用 | 参数更新和优化器状态分别表述，沿用各实验实际观测范围 |
| preserve training behavior / pass acceptance | 前者描述迁移目标，后者描述通过指定检查的实验结果；全文分别沿用 |
| initially correct / initially accepted | 按实际初始验收结果分组时统一用 initially accepted，与图 3 一致 |
| whole-file test-guided repair loop | a repair loop that rewrites the candidate using test feedback |
| source-and-contract pairs | 附录用 distinct combinations of source program and evaluation settings，正文不反复出现 |
| provider-reported cached input tokens | cached input tokens reported by the provider，成本设置只说明一次 |
| target-backend execution | execution in the target framework |
| cross-language comparison | comparison across programming languages，或 Migration Across Languages |
| end-to-end token use | 可保留公认的 end-to-end，但连续出现时写 total tokens 或 tokens for the complete migration process |
| TorchAX / torch4ms / torchms | 实现名称及引用移入附录，正文与框架图只写目标框架 |

术语按对象的含义统一。task specification 和 evaluation protocol 分别说明要求与评估过程，首次出现时给出具体内容即可，作为普通描述性词语使用。表达相同概念时沿用已定义用语，尤其保持图表标签、实验设置与结果分析一致。

全文清理冒号和分号连接的句子，根据实际关系改为因果、条件或递进从句。句内多项技术对象首次定义时可以列举，后文在指代清楚时使用 these observations 等表达。长句拆分后检查段落是否仍然连贯，尤其避免连续几句分别介绍一个角色、一个工具或一个状态。方法说明围绕一次完整调查展开，让读者看到前一步的证据如何影响后一步的行动。

摘要和方法用现在时说明 LaDiM 的组成与行为，结论用 We introduced 回顾本文工作。Specifically 用于展开刚提出的机制，To this end 用于从目标引出实现手段，两者按句意选择。实验段先给出判断，再选取支持它的数字和具体差异。删去没有增加信息的段末总结，将 efficient model use 等抽象评价改成明确的 token 比较或修复结果。

连字符保留在确有必要的标准术语和专名中，例如 multi-agent、state-of-the-art、SWE-agent。密集修饰链改为介词短语或从句。公式、代码、DOI、论文原题和引文不受正文标点清理影响。

“Twelve task entries reuse existing native source programs”描述数据构造来源；“50 identifiers / 29 pairs / 24 files”描述编号复用。二者移入任务附录，附上来源映射与按实际调用计费的说明。正文只交代任务覆盖的计算类型、统一输入与验收，并指向该附录。

## 7. 关键段落候选

以下段落按上述结构与术语撰写，正式落稿时补齐交叉引用并与相邻段落衔接。仓库段落采用已完成的六组正式结果及共同检查统计。

### 摘要候选

> Migrating deep learning code across frameworks is a practical requirement for reusing training programs in new software and hardware environments. Framework differences can change how a translated program computes gradients and updates its parameters without causing runtime errors. Such semantic drift may remain hidden even when the program runs successfully and its loss initially agrees with the source. We propose LaDiM, a multi-agent framework that uses dependencies between training computations to guide diagnosis and repair. The Verifier investigates where the translated program diverges from the source and passes supporting evidence to a separate Repair Agent. Measurements after each submitted change guide further repair. For repositories, LaDiM tracks dependencies between files and retains evidence as work moves between them. On 50 migration tasks from PyTorch to MindSpore, LaDiM matches MatchFixAgent's full acceptance with 57.4% fewer total tokens, including initial translation. Experiments on MindSpore and JAX, together with migration tasks from Java to Python, demonstrate LaDiM's effectiveness across frameworks and programming languages.

摘要保留跨框架、跨语言结尾，并简要说明仓库协调的作用。核心数字采用 50 项集合上的成本比较，仓库实验的 80.8% 节省放在主实验展开。引言评估段概括时间序列仓库的效率及双塔中的训练行为偏差，使仓库方法与实测证据对应。

### 引言与图 1 的衔接

> A translated training program can produce a loss close to that of the source while computing incorrect gradients. An error in the optimizer can also alter the parameter update without changing the current loss or gradients. Figure 1 illustrates these cases by perturbing gradients or suppressing part of an update. The corresponding measurements detect each fault at the first step, whereas the mean loss difference crosses the detection threshold later. These dependencies also matter for diagnosis because an error in one computation can affect several downstream measurements. Locating the cause therefore requires examining how the translated code produces the observed differences.

### 方法概览

> LaDiM migrates a source training program into the requested language and framework through diagnosis and repair of an initial translation. After the Translator generates a candidate, the Verifier inspects its code and compares its training behavior with the source. The investigation produces hypotheses about the observed discrepancies and records the code and measurements supporting them. A separate Repair Agent examines this evidence to choose and test changes. The Orchestrator evaluates each submitted candidate and returns updated measurements so that the repair process can assess progress and investigate remaining discrepancies. This process continues until the candidate passes the acceptance checks or reaches the task budget.

概览交代各角色如何通过证据和测量衔接，后续小节展开诊断依据、交接内容及仓库协调的具体设计。

### 任务与训练观测

> The migration task requires the target program to preserve the source program's training behavior in the specified environment. The task specification identifies that environment and the files that may be modified. To make the computations comparable, the evaluation protocol supplies both programs with the same inputs and corresponding initial parameters and defines the observations and numerical tolerances used for acceptance. These observations follow the dependencies within a training step. The forward computation produces the values used to evaluate the loss. Differentiating the loss yields the gradients that the optimizer uses to update model parameters. The Verifier uses differences at these stages to direct its investigation. For example, matching forward values with missing gradients motivates an inspection of the differentiation path. If gradients agree but parameter updates differ, the investigation turns to the optimizer.

### 验收和成本设置

> Every submitted candidate is evaluated on the same inputs and corresponding initial parameters as its source. For training tasks, each program retains its own state across consecutive steps. Acceptance requires the applicable forward values and gradients to agree within the specified tolerances. Parameter updates and any optimizer state covered by the evaluation must also agree. All required checks must pass on the three evaluation seeds.

> We measure cost over the complete migration process, including the shared initial translation and all subsequent model calls. Each method's total includes prompt and completion tokens from unsuccessful attempts as well as cached input tokens reported by the provider.

对应具体实验的容差与状态规则在设置表或附录列清楚，正文沿用定义。逐步重置源状态只用于相应诊断实验，不写进一般验收段。

### 主实验的分析段

> LaDiM completes the MindSpore collection with less than half the tokens used by MatchFixAgent at the same acceptance level. The savings occur both when repairing faulty translations and when confirming candidates that already pass the acceptance checks. On initially faulty inputs, LaDiM reduces the additional diagnosis and repair tokens by 49.2%. It also uses fewer tokens on 27 of the 29 distinct migration inputs, so the aggregate reduction extends across most of the collection. Direct translation methods use fewer tokens but leave some tasks unresolved. SWE-agent requires more tokens than LaDiM and achieves lower acceptance.

这一段与图 3 相邻，结合总量和逐输入结果解释成本差异。主表保留完整数字，正文选用相同验收水平下的成本比较及节省覆盖范围。

### 仓库主实验段

> All three agents pass the complete evaluation on the time series repository, where a shared model is used by the training script, notebook and teaching examples. LaDiM completes the repair in 35 model calls and uses 80.8% fewer total tokens than MatchFixAgent and 68.1% fewer than SWE-agent. This result extends the efficiency comparison to a repository in which changes to shared code must work across several entry points.

> None of the three methods passes the complete evaluation on the recommendation repository. LaDiM passes all ten original tests and completes the training command successfully. It also satisfies the file coverage and documentation checks, which MatchFixAgent leaves incomplete along with original tests that cannot run because of a remaining source framework import. LaDiM and MatchFixAgent each pass 99 of 114 numerical checks, compared with 74 for SWE-agent. The remaining discrepancies in LaDiM occur despite agreement in every measured loss and gradient. Three parameter update checks fail, and item embeddings differ in the second and third training steps across all six paths. These failures show why verification must follow the evolving training state even after losses, gradients and the original tests pass.

### 自然故障分析段

> LaDiM repairs four of the five faulty programs from earlier translations and preserves acceptance for all five programs that initially pass the checks. The three repair baselines preserve the accepted programs but leave all five faults unresolved. Some baseline investigations identify gradient discrepancies, yet the submitted changes do not restore the required training behavior. The comparison therefore examines whether diagnosis leads to an effective repair when errors occur in translated code or in the libraries it uses.

### 结论候选

> We introduced LaDiM, a multi-agent framework for migrating deep learning code while preserving training behavior. Specifically, LaDiM uses dependencies between training computations to guide diagnosis and passes the resulting evidence to a separate Repair Agent. Verification after each submission guides subsequent changes, and dependency tracking with evidence retrieval supports repair across files. This design helps detect and repair semantic errors that remain hidden when evaluation checks only execution or loss. Experiments across frameworks and programming languages demonstrate LaDiM's effectiveness in preserving training behavior and its efficiency in diagnosis and repair.

结论按用户提供的 MOST 段落组织。首句用 We introduced 交代方法及目标，Specifically 展开诊断与证据交接，下一句补充复验和仓库支持，随后说明这些设计如何处理引言中的问题，最后概括实验支持。保持一个完整段落，不重复具体通过数和节省比例。这里用 Specifically 是因为后文直接解释方法如何工作。若改用 To this end，应让它紧接明确目标并引出为实现该目标所采取的设计。[本地写作 DNA](../literature/zhekai-du/Academic-Writing-DNA.md)、[LoCA 正式论文](https://openreview.net/pdf?id=4NRjdISWby)、[MIT 结论指南](https://mitcommlab.mit.edu/eecs/commkit/journal-article-discussion/)

## 8. 相关工作需要补的内容

相关工作适当压缩 DeepXplore 和 DeepGauge 的介绍，增加与框架迁移和训练行为更直接相关的研究。TensorScope 比较跨框架对应 API 的行为，NablaFuzz 检验自动微分产生的梯度。介绍它们之后，说明 LaDiM 如何利用测得的训练差异调查代码，并指导修改和复验。[TensorScope](https://www.usenix.org/conference/usenixsecurity23/presentation/deng-zizhuang)、[NablaFuzz](https://arxiv.org/abs/2302.04351)

与 MatchFixAgent 的比较围绕输入和诊断过程展开。它以已有源程序和译文为输入，通过多种语义分析指导测试和修复。LaDiM 包含初译阶段，并利用训练计算的依赖调查偏差。主实验比较两者从共同起点完成迁移所需的 token 和验收结果。与仓库 agent 的比较则解释共享接口如何协调修改、代码变化后如何更新检查状态，以及如何验证多个入口的训练行为。

## 9. 实施顺序与交付检查

1. 按本方案冻结章节和每节要证明的判断，先移动相关工作、补充仓库方法、安排自然故障，再改句子。
2. 统一角色和任务术语。将重复配置说明、输入复用、torch4ms/TorchAX 接入移入附录，同步清理图 2 及表头。
3. 按完整段落重写摘要、引言、方法和结果分析，采用少量数字支撑判断。保留贡献、真实失败和实际费用口径。
4. 采用图 3 方案 B 的简洁版，图例置于图内，解释集中到 caption，同步更新生成脚本、标签、图注和输出资产。仓库面板从最终六条件和共同检查统计导出，保留完整接受状态、失败、缺测及全部调用成本。
5. 按仓库 humanizer 规则审阅全文，包括标题、图注和表注。重点检查并列清单、密集修饰词、同形短段、冒号/分号连接及重复总结。
6. 图表更新后运行已有数据与布局检查，核对总量和逐输入成本相加一致。用 `latexmk` 编译，在正文实际宽度检查图文与分页，满足当前九页主文限制。方案与小样阶段只读账本并作统计，不启动训练或模型 API。

复算结果保存在 [evidence-summary.json](../output/paper-revision-plan-20260921/evidence-summary.json)，包含输入 SHA-256、三方法分阶段 token 和配对统计。本次交付为修改方案与图形小样，工作分支为 `codex/iclr-2027-template`。方案阶段的写作审阅仅更新本文档，已有论文、正式图表及实验修改保留在原工作区。
