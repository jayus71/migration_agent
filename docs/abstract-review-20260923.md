# 2026-09-23 摘要原稿核对与局部修复

检查点为`8e6666c`。9月21日原摘要保存在`data/manuscript_baselines/pre-6pro-20260921/conference_101719.tex`的abstract环境，用户此次引用的LaDiM定义、仓库句和两个结果句均与该存档一致。固定基线不变。

此前把A04记为“已落实”的核验不充分：摘要仍以保存证据、协调文件修复描述操作，没有直接说明要解决上下文丢失的问题。A05也只保留了分开的成本句和范围句，没有实现用户要求的统一末句。此次重开并按用户最后明确的顺序修复。

## 本次修改

摘要前六句保持，包含Translator、Verifier、Repair Agent和Orchestrator。仓库句改为：

> To prevent these agents from losing relevant code context and diagnostic evidence during repository repair, we introduce repository context management.

“these agents”承接前文协作，目的明确为避免修复过程中丢失代码上下文和诊断证据。组件名称沿用正文，不再引入新的简称或复合名称。

最后两句合并为：

> Evaluation across framework migration, language migration, and repository tasks shows that LaDiM achieves comparable or better migration results with up to 80.8% fewer tokens than state of the art methods, demonstrating its effectiveness.

按用户最新要求依次给出范围、比较与最高节省、有效性；“最高节省”使用up to，不用表达上界限制的at most。摘要只保留80.8%这一数值，不再单列50任务/57.4%，不恢复已删除的初译四/五结果，不列具体基线名称。原50任务/57.4%的事实继续保留在引言、结果、图注和结论。

## 数值来源

`data/paper_figures/unified_results.json`的时间序列仓库行：LaDiM总token为2,614,230，MatchFixAgent为13,597,778，两者均通过69/69检查。节省为`100 × (1 − 2614230 / 13597778) = 80.774579%`，按主文现有精度为80.8%。这是比较中的最高节省值，未更改任何成本或验收数据。

## 本次实际联网查阅

旧意见表只记录了R2D2一个短语样例。本次重新在线读取以下原文摘要，并保存响应到`output/abstract-review-20260923/`：

- [R2D2](https://openreview.net/references/pdf?id=Hy7PKCFCQ)：摘要实际有“matches the state of the art on DMLab-30”。这能支持该名词短语的用法，但单独借用短语不足以完成本稿的比较句。
- [ViT](https://arxiv.org/abs/2010.11929)：摘要将比较对象（先进卷积网络）、分类结果和更低训练资源消耗写在同一句中。
- [Agentless](https://arxiv.org/abs/2407.01489)：摘要在说明SWE-bench Lite后，将修复表现、成本和现有软件agent比较联系起来。
- [EfficientNet](https://proceedings.mlr.press/v97/tan19a.html)：摘要明确ImageNet准确率及相对既有ConvNet的尺寸、推理速度差异。

这些原文采用不止一种结构。R2D2用无连字符名词短语，ViT等用带连字符的前置修饰。本稿依用户明确偏好保留无连字符的state of the art methods；没有声称外部论文都使用这一拼写，也没有向参考文献列表增加仅供行文参考的论文。

## 核验记录

主文源文件仅abstract环境变化，其他章节、算法、图表、数据、用户方法图及固定基线通过文件哈希对照。摘要从139词改为143词，未增加角色列表或实验数字堆叠。意见表106条全部重新对照：摘要相关项重核含义与来源，其他项依据未变源文件及新PDF版面核验。

最终编译、PDF查看和两份比较稿的实际结果在持久意见清单本轮日志中记录。没有运行或扩展实验。

主稿提交120f8c1；latexmk成功，23页，首屏及全部页面已检查。提交后LaTeX差异稿重建为33页，摘要页增删标记清楚，无overfull、未定义引用或链接警告。HTML比较同步更新。
