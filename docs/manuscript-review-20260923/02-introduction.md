# 引言逐句审查方案

## 范围与依据

审查版本：`d1d6a53d452827590969bc8e917b18f566f0b73d`，2026-09-23 工作区。范围为 `conference_101719.tex:48–72`，包括 Introduction 标题、38 句正文（贡献列表内 7 句）、Figure 1 的 2 句图注，以及图中的 10 个文字标签。全部逐项登记；本节没有表格或算法。仅生成本审核文件，没有修改论文或资产、运行实验、重新编译或提交 Git。

已读 `AGENTS.md`、`README.md`、意见清单、`.claude/skills/humanizer/SKILL.md`、写作 DNA，以及 `data/paper_figures/README.md` 的当前来源说明。以 `sections/methods.tex:4–101`、`sections/experiments.tex:7–125` 核对机制与结果语境；以 `figures/make_migration_motivation.py:9–30` 核对图中文字和成本口径，并查看现有 `migration_motivation.png`。此处的视觉检查只覆盖现有独立图片，未重新检查排版后 PDF 的实际尺寸。

适用既有意见：W01–W07、A04/A06–A08、M12–M14、E05/E08、R07/R08、F02、B01–B03。下文“新意见 6/7/8/9”指共同审查简报中的 2026-09-23 用户意见，分别对应通俗解释、全文逐句清理、保持科学主张力度、已确认范围和正式名称。候选均为待审方案，不替换清单中的已批准决定。

## 逐句台账

源文件行号均指 `conference_101719.tex`；同一行内按原句顺序编号。

| ID | 行号与短引文 | 处置 | 理由与方向 |
|---|---|---|---|
| IN-H01 | 48，`Introduction` | 保留 | 标题标准、准确。 |
| IN-01 | 50，`Migrating deep learning code allows existing models...` | 保留 | 一句明确迁移对象、作用与环境，适合作为背景。 |
| IN-02 | 50，`Differences in operator semantics, numerical precision...` | 保留 | 三项是实际不同来源，不属于装饰性列举。 |
| IN-03 | 50，`Automatic differentiation and optimizer interfaces...` | 保留 | 从一般计算差异推进到训练差异，引用保留。 |
| IN-04 | 50，`Large language models (LLMs) reduce the manual effort...` | 保留 | 准确定义 LLM 并区分翻译、测试和修复作用；现有引用不变。 |
| IN-05 | 50，`Training programs require these capabilities...` | 改写 | `these capabilities` 指代较远，重述泛化要求；改为明确迁移目标，承接下一段例子。见 C01。 |
| IN-06 | 60，`A translated program can produce a loss close...` | 保留 | 具体解释 loss 接近与梯度错误并存的机制，真实比较有必要。 |
| IN-07 | 60，`An optimizer error can also alter...` | 保留 | 独立说明更新错误出现的阶段，保留 current 时间条件。 |
| IN-08 | 60，`We use semantic drift to describe...` | 保留 | 定义全文问题术语，含义紧接两个具体例子。 |
| IN-09 | 60，`Training computations have dependencies...` | 改写并与下一句衔接 | 泛泛说有依赖；可让具体依赖承担解释。见 C02。 |
| IN-10 | 60，`A forward error may change gradients and updates...` | 改写并入 IN-09 | 两个方向都保留，直接阐明依赖如何指导诊断。见 C02。 |
| IN-11 | 60，`Locating the cause requires examining how...` | 保留 | 将数值差异推进到代码调查，是问题到方法的必要桥梁。 |
| IN-12 | 60，`This investigation also affects migration cost.` | 删除 | 没有交代影响方式或增量信息，下一句直接提供成本比较；删除后不损失数据或机制。见 C03。 |
| IN-13 | 60，`Figure...compares complete token use on common migration tasks...` | 改写 | `common migration tasks` 与 `full acceptance` 在引言初读时尚不具体；补出 PyTorch→MindSpore、共同 50 项，保留不到一半的优势。见 C04。 |
| IN-14 | 62，`We introduce LaDiM (Layered Diagnosis for Multi-Agent Code Migration)...` | 保留 | 定义方法全名及目标；专名中的 Multi-Agent 保持，不机械去连字符。 |
| IN-15 | 62，`Its Verifier Agent uses Layered Diagnosis to connect...` | 改写 | `connect discrepancies to code inspections and tests` 隐去指导关系；改为直接说明差异如何指导检查。见 C05。 |
| IN-16 | 62，`For example, matching forward values with missing gradients...` | 保留 | 具体例子能解释 Layered Diagnosis；`directs attention` 是调查线索，不把其扩写为固定诊断路由。 |
| IN-17 | 62，`Independent evidence handoff supplies the supporting...` | 改写 | 对大同行解释 independent 的可观察含义：将证据给在独立会话中的 Repair Agent；机制名和三类内容保持。见 C06。 |
| IN-18 | 62，`The Orchestrator schedules their work...` | 保留 | 明确调度和提交后验证职责，是用户确认表达。 |
| IN-19 | 62，`The Repair Agent retains its earlier attempts and feedback...` | 改写 | 一个句子叠加保留、关联、指导三个动作，拆成两句保留因果链。见 C07。 |
| IN-20 | 64，`For repositories, migration must preserve shared implementations...` | 改写 | `preserve shared implementations` 容易被读成保持实现不变；实际保留的是不同入口调用共享实现时的行为。见 C08。 |
| IN-21 | 64，`A change that corrects one caller can alter...` | 保留 | 准确提出共享代码影响与跨文件证据需要，为后续两个模块提供动机。 |
| IN-22 | 64，`LaDiM's repository context management combines Repository Structural Analysis...` | 改写 | 两正式名称保留；`exposes files and their interfaces`、`work units`、`prerequisites` 连续出现但作用不够直观。见 C09。 |
| IN-23 | 64，`Notebook editing tools, evidence associated with code versions...` | 改写 | 当前是工具/记录名词罗列；分别说工具做什么、上下文保留什么。见 C10。 |
| IN-24 | 64，`Changes to shared code invalidate affected checks...` | 保留 | 把共享实现变动和重新验证相关调用者连接起来，属于必要机制而非无用记账。 |
| IN-25 | 66，`We evaluate migration acceptance and token use from common initial translations...` | 改写 | 将 shared/common 的比较对象讲清，避免让读者以为所有原生翻译工具都接收共同初译。见 C11。 |
| IN-26 | 66，`LaDiM completes all 50 migrations...pass the initial checks.` | 改写 | 50、57.4% 保留，`pass the initial checks` 改成首次评估通过且无需修复；全文同步同一说法。见 C12。 |
| IN-27 | 66，`It also accepts 9/18 migrations...compared with 8/18...` | 保留 | 明确方向、分母和两基线；是与框架迁移不同的实证结果。 |
| IN-28 | 66，`On the time series repository...68.1% and 80.8%...two baselines.` | 改写 | 两个百分比没有逐一绑定方法；按结果段核对后明确对应 SWE-agent、MatchFixAgent。见 C13。 |
| IN-29 | 66，`On recommendation...highest behavioral coverage...` | 改写 | `recommendation` 缺对象，`behavioral coverage` 可直接用已定义的通过检查数量表达；保留最高及十个原始测试。见 C14。 |
| IN-30 | 66，`The JAX study verifies the same repair procedure...` | 保留 | 已有六例研究支持第二目标框架结论；不加防御性尾句，不塞入后端名称。 |
| IN-31 | 66，`Our contributions are as follows.` | 保留 | 为真实贡献列表提供简短导语，非机械段尾总结；列表仍有必要。 |
| IN-32 | 69，`We develop Layered Diagnosis, which uses dependencies...` | 保留 | 四类信息完整，贡献命名清楚，描述的是调查选择而非虚构固定路由。 |
| IN-33 | 69，`Adding these signals increases full acceptance from 4/16 to 16/16...` | 改写 | `these signals` 会把已有 execution 也当成新增；明确以 execution feedback 为起点，增加另三种观测，数字不变。见 C15。 |
| IN-34 | 70，`We introduce independent evidence handoff and repair history...` | 保留 | 汇总已经解释的机制和仓库作用，无新增内部术语。 |
| IN-35 | 70，`LaDiM repairs four of five failed saved translations...` | 改写 | `failed saved translations` 按新意见换成初次翻译后未通过评估的程序，保留四/五及支持库错误。见 C16。 |
| IN-36 | 70，`All three repair baselines repair none.` | 改写 | 读者此时只明确见到两种 agent 基线；补上 Direct repair，并说明零修复针对同五份程序。见 C17。 |
| IN-37 | 71，`We establish migration acceptance and efficiency...` | 保留 | 对应跨框架、语言、仓库实证贡献，保留有证据的结论力度。 |
| IN-38 | 71，`LaDiM preserves complete MindSpore acceptance with 57.4%...` | 保留 | 该数值在结果概览和贡献中重复，但贡献列表应独立可读；保留，不为纯去重削弱结果力度。 |
| IN-F01 | 55，`MindSpore migration costs, including initial translation...` | 改写 | 图需独立明确来源框架及成本单位；`all subsequent calls` 可明确为 LLM calls。见 C18。 |
| IN-F02 | 55，`Labels give accepted tasks out of 50.` | 保留 | 简短解释纵轴括号数的含义及共同分母。 |

正文共 38 句：20 句保留，17 句改写（其中两句合并），1 句删除。图注 2 句：1 句改写、1 句保留。另登记 1 个标题和 10 个图中文字标签。没有建议将引言的贡献、结果或必要机制移至附录。

## 需调整项与英文候选

### C01：明确训练迁移目标（IN-05；W01/W06、新意见 7）

原句：`Training programs require these capabilities to preserve the computations that determine each parameter update.`

问题：`these capabilities` 重复指回翻译、测试、修复，句子重点落在宽泛的“需要能力”。

候选：`Successful migration must preserve the training computations that determine each parameter update.`

### C02：用具体依赖替换抽象铺垫（IN-09/10；W01/W06、A08）

原句：`Training computations have dependencies that help investigate such errors. A forward error may change gradients and updates, while an incorrect update may affect later forward computations.`

候选：`Dependencies between training computations guide this investigation: a forward error may change gradients and updates, while an incorrect update may affect later forward computations.`

这里单个冒号用于立即解释依赖，不是连续枚举。若主代理选择全文减少冒号，可用：`These errors can propagate through training computations. A forward error may change gradients and updates, while an incorrect update may affect later forward computations.` 两个候选只选一个；后一候选更接近原稿句子节奏。

### C03：删无信息成本过渡（IN-12；W06、新意见 7）

原句：`This investigation also affects migration cost.`

删除此句，下一句直接引用图中成本事实。不要改成“调查导致全部成本下降”等未经独立归因的因果结论。

### C04：把图的比较对象写清（IN-13；A06、F02、新意见 6）

原句：`Figure~\ref{fig:migration-motivation} compares complete token use on common migration tasks, where LaDiM achieves full acceptance with less than half the tokens used by MatchFixAgent.`

候选：`Figure~\ref{fig:migration-motivation} compares total token use on the same 50 migrations from PyTorch to MindSpore. LaDiM completes all 50 with less than half the tokens used by MatchFixAgent.`

保留不到一半的强结果，与 5,159,134 / 12,097,425 = 42.65% 一致。初译和后续调用的范围由图注说明，正文无需再列成本账本。

### C05：将 connect 换成具体指导关系（IN-15；A08、W01）

原句：`Its Verifier Agent uses Layered Diagnosis to connect training discrepancies to code inspections and tests, establishing where source and target computations diverge.`

候选：`Its Verifier Agent uses Layered Diagnosis to guide code inspections and tests that locate differences between source and target computations.`

保留诊断指导检查与定位差异的机制，不增加自动分类器或固定诊断流程。

### C06：说明独立交接的实际形式（IN-17；W03、B03、新意见 6）

原句：`Independent evidence handoff supplies the supporting code observations, measurements, and hypotheses to a separate Repair Agent.`

候选：`Through independent evidence handoff, the Verifier gives its code observations, measurements, and hypotheses to a Repair Agent in a separate conversation.`

依据：方法 `sections/methods.tex:70–78` 与组件解释 `sections/experiments.tex:122`。这里保留机制名称，只用自然语言解释“独立”，不添加新分类或缩写。

### C07：拆开修复历史与后续使用（IN-19；W01/W04）

原句：`The Repair Agent retains its earlier attempts and feedback as repair history, connecting each correction to its measured effects and using unresolved discrepancies to guide the next attempt.`

候选：`The Repair Agent retains earlier attempts and feedback as repair history. It relates each correction to its measured effects and uses unresolved discrepancies to guide the next attempt.`

### C08：明确保留对象是行为（IN-20；W01、新意见 6）

原句：`For repositories, migration must preserve shared implementations across multiple entry points.`

候选：`Repository migration must preserve the behavior of shared code when it is called from different scripts and notebooks.`

脚本和 notebook 在仓库结果中均有明确对象（`sections/experiments.tex:47`）。后续正文仍可使用标准术语 entry point；此处不用新增名词表。

### C09：保留正式模块名并解释工作单元（IN-22；M12/M13、新意见 6/9）

原句：`LaDiM's repository context management combines Repository Structural Analysis, which exposes files and their interfaces, with Repair Dependency Graph Planning, which organizes related files into work units and coordinates their prerequisites.`

候选：`LaDiM's repository context management combines two modules. Repository Structural Analysis identifies files and their interfaces. Repair Dependency Graph Planning groups related files for repair and tracks dependencies between these groups.`

两个正式名称逐字保持。`groups related files for repair` 解释 work units；`tracks dependencies` 保持现有依赖规划作用，不虚构逐单元重启 Verifier。三句应留在同一段内，不拆成等长小段。

### C10：工具清单改为功能（IN-23；M13/M14、W06、新意见 7）

原句：`Notebook editing tools, evidence associated with code versions, and context reconstruction carry the investigation across files.`

候选：`Notebook tools edit code cells, while the evidence archive and context reconstruction preserve relevant findings as the agents move across files and code versions.`

候选保留 notebook、证据与代码版本、上下文重建三项作用。其语义应与后续方法保持一致：证据关联原代码版本并按相关性重建上下文；不要改写成任何旧证据在代码改变后都继续有效。下一句已经负责描述相关检查失效和重验，无需在这里再添限制句。

### C11：指明共同初译用于 agent 比较（IN-25；A06/W07、新意见 6）

原句：`We evaluate migration acceptance and token use from common initial translations under a shared protocol.`

候选：`The agent comparisons start from the same initial translations and measure migration acceptance and total token use under a shared evaluation protocol.`

这个范围条件落在实际比较处。原生 Direct LLM、CodeTransEngine 和 MSAdapter 等另有各自输入，不把它们改写为都接收共同初译。

### C12：把初次通过写明白（IN-26；E08/W01、新意见 6）

原句：`LaDiM completes all 50 migrations from PyTorch to MindSpore with 57.4\% fewer tokens than MatchFixAgent, covering both programs that require repair and programs that pass the initial checks.`

候选：`LaDiM completes all 50 migrations from PyTorch to MindSpore with 57.4\% fewer total tokens than MatchFixAgent. The savings cover programs that require repair and programs that pass the first evaluation without needing repair.`

此处的 `without needing repair` 表示初次评估已通过，不声称这些输入之后完全没有 LLM 调用；来源说明明确成本还包括最初通过输入上的后续调用。

### C13：将仓库节省数字与方法一一绑定（IN-28；A06/W07）

原句：`On the time series repository, all three agents complete migration, and LaDiM uses 68.1\% and 80.8\% fewer tokens than the two baselines.`

候选：`All three agents complete migration of the time series repository. LaDiM uses 68.1\% fewer total tokens than SWE-agent and 80.8\% fewer than MatchFixAgent.`

对应关系由 `sections/experiments.tex:47` 核对。这是主比较，不与组件的 68.0% 和 19.8% 混合。

### C14：用检查数含义代替宽泛 coverage（IN-29；E05/R04、新意见 6）

原句：`On recommendation, LaDiM achieves the highest behavioral coverage and passes all ten original tests.`

候选：`On the recommendation repository, LaDiM passes the most behavior checks and all ten original tests.`

保留最高表现主张，不新增数字堆叠。具体 130/145 保留在结果与表中；此处无需提前重列评价定义。

### C15：说清逐步加入哪些训练观测（IN-33；B01/W07、新意见 6）

原句：`Adding these signals increases full acceptance from 4/16 to 16/16 in the controlled repair study.`

候选：`In the controlled repair study, adding forward values, gradients, and parameter updates to execution feedback increases acceptance from 4/16 to 16/16 under complete verification.`

这里的四/十六至十六/十六属于独立的 16 个错误候选程序研究，与主比较 50 项分母分开。最终验收仍检查全部观测，不能将较少反馈条件写成采用较弱验收标准。

### C16：解释实际翻译错误研究（IN-35；E08/R08、新意见 6）

原句：`LaDiM repairs four of five failed saved translations, including errors in a supporting library.`

候选：`LaDiM repairs four of the five programs that fail evaluation after initial translation, including errors in a supporting library.`

保留 4/5，五是该研究中初次失败程序的数量；原有十份初译、另外五份初次通过的完整设置仍在实验部分定义，不能误换成主比较的初次错误子集。

### C17：明确三种零修复对照（IN-36；A06/R08、新意见 6）

原句：`All three repair baselines repair none.`

候选：`Direct repair, SWE-agent, and MatchFixAgent repair none of these five programs.`

此句明确指向上一句的相同五个程序，保留三种基线零修复的强比较。Direct repair 的工具和流程定义继续在实验设置，不在贡献条目中展开。

### C18：图注直接定义完整成本（IN-F01；F02/A06）

原句：`MindSpore migration costs, including initial translation and all subsequent calls.`

候选：`Total token costs for migration from PyTorch to MindSpore, including initial translation and all subsequent LLM calls.`

与后句合起来的图注候选为：`Total token costs for migration from PyTorch to MindSpore, including initial translation and all subsequent LLM calls. Labels give accepted tasks out of 50.`

## Figure 1 标签台账与同步位置

| ID | 标签及位置 | 处置与依据 |
|---|---|---|
| IN-L01 | `LaDiM (50/50)`，生成器 16 行 | 保留；方法名与共同分母准确。 |
| IN-L02 | `MatchFixAgent (50/50)`，生成器 16 行 | 保留；与 LaDiM 并列完整接受，不能改成低于 LaDiM 的接受数。 |
| IN-L03 | `SWE-agent (44/50)`，生成器 16 行 | 保留；分母包含执行失败/不可用结果，不能删减。 |
| IN-L04 | `Total tokens (millions)`，生成器 17 行 | 保留；完整词语，单位明确，与全部迁移调用口径一致。 |
| IN-L05 | LaDiM 柱端 `5.16`，生成器 15 行 | 保留；完整总量 5,159,134，按百万取两位小数。 |
| IN-L06 | MatchFixAgent 柱端 `12.10`，生成器 15 行 | 保留；完整总量 12,097,425，按百万取两位小数。 |
| IN-L07 | SWE-agent 柱端 `20.83`，生成器 15 行 | 保留；完整总量 20,831,495，按百万取两位小数。 |
| IN-L08 | 横轴 `0`，生成器 17 行 | 保留；横柱从零起点展示绝对成本。 |
| IN-L09 | 横轴 `10`，生成器 17 行 | 保留；统一百万单位。 |
| IN-L10 | 横轴 `20`，生成器 17 行 | 保留；统一百万单位。 |

Figure 1 维持简单横柱与右侧环绕布局，三方法都保留。现有 PNG 无文字重叠或裁切。生成器为 `figures/make_migration_motivation.py`，从 `figures/make_unified_results.py::load_data` 读取主结果；当前来源说明在 `data/paper_figures/README.md:79–85`。资产为 `figures/migration_motivation.pdf`、`.png`、`.svg`，LaTeX 在 `conference_101719.tex:54` 引用 PDF。

本轮建议仅改图注，不需修改标签或重生成图。以后若改标签，应同步生成器和三类资产，并在实际 2.42 英寸宽度检查；不要把图 4 的检测 step、均值 crossing 或未测基线检测成本加到 Figure 1。

## 重要发现与整合判断

1. 引言的问题→机制→证据链完整，38 句中 20 句可原样保留。重点修复具体含义与句子组织，不建议重写引言或削弱既有贡献。
2. 最直接的含义缺口是 `failed saved translations`、`pass the initial checks`、`behavioral coverage` 和 `two baselines`：应分别说明初次翻译后程序、首次评估、通过检查数量及具体方法对应关系。
3. 贡献中的 4/16→16/16 应明确反馈从 execution 扩展到其他三种观测，完整验收标准始终不变。4/5、三基线零修复和 57.4% 均保留。
4. 仓库段应解释共享代码在不同调用者中的行为，以及文件分组之间的依赖。两个正式模块名保持；不将依赖规划扩写为每个工作单元重新启动 Verifier。
5. Figure 1 的全部标签、数字和成本含义正确；图注补全 PyTorch→MindSpore 即可。引言仍只用横柱图，不加入未测量的检测时间或成本。
6. 需主代理统一的范围仅有两处：C11 应与实验设置共同初译的适用方法一致；C10 应与方法章对证据版本和上下文重建的具体解释一致。两处均有现有依据，不需要用户补新事实。既有清单 E10 关于 TorchAX 的旧决定已被新意见覆盖，但引言本身未出现 TorchAX，无需为此增加或删改引言内容。
