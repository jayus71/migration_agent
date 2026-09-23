# 2026-09-23 摘要、算法和版面修改记录

本轮按用户 S18 修改。分支为 `codex/iclr-2027-template`，检查点为 `9bb5033`：单独保存用户删除摘要中 `including initial translation` 的改动。用户四个方法图资产、编辑器配置及其他文件保持原状。

## 文献核对与采用安排

实际查阅本地 MatchFixAgent 原文第 2–5 页及附录 C，和 CGDM 原文第 2 页、§5.1–5.3。MatchFixAgent 的三条贡献分别概括方法、验证价值及多 agent 架构，具体百分比放在贡献前的实验概述；CGDM 的贡献说明两个设计及实验验证，不逐条重复性能数字。因此本稿三条贡献删除重复的 4/16、16/16、4/5、零修复及 57.4%，保留设计与验证发现。原实验结果仍在引言前段、结果和表格中。

MatchFixAgent 在 Evaluation 开头简述研究问题、benchmark、基线及模型，把修复子集与评价条件放在对应结果小节，把完整设置放入附录 C。CGDM 在 Dataset Description 中介绍规模和划分，在 Implementation Details 中定义共同条件。这支持本轮安排：setup 保留所有任务集合、规模和研究用途；十程序的可编辑范围放到 Repairing Translation Errors；检测实验的共同初态和独立训练条件放到 Training Signals and Detection Latency。没有删除任务定义。

参考文件：

- `literature/Ibrahimzada 等 - MatchFixAgent Language-Agnostic Autonomous Repository-Level Code Translation Validation and Repair.pdf`
- `literature/zhekai-du/pdfs/P006_2021_Cross_Domain_Gradient_Discrepancy_Minimization_for_Unsupervised_Domain_Adaptation.pdf`
- `literature/zhekai-du/Academic-Writing-DNA.md`

MatchFixAgent 的算法使用具名函数、条件和 LLM 调用。本稿采用相同的表达原则。算法 1 保留一个实际 LLM 调用，用计算依赖关系及定位、假设、工具选择解释其内部诊断推理。四类差异的具体处理仍在正文，只在这里说明它们之间的关系。算法 2 显示独立交接、持续历史、模型调用、测试和提交。算法 3 显式调用前两个算法，将结构分析、依赖规划、就绪单元选择、证据归档、依赖失效和上下文重建写成操作。

真实性核对使用 `output/repository-migration-20260921/final-evidence.tar.gz` 中 `implementation_final/autofix/autonomous/agent.py` 及仓库工具实现。算法中的诊断位置和假设是模型推理的抽象，不增加独立模型调用、硬编码四分支路由、强制初始结构扫描或逐单元 Verifier。工具权限、编辑后测试、共享预算和完整仓库验收保持。

## 已落实内容

- 摘要局部新增 Translator Agent 生成初始候选的职责，共 139 词；末句、state of the art、唯一主要定量比较保持。
- §3.2/§3.3 标题体现 agent 和对应机制；正文衔接 Translator、Verifier、Repair Agent 与 Orchestrator。
- MindSpore、语言迁移、仓库迁移各部分说明对应优势：较低上下文成本与提交预算、跨语言验收与效率、共享代码上的成本及行为覆盖。
- 主表、自然错误表、消融表及附录成本表缩短表头。Calls、Tokens、Checks、Entries、Tests、Repaired、Preserved、Saved 的含义在设置、正文或表注中定义。Token 单位从表头移到表注，原来的百万单位与完整计数不互换。横排面板同步修改。
- 附录仓库成本表中的 Parameter updates 保留完整两行词组，以保证八列数据可读；主文表头均为单行。
- 图 3、图 4 宽度设为正文的 96%，图注均为五行。图 4 的单次检测统计移到紧邻正文；均值 31/18 步、所有运行第 1 步检测、12 次运行和阈值归一化仍清楚对应。
- 原第 10 页的表格与结论间距受模板 `flushbottom` 的弹性间隔影响。本轮内容和表格重新分页后，第 10 页容纳消融说明及表格，结论自然进入第 11 页。没有修改官方模板、字号、边距或用负间距压缩正文。

## 核验

意见清单本轮合计 100 项，逐项复核主文、三个算法、表头、图注及附录。旧来源和历史日志保留。新条目为 A16/A17、M18/M19、E11、R19、F09/F10。

实际执行：

- 两个表格生成器；最初调用系统 Python 缺少 matplotlib，改用项目 `.venv/bin/python` 后成功。
- `test_paper_figure*.py` 15 项和 `test_unified_paper_results.py` 10 项全部通过。
- 对照检查点，25 张表的数值行完全一致；方法和附录原有公式块完全一致；34 个定量来源、固定基线及用户图形文件哈希不变。
- `latexmk` 编译成功，23 页，无 overfull 或未定义引用。全页缩略巡检并放大检查摘要、算法、主表、图 3/4、第 10 页及附录表格。官方模板在部分附录页面仍报告 underfull vbox，不影响内容完整性。
- HTML 固定基线比较随构建刷新。LaTeX 差异稿在论文提交后重建；其最终状态追加到主清单复核日志。

本轮只修改论文表达和排版，没有运行或扩展实验。中间快照、数值核对及渲染记录位于 `output/manuscript-refinement-20260923/`。
