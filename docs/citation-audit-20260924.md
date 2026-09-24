# 引用审查（2026-09-24）

## 审查范围

本审查对应意见表 A22/A23 和用户 2026-09-24 的引用核查要求。审查对象是当前稿中使用的 37 个唯一 BibTeX 键，覆盖主文引言、相关工作、实验设置和补充实验。核对包括论文或项目的题名、作者、年份、出版信息（在公开记录可得时）以及正文论断和引用位置的对应关系。

本轮打开了主要论文的正式页面、作者或会议页面、论文 PDF、官方项目文档和代码仓库，并对部分受限页面使用了同一论文的 arXiv 或作者存档。审查没有声称逐页阅读所有引用论文；无法直接取得正式全文或固定版本的条目在表中标明证据边界。数据集中的任务数量和冻结实验分母属于本地 provenance，本报告不以在线项目 README 替代这些记录。

## 已核对并已落实的元数据

当前稿已落实以下四项更正：

* `roziere2020transcoder` 的正式作者顺序为 Baptiste Rozière、Marie-Anne Lachaux；[NeurIPS 2020论文](https://proceedings.neurips.cc/paper_files/paper/2020/file/ed23fbf18c2cd35f8c7f8de44f85c08d-Paper.pdf) 的首页说明两位作者作出相同贡献，但正式作者列表仍按该顺序记录。
* `szafraniec2023compiler` 当前 Bib 已按公开 [arXiv 记录](https://arxiv.org/abs/2207.03578)核对，作者列表中的 Charton 位于 Labatut 之前；这处顺序已修正。
* `wang2024codeact` 的 PMLR 页码为 **50208--50232**，已据 [PMLR 正式记录](https://proceedings.mlr.press/v235/wang24h.html) 修正。
* `mindspore2020whitepaper` 的题名为 **MindSpore: An All-Scenario Deep Learning Computing Framework**，直链改为 [官方白皮书 PDF](https://mindspore-website.obs.cn-north-4.myhuaweicloud.com/white_paper/MindSpore_white_paper_enV1.1.pdf)。

`mindspore2024gradient` 使用 MindSpore 2.4.0 官方迁移文档；版本发布日期已由官方 [v2.4.0 发布页](https://gitee.com/mindspore/mindspore/releases/tag/v2.4.0)核对为 2024-10-29。

## 论断与引用位置

| BibTeX 键 | 当前使用位置和论断 | 来源核对与判断 |
|---|---|---|
| `paszke2019pytorch` | 引言框架介绍；框架接口/执行机制与自动微分差异 | [PyTorch NeurIPS 论文](https://papers.neurips.cc/paper/9015-pytorch-an-imperative-style-high-performance-deep-learning-library.pdf)支持动态图、自动微分和优化器接口。与 `mindspore2024gradient` 一起支持当前“接口和执行机制不同”的改写；不支持无条件断言基本计算顺序不同。 |
| `abadi2016tensorflow` | 引言框架介绍 | [OSDI 2016正式页面](https://www.usenix.org/conference/osdi16/technical-sessions/presentation/abadi)支持 TensorFlow 的数据流计算、共享状态和异构硬件定位，引用位置合适。 |
| `mindspore2020whitepaper` | 引言框架介绍；算子、自动微分和优化器接口差异 | [官方白皮书](https://mindspore-website.obs.cn-north-4.myhuaweicloud.com/white_paper/MindSpore_white_paper_enV1.1.pdf)支持框架定位、图执行和自动微分设计。具体 API 差异由后面的迁移文档更直接支持。 |
| `guan2025repotransagent` | 引言中迁移可降低开发成本；相关工作中的仓库上下文、测试失败和反思 | [RepoTransAgent 记录](https://arxiv.org/abs/2508.17720)的摘要和方法说明支持仓库上下文、动态提示、测试反馈与迭代反思。它支持“可以降低迁移成本”的温和表达；“解决所有迁移成本”会超出来源。 |
| `he-etal-2025-execoder` | LLM 翻译达到语法和程序语义层面；相关工作中的功能语义、语法结构和变量依赖 | [ACL Anthology/EMNLP 2025](https://aclanthology.org/2025.emnlp-main.362/)明确介绍渐进式功能语义、语法和变量依赖建模，位置合适。 |
| `macedo2024intertrans` | LLM 翻译结果；中间翻译路径 | [InterTrans arXiv 记录](https://arxiv.org/abs/2411.01063)和论文 HTML 说明 ToCT 中间语言路径，并在给定测试集上执行候选程序，支持当前两处概括。 |
| `roziere2021unittests` | LLM 翻译结果；测试筛选无效翻译 | [Unit Tests 论文记录](https://arxiv.org/abs/2110.06773)支持利用单元测试筛除无效翻译和自训练。该文不是框架语义漂移检测的证据。 |
| `roziere2020transcoder` | 多语言语料学习代码映射 | [TransCoder 正式论文](https://proceedings.neurips.cc/paper/2020/hash/ed23fbf18c2cd35f8c7f8de44f85c08d-Abstract.html)支持无监督代码翻译和跨语言映射；“multilingual corpora”表示多语言联合训练，当前用法可保留。 |
| `szafraniec2023compiler` | 编译器表示改进翻译 | [Compiler Representations](https://arxiv.org/abs/2207.03578)支持用编译器中间表示辅助代码翻译，位置合适。 |
| `mindspore2024gradient` | “Different frameworks use different interfaces and execution mechanisms...” | [MindSpore 自动微分迁移文档](https://www.mindspore.cn/docs/en/r2.4.0/migration_guide/model_development/gradient.html#principle-comparison)逐项比较 PyTorch 与 MindSpore 的前向记录、反向图构建、图模式和训练封装；与 PyTorch 论文共同支持当前改写。 |
| `mindspore2023mindconverter` | MindConverter 提供接口映射 | [官方 MindConverter 文档](https://www.mindspore.cn/mindinsight/docs/en/r2.0.0-alpha/migrate_3rd_scripts_mindconverter.html)更直接地描述模型文件/权重转换及 API 映射。若继续精确化，建议将“mappings between programming interfaces”改为“converts model definitions and weights and maps supported APIs”。 |
| `le2014emi` | 差分测试暴露编译器或程序故障 | [EMI PLDI 2014作者论文](https://www.vuminhle.com/pdf/pldi14-emi.pdf)支持通过等价变体进行差分编译器测试。 |
| `yang2011csmith` | 差分测试暴露编译器或程序故障 | [Csmith PLDI 2011作者论文](https://users.cs.utah.edu/~regehr/papers/pldi11-preprint.pdf)支持生成定义良好的 C 程序并比较编译器输出。两篇合引可支持当前概括。 |
| `pei2017deepxplore` | 深度学习系统行为差异 | [DeepXplore arXiv 记录](https://arxiv.org/abs/1705.06640)支持差分神经网络测试和神经元覆盖驱动搜索；当前位置合适。 |
| `ma2018deepgauge` | 深度学习测试覆盖率 | [DeepGauge arXiv 记录](https://arxiv.org/abs/1803.07519)支持多粒度神经元覆盖指标；当前位置合适。 |
| `deng2023tensorscope` | 跨框架对应 API 的差异测试 | [USENIX Security 2023正式页面](https://www.usenix.org/conference/usenixsecurity23/presentation/deng-zizhuang)支持 TensorScope 的跨框架 API 一致性测试；当前位置直接对应。 |
| `yang2023nablafuzz` | 自动微分的一阶和高阶梯度执行场景 | [NablaFuzz arXiv 记录](https://arxiv.org/abs/2302.04351)明确覆盖一阶与高阶梯度的自动微分测试场景；当前位置合适。 |
| `nguyen2013semfix` | 用测试或语义约束指导程序修复 | [SemFix ICSE 2013论文](https://abhikrc.com/pdf/ICSE13-SEMFIX.pdf)支持测试约束、符号执行和程序修复合成；当前位置合适。 |
| `xia2023aprplm` | 预训练模型从代码和失败证据生成补丁 | [作者 ICSE 2023论文](https://lingming.cs.illinois.edu/publications/icse2023a.pdf)支持从有缺陷代码及其上下文生成补丁并用测试验证。若保留“failure evidence”，建议明确为测试或错误上下文，而不要暗示论文实现了迭代失败消息提示。 |
| `yang2024sweagent` | 交互式 agent 的仓库导航、编辑和执行 | [SWE-agent arXiv 记录](https://arxiv.org/abs/2405.15793)直接支持仓库导航、编辑、测试和执行；该条目是当前句最直接的来源。 |
| `shinn2023reflexion` | 交互式 agent | [Reflexion arXiv 记录](https://arxiv.org/abs/2303.11366)支持执行反馈、反思和记忆，但不直接支持完整仓库导航。应与 SWE-agent 的能力区分。 |
| `chen2023selfdebugging` | 交互式 agent | [Self-Debugging arXiv 记录](https://arxiv.org/abs/2304.05128)支持代码解释、执行和自我调试，不直接支持仓库导航。 |
| `wang2024codeact` | 交互式 agent | [PMLR 正式记录](https://proceedings.mlr.press/v235/wang24h.html)支持通过可执行代码、观察结果和多轮修正完成任务，不直接支持一般仓库导航。 |
| `qian2023chatdev` | 多 agent 专门化软件开发角色 | [ACL 2024正式论文](https://aclanthology.org/2024.acl-long.810/)直接支持角色化软件开发流程，当前位置合适。 |
| `hong2023metagpt` | 多 agent 专门化软件开发角色 | [MetaGPT arXiv 记录](https://arxiv.org/abs/2308.00352)支持按软件工程 SOP 分工的角色化协作，当前位置合适。 |
| `wu2023autogen` | 多 agent 系统 | [AutoGen arXiv 记录](https://arxiv.org/abs/2308.08155)支持可定制 agent、工具和人工参与；它是通用协作框架，不单独证明“专门化软件开发角色”。 |
| `chen2023agentverse` | 多 agent 系统 | [AgentVerse arXiv 记录](https://arxiv.org/abs/2308.10848)支持动态多 agent 群体和任务协作；同样属于通用多 agent 证据。建议把“specialized roles”限定为 ChatDev/MetaGPT，把 AutoGen/AgentVerse 用于通用协作。 |
| `ibrahimzada2025matchfixagent` | 源程序+现有翻译、语义分析、测试生成和修复 | [MatchFixAgent arXiv HTML](https://arxiv.org/html/2509.16187v3#S2.SS2.SSS4)明确描述源/目标程序、外部库 API 分析、测试和修复；该来源直接支持相关工作句，也说明它不能作为“现有方法无法检测或修复语义漂移”的证据。 |
| `macedo2025codetransengine` | CodeTransEngine 的直接翻译配置 | [项目官方指南](https://codetransengine.github.io/guides/)支持 Direct、InterTrans 和 few-shot 配置及测试流程。正式论文页面在本轮未能稳定打开，Bib 的题名/作者与项目记录一致；若需要最终投稿级出版信息，应再用会议记录核对。 |
| `openi2025msadapter` | MSAdapter 基线 | [官方快速开始文档](https://www.mindspore.cn/msadapter/docs/zh-CN/master/msadapter_user_guide/quick_start.html)和 [PyPI 项目页](https://pypi.org/project/msadapter/)支持 PyTorch 到 MindSpore 的适配用途。当前冻结 Bib 指向 v0.6.0 的仓库标签和 2025 年，线上本轮未独立确认该精确标签的日期；实验 provenance 应作为版本依据。 |
| `ivy2026transpiler` | Ivy 在框架间转译模型 | [Ivy 官方仓库](https://github.com/unifyai/ivy)支持跨框架模型转译；这是软件版本/访问年份引用，不能当作经过同行评审的论文。 |
| `torch2jax2026` | torch2jax 的 PyTorch/JAX 操作和自动微分互操作 | [torch2jax 官方仓库](https://github.com/samuela/torch2jax)支持该用途；同样应按软件项目引用理解。 |
| `google2025torchax` | TorchAX 为 JAX 的 PyTorch frontend | [TorchAX 官方文档](https://google.github.io/torchax/)明确说明 PyTorch frontend、JAX 数组及 grad/Optax 互操作；补充实验中的软件定位合适。 |
| `djl2026` | DJL Java 深度学习引擎 | [DJL 官方仓库](https://github.com/deepjavalibrary/djl)支持 Java、引擎无关和训练用途；任务数量来自本地冻结 provenance。 |
| `d2ljava2026` | d2l-java 教材示例 | [d2l-java 官方仓库](https://github.com/deepjavalibrary/d2l-java)支持 Java 版教材示例和 DJL 实现；当前实验句的样本来源定位合适。 |
| `jingles2026timeseries` | 时间序列公开仓库 | [项目仓库](https://github.com/jinglescode/time-series-forecasting-pytorch)包含 PyTorch LSTM 时间序列示例；任务计数和选取范围以本地 provenance 为准。 |
| `chak2026twotower` | 推荐系统 two-tower 仓库 | [项目仓库](https://github.com/gauravchak/two_tower_models)支持 two-tower 检索与排序示例；当前实验句可保留，具体两项任务数量不由 README 单独证明。 |

## 仍需用户审阅的论断

1. 引言第 63 行的 “Current translation and repair methods are designed mainly for language-level correctness, **being unable to detect or repair such semantic drift**.” 超出本轮核对的来源。TransCoder、Unit Tests、Compiler Representations、ExeCoder、InterTrans 和 MatchFixAgent 说明它们的目标和检测范围，但没有共同证明“无法检测或修复”；MatchFixAgent 还明确分析外部库 API 并进行测试和修复。当前稿保留用户原句，建议与旧版引言一并审阅后改为可由来源直接支持的正面范围句，例如：`These methods primarily target language level translation and test based functional correctness, leaving framework specific computational drift less directly addressed.`
2. 相关工作第 121 行把 SWE-agent、Reflexion、Self-Debugging 和 CodeAct 共同概括为“combine repository navigation, editing, and execution”。四者共同支持代码执行/反馈式修正，但只有 SWE-agent 直接支持完整仓库导航。建议改为分层表述：SWE-agent 支持仓库导航、编辑和测试；其他工作支持执行反馈、反思或代码行动。
3. 第 122 行的“specialized roles”由 ChatDev 和 MetaGPT 直接支持；AutoGen 和 AgentVerse 是更一般的多 agent 协作框架。建议将后一组改写为通用协作证据，保留四个引用但缩小各自 claim。
4. 第 106、120 行分别可进一步精确为 MindConverter 的“模型定义/权重转换与 API 映射”、APR-PLM 的“有缺陷代码及上下文和测试证据”。这两项属于措辞改进，不是元数据错误。

## 未使用条目

本轮发现 `yang2025multiagentcollaboration`、`gray2025workflows`、`erer2025fullyautomated` 和 `lattner2021mlir` 在当前稿中没有被引用；它们不属于本轮 37 个已使用键的审查范围，也没有因未使用而从 BibTeX 删除。

## 结论

引言硬编码作者年份和空方括号已全部改为 `\citep`，框架差异句已改成来源能够支持的“接口与执行机制差异”，并补入 PyTorch 与 MindSpore 的针对性引用。当前需要用户决定的是第 63 行的过强“unable”断言、相关工作第 121/122 行的能力范围，以及是否采用旧版引言中更充实的介绍段落；这些建议不应在用户确认前写成已批准正文修改。
