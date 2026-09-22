# Related Work 逐句审查

## 范围与依据

审查版本为 `d1d6a53`，日期为 2026-09-23。范围为 `conference_101719.tex:74–83` 的 Related Work：19 个正文句子、1 个节标题、3 个段落标题；本节没有公式、算法、图、表、图注或表注。正文三段分别为 6、6、7 句。以下使用 RW-01–RW-19 作为稳定局部编号；同一源码行包含多个句子，编号按阅读顺序区分。

已按 `tmp/manuscript-review-20260923/review-brief.md`，读取项目规则、完整有效意见清单、项目 humanizer 技能和 Zhekai Du 写作 DNA，并对照引言、方法中的角色分工及实验中的共同输入和成本定义。有关成本表述的来源另见 `data/paper_figures/README.md` 的 Current unified migration comparison。引用键和文献名称对照 `ref.bib`；本轮没有逐篇重新审读被引论文全文。

适用意见为 W01–W06、A08、M14、E06，以及本轮共同要求第 7、8 条。方案保持已有贡献和文献范围，重点处理笼统对象、动作主体和章节分工。下文全部是待审核建议，没有修改论文或更新共享意见清单。

## 逐句台账

| 编号 | 源位置与短引文 | 决定 | 具体理由 |
|---|---|---|---|
| RW-01 | `conference_101719.tex:77`，句 1， “Neural translation methods learn code mappings...” | 保留 | 交代神经代码翻译的学习材料和测试、编译器表示两类辅助机制，直接进入技术路线。三个引用各有用途，不需要拆成文献名单。 |
| RW-02 | 同上，句 2，“ExeCoder encodes functional semantics...” | 保留 | 将 ExeCoder 的表示与 InterTrans 的中间翻译路径放在同一句比较，信息明确。三个编码对象是真实的不同内容，无需按 humanizer 机械删掉三项并列。 |
| RW-03 | 同上，句 3，“Framework migration tools such as MindConverter...” | 保留 | 编程接口映射是此类迁移工具的实际机制；这里的 interfaces 有明确技术对象，应与无用的接口记账描述区别处理。 |
| RW-04 | 同上，句 4，“RepoTransAgent uses repository context...” | 保留 | 准确交代仓库上下文、测试失败和反思如何用于翻译修正，接下来的仓库级定位可以自然承接。 |
| RW-05 | 同上，句 5，“LaDiM investigates how a translated training program computes and updates its state.” | 改写，见 C1 | computes 缺少计算对象，state 可指参数、优化器状态或一般执行状态。用已有训练观测说明调查对象，保持训练语义诊断的贡献。 |
| RW-06 | 同上，句 6，“At repository scale, it coordinates changes...” | 改写，见 C1 | “their effect across declared entry points” 把影响关系压成抽象名词。说明哪些入口使用共享接口，读者更容易理解跨文件检查的原因。保留 shared interfaces 的科学含义。 |
| RW-07 | `conference_101719.tex:80`，句 1，“Differential testing exposes compiler and program faults...” | 保留 | 用相关执行之间的不一致解释差分测试，功能明确；related executions 在此涵盖不同编译器和等价程序执行，不应收窄成只有跨框架比较。 |
| RW-08 | 同上，句 2，“DeepXplore and DeepGauge investigate behavioral differences and test coverage...” | 改写，见 C2 | 合并主语和宾语使两项工作的作用对应不够清楚。分别交代行为差异检测与覆盖衡量，并将引用跟随对应方法。 |
| RW-09 | 同上，句 3，“More directly related to framework migration, TensorScope tests...” | 保留 | 过渡明确了从一般深度学习测试到跨框架 API 测试的关系，后半句给出具体机制；不是空泛的“值得注意”。无需仅为减少过渡词而改写。 |
| RW-10 | 同上，句 4，“NablaFuzz compares execution scenarios...” | 保留 | 自动微分及一阶、高阶梯度明确了与本研究相邻的问题。first-order 和 higher-order 是标准数学术语，保留必要连字符。 |
| RW-11 | 同上，句 5，“LaDiM uses training differences as evidence for code repair.” | 保留 | 这句承担从发现不一致到据此修复代码的段内连接，后句解释操作，合起来推进论证。它不是重复收尾。 |
| RW-12 | 同上，句 6，“Its Verifier Agent relates the measured forward values...” | 改写，见 C3 | “relates ... to the implementation” 和 “their origin” 没有清楚说出调查行为及原因的对象。以检查代码、解释差异、交接证据三个实际动作展开。 |
| RW-13 | `conference_101719.tex:83`，句 1，“Automated program repair uses tests or semantic constraints...” | 保留 | 两个分句分别说明传统约束和预训练语言模型的补丁生成，引用落点明确，没有分号堆句。 |
| RW-14 | 同上，句 2，“Interactive agents combine repository navigation...” | 保留 | 概括交互式智能体可组合的活动，不逐项宣称每个引用都实现全部工具。navigation、editing、execution 各有作用，保留三项。 |
| RW-15 | 同上，句 3，“Multi-agent systems distribute development activities...” | 保留 | 一句话定义角色分工这一邻近路线，为独立 Verifier/Repair 分工提供背景。multi-agent 是成熟术语，标题和正文继续一致使用。 |
| RW-16 | 同上，句 4，“MatchFixAgent takes a source program and an existing translation...” | 保留 | 清楚说明最直接对比方法的真实输入、分析、测试和修复。保留其语义分析能力，不能为突出 LaDiM 改写成仅看执行错误或仅做测试。 |
| RW-17 | 同上，句 5，“LaDiM includes initial translation and organizes diagnosis...” | 保留 | 保留 LaDiM 包含初译和依赖驱动诊断这两项事实；后者是这里的方法定位重点。不增加“其他方法无法处理训练程序”等没有在本段证明的排他性主张。 |
| RW-18 | 同上，句 6，“The independent investigation and its supporting observations pass...” | 改写，见 C4 | investigation 本身“传递”的主语不自然，也弱化了独立调查者与修复者之间的分工。明确 Verifier Agent 传递调查结果，保持每次提交后依据测量修正假设。 |
| RW-19 | 同上，句 7，“The comparison evaluates both methods from the same initial translation...” | 从本节删除，事实保留在现有实验位置，见 C5 | 这是实验输入和成本口径，未补充相关工作的技术关系。共同初译已见 `sections/experiments.tex:15`，初译成本已见主表 caption `sections/experiments.tex:21`，无需在本节再次说明。 |

台账合计：13 句保留、5 句改写、1 句从本节删除并沿用现有实验说明。没有需要移入附录或来源记录的新内容。

## 标题和本节结构

| 编号 | 源位置 | 决定与理由 |
|---|---|---|
| RW-H01 | `conference_101719.tex:74`，Related Work | 保留；与整篇论文结构一致。 |
| RW-H02 | `conference_101719.tex:76`，Code Translation and Framework Migration | 保留；覆盖代码翻译、接口映射和仓库迁移，不增加新的分类名。 |
| RW-H03 | `conference_101719.tex:79`，Differential Testing and Deep Learning Verification | 保留；对应差分测试、测试覆盖、跨框架 API 与自动微分。 |
| RW-H04 | `conference_101719.tex:82`，Automated Program Repair and LLM Agents | 保留；传统修复、语言模型补丁、交互和多角色智能体的关系清楚。 |

三段均以对应技术路线的文献为主体，再说明 LaDiM 的具体定位。这一结构符合写作 DNA 的相关工作组织方式。每段的 LaDiM 句分别讨论训练程序与仓库、差异到修复证据、独立角色和提交反馈，保留各自作用，不把它们一律当成重复总结删除。

## 需调整项与具体英文候选

### C1：明确训练计算和仓库影响关系（RW-05、RW-06）

原句：

> LaDiM investigates how a translated training program computes and updates its state. At repository scale, it coordinates changes to shared interfaces and checks their effect across declared entry points.

候选：

> LaDiM investigates how translated training code computes forward values and gradients and updates model parameters. At repository scale, it coordinates changes to shared interfaces and checks their effects on the repository entry points that use them.

这里用已在引言和方法定义的 forward values、gradients、model parameters 解释计算和更新对象；后句把共享接口与调用入口连起来。没有加入新的训练信号、自动路由或检查流程。依据：W01、W03、M14，本轮要求 7。候选保留了原句两个贡献范围，未添加免责尾句。

### C2：分别说明 DeepXplore 与 DeepGauge 的作用（RW-08）

原句：

> DeepXplore and DeepGauge investigate behavioral differences and test coverage in deep learning systems~\citep{pei2017deepxplore,ma2018deepgauge}.

候选：

> DeepXplore detects behavioral differences between deep learning systems~\citep{pei2017deepxplore}, while DeepGauge measures test coverage in these systems~\citep{ma2018deepgauge}.

两个方法分别对应差异检测和覆盖衡量，引用随各自描述放置。本句仅拆清原有并列关系，不增补原稿没有介绍的覆盖指标或白盒优化细节。依据：W01，本轮要求 7、8。

### C3：用调查动作解释证据如何形成（RW-12）

原句：

> Its Verifier Agent relates the measured forward values, gradients, and parameter updates to the implementation, develops hypotheses about their origin, and supplies evidence that the Repair Agent can test when selecting a change.

候选：

> Its Verifier Agent inspects code to explain discrepancies in forward values, gradients, and parameter updates, then passes the supporting observations and hypotheses to the Repair Agent for testing during repair.

“their origin” 原本可指前向数值、梯度或更新本身，候选明确解释的是 discrepancies。代码检查、假设和支持观测均已在 `sections/methods.tex:31`、`:70` 定义；候选沿用已有机制，不引入固定诊断路径。依据：W01、W03、A08、M14，本轮要求 7、8。

### C4：明确证据交接的动作主体（RW-18）

原句：

> The independent investigation and its supporting observations pass to a separate Repair Agent, which uses measurements after each submission to revise its hypotheses.

候选：

> The Verifier Agent passes its findings and supporting observations to a separate Repair Agent, which uses measurements from each submitted revision to revise its hypotheses.

独立分工由明确的 Verifier Agent 与 separate Repair Agent 表达，不将 investigation 当成自行移动的实体。submitted revision 直接表明送检的是修改后的程序；没有把 submission 写成一次 LLM 调用，也没有改变调用或提交预算。依据：W01、W03、M04，本轮要求 7。

### C5：将比较协议留在实验中的现有定义处（RW-19）

原句：

> The comparison evaluates both methods from the same initial translation and includes translation costs.

处理：删除该句，不新增替换句。其事实已有两个准确承接位置：

- `sections/experiments.tex:15`：`Repair methods also receive the same initial translations.`
- `sections/experiments.tex:21`：`End-to-end costs include the shared initial translation once and all subsequent calls, including failed attempts.`

后一处还说明初译只计一次和失败成本，语义比本节更完整。保留这些现有定义即可，避免把同一口径在 Related Work、setup、caption 中反复说明。本条不要求该章节审查修改 setup 或 caption。依据：W06、E06，本轮要求 7。

## 同步与核验范围

本节无图表或算法，候选不涉及生成器、资产、结果数值或参考文献条目修改。C2 仅调整现有引用键的落点，全部现有引用保留。术语与方法正文的 forward values、gradients、parameter updates、Verifier Agent、Repair Agent 保持一致。

本轮完成源码逐句检查、相关上下文对照和引用键存在性检查。没有修改或编译论文，没有生成 PDF，也没有执行实验；排版检查留待用户批准后实施论文修订时进行。共享清单由主代理统一整合，本报告的建议不自动成为已批准修改。

## 最重要发现与待整合决定

1. 本节 19 句已逐句登记。主要缺口集中在 LaDiM 的两个抽象动作描述和一个交接主体表达，文献综述主体可保留。
2. “computes and updates its state” 应直接说明训练计算与参数更新，避免 state 同时指向多种对象。
3. DeepXplore 和 DeepGauge 的作用宜分别对应到行为差异与测试覆盖，保持对前人工作的准确陈述。
4. 独立调查和证据交接的贡献应保留，用明确角色及其动作说明；不添加“仅在当前任务成立”等防御性降调。
5. 比较输入和成本句在实验中已有完整定义，建议从 Related Work 删除重复句。主代理只需确认实验审查最终仍保留这两项事实。

本节没有需要改变用户既定决定的冲突。共同要求第 2 条覆盖旧 E10 的 TorchAX 主文安排，但 Related Work 没有 TorchAX 或执行后端描述，本节无需据此增删内容。
