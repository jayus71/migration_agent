# 论文方案第二次修订：0925加粗架构图、紧凑数字轴与Figure 4去留

2026年9月25日。用户指定figures/架构图0925加粗版.svg，并接受略微缩小；明确拒绝Figure 3上下排列，要求左右并排，横轴只写一次Task，逐柱显示1–29；继续询问loss对照是否有具名方法依据，以及Figure 4是否适合留在当前位置。本文件替代[本日上一版方案](manuscript-revision-plan-20260925.md)中的架构图满宽建议和Figure 3上下排列建议。其余论文修改维持先审方案的范围。用户随后认可检测claim的证据解释，要求按这一方向更新论文修改方案；以下第1节已纳入确认的表述和证据安排。本轮修改方案文件，正式论文实施尚未开始。

## 完整任务清单：原始十项意见与后续确认

原始要求全部保留。以下作为当前方案的统一入口，补齐初版与本轮修订之间的对应；后续明确决定优先。用户此次重贴原始清单用于检查覆盖情况，不恢复0914图源、重复Task标签或上下排列候选。

| 原始要求 | 当前修改安排 | 详细依据与进度 |
|---|---|---|
| 架构图及解释 | 使用0925加粗SVG导出矢量PDF，按90%正文宽度包含；同步方法开头和图注，解释调度、三个Agent、分层诊断、证据交接与仓库模块 | 本文第2节；英文统一见本文第5节E01–E02，图源由后续确认替换；PDF和尺寸预览已完成，论文未替换 |
| 1. 伪代码稍缩字号，比较全宽与半宽／环绕 | 比较10pt全宽、10pt环绕、9pt全宽、9pt环绕，按相同内容测整页净收益 | 初版第2节；9pt已列为试排候选，正式稿字号与官方规则的冲突待处理，尚未试排算法 |
| 2. 表格稍缩字号并排查表前空白 | 9pt候选与算法共享字号决定；检查固定两行标题框、浮动体间距、齐底伸展、主动间隔及分页保护，分别处理多余占位 | 初版第3节；已定位表4标题固定高度等来源，尚未更改表格 |
| 3. 正文／附录自动识别引用 | 用cleveref的cref/Cref替代硬编码Appendix加ref，编译核对附录及附录子节类型 | 初版第4节；此处为交叉引用，文献cite命令保持 |
| 4. 图号前缀可配置 | 集中定义figure引用为Fig./Figs.，正文用自动引用输出Fig. 1等 | 初版第4节；图注编号沿用模板 |
| 5. 3.4未定义组件 | 删除指定首句及先列名称再使用的开头，按结构分析、依赖规划、证据和上下文、算法接口展开，首次出现即解释职责 | 本文第5节E03给出完整四段英文拟稿，保留notebook工具、代码版本相关证据和检查失效机制 |
| 6. Figure 3(b)横轴 | 两子图左右并排，横轴左端仅写一次Task，逐柱横排1–29，删除Migration inputs | 本文第3节；已试排并核对，图高45.1 mm，正式论文未替换 |
| 7. Figure 4阴影与loss对照依据 | 明确阴影为12次运行min–max；引用已核对的loss比较实践；采用已确认的受控故障claim，将曲线及阈值敏感性纳入附录方案，正文保留机制说明与信号消融 | 本文第1节含正文英文拟稿、附录图注、阈值分析和claim—证据对应；不把曲线标为未测具名方法 |
| 8. Table 3窄表、正文环绕与单位 | 将方法列转成方法行，尝试约55%–60%宽度的左表右文；比较图注及旁侧正文后的净占高，token单位millions | 初版第8节已有表格候选，保留全部方法、分组、验收和成本含义；尚未试排 |
| 9. Table 4(b)标题及全文token单位 | 改为单行Repair components，取消两行固定标题占位；正文、图表及附录成本统一millions，成本通常三位小数，预算按精确值换算，同步生成器 | 初版第9节；原始整数账本及预算不变 |
| 10. 页数检查及压缩 | 实施后编译检查主文结束页与总页数；优先调整图表、算法和占位，再精简重复说明，超出方案的大段删移另列审核 | 初版第10节，纳入本轮Figure 4附录安排及最新图形尺寸；当前仍24页、主文至第10页，新稿页数未测 |

[初版完整方案](manuscript-revision-plan-20260924.md)保留各项的详细实现与文字候选。本表及本文第1–3节确定当前安排；初版已被更新的图源、标签形式和Figure 4定位按本表执行。拟写入论文的英文统一以本文第5节为准，供用户逐段润色；此前各版英文保留为历史，不再作为并行候选。

字号问题尚有一个具体待决条件：初版核对的ICLR官方要求写明“do not change font sizes”，未列算法或表格例外，因此当前方案包括9pt独立试排，不把正式稿缩为9pt记作已经确定或已经满足格式要求。该状态不影响其余项目继续准备。

## 1. 已确认的检测claim与证据安排

用户认可的claim为：

> 在受控的梯度和参数更新故障中，当前loss的一致性不足以判断训练计算是否正确；直接比较对应训练信号，可以在故障发生的训练步发现差异。

这一表述用于解释LaDiM为何需要同时观察forward、梯度和参数更新。实验条件为梯度缩放与部分更新抑制两类受控故障，各含四个模型、三个种子，共12条运行。每对匹配运行在第1步的loss差值完全相同，正常与故障由loss检查得到相同结果；对应的梯度／更新检查各12/12在第1步检出。这是信号检测和设计动机的证据。

### 正文拟采用的文字

将sections/experiments.tex目前“Training Signals and Detection Latency”段改为简短的训练信号机制说明，引用附录中的完整轨迹与敏感性分析。完整英文见第5节E06；表4(a)相邻的完整消融分析见E07。两处分别交代信号可观测性和修复效果，并保留各自的模型、候选、反馈及预算条件。

正式实施时使用自动附录／表格引用。中间两行8/16、12/16及完整成本保留在表4(a)。

### Figure 4与阈值分析的安排

将现有Figure 4和已有阈值敏感性结果纳入附录sec:detection-measurements，正文保留上述机制说明和16例信号消融。该安排已经写入本轮修改方案；当前没有移动图、调整编号或改写论文。

附录图保留两类故障、第1步直接检测、原始归一化曲线、12次运行的min–max阴影、分母与检测协议。图例继续使用Loss difference、Gradient norm difference、Update difference；相邻文字使用verification using loss alone，说明它是我们在同一轨迹上计算的检查规则；图例直接标信号名称。

附录图注、完整解释、阈值表及全部图内标签的英文见第5节E08–E11。原来的连字符密集候选由这些完整拟稿替代。

附录相邻文字／敏感性表同时报告：0.02下，50步内loss检出分别为3/12和4/12；10⁻⁵下，两类故障均12/12检出，梯度故障均在第2步，更新故障在第2–8步，两条均值曲线均在第2步越阈，同批正常对照0/12误报。正常样本和事后阈值重算的条件就近写明。原冻结阈值和主方法验收结果保持，敏感性分析不反向改写历史协议。

31／18步用于描述0.02这一具体设置。正文的claim采用第一步的信号可观测性解释，不再将“普遍早几十步”作为这张图的结论。故障注入发生在forward之后这一构造条件在附录协议中保持明确。

### 每项claim由哪项证据支撑

| Claim或分析目的 | 对应证据 | 方案中的用途 |
|---|---|---|
| 当前loss不足以覆盖后向／更新错误，直接检查能识别本组受控故障 | 匹配正常对照、第1步12/12检测、完整轨迹与敏感性 | 正文简述设计动机，附录呈现机制验证 |
| 增加训练反馈改善本组候选的完整修复验收 | 表4(a)：16个固定候选，完整验收4/16、8/16、12/16、16/16 | 主文保留信号消融及机制分析 |
| 依赖关系如何帮助定位错误原因 | 对应的诊断记录、代码证据或明确隔离此因素的实验 | 不从这张曲线推导排序优越性，也不将信号越阈写成LLM代码定位正确 |
| 完整方法的修复效果与token效率 | 共同任务上的方法比较、真实翻译错误修复和组件消融 | 保留现有实测范围、预算、分母与成本结果 |

实施时联动检查摘要、贡献、方法、实验、图注与附录对该图的引用。Layered Diagnosis的机制描述继续说明如何使用训练依赖关系指导调查；其效果归因按上表对应证据组织。本方案不增加“首次检查梯度／更新”或“优于所有loss检测方法”等新结论，不启动额外实验。

### Loss对照的具名来源

已核对MindSpore TroubleShooter的loss_compare API与实现。它读取两份训练日志，输出loss曲线、逐项误差和最大绝对／相对误差统计，提供loss比较用于训练核查的具体工程来源。该工具没有自动判错阈值、在线停止规则或首检时间输出；其误差曲线为left−right，我们的图使用绝对差值并按自身协议阈值归一化。因此只把它引用为loss对照的实践依据，不把本文曲线标为TroubleShooter或MatchFixAgent的检测结果。

MindSpore Transformers的Precision Tuning Guide依次比较第1步loss、第1步梯度local norm、第2步loss或更新后权重，并在长训练中继续比较loss。它用于说明训练信号核查的已有实践；本研究对信号组织和修复流程的效果仍由相应实验说明。

### 本轮核对的直接来源

1. [TroubleShooter loss_compare API](https://github.com/mindspore-ai/toolkits/blob/e0486eee96a1893b5e1b59f02669804a2d796030/troubleshooter/docs/api/widget/loss_compare.md)：两份日志、loss曲线、误差图、CSV及统计输出。日志横轴是提取值的序号，工具要求两份日志的打印间隔一致。
2. [TroubleShooter loss_compare实现](https://github.com/mindspore-ai/toolkits/blob/e0486eee96a1893b5e1b59f02669804a2d796030/troubleshooter/troubleshooter/widget/loss_compare.py)：检查FileInfo、plot_error、get_stat_info和compare_loss，确认上述计算及没有自动阈值规则。文档与源码固定到同一提交，分别核对下载哈希。
3. [MindSpore Transformers Precision Tuning Guide](https://www.mindspore.cn/mindformers/docs/en/r1.7.0/advanced_development/precision_optimization.html)：核对Stage 2的Comparison of Step1 Losses、Comparison of local norm Values for step1、Optimizer Computational Troubleshooting，以及Stage 3的训练loss比较。
4. [DeepDiagnosis官方复现仓库](https://github.com/Wardat-ISU/ICSE2022)：README说明它通过训练回调观察内部状态与统计。此轮只核对其用途，未运行或评估该方法，不把它当作当前loss曲线的来源。

检索接口本轮连续返回503；以上结论来自直接读取并核对官方网页和代码，未根据搜索摘要推定。来源链接和哈希见[sources.json](review-evidence/manuscript-20260925-r2/sources.json)。

## 2. 架构图：改用0925加粗版，按90%正文宽度预览

已确认文件为figures/架构图0925加粗版.svg，SHA-256为734e9aa91ab771394d990ceee4c2029f7fe8772dd089825c4b762c01275421a5。导出PDF的全部可提取文字使用Times New Roman Bold，无位图；原SVG没有修改。

按用户接受缩小的决定，当前选用90%正文宽度，物理尺寸125.7×76.2 mm；95%备查版本为132.7×80.5 mm。90%比新图满宽省8.5 mm，比当前旧图仍高13.9 mm。最小字为4.27 pt，粗体增强了字形对比；已直接查看最终截图，主要模块、流程和小标签保持原内容，没有发现导出裁切或新增重叠。

方案不再推荐上一轮的满宽要求。后续正式替换时使用0925源图与这一缩放比例，方法图解释同步采用已提案的内容，具体正文改动继续待审核。

[90%加粗图截图](review-evidence/manuscript-20260925-r2/architecture-90percent.png)；[矢量PDF](review-evidence/manuscript-20260925-r2/architecture-0925-vector.pdf)。

## 3. Figure 3：左右并排，Task只写一次

按用户要求取消上下排列，也不再重复Task 1、Task 2等文字。最终试排保持两个子图左右并排，(b)横轴左端只写Task，下方横排1至29；没有Migration inputs。为容纳全部数字，适度增加(b)宽度，将单位移至子图标题“(b) Tokens saved (millions)”，保留(a)总成本轴的millions单位。右图表示MatchFixAgent减LaDiM的token数，正负方向继续由图例和图注说明。

图在正文中的宽度134.1 mm，高度45.1 mm；当前正式资产同宽高度44.2 mm，差约0.9 mm。这版比上一轮上下排列的73.2 mm减少28.1 mm。全部数字均无重叠、无裁切，数字最终字号6.24 pt，最小相邻间距约0.74 pt；已目视查看导出截图，能够逐项对应柱子。

保留全部29根柱、两个负值、20个初始通过／9个需要修复的输入分组、组内排序、左图三个方法及各成本分层。20与21之间的分隔线保留，分组含义由现有图注解释。编号沿用上轮冻结输入映射，50个任务标识的验收分母不变，总token节省仍为6,938,291。此处只调整展示，没有重新运行方法。

[数字横轴截图](review-evidence/manuscript-20260925-r2/figure3-horizontal.png)；[矢量试排](review-evidence/manuscript-20260925-r2/figure3-horizontal.pdf)。

## 4. 交付和验证

[单页选定布局预览](review-evidence/manuscript-20260925-r2/selected-layouts.pdf)展示90%加粗架构图和左右并排数字横轴。复现入口为[scripts/review_manuscript_figures_20260925_r2.py](../scripts/review_manuscript_figures_20260925_r2.py)，独立输出位于output/manuscript-review-20260925-r2/。上轮0924图、完整Task标签和上下排列试排保留为历史证据，不再作为当前推荐。

本轮检查点983d2c1，新增方案、预览、脚本和反馈登记后单独提交。1,080个受保护文件前后哈希相同，包含论文源码、正式图形生成器、已包含图表、冻结数据、官方样式与新SVG。核对字体、矢量属性、标签重叠、冻结成本与源文件哈希，并查看最终截图；没有编译或修改正式论文、刷新未变的基线比较、重跑实验或推送。完整验证见[verification.json](review-evidence/manuscript-20260925-r2/verification.json)。

本轮按用户认可的claim方向更新第1节，将正文短机制说明、表4(a)修复证据、附录曲线及敏感性组织为明确的修改安排。方案和反馈记录已更新，正式论文实施及整稿页数核验尚未开始。算法与表格布局继续待试排；英文候选按下文S58更新记录及第5节汇总。


### 2026年9月25日claim方案更新记录

本轮检查点eb9e387。修改限于本方案、claim证据说明的状态提示及反馈登记；源稿、既有图表、冻结数据和基线不变。逐项核对上述文字中的12次运行、16个候选、阈值、个体首检及均值越阈的含义，沿用已经核验的数据；没有新增实验、重新编译或将历史检查写成本轮全稿核验。0925加粗架构图90%宽度及Figure 3左右并排、单次Task加数字轴的安排保持。


## 5. 拟加入和替换的英文全文（供逐段润色）

本节把本轮方案涉及的英文集中在同一处。E01–E17覆盖正文、图注、表注、标题与标签；E18列出全文统一token单位时需要替换的句子。引号块内是拟写入论文的英文，块外中文说明修改位置与范围。编号仅供审阅，不写入论文。参考命令保留LaTeX形式，正式实施后自动生成编号。

这一版减少连字符，优先写清谁做什么、观察到什么、为什么需要这些信号。组件名称在首次出现的同一句中解释；算法函数名、方法专名及数学记号保持。摘要、贡献、结论和其余未列段落没有新增改写；Generalization Across Frameworks标题保持。

### E01　方法开头：替换方法节第一段

> LaDiM uses the dependencies among execution, forward computation, gradients, and parameter updates to guide diagnosis and repair. The Translator produces a candidate in the requested language and framework. The Verifier Agent examines the code and compares source and target computations to investigate discrepancies. It passes its observations and hypotheses to a separate Repair Agent, which tests the proposed causes and revises the candidate. The Orchestrator schedules the agents, evaluates each submitted candidate, and returns the results for further repair. For repository migration, the agents also use tools to inspect code structure, plan work across files, and retrieve evidence from earlier conversations. \Cref{fig:architecture} shows the workflow.

这里的依赖关系用于解释诊断依据；不加入“每个训练步调用LLM”或“固定顺序遍历所有层”的新说法。MindSpore与JAX的适用范围已有正文和图示，保留各自实验设置。

### E02　0925加粗架构图：完整图注

> LaDiM's migration workflow. The Translator creates a candidate, the Verifier Agent investigates discrepancies in execution and training computations, and the Repair Agent uses the evidence to test possible causes and revise the code. The Orchestrator schedules their work and checks each submission. Repository tools support code inspection, repair planning, and evidence retrieval across files and conversations. The code edit and signal traces illustrate the workflow.

最后一句说明图中代码与曲线的示意性质。图内已有英文沿用用户0925加粗SVG，不在这次方案中重写图源文字；论文使用其矢量PDF和90%宽度安排。

### E03　3.4 Repository Coordination：完整替换四段正文

删除指定首句“A change to a shared implementation can affect several callers in a repository.”及原先罗列组件的开头；算法3保持现有操作和记号。

> LaDiM coordinates repository repair by keeping the repair plan, code observations, and investigation evidence available as work moves between files and conversations. Repository Structural Analysis lets the agent inspect files, imports, function and class definitions, and notebook structure when needed. Repair Dependency Graph Planning groups related target files into work units, assigns each unit a repair goal and selected tests, and records prerequisites between units as a directed acyclic graph.

> The agent selects a work unit whose prerequisites have valid local checks, then edits the files assigned to that unit. LaDiM records syntax checks and the tests selected in the plan. When the target files or dependency plan change, it invalidates checks for the affected units and any units that depend on them, so the agent can check those files again. The Orchestrator determines acceptance by evaluating the complete repository, including its entry points and training computations.

> Notebook tools let the agent inspect and revise code cells while checking the syntax of each edit. An evidence archive stores code observations, measurements, hypotheses, and conversations together with the corresponding code versions. When evidence passes to the Repair Agent, work moves to another unit, or the conversation approaches its capacity, \textsc{PrepareContext} rebuilds the conversation from the current plan and relevant records. It can restore observations from earlier code reads when the corresponding files have not changed.

> \Cref{alg:repository} connects these tools to the diagnosis and repair procedures in \cref{alg:diagnose,alg:repair}. The context $C$ stores the dependency graph in $C.G$, local check results in $C.Q$, and archived evidence in $C.E$. \textsc{UpdateDependencyGraph} updates the repair plan. \textsc{Execute} handles unit selection, file and notebook operations, tests, and evidence retrieval. These operations update the shared state $S$ and context $C$, returning observations $o$ and the units $U$ affected by changes to the files or plan. All work units share the repository files, repair history, and total budget.

### E04　Figure 3：完整图注

> Token costs for MindSpore migration. (a) Total costs include initial translation and subsequent calls, grouped by whether the programs pass evaluation before repair. (b) Each bar shows MatchFixAgent's token cost minus LaDiM's for one distinct input. Inputs 1 to 20 pass before repair, and inputs 21 to 29 require repair. Bars are sorted by savings within each group. Positive values indicate lower costs for LaDiM. The 29 distinct inputs represent the 50 task identifiers used to report acceptance. Both methods accept all 50 tasks. Token costs and savings are in millions.

正文关于1、2、4次提交预算的46/50、50/50、50/50结果保持，不因图注写最终验收而删去。

### E05　Figure 3：拟变更的图内文字

| 位置 | 最终英文／数字 |
|---|---|
| 左子图标题 | (a) Total tokens |
| 左纵轴 | Tokens (millions) |
| 右子图标题 | (b) Tokens saved (millions) |
| 右横轴左端，只出现一次 | Task |
| 右横轴逐柱刻度 | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29 |

两个子图继续左右并排。删除Migration inputs；已有方法名、成本分层和分组图例保留，E04说明分组与正负方向。这里的Task编号是图内展示编号。

### E06　正文检测段：完整小标题与段落

小标题：

> Checking Training Computations

正文：

> A fault in gradient computation or a parameter update can occur after the loss for the current step has already been computed. We examine this case by scaling gradients or suppressing part of an update in four models with three seeds each. At step 1, the loss difference between source and target is identical in each faulty run and its matched run without the fault. The corresponding gradient or update check detects the fault at that step in all 12 runs for each fault. These results show why migration verification needs to check gradients and parameter updates as well as forward values. \Cref{sec:detection-measurements} reports the trajectories and the effect of changing the loss threshold.

### E07　表4(a)相邻正文：完整训练信号消融段

保留原小标题Training signals。这段替换原段全部内容，保留16个候选和固定实验条件。

> We compare four sets of feedback on 16 fixed candidates from a CNN, an image MLP, a Transformer classifier, and a small causal language model. Each model contributes one candidate with an execution fault, one with a forward fault, one with a gradient fault, and one with an update fault. The source programs, candidates, tools, and budgets are the same across settings. The available feedback determines when repair starts and stops, while final acceptance always uses complete verification. Adding forward, gradient, and update feedback to execution checks raises final acceptance from 4/16 to 16/16 (\cref{tab:signal-ablation}a). The number of faults missed before repair falls from 12 to 8 to 4 to 0. Forward comparisons reveal incorrect computed values, gradient comparisons reveal errors in differentiation, and update comparisons reveal errors in parameter changes. Each added signal makes another class of faults available for repair.

### E08　附录检测实验：完整替换说明

保留Detection Measurements小节和sec:detection-measurements标签。下列英文替换现有实验说明；原来的三条差值公式放在最后两个短段之间，公式本身不改。

> The detection study uses four models, three seeds, and 50 training steps. We introduce two faults after the loss for the current step has been computed: scaling the gradients and suppressing part of the parameter update. For each fault, we compare source and target executions under two settings. In one setting, the target starts every checked step from the source state. In the other, the executions start from matching states and then retain their own states as training proceeds. The thresholds are 0.02 for the absolute loss difference, 0.05 for the absolute difference between gradient norms, and 0.03 for the relative parameter update difference.

> \Cref{fig:gradient-drift} shows the executions that retain their own states. At step 1, the loss difference in every faulty run is identical to that in its matched run without the fault. A decision based on this value alone therefore gives the same result for both runs at that step. The gradient check detects gradient scaling at step 1 in all 12 runs, and the update check detects partial update suppression at step 1 in all 12 runs.

> At the loss threshold of 0.02, loss checks detect gradient scaling in 3 of 12 runs and partial update suppression in 4 of 12 runs within 50 steps. The mean loss curves cross the threshold at steps 31 and 18, respectively. These are the first crossings of the mean curves; individual runs cross at different steps or stay below the threshold. The shaded bands show the minimum and maximum at each step across the 12 runs.

> Reducing the loss threshold detects more of these faults and detects them sooner (\cref{tab:loss-threshold-sensitivity}). At $10^{-5}$, the loss check detects gradient scaling at step 2 in all 12 runs and partial update suppression between steps 2 and 8 in all 12 runs. No matched run without a fault crosses this threshold in the recorded 50 steps. The largest loss difference in those runs is $3.815\times10^{-6}$. Thus, the delay after step 1 depends on the threshold, while the identical loss values at step 1 explain why the loss check cannot distinguish these faults at that step. We recompute the thresholds on the saved trajectories; the runs without faults are matched controls, not a separate set used to calibrate a threshold.

> Comparing loss values is an established practice in migration checks. MindSpore TroubleShooter's \texttt{loss_compare} tool compares two training logs and reports loss curves and error statistics \cite{mindspore_troubleshooter_loss_compare}. The MindSpore Transformers precision guide also uses loss, gradient norms, and updated weights to investigate numerical discrepancies \cite{mindspore_precision_tuning}. Here, verification using loss alone applies our stated threshold to the recorded loss differences. TroubleShooter does not specify this threshold or report the detection times shown here.

> We measure the absolute loss difference, the absolute difference between gradient norms, and the relative parameter update difference as follows.

> Here $\Delta\theta$ and $\Delta\hat\theta$ denote the source and target parameter updates, and $\epsilon$ prevents division by zero. Each curve in \cref{fig:gradient-drift} is divided by its detection threshold. The main migration comparison uses the tensor comparisons specified in \cref{sec:migration-settings}.

两个新文献键为拟新增键，尚未写入bib文件，分别对应第1节已经核对的TroubleShooter固定提交文档及MindSpore Transformers r1.7.0精度指南。正式实施时写入完整文献条目。阈值表标签tab:loss-threshold-sensitivity也为拟新增标签。

### E09　附录检测图：完整图注

> Differences in training computations under (a) gradient scaling and (b) partial update suppression. The source and target start from matching states and then train independently. Gradient and update checks detect their respective faults at step 1 in all 12 runs for each fault. At the loss threshold of 0.02, the mean loss curves first cross at steps 31 and 18. These crossings describe the mean curves, not the detection times of individual runs. Curves show means, and shaded bands span the minimum and maximum across four models and three seeds. Each difference is divided by its detection threshold.

### E10　附录检测图：全部拟用标签

| 位置 | 英文 |
|---|---|
| 子图(a)，放在图内 | (a) Gradient scaling |
| 子图(b)，放在图内 | (b) Partial update suppression |
| 横轴 | Training step |
| 纵轴 | Difference / threshold |
| loss曲线图例 | Loss difference |
| 梯度曲线图例 | Gradient norm difference |
| 更新曲线图例 | Update difference |
| 水平线 | Detection threshold |
| (a)第1步箭头 | Gradient check: step 1 |
| (b)第1步箭头 | Update check: step 1 |
| (a)loss均值越阈箭头 | Mean loss crossing: step 31 |
| (b)loss均值越阈箭头 | Mean loss crossing: step 18 |

阴影在E09解释为最小值至最大值，不在图内追加密集说明。此图移到附录后仍由自动引用编号。


### E11　阈值敏感性表：标题、表头、数据与表注

完整caption：

> Effect of the loss threshold on detection in the saved trajectories. Each fault has 12 runs from four models and three seeds. Detection is measured over 50 training steps.

表格分成上下两块，共用Loss threshold列，避免横向挤入两类故障的所有指标。以下四个阈值来自已保存的敏感性CSV，0.02为原阈值。

(a) Gradient scaling

| Loss threshold | Detected runs | First detection step | Mean curve crossing | False alarms |
|---|---:|---|---:|---:|
| 0.02 | 3/12 | 10 to 11 | 31 | 0/12 |
| 0.005 | 12/12 | 3 to 37 | 9 | 0/12 |
| 0.001 | 12/12 | 2 to 8 | 3 | 0/12 |
| $10^{-5}$ | 12/12 | 2 | 2 | 0/12 |

(b) Partial update suppression

| Loss threshold | Detected runs | First detection step | Mean curve crossing | False alarms |
|---|---:|---|---:|---:|
| 0.02 | 4/12 | 6 to 20 | 18 | 0/12 |
| 0.005 | 8/12 | 3 to 42 | 6 | 0/12 |
| 0.001 | 9/12 | 2 to 14 | 2 | 0/12 |
| $10^{-5}$ | 12/12 | 2 to 8 | 2 | 0/12 |

完整表注：

> The Detected runs column counts runs that cross the threshold. First detection step gives the earliest and latest first crossings among detected runs. Mean curve crossing is the first step at which the mean loss difference crosses the threshold. The False alarms column counts matched runs without a fault that cross the threshold. Runs that remain below the threshold are excluded from the range of detection steps. All thresholds are applied to the same saved trajectories.

数据来源：[loss-threshold-sensitivity.csv](review-evidence/manuscript-20260925/loss-threshold-sensitivity.csv)。两块False alarms使用同一批正常对照，分母不相加。更低阈值的全部历史结果保留在该CSV，本文选择四行说明从原阈值到两组全部检出的变化。

### E12　Table 3：完整caption、分组与表头

> Repair and native conversion on six faulty JAX candidates. LLM repair allows up to four submissions, and its costs cover investigation and repair. Native conversion runs once without an LLM and is accepted only if it removes the supplied fault. Tokens are in millions.

| Method | Accepted | Calls | Tokens |
|---|---:|---:|---:|
| **LLM repair** | | | |
| LaDiM | 6/6 | 76 | 0.674 |
| Direct repair | 6/6 | 57 | 0.353 |
| **Native conversion** | | | |
| Ivy | 0/6 | 0 | 0 |
| torch2jax | 0/6 | 0 | 0 |

用约55%–60%正文宽度试排左表右文；以上文字同时适用于最终全宽候选。Generalization Across Frameworks正文沿用，仅将引用换成自动引用，不为了环绕新增解释。

### E13　Table 4：完整caption、子标题与表注

Caption：

> Effects of training signals and repair components. (a) Each $+$ adds a signal to the preceding row, ending with all four signals on 16 faulty candidates. Final acceptance uses complete verification. (b) Repair history and independent evidence handoff on ten translated programs. Parentheses give the number of repaired programs among the five that fail before repair. All three settings preserve the five programs that pass before repair. (c) Comparisons with and without each repository component on the time series repository. Every setting passes all 69 behavior checks across three seeds.

子标题：

> (a) Training signals

> (b) Repair components

(c)沿用原表分组与完整组件名称；不新增缩略术语。表头保持Feedback / Accepted / Tokens、Condition / Accepted / Tokens以及Component / Without component / With component / Calls / Tokens / Saved。

完整表注：

> Tokens are in millions. In (a,b), they cover investigation and repair. Panel (b) provides examples of the edit format and feedback on incorrectly formatted edits. In (c), calls cover investigation and repair, and tokens also include initial translation. Saved gives the percentage reduction in tokens. Each setting in (c) is run once. The two comparisons use separate runs of LaDiM with all components, so their token costs differ.

### E14　全文token单位：统一说明

在附录Task Construction and Accounting的成本说明中增加一次：

> Token costs are reported in millions and rounded to three decimal places. Totals are calculated before rounding. Token budgets retain their exact values after conversion to millions.

这段也解释独立四舍五入可能出现的末位差异。成本与预算分开：例如16384的严格预算写0.016384 million，不能舍为0.016。零成本、缺测n/a、不适用的横杠继续保留。

### E15　附录仓库成本表：完整caption

替换tab:repository-costs的caption：

> Training checks and complete costs for repository migration. Each training signal has nine checks for time series, from three steps on three seeds, and 18 for recommendation, from six model execution paths and three steps on the public seed. Calls, input tokens, and output tokens cover investigation and repair. The Tokens column gives the total including the shared initial translation. All token values are in millions.

### E16　附录仓库组件表：两处完整caption

累积组件表tab:repository-cumulative-full：

> Cumulative agent components on both repositories. The Checks column gives the number of passed behavior checks. Calls cover investigation and repair, and tokens also include the shared initial translation. Each row adds a component to the preceding row. Tokens are in millions.

独立组件表tab:repository-independent：

> Repository comparisons that remove one component at a time. Both comparisons use the same LaDiM run with all components for each repository. The Checks column gives the number of passed behavior checks. Calls cover investigation and repair, and tokens include initial translation. Tokens are in millions.

两张表内部的比较口径不同，保留各自caption与表4中的独立运行说明。

### E17　附录原生JAX实验：完整caption

替换tab:native-jax的caption：

> Repair of two failing native JAX translations from twelve source workloads. Calls and Tokens cover repair. Two tasks and All sources give total token costs, including the shared initial translation costs of 0.031 and 0.140 million tokens, respectively, counted once. Each method accepts 1/2 repair tasks and 9/12 source workloads overall. All token values are in millions.

### E18　全文token单位：全部拟替换的英文句子

以下按sections/supplementary_experiments.tex中的小节和出现顺序定位。只替换列出的句子，保留所在段落的其他信息；合入LaTeX时仍按整段一行保存。百分比沿用原始整数计算，不能从三位小数显示值重新计算。

**E18.1　Task Construction and Accounting：InterTrans成本句**

> InterTrans uses 2.286 million tokens, including 0.574 million from incomplete generation calls and 1.712 million from the completed search.

**E18.2　同小节：MindSpore分组成本连续四句**

> The shared initial translations for MindSpore cost 0.429 million tokens. This amount is included once in each repair method's total. Subsequent LaDiM calls use 1.410 million tokens on programs that pass evaluation before repair and 3.320 million on programs that need repair. The corresponding MatchFixAgent totals are 5.136 and 6.532 million tokens.

**E18.3　Numerical Comparisons and Migration Settings：完整预算段**

> For each program, each agent has cumulative investigation and repair limits of 40 LLM calls, 0.120 million output tokens, 1,800 seconds, and four submissions. Each call allows at most 0.016384 million output tokens, and LaDiM allows eight calls per investigation or repair stage. Initial translation is separate from this repair budget and allows at most 0.131072 million output tokens per call. Test-guided repair rewrites the complete candidate, with four repair rounds and at most 0.131072 million output tokens per call. For each repository, each agent has cumulative limits of 80 calls, 0.480 million output tokens, 3,600 seconds, and four submissions, with at most 0.032768 million output tokens per call. Output budgets include reasoning tokens, and all input usage is recorded.

**E18.4　JAX修复协议：预算句与成本句**

> For each task, both methods allow up to four submissions, 40 LLM calls, 0.120 million output tokens, and 1,800 seconds, including investigation.

> Across the six tasks, LaDiM uses 76 calls and 0.674 million tokens, and Direct repair uses 57 calls and 0.353 million tokens.

**E18.5　受控MindSpore修复集合：总成本句**

> Total token use is 39.983 million for LaDiM, 42.579 million for SWE-agent, and 12.459 million for Direct repair.

**E18.6　十二个源程序的配对修复集合：结果句与预算句**

> LaDiM accepts 12/12 and MatchFixAgent accepts 11/12, using 6.643 and 14.506 million tokens, respectively.

> Each method has up to four submissions, 40 LLM calls, 0.120 million output tokens, and 1,800 seconds per task.

**E18.7　十个初始翻译程序：成本句**

> LaDiM uses 13.207 million tokens.

**E18.8　Repository Migration：初始翻译两句**

> The time series translation uses three generation calls totaling 0.164 million tokens. The recommendation translation uses 20 calls totaling 0.368 million tokens.

**E18.9　仓库调查预算句**

> For the repository experiments, investigation allows up to six LLM calls and 0.064 million output tokens.

**E18.10　累积组件：时间序列成本连续三句**

> On time series, LaDiM with all three added components uses 1.937 million tokens in total, 68.4\% fewer than the base Repair Agent. Adding repository context management to investigation and independent evidence handoff reduces total tokens from 6.047 million to 1.937 million. Input tokens for investigation and repair fall from 5.731 million to 1.700 million.

**E18.11　结构分析：推荐仓库成本句**

> Enabling structural analysis uses 9.962 million tokens in total, 38.9\% more than the 7.172 million used without it.

**E18.12　依赖规划：时间序列结果句**

> Without Repair Dependency Graph Planning, time series completes all 69 checks after one submission, using 21 calls and 1.804 million tokens in total.

**E18.13　依赖规划：推荐仓库预算句**

> Removing planning exhausts the budget of 0.480 million output tokens after 69 calls, while LaDiM with all components uses all 80 calls.

**E18.14　原生JAX协议：严格预算两句**

> Each method on each repair task has a cumulative budget of 40 LLM calls, four submissions, 0.120 million output tokens, and 1,800 seconds, including investigation. Each initial translation has one call with at most 0.016384 million output tokens.

**E18.15　原生JAX翻译：输入、输出与总成本句**

> Initial translation of all twelve sources uses 0.029 million input tokens and 0.110 million output tokens, totaling 0.140 million, including both generation failures.

原始值为29455、110269、139724，独立舍入后分项之和与总数显示值相差0.001 million；按E14统一说明，不修改账本。

### E19　引用、伪代码、间距和页数：没有另加英文段落的项目

正文图引用集中配置为Fig.和Figs.，通过\cref或\Cref生成，例如Fig. 3、Figs. 3 and 4。正文／附录引用自动识别为Section或Appendix；不把文献\cite替换为交叉引用命令。本节拟稿里的命令在实施后使用实际编号，不写死附录字母或移动后的图号。

伪代码字号和全宽／环绕试排、表前空白、Table 3环绕、Table 4标题高度、页数压缩均是既定排版任务，不需要新增英文解释。算法caption和指令保持现有文字。若试排后确实需要删减额外正文，会把具体英文删改另列审核。

### 2026年9月25日S58英文集中稿记录

本节是用户润色用的英文候选，替代本方案此前零散英文。保留S53的0925加粗图、S54的Figure 3左右并排与单次Task标签、S56确认的检测claim，以及原始十项要求。E01–E19包含拟替换英文、新增文献键的来源、token数值的显示规则和无须新增正文的排版项。正式论文、正式图表和实验数据不在本轮修改范围内。
