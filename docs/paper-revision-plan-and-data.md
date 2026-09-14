# 论文修改方案与数据交接

整理日期：2026-09-10。论文为 `conference_101719.tex`，修改基准为 `d01cc8c`，分支为 `codex/paper-overview-ppt`。本文档记录已讨论的修改方案及所需证据；不表示论文修改已经实施。所有路径均相对于仓库根目录 `/home/jayus71/code/migration_agent`。

## 1. MindSpore 端到端迁移数据

这组结果已在仓库中，尚未纳入当前论文主表。它来自 Experiment E / Track A，与原始 50 实例故障修复主实验分开计数。

实验覆盖 Image MLP、CNN、ResNet、Transformer classifier 和 Tiny causal language model 五个任务，种子为 642、643、644，共 15 个验证条件。这里的 15 不是 15 个独立任务。通过验证要求满足该实验的配对阈值：loss difference ≤ 0.02，gradient norm difference ≤ 0.05，parameter update relative L2 difference ≤ 0.03。

### 1.1 可直接用于新表的结果

| 论文方法名称 | 原始方法标识 | 编译成功 | 执行成功 | 完成有效训练 | 通过配对阈值验证 |
| --- | --- | ---: | ---: | ---: | ---: |
| LADDER | T-HIER | 15/15 | 15/15 | 15/15 | 15/15（100%） |
| CodeTransEngine | T-CTE | 15/15 | 12/15 | 12/15 | 8/15（53.3%） |
| Direct LLM translation | T-DIRECT | 15/15 | 13/15 | 13/15 | 7/15（46.7%） |
| MSAdapter | T-MSA | 15/15 | 15/15 | 15/15 | 0/15（0%） |
| X2MindSpore | T-X2MS | n/a | n/a | n/a | n/a |

X2MindSpore 的计划矩阵是 15 个条件，实际可测条件为 0，归档状态为 `blocked`。它不能作为 0/15 失败行加入成功率比较；建议在实验设置中交代未纳入的原因，主结果分区只列前四种方法。

### 1.2 各任务通过配对阈值验证的条件数

| 方法 | Image MLP | CNN | ResNet | Transformer classifier | Tiny causal language model |
| --- | ---: | ---: | ---: | ---: | ---: |
| LADDER | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| CodeTransEngine | 1/3 | 1/3 | 3/3 | 0/3 | 3/3 |
| Direct LLM translation | 0/3 | 1/3 | 3/3 | 0/3 | 3/3 |
| MSAdapter | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 |

### 1.3 准确的数据路径与版本

入口文件：

- `data/experiments/05_experiment_E_track_a_rerun/README.md`
- `data/experiments/05_experiment_E_track_a_rerun/final/overall_results.md`
- `data/experiments/05_experiment_E_track_a_rerun/final/run_manifest.json`

各方法当前有效结果：

| 方法 | 相对仓库根目录的结果文件 | 运行版本 |
| --- | --- | --- |
| LADDER | `data/experiments/05_experiment_E_track_a_rerun/final/T-HIER/formal_b32d9f4_strict_sync_5x3_20260906/summary.json` | `b32d9f4a27ed90646943b671d43f8616b4ad73fe` |
| CodeTransEngine | `data/experiments/05_experiment_E_track_a_rerun/final/T-CTE/formal_4508d0e_no_token_cap_5x3_20260906/summary.json` | `4508d0e962d1f27a582b2fcb0a53f1edea5bfb0f` |
| Direct LLM translation | `data/experiments/05_experiment_E_track_a_rerun/final/T-DIRECT/formal_4508d0e_no_token_cap_5x3_20260906/summary.json` | `4508d0e962d1f27a582b2fcb0a53f1edea5bfb0f` |
| MSAdapter | `data/experiments/05_experiment_E_track_a_rerun/final/T-MSA/formal_patched_5261529_5x3/summary.json` | `52615295ceea067371216564f4310425871b583d` |
| X2MindSpore 状态 | `data/experiments/05_experiment_E_track_a_rerun/final/T-X2MS/summary.json` | `d5f75ac95e406a5258e223f0222612bde258af3f` |

前四项结果目录中也有可读的 `summary.md`。优先按 `run_manifest.json` 的 `source_summary` 取数，不按文件名相似或修改时间猜测版本。特别是 `final/T-CTE/summary.json` 属于历史结果，不是当前 8/15 的来源。

LADDER 的有效结果来自修复验证器初始化对齐后的重新运行。旧 T-HIER 0/15 已被该结果替代。此处仅引用已经完成的运行，本次不重跑实验。

### 1.4 结果的分析用途

MSAdapter 使用 v0.6.0 及记录在 provenance 中的通用兼容补丁。它在全部条件下完成有效训练，但参数更新的相对差异约为 1.38–2.81，未满足 0.03 的阈值。因此可以分析可执行性、有效训练与训练行为一致性之间的差别。

LADDER 配置允许最多四轮修复，但本组 15 个条件均在初始翻译后通过，Fixer 调用为 0。这组结果支持端到端迁移与验证表现；迭代修复的收益应由故障修复实验和消融支撑。CodeTransEngine 与 Direct LLM 各做一次翻译；MSAdapter 为每个任务启用一个候选并在三个种子上验证。

CodeTransEngine 的两个 CNN 条件在原始输出中标为 `environment_or_upstream`，当前汇总已根据生成代码中的无效参数组合将其计作可测的方法失败。后续复算沿用该归档解释。

## 2. 与上述结果合表的 JAX 数据

来源：`data/paper_figures/jax_original_instances.csv`。说明：`data/paper_figures/README.md`。原始 Track C 运行版本为 `3352f71`。

CSV 共 24 行，为四种方法各运行六个故障实例。每个故障阶段包含一个 MLP 和一个 CNN 实例。成功修复须通过三个种子的训练验证；成功数分母仍是六个故障实例。

| 方法 | Execution faults | Forward computation faults | Gradient and parameter update faults | Accepted repairs | 总 tokens | 每个接受修复的 tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| LADDER | 2/2 | 2/2 | 2/2 | 6/6 | 17,543 | 2,923.8 |
| Direct LLM repair | 2/2 | 1/2 | 2/2 | 5/6 | 74,841 | 14,968.2 |
| Ivy | 0/2 | 0/2 | 0/2 | 0/6 | 0 | n/a |
| torch2jax | 0/2 | 0/2 | 0/2 | 0/6 | 0 | n/a |

这里的故障阶段列表示该类故障最终被接受的修复数，不表示各验证阶段本身的通过次数。Ivy 和 torch2jax 的部分候选通过了执行或前向检查，所以正文应写未通过最终训练验证，不能写任何阶段都未通过。

LADDER 最多允许三轮；Direct LLM 与两个转换器各运行一次。所有成功修复均在第一轮完成。CSV 中的 `repair_at_4` 是由成功轮次计算出的字段，不能据此宣称进行了共同四轮预算的实验。

单位接受修复的 token 成本 = 全部尝试的总 prompt 和 completion tokens / 接受修复数。转换器总 tokens 为零，但接受数也为零，因此单位接受修复成本未定义，不能填零。新合并表去掉 tokens 列，在正文保留 LADDER 2.9K 与 Direct LLM 15.0K 的成本比较。

合并采用一个表号、两个分区。MindSpore 分区展示 Method、Training completed、Verification passed；JAX 分区展示 Method、Execution faults、Forward computation faults、Gradient and parameter update faults、Accepted repairs。每个分区保留自己的分母、任务定义和预算，不计算跨分区总成功率。长表头使用完整单词并换行。

## 3. 其余修改所需数据

### 3.1 原始 50 实例修复主实验

仓库内汇总：`data/paper_figures/fixed50_original_summary.csv`。

| 方法 | 四次尝试内接受 | 第一次尝试内接受 | 第二次尝试内接受 | 总 tokens | 每个接受修复的 tokens（约） |
| --- | ---: | ---: | ---: | ---: | ---: |
| Execution only | 33/50 | 58% | 64% | 154,738 | 4.7K |
| All signals | 34/50 | 66% | 66% | 180,465 | 5.3K |
| Direct LLM repair | 40/50 | 72% | 76% | 1,582,865 | 39.6K |
| SWE-agent | 46/50 | 72% | 84% | 7,635,016 | 166.0K |
| MatchFixAgent | 47/50 | 74% | 86% | 5,205,141 | 110.7K |
| LADDER | 50/50 | 84% | 98% | 190,588 | 3.8K |

该组采用原始故障专用接受标准，不能改写为全部接受候选均在每一步通过 loss、gradient 和 parameter update 的配对阈值验证。约 29 倍的成本比值使用上表原始接受数作分母。只使用已有的第 1、2、4 次尝试累计结果，不补第 3 次尝试。

按故障、模型与修复位置进行分析，需要本地子仓库中的详细记录：

- `ascend-torch4ms/experiments/baselines/full_hier_fixed50/instances.csv`：六种方法共 300 条实例记录，含模型、故障、修复位置、轮次、结果、tokens、错误和原始报告路径。
- `ascend-torch4ms/experiments/baselines/full_hier_fixed50/summary.json`：原始设置和汇总。
- `ascend-torch4ms/experiments/baselines/full_hier_fixed50/README.md`：原始运行说明，记录的复现版本为 `3aaafd137cfcb86ac16c7310dbdc85e962270cea`。

保留主表中的 Direct LLM、SWE-agent、MatchFixAgent 和 LADDER。Execution only 与 All signals 继续用于消融。原始 50 实例不能被后续 Experiment A、B、H、J 或 K 的不同重验证、实例池、模型或运行替换。

### 3.2 图 1 与检测分析

直接输入：`data/experiments/03_experiment_C_gradient_and_parameter_faults/results_per_step/section65_per_step_divergence_steps50.csv`。

来源说明：`data/experiments/03_experiment_C_gradient_and_parameter_faults/README.md`、`data/experiments/03_experiment_C_gradient_and_parameter_faults/reproduce.md`。

CSV 完整网格含 3,600 行。图 1 只取 `free-running` 下的 `grad_wrong` 和 `param_wrong`，每种故障为四个模型、三个种子、50 个训练步，共 12 条轨迹。读取 `loss_abs_diff`、`grad_norm_abs_diff` 和 `param_update_rel_l2`，按相应阈值 0.02、0.05、0.03 归一化。

| 子图 | 展示的两种信号 | 对应检查的检测时间 | 平均 loss 差异曲线首次越阈 |
| --- | --- | --- | --- |
| a：错误梯度 | Loss difference、Gradient difference | 所有 12 次运行均为第 1 步 | 第 31 步 |
| b：错误参数更新 | Loss difference、Update difference | 所有 12 次运行均为第 1 步 | 第 18 步 |

曲线为逐步均值，阴影为最小值到最大值。31／18 是平均曲线的越阈时间，不是每次运行的检测时间。

其他诊断输入：

- `data/paper_section_65_66/results_section65_per_step_divergence/section65_per_step_divergence_steps50.csv`
- `data/paper_section_65_66/results_section65_signal_sanity_current/section65_signal_effectiveness_table.csv`
- `data/paper_section_65_66/results_realdata_66/section66_realdata_training_consistency_steps_steps50.csv`

以上用于检查正常运行、执行故障、前向故障与逐步同步诊断。执行失败后未测得的梯度或更新指标为 n/a；不能从原始输出中的占位值推导出零误差或检查通过。

### 3.3 定位与误分类分析

- `data/experiments/11_experiment_K_layer_localization/results/section65_fault_pool_localization_confusion_matrix.csv`
- `data/experiments/11_experiment_K_layer_localization/results/section65_fault_pool_misclassified_instances.csv`
- `data/experiments/11_experiment_K_layer_localization/results/section65_fault_pool_localization_misclassified.json`
- `data/experiments/11_experiment_K_layer_localization/README.md`

定位结果为 48/50，准确率 96%。两个误分类实例为 NU-07-A 和 NU-07-B，从前向类别被归入执行类别。原始解释为非有限值故障先表现为执行或有限值约束失败。写到具体混合精度机制时继续核对故障定义和对应报告。该组另有 46/50 的严格修复结果，不能混入原始 50/50 主实验。

### 3.4 信号与修复指导消融

50 实例的 Execution only、All signals 与 LADDER 使用第 3.1 节数据。比较同时改变阶段选择与对应修复指导，不能把结果全部归因于单独某一个因素。

独立 12 任务信号消融的仓库内数据为 `data/paper_figures/signal_ablation_by_fault.csv`：

| 反馈 | Execution faults | Forward computation faults | Gradient and parameter update faults | 接受总数 |
| --- | ---: | ---: | ---: | ---: |
| Execution only | 4/4 | 0/4 | 0/4 | 4/12 |
| Execution and forward values | 4/4 | 4/4 | 0/4 | 8/12 |
| All three signals | 4/4 | 4/4 | 4/4 | 12/12 |

原始 episode 与设置在本地目录 `ascend-torch4ms/experiments/paper_section_63_64/results/section63_feedback_ablation_nu04_clean_alias_rerun_20260715/`，其中 `section63_episode_results.csv` 和 `section63_summary.json` 用于分析轮次、故障覆盖和条件控制。此组共三种反馈、每种 12 任务，不能与 50 实例组相加。

### 3.5 框架文档消融

修复代理文档实验采用本地目录 `ascend-torch4ms/experiments/paper_section_63_64/results_section641_multiscope_v1/` 中的 `section641_scope_summary.csv`、`section641_tasks.csv` 和 `section641_summary.md`。

该组有 24 个基础任务、四种条件，共 96 次条件运行，预算四轮。所有 binary feedback 条件均接受 0 个任务。以下为 layered feedback 的现有结果：

| 修复位置 | 无文档接受 | 有文档接受 | 无文档／有文档越界编辑率 |
| --- | ---: | ---: | ---: |
| Translated program | 12/12 | 8/12 | 0%／0% |
| Operator code | 6/8 | 6/8 | 12.5%／0% |
| Automatic differentiation and optimizer code | 0/4 | 0/4 | 0%／0% |

逐任务的结果、编辑范围和故障信息用于解释文档在哪种条件下有效，不笼统写成文档提升所有修复结果。汇总文件中的 `macro_average` 是按修复位置平均的比率，不能误当作按 24 个实例加权的成功率；当前论文的分组行不需要改变。

初始翻译文档实验必须使用 `ascend-torch4ms/experiments/paper_section_63_64/results_section642_translator_guide_ablation_v4/section642_translator_guide_ablation_tasks.csv` 和同目录的 `section642_translator_guide_ablation_summary.md`。两个文档条件各 15 次运行，均只调用一次 Translator，Fixer 禁用。

| 条件 | 编译成功 | 执行成功 | 训练成功 | 一次翻译通过全部要求 |
| --- | ---: | ---: | ---: | ---: |
| 无文档 | 2/15 | 2/15 | 0/15 | 0/15 |
| 有文档 | 15/15 | 15/15 | 15/15 | 15/15 |

无 `_v4` 后缀的旧目录结果不同，不用于当前论文。此处训练成功检查非空梯度和非零参数更新，不自动等同于 Experiment E 的配对阈值验证。

## 4. 三个代理与编排器的代码依据

需要读取本地子仓库中的以下文件：

- `ascend-torch4ms/autofix/orchestrator.py`
- `ascend-torch4ms/autofix/agents/translator.py`
- `ascend-torch4ms/autofix/agents/verifier.py`
- `ascend-torch4ms/autofix/agents/fixer.py`
- `ascend-torch4ms/autofix/faults/injection.py`
- `ascend-torch4ms/autofix/README.md`

`run_orchestration` 创建 TranslatorAgent、VerifierAgent 和 FixerAgent；论文中分别写 Translator agent、Verifier agent、Repair agent。Orchestrator 是协调程序，负责运行顺序、预算和回滚。当前核对的本地子仓库 HEAD 为 `f3c84bb20ad585f1d28c0ea1d1f1e903cd51c20f`；这不是所有实验共享的运行版本，各实验以自己的 provenance 为准。

回滚实现会比较修改后的评分，保留有改进的修改并回滚没有改进的修改，不能简化为只要尚未最终成功就回滚。代理类名本身也不等于每个角色都单独调用 LLM；具体调用行为以实现为准。

## 5. 数据可用性与交接方式

| 数据 | 当前本机 | 普通 Git checkout | 现有实验 Release |
| --- | --- | --- | --- |
| 原始 50 实例汇总、JAX 实例、12 任务消融汇总 | 已有 | `data/paper_figures/` 内已有 | 无需依赖 Release |
| Experiment C、E、K 的选定 CSV／JSON／说明 | 已有 | `data/experiments/` 内已有 | 完整归档可补充原始产物 |
| 原始逐步诊断数据 | 已有 | `data/paper_section_65_66/` 内已有 | 清单见 `data/archive-manifest.json` |
| 原始 Fixed50 详细实例与报告 | 本地子仓库已有 | `ascend-torch4ms/` 被忽略 | 清单中不含 `full_hier_fixed50` |
| Section 6.3、6.4 文档与信号消融详细记录 | 本地子仓库已有 | 详细记录未随主仓库交付 | 清单中不含 `section63`／`section64` |
| 代理实现与原始 Track C 报告 | 本地子仓库已有 | 不随主仓库交付 | 清单中不含对应实现或 `track_c` 目录 |

在本机完成这轮修改不需要新增实验。交给另一台机器或云端任务时，除主仓库外，须提供上述本地详细记录和代码，或提供可访问的原始子仓库与相应版本。仅下载现有 Release 不能补齐全部依赖。本次只生成交接文档，未复制原始代码和全部数据，也未发布任何文件。

读取 A–K 完整归档时，在仓库根目录执行：

```bash
python3 scripts/fetch_experiment_data.py
python3 scripts/fetch_experiment_data.py --verify-only
```

下载和逐文件校验由现有脚本完成，目录为 `.experiment-data/20260906-v1/experiment-results-local-20260906/`。这是读取既有证据，不是重跑实验。目录对应关系以 `data/selected-manifest.json` 和 `data/archive-manifest.json` 为准。

三份论文输入的 SHA-256：

| 文件（位于 `data/paper_figures/`） | SHA-256 |
| --- | --- |
| `fixed50_original_summary.csv` | `db4dd52fa1892ee53ec377ff3c5907779611689692d59b75e9c3c01f0f2ddd0e` |
| `signal_ablation_by_fault.csv` | `ca2ba5a14e00716bdd35977b8b30e41096b4932f9e968c8e7f5bc72e4657c0f1` |
| `jax_original_instances.csv` | `de2a165be2f9cf4409a92ff4a23c3711a356e8fe4e5787d3be705857c4800a8d` |

## 6. 完整修改方案

### 6.1 摘要

保留研究问题、现有反馈不足、分层诊断方法、主要结果与跨框架结论的论证顺序。介绍 LADDER 时简要提到 translation、verification、repair 三个代理及负责协调的 orchestrator。预算管理、回滚等实现细节移到方法部分。

结果压成一句，保留 50 实例、四次尝试、84% 首次接受率和约 29 倍 token 优势。保留已确认的跨框架结尾。交付完整原文与建议稿对照，避免逐词修补造成句子失去学术表达。

### 6.2 角色、术语与方法

依据第 4 节代码统一摘要、引言、方法、图注和结论中的角色身份。Repair Loop 简洁说明初始翻译、验证诊断、定向编辑和再次验证。仅修改职责和流程不一致的句子，保留原有段落组织。

统一 execution、forward values、gradients and parameter updates、repair location、repair LLM 等名称。写全 Gradients and parameter updates、Automatic differentiation and optimizer code，禁止 `Grad./upd.`、`optim.` 等临时缩写，避免 `Ac- / cepted` 这种人为拆词。逐步同步直接描述为每步同步，不使用 teacher forcing。原始数据字段和外部方法的正式名称不因润色而改名。

### 6.3 图 1 与图注

以当前恢复版为基础，将画布高度由 3.8 英寸压缩至约 2.6–2.8 英寸，a／b 标题放到各子图右上角。第 1 步标注使用单行 `Detected at step 1`，缩小子图间距，保留原坐标范围和第 3.2 节的数据含义。

Caption 由约 102 词压缩至约 55–65 词。保留主要发现、每面板 12 次运行、均值与阴影定义、阈值归一化和检测时间的统计含义。详细模型、种子和运行设置在实验段说明。按首页摘要旁的实际单栏尺寸验收，不能只看放大的单独图片。

### 6.4 表格

50 实例主表只保留现有 MindSpore 部分，取消原 `(a)` 标记，保留原始方法、结果分项和成本指标。JAX 移出主表，与第 1 节 MindSpore 端到端迁移结果组成第 2 节定义的双分区表。同步表号、交叉引用、图注、表注和生成脚本。

新表加入的是已经归档的 Experiment E 结果，不新增运行。完整表头通过换行、列宽与列组安排保证可读性，不使用读者难以理解的缩写。

### 6.5 实验分析

正文每段先说明观察，再引用关键证据解释其意义。完整结果交给图表，删除逐方法、逐模型报数的段落。不能仅把报数改写为无证据的原因推测。

| 正文部分 | 分析目标 | 需要的证据 |
| --- | --- | --- |
| 整体修复效果 | 优势集中在哪类故障、哪种修复位置；首次修复与累计预算、成本的关系 | 第 3.1 节汇总、300 条实例记录、必要的失败和编辑报告 |
| 检测与定位 | 前向误差为何滞后；误分类如何由失败表现导致 | 第 3.2 节轨迹、故障注入定义、第 3.3 节误分类记录 |
| 消融 | 信号覆盖与阶段选择、修复指导的不同作用 | 第 3.4 节两组独立消融及运行设置 |
| MindSpore／JAX | 可执行性与训练行为一致性的差别；另一目标框架中的诊断、修复表现 | 第 1、2 节的有效版本和错误记录 |
| 框架文档 | 文档在初始翻译、后续修复和编辑范围约束上的不同效果 | 第 3.5 节逐任务记录及文档条件 |

保留 `Generalization Across Frameworks` 标题和跨框架结论。对 Ivy／torch2jax 的描述按第 2 节纠正。MindSpore 初始翻译即通过的结果不用于声称多轮修复带来提升。

### 6.6 工作顺序与验收

按摘要与角色说明、图 1、结果表重组、实验分析、全文与版面检查的顺序修改。每一项单独检查 diff，避免将局部问题扩展成未经讨论的全文重写。方法主图的整体重绘仍单独审核，不夹带执行。

需要同步的文件包括 `conference_101719.tex`、`figures/make_gradient_drift.py`、`figures/gradient_drift.pdf`、`figures/gradient_drift.png`、`figures/make_jax_table.py`、`figures/TABLE_jax_rows.tex`、`figures/latex_includes.tex`，以及必要的表格生成代码和数据来源说明。

现有检查包括 `tests/test_paper_figures.py`、`tests/test_paper_figure_layout.py`、`tests/test_jax_table.py`、`tests/test_experiment_data.py`。表结构和标签发生改变时更新相应预期，保留数据一致性、分母、预算、检测时间和布局检查。

```bash
.venv/bin/python figures/make_gradient_drift.py
.venv/bin/python figures/make_jax_table.py
.venv/bin/python -m unittest discover -s tests
latexmk -pdf -interaction=nonstopmode -halt-on-error conference_101719.tex
```

以上是实施修改时的分析、生成和编译命令，本次交接未执行论文改写或重跑实验。成本与累计接受率图继续使用已测的 1、2、4 次尝试数据；引用变化时同步图注。

编译后检查首页、主表、新合并表、方法相关页及其后续分页。不得用极小字体或扩大坐标空白掩盖布局问题。所有实验数字、分母、判定标准和尝试预算保持不变。提交、推送、PR 和合并按用户另行指示执行。

## 7. 写作与来源参考

- `AGENTS.md`：用户确认的论文与图表约束。
- `README.md`、`data/paper_figures/README.md`：论文输入和复算方式。
- `.claude/skills/humanizer/SKILL.md`：全文学术表达检查，包括图注、标题、表注。
- `literature/zhekai-du/Academic-Writing-DNA.md`：基于第一作者论文的写作风格参考。
- `data/experiments/EXPERIMENT_STATUS_REPORT.md`、`data/experiments/CURRENT_ISSUES.md`、`data/experiments/SOURCE_INDEX.md`：实验口径与版本索引；具体路径优先服从各实验当前 manifest。

写作要求是清楚、准确、论证连贯。保留支持充分的主张与已确认措辞，不将论文改成运行步骤或指标罗列，也不在文字润色中不断加入防御性限定。
