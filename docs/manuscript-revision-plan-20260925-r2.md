# 论文方案第二次修订：0925加粗架构图、紧凑数字轴与Figure 4去留

2026年9月25日。用户指定figures/架构图0925加粗版.svg，并接受略微缩小；明确拒绝Figure 3上下排列，要求左右并排，横轴只写一次Task，逐柱显示1–29；继续询问loss对照是否有具名方法依据，以及Figure 4是否适合留在当前位置。本文件替代[本日上一版方案](manuscript-revision-plan-20260925.md)中的架构图满宽建议和Figure 3上下排列建议。其余论文修改维持先审方案的范围。用户随后认可检测claim的证据解释，要求按这一方向更新论文修改方案；以下第1节已纳入确认的表述和证据安排。本轮修改方案文件，正式论文实施尚未开始。

## 1. 已确认的检测claim与证据安排

用户认可的claim为：

> 在受控的梯度和参数更新故障中，当前loss的一致性不足以判断训练计算是否正确；直接比较对应训练信号，可以在故障发生的训练步发现差异。

这一表述用于解释LaDiM为何需要同时观察forward、梯度和参数更新。实验条件为梯度缩放与部分更新抑制两类受控故障，各含四个模型、三个种子，共12条运行。每对匹配运行在第1步的loss差值完全相同，正常与故障由loss检查得到相同结果；对应的梯度／更新检查各12/12在第1步检出。这是信号检测和设计动机的证据。

### 正文拟采用的文字

将sections/experiments.tex目前“Training Signals and Detection Latency”段改为简短的训练信号机制说明，弱化检测延迟的比较性标题，并引用附录中的完整轨迹与敏感性分析。英文拟稿如下：

> Controlled gradient-scaling and partial-update faults can leave the current loss unchanged while altering subsequent training computations. In all 12 runs per fault, the first-step loss difference is identical to that in the matched fault-free run, whereas the corresponding gradient or update check detects the fault at that step. These observations motivate checking gradients and parameter updates alongside forward values during migration verification.

在Training signals消融段按现有结果承接其修复意义，拟采用：

> On 16 fixed faulty candidates, adding forward, gradient, and update feedback to execution checks raises final acceptance under complete verification from 4/16 to 16/16. Each added signal exposes an additional fault class and provides feedback for repair.

正式实施时使用自动附录／表格引用。中间两行8/16、12/16及完整成本保留在表4(a)，正文分析增加反馈的作用，不重复整张表。

### Figure 4与阈值分析的安排

将现有Figure 4和已有阈值敏感性结果纳入附录sec:detection-measurements，正文保留上述机制说明和16例信号消融。该安排已经写入本轮修改方案；当前没有移动图、调整编号或改写论文。

附录图保留两类故障、第1步直接检测、原始归一化曲线、12次运行的min–max阴影、分母与检测协议。图例继续使用Loss difference、Gradient norm difference、Update difference；在正文称Loss-only verification时，说明它是我们在同一轨迹上计算的检查规则。

附录图注拟稿：

> Training-signal differences under controlled gradient scaling (a) and partial update suppression (b). Source and target executions start from matched initial states and then train independently. Direct gradient and update checks detect their respective faults at step 1 in all 12 runs per fault. At the absolute loss-difference threshold of 0.02, the mean loss curves first cross at steps 31 and 18. Curves show means; shaded bands span the minimum and maximum across four models and three seeds. Differences are normalized by their respective thresholds.

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

本轮按用户认可的claim方向更新第1节，将正文短机制说明、表4(a)修复证据、附录曲线及敏感性组织为明确的修改安排。方案和反馈记录已更新，正式论文实施及整稿页数核验尚未开始。其余算法、表格、引用及3.4候选正文保持此前状态。


### 2026年9月25日claim方案更新记录

本轮检查点eb9e387。修改限于本方案、claim证据说明的状态提示及反馈登记；源稿、既有图表、冻结数据和基线不变。逐项核对上述文字中的12次运行、16个候选、阈值、个体首检及均值越阈的含义，沿用已经核验的数据；没有新增实验、重新编译或将历史检查写成本轮全稿核验。0925加粗架构图90%宽度及Figure 3左右并排、单次Task加数字轴的安排保持。
