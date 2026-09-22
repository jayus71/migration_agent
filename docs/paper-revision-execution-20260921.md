# 论文修改执行记录

本轮依据已确认的 `docs/paper-revision-plan-20260921.md`，在 `codex/iclr-2027-template` 修改论文。开始时已有未提交工作，源文件与图表脚本快照位于 `output/paper-revision-execution-20260921/before/`，原有差异位于 `before-existing.patch`。本轮未修改实验实现、原始结果或候选程序，未调用模型 API、重跑实验、提交或推送。

## 第一阶段：结构与方法

修改文件为 `conference_101719.tex`、`sections/experiments.tex`、`sections/supplementary_experiments.tex`、`ref.bib` 及本文。阶段一独立差异保存在 `output/paper-revision-execution-20260921/stage1-only.patch`。

- 相关工作移至引言之后，形成引言、相关工作、LaDiM、实验、结论的顺序。
- 摘要、引言和方法围绕训练行为偏差、依据训练依赖诊断、独立证据交接及持续复验展开。保留 50 项主比较、57.4% token 节省和跨框架跨语言结尾。引言概述已完成的两个仓库结果，其正式表格与分析留第二阶段。
- 角色统一为 Translator、Verifier、Repair Agent 和 Orchestrator。task specification、evaluation protocol 和 acceptance criteria 按任务要求、比较过程与通过条件分别使用。
- 新增 Repository Coordination，区分候选文件版本与计划版本、全局测量时效与局部 checkpoint、语法检查与已选测试。首次选单元和普通修复阶段续接保留历史；实际单元切换、独立交接和容量边界触发上下文重建。检索档案位于可编辑工作区之外，缓存代码只来自实际读取且哈希匹配的相关片段。
- 将 50 个标识、29 种输入条件、24 个源文件及 12 条复用任务的构造说明放入附录。主图逐输入成本的 29 个输入继续保留。TorchAX/JAX/Optax 接入说明移入附录；torch4ms 桥接说明原已在附录。主文无 torchms 字样。
- 补入 TensorScope 与 NablaFuzz，经 USENIX 官方论文页与 arXiv 原论文页面核对题名、作者和方法范围。保留已有引用，没有引入未核实结果。

### 实现和数字依据

独立调查与交接依据 `output/maintext-ablations-20260918/frozen_v4_agent.py`，特别是提示词对只读调查、可选假设/检验的规定，以及 `_handoff_to_fixer()` 将原调查和工具输出作为带来源记录转交给独立修复会话的实现。未把可选反证测试写成每次必产的字段。

仓库机制依据 `scripts/repository_agent_mode.py` 的 `evidence_state()`、`working_set()`、`_plan()`、编辑后的失效传播、`_checkpoint()`、`_rebuild_context()`、`_stage()` 和 `_handoff_to_fixer()`，并对照 `docs/repository-migration-run-20260921.md`。旧机制开发记录仅用于区分历史行为，不用于描述最终正式运行。

主比较数值沿用 `data/paper_figures/README.md` 和既有审计结果。57.4% 已包含共同初译，不另行加收。仓库引言判断来自最终六组结果的来源文档，未对新增组件作独立效率归因。TensorScope 来源为 https://www.usenix.org/conference/usenixsecurity23/presentation/deng-zizhuang ，NablaFuzz 来源为 https://arxiv.org/abs/2302.04351 。

### 第一阶段验证

`latexmk -pdf -interaction=nonstopmode -halt-on-error conference_101719.tex` 成功，PDF 共 14 页，当前结论与参考文献起始位于第 9 页。日志未发现未定义引用或 overfull 警告。`git diff --check` 通过。用 Poppler 渲染并查看第 1 至 5 页，摘要、引言、相关工作和方法无正文重叠或裁切。编译日志和页面图像位于上述 output 目录。

图 2 仍是原有占位图，其中旧角色和桥接名称待第三阶段连同 PowerPoint、SVG 和矢量 PDF 同步。第二阶段将重写实验与结论并加入仓库和自然故障结果，第三阶段完成图 3、全稿数据检查及九页主文排版。当前阶段的编译和检查不代表实验重跑或最终排版验收。

## 第二阶段：实验与结论

主实验集中解释相同完整验收下的 token 差异，保留 1、2、4 次提交的实测接受数。跨语言段按接受集合和费用分析。Repository Migration 加入主实验，主表新增六行，分别报告完整验收、配对检查和总 token。自然故障分析及紧凑表加入正文，保留四方法的修复、保留、最终接受和选定完整运行修复费用。结论采用已确认的 MOST 结构，以 We introduced 和 Specifically 展开机制及总体实验结论。

`figures/make_unified_results.py` 读取最终仓库 summary、共同检查 partial_results、完整性审计及自然修复冻结 CSV，导出主表和新增的 `TABLE_natural_repairs.tex`、`TABLE_repository_costs.tex`、`TABLE_repository_checks.tex`。JSON 导出保存新输入的 SHA-256。仓库三个小型 JSON 已加入 `.gitignore` 的显式 allowlist，原始轨迹和候选仍不纳入。所有输入原文保持不变。新增检查覆盖缺测保留 145/114 分母、共用初译只计一次和自然修复方法配置的选取。

时间序列总 token 为 2,614,230 / 8,199,825 / 13,597,778，修复调用为 35 / 80 / 69。三方法均通过69/69配对检查。双塔均未完整通过，配对检查130/145、104/145、129/145，数值子集99/114、74/114、99/114。两个基线各一项缺测保留分母。三方法完整仓库接受数均1/2；正文只在相关处交代完整验收，然后分析LaDiM实现的功能及连续训练中的观察。

自然故障实例来自所选 `without_edit_format_feedback` 配置的 `task_002`，来源归档 `output/maintext-ablations-20260918/archives/original_natural10_v3.tar.gz`。已读取其 result.json 与完整 session.json 的实际编辑和工具轨迹，核对三次提交的观测变化、最终验收和确认结果。轨迹先补上 LSTM 的 MindSpore 实现与注册，再处理索引递归，32 次模型调用。初始异常、结果哈希、编辑文件、确认及最终测量保存在 `output/paper-revision-execution-20260921/natural-case-evidence.json`。未使用9月17日独立探索轨迹解释正式比较。

正式自然修复表使用选定完整运行总费用，LaDiM 为13,206,863 token。额外基础设施中断 episode 的78,316已知token和一次缺失usage留内部来源记录；不把选定运行总量称为全历史物理消耗，也不在论文新增历史开发记账。按用户最新纠正，已删除后来加入的JAX正文成本降调句及跨语言重复限制句，保持已确认摘要、跨框架有效性表述和结论。

### 第二阶段验证与待办

现有数据检查 `test_unified_paper_results.py` 8项通过，现有图形检查 `test_paper_figure*.py` 15项通过。`latexmk` 成功，当前17页总PDF，主文结论仍结束于第9页，未调整正文字号或行距。未定义引用与 overfull 警告均未出现。已渲染并查看主表、自然表、训练信号表和仓库附录表所在的第6、8、9、16、17页，未见文字重叠或裁切。编译日志位于 `output/paper-revision-execution-20260921/stage2-latexmk.log`。

阶段二开始快照位于 `before-stage2/`，独立差异保存为 `stage2-only.patch`。图3仍保持原资产及相应原caption，第三阶段同时更换。图2角色名称和仓库协调规格仍需同步可编辑资产。最终全文布局与数据核对留第三阶段。


## 第三阶段：主表、图3、自然故障消融与终稿检查

图3改为5.5英寸实际正文宽度，左图用共同初译、初始通过输入、初始故障输入三段堆叠，右图画29个有符号token节省柱，按20/9两组分别排序。两根负柱完整保留，总节省6,938,291；字号至少8pt，图例置于左图内部。脚本、PDF/PNG/SVG、caption与布局测试同步。

根据用户最新意见，主表程序面板增加输入和输出token列，所有方法逐一核对输入加输出等于总token。跨语言Direct由共同初译的实际调用键汇总，InterTrans使用其累计调用记录。仓库面板以配对检查、梯度、参数更新、入口或原测试、修复调用和总token呈现，删除Passed/Failed及重复行引用。为保留清楚字号，按审查方案省去已包含在配对检查且正文分析的loss列。时间序列细分证据由主代理从冻结final-evidence.tar.gz提取到data/paper_figures/repository_training_check_details.json，保留归档、成员哈希和三seed实际布尔检查；生成器读取该摘录并记录SHA-256。93.0%的输入token节省占比按整数复算为92.9985640556%。

自然故障组件表由recovery_final.json的natural10_v3选定完整组及reference_v4生成。五条件的故障程序修复数4/3/0/2/4，初始通过保留均5/5，token为15,547,813 / 14,516,463 / 10,851,537 / 17,325,026 / 13,206,863。正文说明保留历史4/5、移除0/5，附录说明参考配置的编辑格式示例和格式纠正反馈。程序数与故障点数分开措辞，未混入其他配置的自然故障实例。

全稿按humanizer与写作DNA检查，保留已确认摘要、结论和Generalization Across Frameworks标题，清除附录无必要连字符与分号。README、图表来源README和模板说明更新为当前结构。方法图在用户停止指令前已使用Artifact Tool原生可编辑文本、形状和连接线生成PowerPoint，并从相同布局生成SVG及矢量PDF；收到停止指令后保留现有文件，不再导出、验证或美化。未将占位图列为完整设计交付。

### 第三阶段验证

图表现有测试15项及统一数据测试10项通过，含29柱精确数据、20/9分组、2负值、堆叠总量、图例/标签画布范围、实际尺寸与字体、自然消融分母、仓库信号与缺测、主表费用拆分。latexmk成功，全文17页，结论结束在第9页，正文字号、页边距和行距未改。日志无overfull或未定义引用。已查看第6、7、8、9、15、16、17页的主表、Figure3、自然修复与组件表、训练信号表和仓库附录，表头与图文无重叠或裁切。主代理独立通过新主表与Figure3视觉审查。

本阶段仅重整现有证据、生成图表和编译论文，未执行实验或模型API，未修改实验实现及原始结果，未提交、推送或创建PR。阶段前快照为before-stage3，独立文本差异保存在stage3-only.patch。方法图后续设计由作者处理。
