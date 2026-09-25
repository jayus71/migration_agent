# 论文方案第二次修订：0925加粗架构图、紧凑数字轴与Figure 4去留

2026年9月25日。用户指定figures/架构图0925加粗版.svg，并接受略微缩小；明确拒绝Figure 3上下排列，要求左右并排，横轴只写一次Task，逐柱显示1–29；继续询问loss对照是否有具名方法依据，以及Figure 4是否适合留在当前位置。本文件替代[本日上一版方案](manuscript-revision-plan-20260925.md)中的架构图满宽建议和Figure 3上下排列建议。其余论文修改维持先审方案的范围。

## 1. Figure 4的建议：保留证据，当前图移到附录

本轮找到直接相关、可以具名引用的工程工具：MindSpore TroubleShooter的loss_compare。它读取两份训练日志，提取loss，输出两条loss曲线、逐项误差曲线及最大绝对／相对误差统计。这个工具提供了loss对比用于训练迁移核查的具体来源。

已对照API文档和实现：loss_compare没有自动判错阈值、在线停止规则或首检时间输出。实现中的误差曲线为left−right，最大绝对误差统计取绝对值。本文Figure 4绘制的是绝对loss差值并按我们冻结的阈值归一化；31／18步由我们的0.02阈值和跨运行均值计算得到。图例不宜直接写成TroubleShooter detects at step 31，也不应标成MatchFixAgent。可以在图注或对应正文中引用TroubleShooter，解释loss对照的实际用途，曲线继续标为Loss difference。

另一个直接来源是MindSpore Transformers的Precision Tuning Guide。它依次比较第1步loss、第1步梯度local norm、第2步loss或更新后权重，并在长训练中继续比较loss。该来源既支持loss差异是有意义的核查信号，也说明梯度和更新检查本身已有工程实践。本文需要通过统一任务上的修复、验收与成本结果来说明方法效果。

目前这张图在正文中的证据优先级较低。保存数据已经显示，阈值降到10⁻⁵时两类故障的均值loss曲线都在第2步越阈，同批12条正常轨迹无误报。因此0.02下的31／18步无法作为广泛适用的延迟优势；即使引用一个具名工具，仍需解释阈值选择。两种受控故障在forward之后被注入，第一步loss与匹配正常轨迹完全相同，也使“后向／更新信号先出现差异”具有明确的构造条件。

建议将现有Figure 4及阈值敏感性结果一起放入附录，正文保留简短机制说明，并保留Table 4(a)在16个候选上的反馈消融结果：完整验收随执行、forward、梯度、更新信号逐步开放，从4/16、8/16、12/16到16/16。正文用这项实测结果说明增加训练信号后修复效果的变化；附录解释具体故障怎样在各信号中暴露。Figure 4仍保留第1步直接检测、0.02条件下均值31／18步、12次运行min–max阴影，以及逐运行检出分母。

如果后续决定保留在正文，其定位应为“同一轨迹上的检测信号对照”，并同时交代较小阈值下的结果；它不能承担未经运行的具名Agent检测性能比较。本轮首选移附录，这是待用户审核的新建议，尚未移动图、修改正文或重新编号。

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

Figure 4移附录的建议尚未实施，整稿页数也尚未重新计算。其余算法、表格、引用及3.4候选正文保持此前待审核状态。
