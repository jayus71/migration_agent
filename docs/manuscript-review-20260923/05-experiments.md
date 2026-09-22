# 实验章节逐句审查报告

审查对象为主代理提供的 `d1d6a53` 文本快照。本报告全部内容均为审查结论和修改方案，未修改论文、脚本、图表、结果或 PDF，未运行实验或其他工具。

本轮依据提供的 AGENTS.md、humanizer、Academic-Writing-DNA、意见清单及图表来源说明审核。以下意见 ID 沿用 `docs/manuscript-feedback-register.md`；“方案 01”等编号仅用于本报告内部交叉引用。

## 1. 范围与覆盖

| 审查对象 | 准确位置 | 覆盖量 |
|---|---|---:|
| Experimental Setup | `sections/experiments.tex:3–15` | 正文 27 句 |
| Main Results | `sections/experiments.tex:17–49` | 正文 15 句 |
| Analysis Experiments | `sections/experiments.tex:51–86` | 正文 19 句 |
| Ablation Studies | `sections/experiments.tex:88–125` | 正文 19 句 |
| 全部表题、图注、表下注 | `sections/experiments.tex:21,29,39,58,72,81,97,117` | 32 个句子或紧密说明单元 |
| 主文表格 | 6 个 `TABLE_*.tex` 源文件，见下文 | 4 张表、9 个面板、31 行结果 |
| 主文图形 | `make_unified_results.py:420–479`；`make_gradient_drift.py:9–99` | 2 张图、4 个面板，覆盖全部生成文字 |
| 标题与引用标签 | `sections/experiments.tex` | 1 个章节标题、4 个小节标题、12 个加粗段首、12 个 `\label` |
| 算法 | 本次分配文本未包含算法 | 0 |

正文和图表说明共审查 **112 个句子或紧密说明单元**。表格结果行、表头、面板名和生成标签另立台账，不混入句子计数。

本轮能够直接确认的是源码措辞、给定数值、图形生成逻辑及来源说明之间的关系。冻结实验文件、完整生成器和方法实现未包含的细节，集中列在报告末尾供主代理核对，不据此新增实现判断。

## 2. 正文逐句台账

### 2.1 Experimental Setup：27 句

源文件均为 `sections/experiments.tex`。

| 编号 | 行号 | 短引文 | 判定 | 理由与处理 |
|---|---:|---|---|---|
| S01 | 7 | “The main comparison contains 50 migration tasks…” | 保留 | 数量、迁移方向和覆盖对象明确。50 个任务与去重后的实际调用数属于不同统计对象，不改分母。 |
| S02 | 7 | “We also migrate 18 Java/DJL programs…” | 保留 | 交代 18 个程序的构成及两个公开仓库，引用齐全。 |
| S03 | 7 | “The repositories contain 13 and 24…” | 保留 | 规模按前句仓库顺序对应，文件数和非空行数均有用途。 |
| S04 | 7 | “ten saved initial translations: five require repair…” | 改写 | `saved` 是保存状态；`initial checks` 未直接告诉读者这是首次评估。改为初次翻译产生的十份程序及其首次评估结果。见方案 01。 |
| S05 | 7 | “This study permits changes to the candidates and their supporting library.” | 保留 | 明确可编辑范围，直接支撑后文 LSTM 支持库修复。不能当作接口细节删除。 |
| S06 | 7 | “A separate study controls the training signals…” | 改写 | 实际消融改变提供给修复过程的反馈，`controls the training signals` 容易读成改变训练信号本身。见方案 02。 |
| S07 | 7 | “The JAX study uses six candidates…” | 保留 | 六例、两类模型、三类故障清楚，符合主文保留原六例的决定。 |
| S08 | 7 | “A separate detection study follows four models…” | 保留 | 四模型、三种子、50 步及比较对象完整。后文仍需就地解释 12 的组成。 |
| S09 | 7 | “Appendix…summarizes the program collections…” | 保留 | 数据集表已正确指向附录，不加平均长度。 |
| S10 | 10 | “native algorithms, prompts, tools, parsers, and retry policies” | 改写并移附录 | 主文保留共同 DeepSeek 后端及原生修复流程；解析器、工具和重试配置的逐项说明放实验协议。见方案 03。 |
| S11 | 10 | “The main table also includes Direct LLM initial translation…” | 改写 | 末尾基线未用表中的正式显示名 `Test-guided repair`，读者需要自行对应。定义应与表行直接对齐。见方案 03。 |
| S12 | 10 | “Direct repair…with its existing repair procedure.” | 改写 | `its` 的指代不清，`existing repair procedure` 没有解释实际差别。保留输入和共用工具，具体过程移协议。见方案 03。 |
| S13 | 10 | “Each table lists the methods evaluated in that study.” | 删除 | 表格本身已经列出方法；这句没有新增实验信息。 |
| S14 | 12 | “For JAX, Ivy converts code…while torch2jax maps…” | 保留 | 为实际对比方法提供定义和引用；符合最新要求，不随 TorchAX 一并移走。 |
| S15 | 12 | “We apply each converter once…without LLM repair.” | 保留 | 一次转换、输入已有故障、判断故障是否去除，三项都是解释 0/6 的必要条件。 |
| S16 | 12 | “TorchAX…is the execution backend…” | 移附录 | 最新 S13 明确覆盖此前留主文的安排。整句连同引用和执行细节移入 JAX 协议。见方案 04。 |
| S17 | 15 | “Methods use common source programs…” | 保留 | 给出比较的公共输入和对应初始参数，属于有效公平性条件。 |
| S18 | 15 | “Repair methods also receive the same initial translations.” | 保留 | 明确修复方法共享起点，`initial translations` 在此已有自然含义。 |
| S19 | 15 | “Acceptance requires agreement in execution…” | 保留 | 接受标准包含执行、前向、梯度、更新及任务要求的检查；不缩减为单一 loss 一致。 |
| S20 | 15 | “Accepted programs pass every required check.” | 删除 | 紧接接受定义，语义重复。完整通过的含义已由前句 `requires` 承担。 |
| S21 | 15 | “Behavior checks passed counts…” | 保留 | 直接定义主表列名，必要且具体。 |
| S22 | 15 | “Entry points counts successful execution…” | 保留 | 把入口数量解释为训练脚本、notebook 和教学示例的执行结果。 |
| S23 | 15 | “Original tests counts passing tests supplied by the repository.” | 保留 | 区分仓库自带测试与外部行为检查。 |
| S24 | 15 | “The main migration comparisons check consecutive training steps.” | 移附录并具体化 | 没有提供步数或比较范围，主文信息量低。不能直接把所有研究概括为相同多步协议。见方案 05。 |
| S25 | 15 | “Candidates that pass the public evaluation are checked on additional seeds.” | 保留 | 交代额外种子复核，与预算和接受判断有关。 |
| S26 | 15 | “Investigation and repair allow up to 40 LLM calls…” | 保留 | 明确程序与仓库调用上限及提交上限；`up to` 已准确表达预算。 |
| S27 | 15 | “Appendix…gives the numerical tolerances, seeds, and complete budgets.” | 保留 | 为主文省略的数值协议提供明确入口。 |

### 2.2 Main Results：15 句

| 编号 | 行号 | 短引文 | 判定 | 理由与处理 |
|---|---:|---|---|---|
| M01 | 34 | “LaDiM completes all 50…57.4% fewer tokens…” | 保留 | 比较对象、接受数、成本优势和表格位置明确。保留结果力度。 |
| M02 | 34 | “programs that pass the initial checks” | 改写 | 将状态直接说成首次评估通过，避免内部检查阶段措辞。见方案 01。 |
| M03 | 34 | “locating most of the difference in the context processed…” | 改写 | `locating` 的搭配生硬。保留 93.0% 及输入 token 对成本差异的解释，直接陈述。见方案 06。 |
| M04 | 34 | “retaining full acceptance at four submissions” | 改写 | 应明确 1/2/4 是提交预算，不暗示所有任务实际提交四次。见方案 07。 |
| M05 | 44 | “all programs completed by MatchFixAgent and an additional recurrent network…” | 保留 | 补充集合包含关系和新增接受案例，不只是复述总数。 |
| M06 | 44 | “Its 9/18 accepted programs comprise all eight textbook examples…” | 保留 | 清楚解释 9/18 的构成及与两基线的差别。 |
| M07 | 44 | “11.7% fewer tokens…24.2% fewer…” | 保留 | 两个明确基线对应两个成本差异。 |
| M08 | 44 | “extend training behavior repair to tasks that change both…” | 保留 | 将跨语言结果联系到研究目标，是有证据的适用性结论。 |
| M09 | 47 | “All three agents complete the time series migration…” | 保留 | 同时交代完整迁移及共享模型的多个调用入口。 |
| M10 | 47 | “69/69 checks…68.1%…80.8%…” | 保留 | 在相同接受结果下比较完整成本，条件和结果充分。 |
| M11 | 47 | “The coordinated repair therefore preserves training behavior…” | 删除 | 重复 M09 的多入口保持和 M10 的成本优势，没有新增证据或解释。见方案 09。 |
| M12 | 49 | “restores reward model inference and retrieval…” | 保留 | 明确指出相对基线恢复的功能，并保留训练命令执行结果。 |
| M13 | 49 | “highest behavioral coverage, passing 130/145…” | 保留 | 最高覆盖由表中数值支持；原始测试与行为检查分母分开。 |
| M14 | 49 | “cover the shared model's use in training, inference, and retrieval” | 保留 | 补充这些功能连接到同一个共享模型，解释仓库协调的对象；不必机械删除所有结果总结句。 |
| M15 | 49 | “Appendix…remaining numerical differences and detailed checks.” | 保留 | 提供详细结果入口，未附加新的降调或防御性表述。 |

### 2.3 Analysis Experiments：19 句

| 编号 | 行号 | 短引文 | 判定 | 理由与处理 |
|---|---:|---|---|---|
| A01 | 55 | “reports failed programs repaired…ten saved translations” | 改写 | 保留表头解释，将 `saved translations` 改为初译得到的十份程序，并明确失败/通过指首次评估。见方案 01。 |
| A02 | 55 | “repairs four of the five…raising final acceptance from five to nine” | 保留 | 修复、保留和最终接受三项关系明确，保留 4/5、5/5、9/10。 |
| A03 | 55 | “retain the initial five successes but recover none…” | 保留 | 直接报告真实基线差异，`but` 在此承担有内容的比较关系。 |
| A04 | 55 | “repairs recurrent operations and tensor indexing in the supporting library” | 保留 | 具体机制和修复位置清楚，三种恢复信号与结论对应。 |
| A05 | 55 | “training discrepancies guide repair into library implementations…” | 保留 | 从具体 LSTM 案例解释程序与支持库之间的修复联系，有新增机制信息。 |
| A06 | 67 | “Gradient errors can leave the current loss unchanged.” | 保留 | 用直接因果关系引出检测延迟。 |
| A07 | 67 | “Errors in parameter updates can preserve both current forward values and gradients…” | 保留 | 准确表达参数更新错误在后续步骤体现影响的时间关系。 |
| A08 | 67 | “all 12 runs per fault…mean loss difference curves…31 and 18” | 改写 | 需要就地对应两类具体故障，并区分每次运行的 step 1 与均值曲线的 31/18。见方案 10。 |
| A09 | 67 | “four models for 50 steps…retaining separate state” | 改写 | 保留状态分别演进；把四模型、三种子与 12 次运行合并解释，避免读者回翻 setup。见方案 10。 |
| A10 | 67 | “Individual loss trajectories cross…3/12 and 4/12” | 改写 | `loss trajectories` 应是 loss difference；没有说明越过何阈值、分母和故障对应。见方案 10。 |
| A11 | 67 | “Observing the affected training computation therefore exposes…” | 保留 | 将检测结果解释为观测受影响计算的作用，结论由 step 1 与延后 loss 差异支持。 |
| A12 | 67 | “thresholds, synchronized checks, and healthy controls” | 改写 | `healthy controls` 换为正确程序的检查；保留阈值与同步检查入口。见方案 10。 |
| A13 | 78 | “repairs all six JAX cases…” | 保留 | 六例及故障范围准确，符合已确认主文范围。 |
| A14 | 78 | “single-step SGD verification on three seeds after the first submission” | 保留 | 一步 SGD、三种子、首次提交三项条件都有信息，不能与独立多步研究混合。 |
| A15 | 78 | “Direct repair also accepts all six cases and uses fewer tokens.” | 保留 | 是真实结果，不是防御性免责声明；不能为突出 LaDiM 而删除。 |
| A16 | 78 | “healthy MLP and CNN controls pass” | 改写 | 说明转换器处理已有正确 MLP/CNN 程序后通过评估，避免 `healthy` 的拟人化和抽象控制名。见方案 11。 |
| A17 | 78 | “native conversion preserves the supplied execution or numerical faults…” | 保留 | 解释已有故障经转换仍存在，以及显式修复的作用；与一次转换协议一致。 |
| A18 | 78 | “The same diagnosis and repair procedure thus works beyond MindSpore…” | 保留 | 保留已有跨框架有效性主张，不因 JAX 成本较高自动削弱。 |
| A19 | 78 | “Appendix…details these controls; Appendix…separate study…” | 改写 | 拆分两个附录去向；明确一个是本六例的转换器评估，一个是独立的原生 JAX 多步研究。见方案 11。 |

### 2.4 Ablation Studies：19 句

| 编号 | 行号 | 短引文 | 判定 | 理由与处理 |
|---|---:|---|---|---|
| B01 | 91 | “training signals on 16…ten saved translations…time series repository” | 改写 | 保留三组实验及各自对象，仅去除 `saved translations` 的记录口吻。见方案 01。 |
| B02 | 91 | “reports acceptance and token use for these three studies” | 保留 | 是有内容的表格导航；仓库接受结果由表注给出，不要求新增接受列。 |
| B03 | 94 | “one execution, forward, gradient, and update fault in each CNN…” | 改写 | 当前表达可能被读成每份候选同时有四种故障。改清四模型分别构造四类故障，合计 16 份候选。见方案 02。 |
| B04 | 94 | “Sources, candidates, tools, and budgets are fixed.” | 保留 | 给出受控比较条件，四个并列项均有实质用途。 |
| B05 | 94 | “Available feedback determines whether repair begins and stops.” | 保留 | 解释反馈如何影响启动与停止，是理解未检测故障为何未获修复的必要机制。不得补成未经实现支持的固定诊断路由。 |
| B06 | 94 | “Each added signal exposes another fault class…4/16 to 16/16” | 保留 | 增量反馈与最终完整验证接受率对应；完整验证不能删。 |
| B07 | 94 | “Initially undetected faults decrease from 12 to 8 to 4 to 0…” | 保留 | 提供初始漏检指标，与最终接受数不同，不是重复数字。 |
| B08 | 94 | “Forward values reveal…gradients reveal…updates reveal…” | 保留 | 三项分别解释新增信号的具体作用，属于真实并列关系，不因出现三项而删。 |
| B09 | 122 | “improve repair on the saved initial translations” | 改写 | 对象改为初译程序，保留组件改善修复的判断。见方案 01。 |
| B10 | 122 | “With repair history, LaDiM repairs four…” | 保留 | 该结果与下一句移除历史构成对比；表格应进一步标清完整参照条件。 |
| B11 | 122 | “Removing that history reduces the count to zero.” | 保留 | 直接报告历史组件的实测差异。 |
| B12 | 122 | “Independent evidence handoff repairs one more program…” | 保留 | 与连续调查和修复对话进行具体比较，8/10→9/10 有支持。 |
| B13 | 122 | “preserve the five programs that pass the initial checks” | 改写 | 改为首次评估通过的五份程序，明确这些程序无需修复。见方案 01。 |
| B14 | 122 | “The complete reference retains earlier attempts…” | 改写 | `complete reference` 未指出启用了哪些组件。改用修复历史与独立证据交接作为主语。见方案 12。 |
| B15 | 125 | “repository context management reduces…68.0%…69 checks” | 保留 | 仓库、组件、完整成本和接受结果对应准确。 |
| B16 | 125 | “Both conditions retain investigation and independent evidence handoff.” | 保留 | 是判断组件比较的必要固定条件。 |
| B17 | 125 | “In a separate paired ablation…19.8%…42 to 30” | 改写 | 明说在同一时间序列仓库比较有无结构分析，避免 `paired` 代替实验对象和操作。见方案 13。 |
| B18 | 125 | “Structural context identifies…broader context mechanism carries…” | 改写 | 用正式组件名直接说明动作，消除 `structural context`、`broader context mechanism` 的指代跳转。见方案 13。 |
| B19 | 125 | “complete program component results…both repositories' cumulative comparisons…” | 保留 | 为完整程序组件、累计仓库比较及两个正式模块的消融提供入口；正式名称保持。 |

## 3. 图注、表题与表下注逐句台账

源文件均为 `sections/experiments.tex`。

### 3.1 主结果表及成本图

| 编号 | 行号 | 短引文 | 判定 | 理由与处理 |
|---|---:|---|---|---|
| CM01 | 21 | “Migration acceptance and token use on common inputs.” | 保留 | 表题准确概括接受与成本比较。 |
| CM02 | 21 | “Panels (a,b)…programs…(c,d)…repositories.” | 保留 | 清楚区分两个层级。 |
| CM03 | 21 | “End-to-end costs include the shared initial translation once…” | 保留 | 初译只计一次、后续调用和失败尝试均计入，属于关键成本口径。 |
| CM04 | 21 | “A dash denotes a method without LLM calls.” | 保留 | 与主表 MSAdapter 的横杠一致。适用范围是本表，不能扩展为所有表的统一零值规则。 |
| NM01 | 29 | “0/10…an unmigrated PyTorch import prevents test collection.” | 保留 | 解释 0/10 为已确认通过数，不虚构实际执行了十个失败测试。 |
| NM02 | 29 | “Complete token costs and repository gradient and parameter update checks…” | 保留 | 提供被主表压缩的成本和训练检查入口。 |
| CF01 | 39 | “Token costs on MindSpore migration.” | 保留 | 图题范围明确。 |
| CF02 | 39 | “subsequent calls grouped by the initial checks” | 改写 | 必须说明分组依据是程序首次评估通过或失败，色块计量的是后续调用 token。见方案 08。 |
| CF03 | 39 | “one distinct source and evaluation input, sorted within each group” | 改写 | 来源说明按 source-and-contract 去重；现有 `evaluation input` 容易被理解成一次样本输入。还需说明排序量与方向。见方案 08。 |
| CF04 | 39 | “both accept 50/50 tasks” | 保留 | 图独立阅读时说明成本比较对应相同接受数，必要。 |
| CF05 | 39 | “LaDiM uses 57.4% fewer tokens.” | 保留 | 直接提供总体差异，不必为了避免与正文重复而删除关键图解。 |
| CF06 | 39 | “Positive values indicate lower LaDiM cost.” | 保留 | 明确有符号差值的解释。 |

### 3.2 初译错误修复表

| 编号 | 行号 | 短引文 | 判定 | 理由与处理 |
|---|---:|---|---|---|
| CN01 | 58 | “Repair and preservation on ten saved initial translations.” | 改写 | 用“初次翻译后”的程序状态替代保存记录用语。见方案 01。 |
| CN02 | 58 | “Five programs require repair and five pass the initial checks.” | 改写 | 明确首次评估及无需修复。见方案 01。 |
| CN03 | 58 | “Costs include all investigation and repair calls…” | 保留 | 说明费用范围和候选/支持库可编辑范围，二者都影响解释。 |

### 3.3 检测图

| 编号 | 行号 | 短引文 | 判定 | 理由与处理 |
|---|---:|---|---|---|
| CD01 | 72 | “Training signal detection and loss threshold crossings.” | 改写 | 应为 `loss difference` 的阈值越界，避免被读成原始 loss 超阈值。见方案 10。 |
| CD02 | 72 | “gradient scaling (a)…partial update suppression (b)…12 runs” | 改写 | 故障名称和 step 1 保留，就地补明四模型×三种子的分母。见方案 10。 |
| CD03 | 72 | “The loss check crosses its threshold…on the mean curves.” | 改写 | 主语改为均值 loss difference 曲线，防止把均值越界写成某个方法的检测事件。见方案 10。 |
| CD04 | 72 | “Individual loss trajectories cross…3/12 and 4/12…” | 改写 | 明确差值、阈值、两故障与分母。见方案 10。 |
| CD05 | 72 | “curves showing means and shading showing ranges” | 改写 | 生成器已明确均值与最小—最大范围，直接写清统计量及归一化后阈值为 1。见方案 10。 |

### 3.4 JAX 表

| 编号 | 行号 | 短引文 | 判定 | 理由与处理 |
|---|---:|---|---|---|
| CJ01 | 81 | “Repair and native conversion controls on six faulty JAX candidates.” | 保留 | 六例、修复与转换对照的任务范围明确；不能据此把该集合改称独立原生 JAX 翻译研究。 |
| CJ02 | 81 | “LLM repair allows up to four submissions…” | 保留，待主代理核对预算来源 | 文字正确区分上限与实际执行，正文另说明首次提交通过。但本快照未给当前六例实验的原始预算配置，需核对当前冻结来源，不能套用历史 Track C 的三轮预算。 |
| CJ03 | 81 | “Native conversion runs once without an LLM…” | 保留 | 一次转换、无 LLM、已有故障须被移除，完整解释接受含义。 |

### 3.5 消融表

| 编号 | 行号 | 短引文 | 判定 | 理由与处理 |
|---|---:|---|---|---|
| CA01 | 97 | “Effects of training signals and repair components.” | 保留 | 覆盖三组消融内容。 |
| CA02 | 97 | “Each + adds a signal to the preceding row…” | 保留 | 已明确逐行累加和最终四种信号，符合 B01。 |
| CA03 | 97 | “Final acceptance uses complete verification.” | 保留 | 区分可用反馈与最终判定标准，是实验解释的核心。 |
| CA04 | 97 | “Ten saved translations: parentheses count failed programs repaired…” | 改写 | 将初译对象及括号内分母说清；消除冒号压缩造成的读法跳转。见方案 14。 |
| CA05 | 97 | “Independent pairs on time series…” | 改写 | 明确是时间序列仓库上分别比较有无两个组件，并说明三种子用于评估。见方案 14。 |
| NA01 | 117 | “include investigation in repair tokens” | 改写 | 用表头 `Repair tokens` 作主语，直接定义统计范围。见方案 14。 |
| NA02 | 117 | “includes editing examples and feedback for malformed edits” | 改写 | 保留这项真实配置差异，用“编辑格式不正确时的反馈”解释 `malformed edits`。见方案 14。 |
| NA03 | 117 | “calls cover investigation and repair…tokens also include initial translation” | 保留 | 调用数与 token 的阶段范围不同，需要明确保留。 |
| NA04 | 117 | “Each condition runs once, with a separate complete reference…” | 改写 | 限定为面板 (c)，并将 `complete reference` 换为每项比较各自启用组件的参照运行。见方案 14。 |

## 4. 表格、标题及全部生成标签台账

### 4.1 `figures/TABLE_main_comparison.tex`

| 编号 | 行号 | 对象 | 判定与理由 |
|---|---:|---|---|
| TM01 | 3 | `(a) PyTorch to MindSpore` | 保留。方向准确。 |
| TM02 | 7 | `Method / LLM calls / Tokens (millions) / Accepted` | 保留。完整词、单位和最右接受列均合适。 |
| TM03 | 9 | Direct LLM：29；0.429；29/50 | 保留。29 次调用与 50 个任务标识不矛盾，来源说明已交代去重计费。 |
| TM04 | 10 | CodeTransEngine：29；0.280；31/50 | 保留。正式名不加 `direct` 后缀。 |
| TM05 | 11 | MSAdapter：`--`；`--`；15/50 | 保留。横杠只对应无 LLM 调用与 token，接受数保留。 |
| TM06 | 12 | SWE-agent：1,097；20.831；44/50 | 保留。不移除中断结果所占的分母。 |
| TM07 | 13 | MatchFixAgent：619；12.097；50/50 | 保留。并列最佳接受数加粗合理。 |
| TM08 | 14 | LaDiM：326；5.159；50/50 | 保留。数值和强调不变。 |
| TM09 | 21 | `(b) Java/DJL to Python/PyTorch` | 保留。语言和框架均明确。 |
| TM10 | 25 | 程序面板表头 | 保留。与 (a) 一致。 |
| TM11 | 27 | Direct LLM：18；0.694；1/18 | 保留。 |
| TM12 | 28 | InterTrans：89；2.286；1/18 | 保留。来源说明指出未完成生成调用也计入成本，不改为成功调用成本。 |
| TM13 | 29 | Test-guided repair：71；4.475；7/18 | 保留标签与数值。setup 应补上相同显示名，见方案 03。 |
| TM14 | 30 | SWE-agent：682；24.321；8/18 | 保留。 |
| TM15 | 31 | MatchFixAgent：524；28.355；8/18 | 保留。 |
| TM16 | 32 | LaDiM：345；21.479；9/18 | 保留。9/18 最佳结果强调不变。 |
| TM17 | 39 | 两个 repository 面板名 | 保留。与 setup 的两个仓库对应。 |
| TM18 | 41 | `Behavior checks passed` | 保留。正文已有对应定义，不另造指标名。 |
| TM19 | 41 | `Entry points / Original tests` | 保留。两个仓库使用不同补充结果列，正文已解释。 |
| TM20 | 41 | `Repair calls / Tokens (millions)` | 保留。35 次调用的重点不变；完整生成器的调用统计范围需由主代理核对，见末节。 |
| TM21 | 43 | SWE-agent 两仓库全部结果 | 保留：69/69、3/3、80、8.200；104/145、10/10、80、8.317。 |
| TM22 | 44 | MatchFixAgent 两仓库全部结果 | 保留：69/69、3/3、69、13.598；129/145、0/10、80、8.679。 |
| TM23 | 45 | LaDiM 两仓库全部结果 | 保留：69/69、3/3、35、2.614；130/145、10/10、80、8.811。35 与 130/145 的强调保留。 |

### 4.2 `figures/TABLE_natural_repairs.tex`

| 编号 | 行号 | 对象 | 判定与理由 |
|---|---:|---|---|
| TN01 | 3 | 五列表头 | 保留。修复数、保留数、成本和最终接受分工明确；首次评估的含义在正文和 caption 中补清。 |
| TN02 | 5 | Direct repair：0/5；5/5；3.751；5/10 | 保留。 |
| TN03 | 6 | SWE-agent：0/5；5/5；12.678；5/10 | 保留。 |
| TN04 | 7 | MatchFixAgent：0/5；5/5；14.351；5/10 | 保留。 |
| TN05 | 8 | LaDiM：4/5；5/5；13.207；9/10 | 保留。不得用消融面板的 15,547,813 token 替换此处成本，两者配置不同。 |

### 4.3 `figures/TABLE_jax_repairs.tex`

| 编号 | 行号 | 对象 | 判定与理由 |
|---|---:|---|---|
| TJ01 | 3 | `LLM repair / Single native conversion` | 保留。区分修复与一次转换，直接服务于结果解释。 |
| TJ02 | 5 | `Metric / LaDiM / Direct repair / Ivy / torch2jax` | 保留。方法和 setup 定义对应；不新增 TorchAX 方法列。 |
| TJ03 | 7 | Accepted：6/6；6/6；0/6；0/6 | 保留。不能混入另一项原生 JAX 研究的 1/2。 |
| TJ04 | 8 | LLM calls：76；57；0；0 | 保留。此表零值明确表示没有 LLM 调用，不需照主表改横杠。 |
| TJ05 | 9 | LLM tokens：674,009；353,311；0；0 | 保留。Direct repair 更省 token 的正文结论正确。 |

### 4.4 `figures/TABLE_training_signals_compact.tex`

| 编号 | 行号 | 对象 | 判定与理由 |
|---|---:|---|---|
| TS01 | 3 | `Feedback / Accepted / Repair tokens` | 保留。最终接受使用完整验证，caption 已单独说明。 |
| TS02 | 5 | `Execution and basic checks`；4/16；2,088,915 | 标签需主代理核对后具体化，数值保留。`basic checks` 未在本快照明确列出，不能自行猜成接口、形状或参数检查。 |
| TS03 | 6 | `+ Forward values`；8/16；2,603,211 | 保留。 |
| TS04 | 7 | `+ Gradients`；12/16；3,302,873 | 保留。 |
| TS05 | 8 | `+ Parameter updates`；16/16；3,418,960 | 保留。累加含义与换行对齐不变，16/16 保持加粗。 |

### 4.5 `figures/TABLE_program_components_compact.tex`

| 编号 | 行号 | 对象 | 判定与理由 |
|---|---:|---|---|
| TP01 | 3 | `Condition / Accepted (repaired) / Repair tokens` | 保留。括号内分母 5 与括号外分母 10 在 caption 明确。 |
| TP02 | 5 | `Independent evidence handoff`；9/10 (4/5)；15,547,813 | 改标签，数值保留。该行同时是有修复历史的参照，现名只显露一个组件。见方案 15。 |
| TP03 | 6 | `Continuous conversation`；8/10 (3/5)；14,516,463 | 改标签，数值保留。直接说明调查与修复共用对话。见方案 15。 |
| TP04 | 7 | `Without repair history`；5/10 (0/5)；10,851,537 | 保留。移除对象明确；caption 或表下注应说明另两行分别改变哪个组件。 |

### 4.6 `figures/TABLE_repository_components.tex`

| 编号 | 行号 | 对象 | 判定与理由 |
|---|---:|---|---|
| TR01 | 1–4 | 来源路径与 SHA256 注释 | 保留在来源记录。不是论文可见文字，不移入正文，也不因行文审核删除。 |
| TR02 | 5 | `(c) Repository components on time series` | 改写为 `(c) Components on the time series repository`。明确具体仓库，见方案 15。 |
| TR03 | 8 | `Without component / With component` | 保留。这两个列组已经直接表达比较操作。 |
| TR04 | 10 | `Component / Calls / Tokens / Token reduction` | 保留。调用和 token 的阶段范围由表下注说明。 |
| TR05 | 12 | Repository context management：26、6,047,074；22、1,936,579；68.0% | 保留。 |
| TR06 | 13 | Repository Structural Analysis：42、2,651,248；30、2,126,900；19.8% | 保留。正式名称不缩写，两个参照 token 总量不合并，百分比不相加。 |

### 4.7 成本图全部生成文字

源文件：`figures/make_unified_results.py`。

| 编号 | 行号 | 标签或生成文字 | 判定与理由 |
|---|---:|---|---|
| GF01 | 434 | 各方法总量的动态数值标签 | 保留。按百万 token 显示两位小数，与横轴单位一致。 |
| GF02 | 435 | `LaDiM / MatchFixAgent / SWE-agent` | 保留全部三项及三根总量横柱。 |
| GF03 | 436 | `Total tokens (millions)` | 保留。单位明确。 |
| GF04 | 438 | `(a) Total tokens` | 保留。面板标题简洁。 |
| GF05 | 440 | `Initial translation` | 保留。与初译只计一次的口径一致。 |
| GF06 | 440 | `Passes initial checks` | 改为后续调用的标签，避免与 `Initial translation` 混成不同性质的色块。见方案 16。 |
| GF07 | 440 | `Needs repair` | 同上，应标明该色块是首次评估失败程序的后续调用。见方案 16。 |
| GF08 | 453 | `Tokens saved by LaDiM (thousands)` | 保留。正负差值由图例及 caption 解释，负值可理解为负节省。 |
| GF09 | 455 | `Passes initial checks / Needs repair` | 改为首次评估通过/失败的过去时状态，见方案 16。 |
| GF10 | 456 | `Migration inputs` | 保留。caption 补清每根柱是源程序与评估要求的一个组合，不新增内部术语。 |
| GF11 | 457 | `Lower token use by LaDiM` | 保留。对应正值颜色。 |
| GF12 | 458 | `Higher token use by LaDiM` | 保留。对应负值颜色。 |
| GF13 | 461 | `(b) Savings on each input` | 保留。caption 提供 input 的确切含义。 |
| GF14 | 437、454 | 数值刻度 | 保留。无语言修改需求，不改变范围和数据。 |

### 4.8 检测图全部生成文字

源文件：`figures/make_gradient_drift.py`。

| 编号 | 行号 | 标签或生成文字 | 判定与理由 |
|---|---:|---|---|
| GD01 | 10 | `Loss difference` | 保留。实际字段是 `loss_abs_diff`，与 loss 差值相符。 |
| GD02 | 11 | `Gradient difference` | 改为 `Gradient norm difference`。字段是 `grad_norm_abs_diff`，应避免读成整个梯度向量的差。见方案 17。 |
| GD03 | 12 | `Update difference` | 保留。相对 L2 指标的精确定义可由协议说明；本次无需仅为扩写而加长所有图例。 |
| GD04 | 15 | `(a) Incorrect gradients` | 建议改为 `(a) Gradient scaling`，与具体故障及 caption 对齐。见方案 17。 |
| GD05 | 16 | `(b) Incorrect parameter updates` | 建议改为 `(b) Partial update suppression`，同上。 |
| GD06 | 60 | `LaDiM detects at step {first_detection}` | 保留。源码检查全部 12 次运行的首次检测步相同，标签有实现内校验支持。 |
| GD07 | 68 | `Loss check detects at step {first_loss}` | 必须改为均值 loss difference 越阈值的标签。该值由均值曲线计算，现文字有读成个体检测时间的风险。见方案 17。 |
| GD08 | 76 | `Detection threshold` | 保留。横线位于归一化值 1；caption 补足含义。 |
| GD09 | 86 | `Difference / threshold` | 保留。与每个信号除以自身阈值的计算一致。 |
| GD10 | 92 | `Training step` | 保留。 |
| GD11 | 84、93 | 对数轴及训练步刻度 | 保留。无需改变数值或尺度。 |

### 4.9 标题与 LaTeX 标签

| 对象 | 行号 | 判定 |
|---|---:|---|
| `Experiments` 与四个 subsection 标题 | 1、3、17、51、88 | 全部保留，层次清楚。 |
| Setup 三个段首 | 6、9、14 | 保留加粗段首形式，不新增小节层级。 |
| Main Results 三个段首 | 33、43、46 | 保留。 |
| Analysis 三个段首 | 54、66、76 | 保留，特别保留已确认的 `Generalization Across Frameworks`。 |
| Ablation 三个段首 | 93、121、124 | 保留，Repository Structural Analysis 使用全称。 |
| 章节定位标签 | 4、18、52、77、89 | 保留，内部引用键不作为论文用语重命名。 |
| 表格标签 | 22、59、82、98、99 | 保留。同一消融表的两个标签是引用别名，不是重复显示文字。 |
| 图形标签 | 40、73 | 保留，尤其保留 `fig:gradient-drift` 的定位。 |
| 表面板标题 | 105、110 | 保留；面板 (b) 已写明两项组件，与建议修改的行标签配合即可。 |

## 5. 需调整项及具体英文候选

以下均为待主代理整合的方案，不是已实施改动。

### 方案 01：把“保存的翻译”和“初始检查”改为实际程序状态

对应：W01、W03、W06、E08、R08、B04，以及最新意见 6。

#### 01a. Setup 中首次定义

原句，`sections/experiments.tex:7`：

> To examine repair of actual translation errors, we use ten saved initial translations: five require repair and five pass the initial checks.

候选：

> To examine repair of actual translation errors, we evaluate ten programs produced by an initial translation. Five require repair, and five pass the first evaluation without repair.

保留十份初译、五份需修复、五份无需修复；不把“首次评估通过”扩大为所有可能输入下正确。

#### 01b. 主结果中的分组

原句，`:34`：

> The savings cover both programs that require repair and programs that pass the initial checks (Figure~\ref{fig:repair-comparison}).

候选：

> The savings cover both programs that require repair and those that pass the first evaluation (Figure~\ref{fig:repair-comparison}).

#### 01c. 自然错误段的表头解释

原句，`:55`：

> Table~\ref{tab:natural-repairs} reports failed programs repaired, passing programs preserved, and final accepted programs for the ten saved translations.

候选：

> For the ten programs produced by an initial translation, Table~\ref{tab:natural-repairs} reports how many initially failing programs are repaired, how many initially passing programs remain accepted, and how many programs are accepted at the end.

这句可以略长，因为它同时解释三项指标；不要另造三个指标缩写。

#### 01d. 自然错误表题

原句，`:58`：

> Repair and preservation on ten saved initial translations. Five programs require repair and five pass the initial checks.

候选：

> Repair and preservation of ten programs after initial translation. Five require repair, and five pass the first evaluation without repair.

#### 01e. 消融开头

原句，`:91`：

> We evaluate training signals on 16 faulty candidates, repair history and independent evidence handoff on ten saved translations, and repository context management and Repository Structural Analysis on the time series repository.

候选：

> We evaluate training signals on 16 faulty candidates, repair history and independent evidence handoff on ten initial translations, and repository context management and Repository Structural Analysis on the time series repository.

此处已在 setup 定义初译程序，无需每次展开成同样的长解释。

#### 01f. 程序组件结果

原句，`:122`：

> Repair history and independent evidence handoff improve repair on the saved initial translations (Table~\ref{tab:signal-ablation}b).

候选：

> Repair history and independent evidence handoff improve repair of the initial translations (Table~\ref{tab:signal-ablation}b).

原句，同处：

> All three conditions preserve the five programs that pass the initial checks.

候选：

> All three conditions preserve the five programs that pass the first evaluation without repair.

### 方案 02：区分反馈消融与故障构造

对应：E01、B01、B04、W03、W07。

原句，`sections/experiments.tex:7`：

> A separate study controls the training signals on 16 faulty candidates.

候选：

> A separate study varies the training signals provided as feedback for repairing 16 faulty candidates.

原句，`:94`：

> We compare cumulative feedback on 16 fixed candidates, with one execution, forward, gradient, and update fault in each CNN, image MLP, Transformer classifier, and small causal language model.

候选：

> We compare cumulative feedback on 16 fixed candidates. For each of four models—a CNN, an image MLP, a Transformer classifier, and a small causal language model—we use four candidates with execution, forward, gradient, and update faults, respectively.

为避免破折号，建议最终采用：

> We compare cumulative feedback on 16 fixed candidates from a CNN, an image MLP, a Transformer classifier, and a small causal language model. Each model contributes four candidates with execution, forward, gradient, and update faults, respectively.

这里表达的是四模型×四故障。主代理应保持冻结构造中的“一份候选对应一类故障”，不补充未经提供的注入位置或故障实现。

### 方案 03：让基线定义与表行一一对应，移走配置清单

对应：E07、E09、E06、W03、W06。

原句，`sections/experiments.tex:10`：

> We compare LaDiM with SWE-agent~\citep{yang2024sweagent} and MatchFixAgent~\citep{ibrahimzada2025matchfixagent} using a common DeepSeek backend and each baseline's native algorithms, prompts, tools, parsers, and retry policies.

主文候选：

> We compare LaDiM with SWE-agent~\citep{yang2024sweagent} and MatchFixAgent~\citep{ibrahimzada2025matchfixagent} using a common DeepSeek backend and each baseline's native repair procedure.

移动目标：`sec:supplementary-protocols` 中的基线配置说明，保留算法、prompt、工具、parser 和重试策略的实际配置。科学配置不删成来源哈希记录，也不继续以长接口清单占主文。

原句，同处：

> The main table also includes Direct LLM initial translation, CodeTransEngine's direct translation configuration~\citep{macedo2025codetransengine}, MSAdapter~\citep{openi2025msadapter}, InterTrans~\citep{macedo2024intertrans}, and a repair loop that rewrites the complete candidate from test feedback.

候选：

> The main table also includes Direct LLM for initial translation, CodeTransEngine's direct translation configuration~\citep{macedo2025codetransengine}, MSAdapter~\citep{openi2025msadapter}, and InterTrans~\citep{macedo2024intertrans}. Test-guided repair rewrites the complete candidate using test feedback.

原句，同处：

> Direct repair in the analysis studies is a separate control that receives the saved candidate and uses LaDiM's inspection, testing, and editing tools with its existing repair procedure.

主文候选：

> Direct repair in the analysis studies starts from the initial translation and uses LaDiM's inspection, testing, and editing tools.

`existing repair procedure` 所指的具体流程由主代理对照冻结配置补入相应协议。当前材料不足以补写“没有 Verifier”“固定提示词”或某种重试机制。

删除：

> Each table lists the methods evaluated in that study.

### 方案 04：TorchAX 整句移到 JAX 协议

对应：E10，最新意见 2。

原句，`sections/experiments.tex:12`：

> TorchAX, a PyTorch frontend for JAX~\citep{google2025torchax}, is the execution backend for LaDiM and Direct repair, with JAX differentiation and Optax parameter updates.

移动目标：`sec:jax-protocol` 的运行环境或执行协议段。整句信息与引用保留，主文删除该句。

主文继续保留 Ivy 与 `torch2jax` 的定义、一次转换方式及故障移除判定；TorchAX 不进入对比方法表。

### 方案 05：精简评价段中的重复和无信息概括

对应：E04、E06、W06，最新意见 3。

删除原句，`sections/experiments.tex:15`：

> Accepted programs pass every required check.

前句已定义接受所需检查。

移出主文：

> The main migration comparisons check consecutive training steps.

移动目标：`sec:supplementary-protocols` 下各项研究的具体评估协议。附录需说明对应研究的训练步数及比较方式，不能原样挪过去继续保持抽象。

本快照没有各主比较的具体步数，因此不提供带猜测数字的英文完成句。已知的 JAX 六例“一步 SGD”与独立检测研究“50 步”保留各自位置，不拿它们填补其他研究的协议。

### 方案 06：直接解释 93.0% 的输入 token 差异

对应：R07、W01、W02、W07。

原句，`sections/experiments.tex:34`：

> Reduced input usage accounts for 93.0\% of the token savings, locating most of the difference in the context processed during investigation and repair.

候选：

> Reduced input-token usage accounts for 93.0\% of the savings, so most of the reduction comes from processing less context during investigation and repair.

如整段希望减少连字符，可用：

> Reduced input token usage accounts for 93.0\% of the savings, so most of the reduction comes from processing less context during investigation and repair.

不把这个成本构成分解扩写成“已经单独证明全部节省由某一个组件造成”；组件贡献仍由各自消融解释。

### 方案 07：将 1/2/4 写成预算结果

对应：R07、W07，最新意见 4。

原句，`sections/experiments.tex:34`：

> LaDiM accepts 46/50 tasks after the first submission and all 50 after the second, retaining full acceptance at four submissions.

候选：

> At submission budgets of one, two, and four, LaDiM accepts 46/50, 50/50, and 50/50 tasks, respectively.

这保留全部真实预算点，不增加第三次提交结果，也不暗示四次提交或四次修复均实际执行。

### 方案 08：补清成本图的色块、柱子和排序含义

对应：F03、F04、R12、W03、W07。

原句，`sections/experiments.tex:39`：

> (a) LaDiM, MatchFixAgent, and SWE-agent totals include initial translation and subsequent calls grouped by the initial checks.

候选：

> (a) Total tokens for LaDiM, MatchFixAgent, and SWE-agent are divided into initial translation and subsequent calls for programs that passed or failed the first evaluation.

原句，同处：

> (b) Each bar shows MatchFixAgent tokens minus LaDiM tokens for one distinct source and evaluation input, sorted within each group.

候选：

> (b) Each bar shows MatchFixAgent tokens minus LaDiM tokens for one distinct combination of source program and evaluation requirements. Bars are grouped by whether the first evaluation passed and sorted by increasing token difference within each group.

`evaluation requirements` 对应来源说明中的 contract，避免把内部 `contract` 作为新术语重新引入。主代理可按正文已有评估定义确定最终用词；不要改成“每个任务标识一根柱”，因为图形实际按去重组合绘制。

保留图注中的共同 50/50、57.4% 和正值含义。无需为解释柱子而把 29、20/9 等细账重新塞回结果段。

### 方案 09：删除时间序列段的重复结尾

对应：R07、W01、W06。

原句，`sections/experiments.tex:47`：

> The coordinated repair therefore preserves training behavior across several callers with substantially lower token use.

建议删除。前两句已经提供多个调用入口、69/69、68.1% 和 80.8%。删除不损失结果力度，也不改变仓库协调机制的论述。

### 方案 10：重写检测解释，严格分开个体运行与均值曲线

对应：F05、R13、W03、W07，最新意见 5。

原句，`sections/experiments.tex:67`：

> LaDiM's gradient and update checks detect their respective faults at step~1 in all 12 runs per fault, while the mean loss difference curves cross the detection threshold at steps 31 and 18 (Figure~\ref{fig:gradient-drift}).
>
> The trajectories cover four models for 50 steps with source and target executions retaining separate state.
>
> Individual loss trajectories cross within this window in only 3/12 and 4/12 runs.

建议将这三句组织为：

> For each fault, we run four models with three seeds each, giving 12 runs of 50 training steps. Source and target executions maintain separate states throughout these trajectories. LaDiM detects gradient scaling and partial update suppression at step~1 in all 12 runs for each fault (Figure~\ref{fig:gradient-drift}). The mean absolute loss difference between source and target first exceeds the loss detection threshold at step~31 for gradient scaling and step~18 for partial update suppression. Across individual runs, this loss difference exceeds the same threshold within 50 steps in 3/12 runs with gradient scaling and 4/12 runs with partial update suppression.

其中：

- 12 明确为四模型×三种子。
- 3/12 对应 gradient scaling，4/12 对应 partial update suppression。
- 越过阈值的是源与目标的绝对 loss difference。
- 31/18 是均值曲线的首次越界，不是个体检测时刻，也不是 SWE-agent 或 MatchFixAgent 的结果。
- 阈值绝对数值未在提供的快照中出现，不自行补写。

原句，同处：

> Appendix~\ref{sec:detection-measurements} gives the thresholds, synchronized checks, and healthy controls.

候选：

> Appendix~\ref{sec:detection-measurements} gives the thresholds, checks with synchronized states, and evaluations of correct programs.

检测图完整 caption 候选，替换 `:72`：

> Training signal detection and loss difference threshold crossings. Each panel contains 12 runs from four models and three seeds. LaDiM detects gradient scaling (a) and partial update suppression (b) at step~1 in every run. The mean loss difference first exceeds its detection threshold at step~31 in (a) and step~18 in (b). Within 50 steps, the loss difference exceeds this threshold in 3/12 individual runs in (a) and 4/12 in (b). Each difference is divided by its detection threshold, so a value above 1 indicates a threshold crossing. Curves show means, and shaded regions span the minimum and maximum across the 12 runs.

该候选略长，但每句分别承担分母、step 1、均值、个体和绘图统计量的解释，不能靠删掉其中一种统计口径来缩短。

### 方案 11：解释 JAX 正确程序对照，并拆分附录去向

对应：E08、R09、R10、R11、R14、W04。

原句，`sections/experiments.tex:78`：

> Ivy and \texttt{torch2jax} accept none of the faulty candidates after native conversion, while their healthy MLP and CNN controls pass.

候选：

> Ivy and \texttt{torch2jax} accept none of the faulty candidates after native conversion. Their conversions of the corresponding correct MLP and CNN programs pass the evaluation.

这解释了对照是什么，不新增转换器功能，也不把 0/6 说成无法处理所有正确程序。

原句，同处：

> Appendix~\ref{sec:jax-protocol} details these controls; Appendix~\ref{sec:native-jax-study} reports the separate study of native JAX translations with consecutive training steps.

候选：

> Appendix~\ref{sec:jax-protocol} details the converter evaluations. Appendix~\ref{sec:native-jax-study} reports the separate study of native JAX translations evaluated over consecutive training steps.

保留 Direct repair 同为 6/6 且 token 更少的原句，也保留 LaDiM 跨框架有效性的结论。

### 方案 12：用组件直接解释程序消融的完整条件

对应：B02、B03、B04、W03。

原句，`sections/experiments.tex:122`：

> The complete reference retains earlier attempts and their verification feedback while allowing the Repair Agent to reassess the Verifier's evidence in its own conversation.

候选：

> Repair history retains earlier attempts and their verification feedback, while independent evidence handoff lets the Repair Agent reassess the Verifier's evidence in its own conversation.

这样说明两个组件各自提供什么，不要求读者先理解未定义的 `complete reference`。两个动作均来自原句，不增加新的代理通信机制。

### 方案 13：明确仓库上有无组件的比较及组件动作

对应：B04、B05、M12、W03，最新意见 6。

原句，`sections/experiments.tex:125`：

> In a separate paired ablation, Repository Structural Analysis reduces end-to-end token use by 19.8\% and LLM calls from 42 to 30, with the same complete acceptance.

候选：

> A separate comparison on the same time series repository evaluates LaDiM with and without Repository Structural Analysis. Enabling this component reduces total token use by 19.8\% and LLM calls from 42 to 30, while retaining acceptance on all 69 checks.

原句，同处：

> Structural context identifies relevant implementations, while the broader context mechanism carries plans, measurements, and inspected code across the investigation.

候选：

> Repository Structural Analysis identifies relevant implementations. Repository context management keeps plans, measurements, and inspected code available throughout the investigation.

这两句仍解释为何这些组件有助于减少重复上下文，不把整体包的 68.0% 分摊给某个子组件。

### 方案 14：改清消融表的分母、独立比较和统计阶段

对应：B01、B02、B04、B05、W03、W07。

原句，`sections/experiments.tex:97`：

> (b) Ten saved translations: parentheses count failed programs repaired, and all conditions retain 5/5 initially passing programs.

候选：

> (b) Results on ten initial translations. Parentheses report repairs among the five programs that failed the first evaluation. All conditions preserve the five programs that passed that evaluation.

原句，同处：

> (c) Independent pairs on time series, with every condition passing 69/69 behavior checks on three seeds.

候选：

> (c) Separate comparisons with and without repository context management or Repository Structural Analysis on the time series repository. Every condition passes all 69 behavior checks evaluated across three seeds.

原表下注，`:117`：

> Panels (a,b) include investigation in repair tokens. Panel (b) includes editing examples and feedback for malformed edits. In (c), calls cover investigation and repair, and tokens also include initial translation. Each condition runs once, with a separate complete reference for each pair.

候选：

> In (a,b), repair tokens include investigation and repair. Panel (b) uses editing examples and feedback when edits are incorrectly formatted. In (c), calls cover investigation and repair, and tokens also include initial translation. Each condition in (c) is run once, and each comparison has its own run with the component enabled.

最后一句保留两组独立参照，避免把三种子误写成三次独立修复重复。不得合并 1,936,579 与 2,126,900 两个参照成本。

### 方案 15：让程序组件行标签说明实际条件

对应：B02、B04、F07。

| 位置 | 原标签 | 候选 |
|---|---|---|
| `TABLE_program_components_compact.tex:5` | `Independent evidence handoff` | `Repair history and independent evidence handoff` |
| 同文件 `:6` | `Continuous conversation` | `Shared investigation and repair conversation` |
| 同文件 `:7` | `Without repair history` | 保留 |
| `TABLE_repository_components.tex:5` | `(c) Repository components on time series` | `(c) Components on the time series repository` |

程序组件表需要配合一句简短说明：

> The second and third rows replace independent evidence handoff with a shared conversation and remove repair history, respectively.

放在消融表下注面板 (b) 的说明之后。这样明确两行各自改变什么，避免读成从第一行到第三行累计删除。

标签增长可能增加行高，后续实施时应通过自然换行解决；本轮没有渲染，不能声称已验证版面。

### 方案 16：同步成本图的分组标签

对应：F03、F04、E08。

`figures/make_unified_results.py:440` 的图例：

| 原文 | 候选 |
|---|---|
| `Initial translation` | 保留 |
| `Passes initial checks` | `Later calls: initially passed` |
| `Needs repair` | `Later calls: initially failed` |

`:455` 的分组横轴标签：

| 原文 | 候选 |
|---|---|
| `Passes initial checks` | `Passed first evaluation` |
| `Needs repair` | `Failed first evaluation` |

“later calls” 表达初译之后的调用，具体分组依据由方案 08 的 caption 说明。颜色、三种阶段、三方法总量和正负柱均保留。

### 方案 17：同步检测图的统计对象与故障标签

对应：F05、W03、W07。

`figures/make_gradient_drift.py`：

| 行号 | 原文 | 候选 |
|---:|---|---|
| 11 | `Gradient difference` | `Gradient norm difference` |
| 15 | `(a) Incorrect gradients` | `(a) Gradient scaling` |
| 16 | `(b) Incorrect parameter updates` | `(b) Partial update suppression` |
| 68 | `Loss check detects\nat step {first_loss}` | `Mean loss difference\ncrosses threshold at step {first_loss}` |

`LaDiM detects at step 1` 保留。31/18 的计算也保留，仅修改标签，使其准确表达源码中“均值先计算、再找越阈步数”的操作。

## 6. 图表生成器与资产同步位置

以下是方案实施时的同步清单，本轮未执行。

| 修改内容 | 文字源／生成器 | 关联输出及核对点 |
|---|---|---|
| 正文、全部图注与表下注 | `sections/experiments.tex` 对应行 | 确认术语、分母、预算与图表一致。 |
| 程序组件条件标签 | `figures/make_unified_results.py:410–417` | `figures/TABLE_program_components_compact.tex`。第 415 行直接使用 `row['label']`；标签的上游定义未在快照给出，主代理需定位。同步核对完整程序组件表。 |
| 主表、自然修复表、JAX 表、信号表 | `figures/make_unified_results.py` 的表格导出逻辑，精确函数行未提供 | 对应 `TABLE_main_comparison.tex`、`TABLE_natural_repairs.tex`、`TABLE_jax_repairs.tex`、`TABLE_training_signals_compact.tex`。仅在采纳相关表头建议时修改，数值不变。 |
| 仓库组件面板标题 | `figures/make_cumulative_components.py`，精确行未提供 | `figures/TABLE_repository_components.tex:5`；其他同源表的命名一致性。 |
| 成本图标签 | `figures/make_unified_results.py:435–461` | `figures/repair_comparison.pdf/.png/.svg`，由 `:474–479` 导出。保留全部三方法与三阶段。 |
| 检测图图例、面板名、标注 | `figures/make_gradient_drift.py:9–16,60–74` | `figures/gradient_drift` 对应资产；论文引用 `gradient_drift.pdf`。核对长标注、箭头及面板标题无重叠。 |
| TorchAX 与多步协议移动 | 附录的 `sec:jax-protocol`、`sec:supplementary-protocols` | 主代理定位实际源文件行；引用随信息移动，不新增基线行。 |
| `basic checks` 的解释 | 信号表生成器及 `sec:supplementary-protocols` | 必须先对照冻结定义确定具体检查项目，再决定补注或改标签。 |

不涉及引言动机图、用户负责的方法图或任何实验结果重算。

## 7. 最重要发现与需主代理裁定事项

1. **检测图必须同时改正文、caption 和生成标注。**
   正文的 “Individual loss trajectories cross” 缺少差值对象、阈值、分母和故障对应；图上的 `Loss check detects` 又把均值越阈写成检测事件。源码明确 31/18 来自均值曲线，支持直接改成 “Mean loss difference crosses threshold”。四模型×三种子、step 1、3/12、4/12 和 50 步全部保留。

2. **1/2/4 应明确写成提交预算；TorchAX 按最新决定移附录。**
   两项已有明确用户决定，无需再讨论是否保留原句。Ivy/torch2jax 的主文定义继续保留，不能随执行后端一起移出。

3. **消融中的两个参照关系需要写清，但不能合并实验。**
   程序组件表第一行实际上同时承担有历史和有独立交接的参照；仓库两行分别使用自己的参照运行。应改标签与表注，保留十份初译／时间序列仓库的既定分组，保留两个 token 参照及 68.0%／19.8%。

4. **有用实验条件应保留，无用记录话语可以删除。**
   支持库可编辑、完整验证、编辑示例与格式纠错、原始测试收集失败原因、成本统计阶段都有解释作用。`Each table lists…`、接受定义后的重复句和时间序列结果末尾的重复总结可直接删除。`saved`、`healthy controls`、`complete reference`、`independent pairs` 则应改成实际对象或比较操作。

5. **三处事实定义需主代理对照当前冻结来源确认。**
   一是当前六例 JAX 的“四次提交上限”，不能沿用 README 历史部分的三轮预算；二是信号表 `basic checks` 的具体内容；三是主表仓库 `Repair calls` 是否完整计入调查调用及其与初译调用的关系。当前快照不足以完成这三项实现核对，本报告未替它们补造定义或改数值。

6. **Direct repair 与早期配置的真实差别需要准确落位。**
   setup 的 `its existing repair procedure` 指代不清，应由主代理结合冻结配置确定附录说明。自然错误主比较与程序组件消融分别使用 13.207M 和 15,547,813 token，来源说明指出编辑示例和格式纠错配置存在区别；该区别应在协议及表下注保留，不能为表面统一而改成相同成本或相同配置。
