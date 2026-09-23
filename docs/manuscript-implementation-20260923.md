# 已批准方案执行记录

2026-09-23。检查点 `651a796`，分支 `codex/iclr-2027-template`。用户批准全文修改方案并要求子agent严格按方案执行。

分工：Astra/high分别负责方法、实验、附录A–H、引言/相关工作/结论、图表生成器。各自独占文件；主代理核对事实、维护意见表、整合并检查PDF与逐词对照。综合方案的最终取舍固定，审查报告中的其他候选不自动采用。

## 实施前状态

论文任务文件干净，当前提交作为检查点；现有方法图PDF/PNG/PPTX/SVG、其他用户文件保留。快照记录127个文件哈希、各表数值和摘要原文。读取全部91个意见，待执行项按S16改为已批准待执行。

## 追加证据核对

原生JAX的formal_launch_manifest列出2任务×4方法共8条件，每条件40调用，总上限320调用；据此明确预算单位。推荐的前向loss由train_forward返回，训练loss由train_one_epoch返回，均为六条模型执行路径的三步观测。position映射到TwoTowerWithPositionDebiasedWeights，论文用位置去偏模型的普通描述，不使用内部case名。

## 实际结果与验收

已完成[批准方案](manuscript-review-20260923/00-revision-plan.md)的全部采用项，并按[持久清单](manuscript-feedback-register.md)重新核对91项要求。原审查报告中的其他候选没有自动进入修改。

| 范围 | 实际落实 |
|---|---|
| 方法 | 正文保留四类差异与调查动作；算法删除重复分支和低层状态操作；LLMCall、LLMToolStep和LLMTranslate标明模型调用；仓库操作通过共享上下文接入算法1、2。 |
| 实验与图表 | 初译程序及修复前评价状态统一；提交上限直接对应46/50、50/50、50/50；检测图区分均值31/18与个体3/12、4/12；程序/仓库消融分别说明对象、组件和成本。 |
| 引言、相关工作和结论 | 以具体训练计算、独立交接及修复动作说明贡献，明确具名成本比较；完整迁移、效率和跨框架结论保留。摘要逐字未改。 |
| 附录A–H | TorchAX仅在A.5；删除残余平均长度；修正Java应用对应；明确基线流程、预算单位、两类loss、检查分母、上下文机制及两种仓库消融；原生JAX十二来源与两修复任务分开说明。 |
| 排版整合 | 主文JAX caption及A.5标题去掉含糊的controls；首次PDF检查发现引言环绕图的内部分组使后续段落继承窄行宽，改为把图和相邻段落放入同一作用域。此修复没有改变段落文字、字号或边距。 |

图表子agent运行四个生成器，执行`tests/test_paper_figures.py`与`tests/test_paper_figure_layout.py`的15项既有检查，以及`tests/test_unified_paper_results.py`的10项检查，共25项通过。此后只调整文字和LaTeX分组，没有再次改图形生成逻辑。

主代理在最终版本执行以下核验：

- 全部25张表的数字序列与`651a796`一致；方法与附录的公式逐字不变。
- 摘要8句、135词，与编辑前快照及检查点原文一致。
- 33个受保护文件哈希不变，覆盖不可变基线、定量来源和用户4个方法图资产。`unified_results.json`唯一变化为`/natural_components/0/label`从`Independent evidence handoff`改为`LaDiM`，不涉及数值。
- `latexmk -pdf -interaction=nonstopmode -halt-on-error conference_101719.tex`成功。最终23页，正文至第10页；无overfull、未定义引用或重复标签警告。渲染全部23页巡检，并放大检查算法、主表、图3/4、消融表和附录末页，没有重叠、裁切或孤立短尾。
- 最终运行`scripts/update_manuscript_diff.py`。`output/manuscript-comparison/current.pdf`与主PDF的SHA-256相同，基线仍为`data/manuscript_baselines/pre-6pro-20260921/`。
- 清单91个ID唯一且全部写入本轮证据，相关本地文档链接、任务差异空白和提交范围检查通过。

核验快照及渲染保存在`tmp/manuscript-implementation-20260923/`和`tmp/pdfs/manuscript-20260923-final/`。以下指纹明确本次检查的版本：

| 文件 | SHA-256 |
|---|---|
| `conference_101719.tex` | `869e5113a9f2aff78ad7be244e62ae57a96b68da78851073cc21b1696f7beb05` |
| `sections/methods.tex` | `6b4e0ca46c3f6d0745d9334c7fa9f1049e2f98bbf6d8e454b1fe827dede83613` |
| `sections/experiments.tex` | `ce19b6414ee880b3ce78be462161710fc6572d67cb850e7d9d981bb08280f1e4` |
| `sections/supplementary_experiments.tex` | `6c98baf3423e276265163fb56ea466b05c29a9e0e8b048cb8a71cfc147cd4f67` |
| `conference_101719.pdf` | `4436fb3bd477e69100d0233e84f0e83018e6d23feef50836ecb9696c2a8a9b5e` |

本轮未运行或扩展实验。任务变更独立提交；用户方法图、`.vscode/`、`other/`及已有图形脚本留在提交之外。
