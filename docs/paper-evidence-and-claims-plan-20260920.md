# 论文实验与主要主张安排

2026-09-20 后续调整：用户要求摘要与引言只保留关键结果，并将图 3(b) 的平坦预算曲线替换为 LaDiM 与 MatchFixAgent 的逐输入 token 散点图。以下原计划中的预算曲线安排由此项调整取代，已测提交预算数据继续在实验正文报告。当前实现见 `paper-revision-20260920.md`。

论文主线建议确定为：训练代码迁移需要检查前向值、梯度与参数更新；LaDiM 让 agent 根据这些观测自主调查并修复，在统一验收下达到强 agent 的迁移覆盖，同时降低 token 开销。正文围绕这条主线选择实验，每个实验承担明确的论证任务。本文档记录已获批准的改稿方案。根据用户后续要求，正文主结果按 50 个任务编号呈现，实际执行分组在实验设置中说明；本轮已同步 LaTeX、图表及生成脚本，未重跑实验。

正文保留主要方法的完整比较，撤去没有得到当前证据支持的增益主张。与核心主张直接相关的组件对照完整放入补充材料，不从同一消融矩阵只挑一行有利结果。与当前方法定义不同的开发试验和带答案指导实验留在可追溯的仓库归档。这样控制正文范围，也保持主张与公开证据一致。

| 主要主张 | 建议采用的内容 | 最直接的支撑 |
| --- | --- | --- |
| 训练行为需要多阶段验证 | 梯度和参数更新检查能够发现执行与前向检查漏掉的故障，并更早暴露训练差异 | 四模型信号消融；梯度与更新的检测延迟图 |
| 自主证据调查支持有效迁移修复 | 独立 verifier 从合法源程序、候选和实际观测形成假设，修复流程通过外部验收完成迁移 | 统一集合的 9/9 实际修复、20/20 健康保持；跨语言 8/17 实际修复 |
| 相同覆盖下减少 token | 在 MindSpore 统一集合上与 MatchFixAgent 同为 50/50，端到端 token 少 57.4% | 完整六方法主表；逐任务 token 和故障子集开销 |
| 流程适用于多种迁移设置 | MindSpore、Java/DJL 到 Python/PyTorch，以及 JAX 研究支持在多种后端和输入语言上应用该流程 | 跨语言完整比较；JAX 六例修复 |

第二项是系统设计与实际效果主张。主实验衡量整个流程，正文不把全部增益单独归因于角色拆分、类别命名、修复历史或进展提醒。第四项使用所测设置的实际表现来说明适用范围，避免“跨所有框架稳定领先”的表述。

实验章节继续使用现有的 4.1 Experimental Setup、4.2 Main Experiments、4.3 Analysis Experiments、4.4 Ablation Studies。保留 `Generalization Across Frameworks` 标题。

| 论文位置 | 放入的实验或分析 | 段落的主要结论 | 图表安排 |
| --- | --- | --- | --- |
| 第 1 节 Introduction | 梯度、更新信号与损失差异的检测延迟 | 训练内部错误在损失显著漂移前即可被观测，形成多阶段验证的动机 | 图 1，保留两面板；详细协议在 4.3 |
| 第 3 节 Method | 自主调查、证据交接、外部验收与预算内重试 | 说明观测如何进入调查和修复，验收如何决定结束 | 图 2，更新后端与输入输出关系 |
| 4.1 Experimental Setup | 冻结输入、公开契约、验收、baseline 接入、预算和用量定义 | 建立一套清楚的比较协议 | 一段主设置和必要表注，具体哈希留复现材料 |
| 4.2 Main Experiments | 同一源程序集上的六方法端到端迁移 | LaDiM 与 MatchFixAgent 获得相同验收覆盖，使用更少 token | 表 1(a)，所有六方法完整展示 |
| 4.3 Analysis Experiments：Repair Effectiveness and Efficiency | 初译正确／失败分解、逐任务开销、重试 | 修复全部 9 个自然初译故障并保持全部 20 个正确候选；效率优势也存在于实际修复任务 | 图 3，完整预算与开销分析；少量关键数字写正文 |
| 4.3 Analysis Experiments：Training Signals and Detection Latency | 受控训练轨迹与图 1 的详细测量 | 直接训练信号及时发现梯度和更新错误，解释信号设计 | 复用图 1，不再增加同内容小表 |
| 4.3 Analysis Experiments：Generalization Across Languages | 18 个 Java/DJL 到 Python/PyTorch 任务上的六方法比较 | LaDiM 将已有初译的 1/18 提高到 9/18，在所测 agent 中取得最高覆盖 | 表 1(b)，使用独立面板、任务名称及分母 |
| 4.3 Analysis Experiments：Generalization Across Frameworks | 六例 JAX 修复 | 验证调查与修复流程能够在另一目标框架使用；LaDiM 与直接修复均通过 6/6 | 简短段落，完整任务与用量放补充材料 |
| 4.4 Ablation Studies：Training-Signal Coverage | 四种反馈各 16 个条件 | 增加前向值、梯度和更新检查逐步减少漏检，使完整验收从 4/16 提高至 16/16 | 表 2，四行反馈设置统一比较 |
| 4.4 Ablation Studies：Evidence Handoff and Repair Context | 指向完整组件对照 | 交代设计选择的实测结果，正文主要展开训练信号的机制贡献 | 完整组件表放补充材料，正文用一小段准确概括 |

表 1 用两个面板组织主迁移与跨语言比较，面板内方法使用同一输入及验收；面板之间不计算合并成功率。这样保留各自科学问题，也避免把多份小表散落在正文。主集合在设置中一次说明“50 个登记编号，对应 29 个不同输入组合、24 个源文件”；主表、摘要和预算曲线按 50 个编号呈现，逐输入的费用分析按 29 个不同组合进行，token 计入实际调用。

表 1(a) 展示 LaDiM、MatchFixAgent、SWE-agent、Direct LLM、CodeTransEngine 的直接转换配置和 MSAdapter。成功数及端到端 token 分别为 50/50 与 5,159,134；50/50 与 12,097,425；44/50 与 20,831,495；29/50 与 429,109；31/50 与 279,536；15/50 与 0。SWE 的一个接入中断在表注中标识为未测最终验收，实际费用保留。主结果段用相同成功覆盖下 57.4% 的 token 节省建立效率结论，完整表也展示单次翻译方法的低用量。

表 1(b) 展示 LaDiM、SWE-agent、MatchFixAgent、普通测试修复、Direct LLM、InterTrans，接受数分别为 9、8、8、7、1、1，分母均为 18。主集合的 CodeTransEngine 直接路径与跨语言的 InterTrans 搜索按实际算法配置分别命名。正文解释修复流程将原有初译的覆盖从 1 提高到 9；与两个 agent 的差距分别为一例，使用准确的观察性表述。

图 3 可以保留成本与累计验收的两面板组织。成本面板使用完整任务的开销；重试面板使用已经测量的 1、2、4 次提交预算，清楚区分初始正确候选与新增修复。LaDiM 的 9 个故障中，7 个首次修复提交后通过，2 个第二次通过。图中按预算结束时的候选验收记分，不能让曾经通过、随后被改坏的原生 episode 保持在最终成功曲线上。各方法提交内部允许的动作保留原生定义。图表编制直接重算已有检查点，不调用模型。

效率段有两项适合正文的分析。第一，27/29 个输入组合上 LaDiM 的 token 少于 MatchFixAgent，说明整体差异分布于大部分任务。第二，只看 9 个初始故障，新增修复 token 分别为 3.320 百万和 6.532 百万，LaDiM 少 49.2%。这项结果支持实际修复过程中的效率优势。保持健康程序和及时停止也属于流程的实际行为，在同一段分析，无需另起一张表。

表 2 使用执行与基础契约、增加前向值、增加梯度、增加参数更新四行，完整验收依次为 4/16、8/16、12/16、16/16。可以同时展示未触发修复的故障数 12、8、4、0。正文强调各信号如何决定发现故障、触发修复与结束修复，明确这是一项完整流程的信号覆盖消融。该实验的四类受控修改和模型范围在设置中列明，不能将它说成自然迁移中的随机错误比例。

主方法的精确实现、JAX 和信号实验各自已测实现需要按科学设置描述。JAX 与信号研究的工具提示包含编辑格式示例和纠错反馈，主比较使用基础工具 schema 与验证。这个实际差异在设置或补充协议中写清楚，论文不出现开发版本名。也不能把主实验本次原生 MindSpore 程序执行路径写成旧的 torch4ms 优化器桥路径；方法与后端说明要随新主协议同步调整。

完整组件对照包含独立证据交接、连续原会话、移除跨轮历史、移除进展提示，按 50 个编号的接受数为 50、49、50、50。正文可以写“独立证据交接覆盖全部任务；连续原会话在一例未达到最终验收，完整组件对照见补充材料”。同一处简洁说明移除历史或进展提示保持覆盖，因而论文将它们作为运行设置，不主张它们各自带来提升。完整表必须同时报告 token，不能从组件矩阵只保留 50 对 49 的比较来宣称所有组件有效。

| 其他已有实验 | 建议位置 | 处理理由 |
| --- | --- | --- |
| 原自主 50 例故障修复 | 补充材料的受控修复研究 | 它回答给定故障候选的修复问题，45/50 保留原验收身份；主比较已由统一端到端实验承担 |
| 十例自然迁移修复 | 与受控修复合并为补充实验 | 4/5 实际修复可作为额外应用证据，正文无需再引入第三个主分母 |
| 十二例 MatchFix 配对修复 | 补充材料或复现资料 | 12/12 对 11/12 是额外证据，最新统一主表已有完整 MatchFix 比较 |
| 调查模块加入 SWE-agent、MatchFixAgent | 补充材料的完整宿主集成研究 | 记录实际集成效果；撤去通用插拔增益主张，因此不占核心论证篇幅 |
| 旧五模型翻译比较与文档试验 | 复现资料；仅在另有文档贡献时进入补充材料 | 当前主比较与跨语言比较已覆盖迁移效果，旧翻译配置不承担当前修复框架的效果归因 |
| 旧 fixture 信号实验 | 仓库归档 | 四模型、16 实例研究已经提供更直接的信号覆盖证据 |
| 长训练与真实规模探索 | 复现资料；若论文主张长训练等价则必须对应报告 | 当前主张按已测训练步和契约表述，正文无需新增与短程验收不同的问题 |
| 旧定位分数、未完成语义复核的诊断评分 | 评分资料归档 | 论文描述自主调查过程，不给未经充分确认的定位准确率 |
| 所有含故障类别答案、指定修复位置或健康目标答案的旧实验 | 从投稿正文和附录撤下，仓库独立归档 | 与当前自主方法的输入条件不同，不能作为其效果证据 |
| 开发配置与反复版本比较 | 仓库归档 | 内部开发过程不占论文篇幅，不逐例选择最优结果 |

摘要、引言和结论的主要修改如下。

| 当前内容或潜在表述 | 修改方向 |
| --- | --- |
| 45/50 故障修复和自然十例承担摘要主结果 | 换为统一集合的 50/50、与 MatchFixAgent 相同覆盖及 57.4% token 节省；跨语言作为扩展证据 |
| 组件研究证明保留历史有益 | 从核心贡献和结论移除；历史保留作为实现设置准确描述，组件表完整保留 |
| 插拔诊断模块可改善任意 agent | 不提出该主张；明确本文评估的是完整 LaDiM 流程 |
| 通过分类显著提高定位准确率 | 描述自主调查形成可检验假设与代码位置；不使用旧的确定性阶段一致性充当自主定位准确率 |
| 压缩机制导致成本优势 | 直接报告完整方法的 token 效率；若没有触发与因果对照，不把成本差归于压缩 |
| 对所有 baseline 同时有成功率和成本优势 | 用“与 MatchFixAgent 相同覆盖、较少 token；在该统一集合高于单次迁移方法的覆盖”替换 |
| 跨框架有效性 | 保留，以 MindSpore 与 JAX 的实际结果支撑，并新增跨语言适用性 |
| 通用训练语义完全等价 | 写为“通过源目标训练行为的指定验收”，在设置中给出观测范围、种子与阈值 |

建议的三项贡献文字如下，可用于引言改写：

1. We formulate autonomous training-code repair around observations of execution, forward values, gradients, and parameter updates, enabling agents to investigate faults that remain hidden under incomplete checks.
2. We develop LaDiM, which separates evidence gathering from code repair and evaluates submitted programs through a common acceptance and retry procedure.
3. We evaluate LaDiM on unified migration tasks and show that it matches MatchFixAgent's acceptance coverage with fewer tokens on MindSpore. Controlled signal studies explain verification coverage, while cross-language and JAX studies examine applicability across migration settings.

建议的摘要结果部分如下：

> On a collection of 50 PyTorch-to-MindSpore migration tasks, LaDiM achieves 50/50 acceptance, matching MatchFixAgent while using 57.4% fewer end-to-end tokens. It repairs every failing initial translation and preserves every initially accepted program. On 18 Java/DJL-to-Python/PyTorch tasks, LaDiM accepts nine translations, compared with eight for SWE-agent and MatchFixAgent and one for direct translation. Experiments on MindSpore and JAX demonstrate the applicability of the diagnosis and repair procedure across target frameworks.

正文的分析段应说明这些数值对应什么能力。例如：共同初译已正确的任务上保留正确行为；有故障的任务上通过实际修改获得新增覆盖；跨语言任务中复用同样的调查与验收接口。分析段不再逐行复述主表，不把调用恢复、开发命名、审计数量或费用账本处理写成科研贡献。

现有稿件中需要具体替换的范围是：摘要；引言最后一段与贡献列表；方法中的主后端和编辑范围说明；4.1 全部实验设置；4.2 主表、结果段与图 3；4.3 旧故障失败分类段及成本段；4.4 旧组件主表与历史收益结论；Conclusion；附录中的历史指导案例及带答案比较表。`Generalization Across Frameworks` 标题保留，图 1 的科学含义和均值曲线／单次检出区别保留。

推荐的正文规模为两张结果表、三张图：表 1 两个面板分别比较统一迁移和跨语言迁移；表 2 解释训练信号消融；图 1 展示检测动机；图 2 展示框架；图 3 展示效率和已有重试预算。这一安排使用已经完成的结果，不需要增加模型调用。

证据来源：[统一实验完成报告](unified-experiments-results-20260919.md)、[逐任务分析](experiment-analysis-20260920.md)、[训练信号审查](maintext-training-signal-independent-review-20260918.md)、[检测实验](maintext-diagnostic-rerun-20260918.md)、[历史自主实验及 JAX 汇总](maintext-results-20260918.md)。布局按当前 `conference_101719.tex` 的结构安排；改稿与验证记录见 `docs/paper-revision-20260920.md`。
