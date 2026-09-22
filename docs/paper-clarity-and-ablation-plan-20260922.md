# 论文内容与行文修改方案

JAX 正式比较与修复依赖图规划消融均已完成，费用、最终验收和原始证据已通过审计。本方案结合完整结果，明确全文的贡献、结果表达与证据范围。方案已落实到全文、图表和附录，执行与验证见 [修改记录](paper-clarity-execution-20260922.md)；方法图由用户负责，篇幅压缩暂不处理。

全文改写采用用户确认的方向：在现有证据支持下坚定陈述方法解决的问题和取得的结果，突出比较对象、指标、评价条件及量化差异，并充分表达已覆盖的任务和模型范围。摘要、引言、方法动机、实验分析、图表标题与结论共同落实这一方向。

本轮按任务尺度组织四项组件证据：修复历史与独立证据交接采用十个保存初译的消融，仓库上下文机制整体与 Repository Structural Analysis 采用时间序列仓库的消融。主文的 JAX 泛化分析回到原六例，加入定义明确的 Ivy 和 torch2jax 原生转换对照，并保留 Direct repair。新 JAX 研究及其他消融结果在附录中完整说明。

## 1. 全文的论证顺序

论文的核心问题是：迁移后的程序即使能够运行，训练行为也可能改变。方法章围绕训练计算之间的依赖解释如何诊断和修复；实验章先展示迁移成功与成本，再解释新增成功来自哪里、哪些观测和组件发挥了作用。

| 部分 | 读者应得到的结论 | 本轮改法 |
|---|---|---|
| 方法概述 | 谁调查、谁修复、谁调度和验证 | 恢复 Orchestrator 的调度职责，以实际动作串起流程 |
| 3.1 | 后文使用哪些 discrepancy | 保留执行、前向值、梯度、参数更新的定义，移出编辑计数和运行细节 |
| 3.2、3.3 | 训练差异怎样缩小调查范围，证据怎样帮助修复 | 用依赖关系解释判断，保留 LLM 与工具调用的伪代码，删除逐行复述算法的正文 |
| 3.4 | 多个文件如何组织，修改共享代码后如何继续检查 | 说明仓库上下文机制的组成，展开仓库结构分析、修复依赖图规划和证据保留 |
| 4.1 | 比较哪些任务、方法，以及什么算成功 | 先定义任务和初始状态分组，简述协议，复现细节集中到附录 |
| 4.2 | LaDiM 在迁移接受、成本或功能覆盖上有什么优势 | 每段围绕一个比较结论，用少量数字和具体行为支撑 |
| 4.3 | 新增成功和更早检测分别来自什么能力，能否迁移到 JAX | 分别讨论真实翻译错误、训练信号及原六例 JAX 跨框架结果 |
| 消融 | 哪项设计改变了接受结果或修复成本 | 程序级组件采用历史初译，仓库级组件采用时间序列，各比较保留自己的配对参照 |

沿用已确认的摘要结构、跨框架结论和 Generalization Across Frameworks 标题。摘要同时强化研究定位、方法动作和核心定量结果；JAX 的跨框架适用证据采用原六例，新的两任务修复比较在附录独立呈现。

### 摘要、引言和结论的主张

研究定位直接写为“以训练行为引导代码迁移与修复”。方法创新围绕训练计算依赖展开：用执行、前向值、梯度和参数更新确定调查方向，由独立智能体形成证据并据此修复，再用提交后的测量继续定位问题。修复历史和独立证据交接的贡献用历史初译上的修复数量说明；仓库上下文机制与其中的仓库结构分析用时间序列上的成本差异说明。修复依赖图规划在方法章解释组织作用，其独立消融放在附录。

| 证据 | 可直接突出的问题与结果 | 全文安排 |
|---|---|---|
| MindSpore 共同迁移集合 | LaDiM 与 MatchFixAgent 都接受 50/50，LaDiM 的端到端 token 少 57.4% | 摘要、引言和结论的主要效率证据 |
| Java/DJL 到 Python/PyTorch 的 18 项任务 | LaDiM 接受 9/18，SWE-agent 与 MatchFixAgent 各 8/18；token 分别少 11.7% 和 24.2% | 支持同时改变语言与框架的任务范围 |
| 十个保存的初译 | LaDiM 修复 4/5 个初始失败并保留 5/5 个初始通过；三个修复对照各修复 0/5 | 突出真实翻译错误及支持库修复能力 |
| 四模型、16 实例的训练信号消融 | 执行反馈、加入前向值、再加入梯度、再加入更新时，完整验收为 4/16、8/16、12/16、16/16 | 解释训练观测对触发和引导修复的作用 |
| 时间序列主比较 | 三种智能体均通过 69/69；LaDiM 比 SWE-agent、MatchFixAgent 少用 68.1%、80.8% 的端到端 token | 支持共享模型与多个仓库入口的实际意义 |
| 原六例 JAX 分析 | LaDiM 与 Direct repair 均修复 6/6；LaDiM 的六例均在首次提交通过三种子验收 | 支持训练行为修复流程在 MindSpore 之外的 JAX 后端上工作 |

摘要保留两至三个最能支撑主张的结果，避免把所有研究压进数字列表。可采用的核心结果句为：

> LaDiM completes all 50 MindSpore migrations with 57.4% fewer tokens than MatchFixAgent. On saved initial translations, it repairs four of five failed programs, while Direct repair, SWE-agent, and MatchFixAgent repair none. Evaluation across framework migration, language migration, and repository tasks demonstrates its ability to preserve training behavior across distinct migration settings.

引言先用前向一致却梯度错误、当前观测一致却后续更新偏离的具体机制建立动机，再介绍 LaDiM 的调查与修复流程。贡献陈述分别对应训练行为诊断、独立证据交接与验证流程、以及共同协议下的迁移比较。每项写清提出了什么、处理哪种困难，并把最有力的结果紧接在相应主张后。全文保留可直接核对的比较，创新性通过机制与已有工作的具体差异表达。

适用范围按已测条件展开：从 PyTorch 到 MindSpore 的框架迁移、从 Java/DJL 到 Python/PyTorch 的语言与框架迁移，以及共享代码跨训练脚本、notebook 和其他入口的仓库迁移。原六例 JAX 研究覆盖 MLP 和 CNN 的执行、前向与梯度错误，在 TorchAX 执行后端上验证真实 JAX 求导和参数更新。计算机视觉、语言、时间序列和推荐等名称用于说明所测模型与工作负载的覆盖，整应用能力按实际执行的入口和功能说明。

结论明确回扣训练行为诊断与修复的关系，用 MindSpore 的完整接受和成本差异、真实翻译错误的修复差异支撑主要贡献，再概括语言迁移与仓库任务的覆盖。跨研究一致性落在 MindSpore、Java/DJL 和时间序列主比较中均观察到的 token 节省；JAX 和独立组件消融的不同结果放在各自分析段解释。

## 2. 方法章怎样改

### 调度与反馈

摘要、方法概述及相关文字采用同一个职责定义：

> The Orchestrator schedules their work and returns verification results after each submission to guide further repair.

方法概述按“初始翻译 → Verifier 调查差异 → Repair Agent 接收证据并修改 → Orchestrator 验证并反馈”展开。每个角色的动作在首次出现时讲清楚，后文直接使用角色名。

### 训练差异与两个智能体

3.1 保留四种 discrepancy 及其训练依赖关系。编辑操作如何计数、一次提交可能包含几次模型调用、预算变量如何递减，转入算法说明或附录。

3.2 和 3.3 的标题分别简化为 Verifier Agent 和 Repair Agent，两个标题保持一致，去掉冒号。算法 1 保留 Layered Diagnosis 名称。正文依次解释：执行异常引导检查出错调用，前向差异引导追踪算子，前向一致时的梯度差异引导检查求导路径，前向与梯度一致时的更新差异引导检查优化规则和状态。每一层都回答“这条观测为何能缩小调查范围”。

Repair Agent 段落先说明独立接收哪些证据，再说明如何测试修改及使用后续反馈。删除“证据被标记为来自 Verifier”、阶段 flags 如何更新等实现叙述。伪代码中保留这些控制所需的条件，正文只讲作用。

三个算法继续显式传入 LLM 参数 M；算法 2 复用算法 1 的 AgentStep。共享的模型查询、工具执行和记录操作只定义一次，算法 3 负责组合流程和仓库上下文操作。

### 仓库结构分析与修复依赖图规划

两个模块采用以下正式名称，统一用于方法介绍、贡献陈述、消融条件、图表标题和相关讨论：

| 模块名称 | 作用 |
|---|---|
| Repository Structural Analysis（仓库结构分析） | 提取文件、导入和符号结构，为修复提供上下文 |
| Repair Dependency Graph Planning（修复依赖图规划） | 将修复单元及其先后关系组织成图，并据此协调执行 |

方法段按“提取仓库结构 → 智能体组织修复依赖图 → 沿依赖执行与验证”展开。仓库结构分析提供文件、导入、定义和 notebook 单元信息；智能体据此划分修复单元并声明前置关系，形成有向无环图。拟写为：

> Repository Structural Analysis exposes files, imports, function and class definitions, and notebook cells for the agent to inspect. The agent uses Repair Dependency Graph Planning to group related files into work units, specify their repair goals, and organize their prerequisites as a directed acyclic graph. It selects a unit whose prerequisites have current checkpoints, then edits the files assigned to that unit. Local checks establish each unit's current status. When an edit changes a shared implementation, LaDiM invalidates the checks for affected units and their dependents, prompting the agent to check the relevant callers again.

仓库上下文机制整体包括以下五部分。方法章先说明它们如何共同支持跨文件调查，再展开前两个正式命名的模块。

| 组成 | 在修复中的作用 |
|---|---|
| Repository Structural Analysis（仓库结构分析） | 提供文件、导入、函数与类定义、notebook 单元的结构清单，帮助查找相关实现 |
| Repair Dependency Graph Planning（修复依赖图规划） | 组织修复单元、文件范围和前置关系；检查依赖是否就绪，并在共享代码改变后向依赖单元传播检查点失效 |
| Notebook 单元工具与修改校验 | 支持读取和修改 notebook 单元，对修改进行事务和语法校验 |
| 带代码版本的证据归档与检索 | 保存观测、代码、假设及对话，将证据与文件哈希关联，支持取回与当前调查相关的记录 |
| 上下文重建 | 在独立角色交接、实际单元切换或容量达到上限时整理上下文，保留当前计划、结论、测量和已读且未变化的相关代码 |

独立证据交接先定义为把调查证据交给新的修复对话；仓库上下文机制进一步管理跨文件计划、代码版本和可检索证据。修复历史保留此前尝试及其反馈，支持后续程序修复。这两个程序级组件也可用于涉及支持库的修改，方法定义不把它们限制为只能编辑一个文件。缓存容量、工具标识和触发条件的实现细节进入附录。

方法章在消融之前明确介绍四项组件。Verifier Agent 与 Repair Agent 段说明独立证据交接传递的代码观测、测试结果和假设，以及修复历史怎样保留此前修改、失败测试和验证反馈，供后续尝试修正假设。仓库段先定义整体上下文管理，再展开结构分析及其他组成。消融直接沿用这些名称进入比较，不机械回指方法小节编号，也不为对应关系额外制造小标题。

删除以下控制流复述：

> Otherwise, the initial measurements support diagnosis, and the resulting evidence starts the repair loop.

这句话重复算法中的“初始检查失败后诊断，再进入修复”。同段“算法先验证，已通过就立即返回”“这些上下文操作服务于算法 1 和 2”等重复说明一起清理。

代码核对还发现，仓库结构分析由 `repository_map` 工具调用触发，初始化及上下文重建不会自动执行该扫描。因此算法 3 的 `RepositoryContext(Map(T))` 拟改为 `RepositoryContext(T)`，结构分析结果通过共享工具调用取得。正文和伪代码统一为实际实现的行为，代码中的工具标识保持不变。

方法核心流程已经稳定。贡献与结果分析突出四项已有直接支持的组件作用，修复依赖图规划作为仓库上下文机制的组成说明；图由用户修改。

## 3. 4.1 缩短 setup，先把比较对象讲清楚

保留加粗标签，按 Tasks、Compared methods、Evaluation 三部分组织，不增加小标题层级。

Tasks 交代主迁移集合、两个仓库、十个保存的首次翻译和训练信号研究分别用于什么问题。十个保存的翻译中，五个需要修复，五个已通过初始检查；该比较允许修改候选及其支持库。这一定义放在结果之前。

初始分组统一为 programs that require repair 和 programs that pass the initial checks。图中采用 Needs repair 和 Passes initial checks。表 1 中 Natural translation faults 改为 Saved initial translations，与包含五个初始通过程序的事实一致。JAX 主文任务行保留原六例：MLP、CNN 各包含执行、前向和梯度故障。附录的新 JAX 研究单独列出 12 个来源、10 个非空候选和 2 个初始失败修复任务。

Compared methods 区分主表的 Direct LLM 初次翻译与分析实验中的 Direct repair，避免两个 Direct 被读成同一种流程。说明 LaDiM、SWE-agent 和 MatchFixAgent 的比较角色，以及相同的 LLM 后端；各研究包含的方法由相应表格直接列明。

在 JAX 结果出现之前，补充以下定义及对应引用。实际转换对照名称为 Ivy 和 torch2jax，TorchAX 用于 LaDiM 与 Direct repair 的执行后端。

| 名称 | 定义与本研究中的用途 |
|---|---|
| Ivy | 框架间代码转换工具；本实验通过 `ivy.transpile` 将给定候选模型转换为 JAX/Flax 实现，执行一次原生转换，不调用 LLM 修复 |
| torch2jax | 将 PyTorch 运算映射到 JAX 的转换工具；本实验使用 `samuela/torch2jax` 的 `t2j` 转换模型和张量，再通过 JAX 求导及 Optax 更新进行评价 |
| TorchAX | 基于 JAX 的 PyTorch 前端；本实验供 LaDiM 和 Direct repair 执行候选，并使用真实 JAX 数组、自动微分和 Optax 更新 |
| Direct repair | 与 LaDiM 接收相同初始候选的直接修复控制，保留其既有共享工具及修复流程，用于比较修复接受和模型成本 |

工具定义引用 [Ivy 官方仓库](https://github.com/unifyai/ivy)、[torch2jax 官方仓库](https://github.com/samuela/torch2jax) 和 [TorchAX 官方文档](https://google.github.io/torchax/)。实际版本、调用和输入以冻结实验记录为准。Ivy 与 torch2jax 在结果表中作为原生转换对照单独分组；其输入是已经含有故障的候选，评价的是转换后是否消除了既有故障。原生转换与 LLM 修复的任务及预算在此定义一次。

Evaluation 正文保留共同源程序、初始候选和输入、核心接受标准、主要调用预算及成本范围。拟替换核心段落为：

> Methods use common source programs, evaluation inputs, and corresponding initial parameters. Repair methods also receive the same initial translations. Acceptance requires agreement in execution, forward values, gradients, and parameter updates, together with the task's optimizer and interface checks. Repository evaluation also covers shared entry points and original tests. Candidates that pass the initial evaluation are checked on additional seeds. The appendix gives the numerical tolerances and detailed settings.

正文再用简短文字说明每程序 40 次、仓库 80 次调用及四次提交上限。完整迁移和给定初译修复的成本范围在对应表注各交代一次。

| 用户指出的句子或信息 | 含义 | 处理 |
|---|---|---|
| individual programs retain their own state over two consecutive steps, and repositories use three | 源和目标从对应初态出发，分别连续训练，中途不重置目标为源状态 | 正文概括连续训练检查；两步/三步、初态与状态规则进入附录 |
| A submission can follow several model calls and edits | 外部验证前可以有多次模型交互和修改 | 从 setup 删除；提交定义在方法中说明一次 |
| Supplied-candidate studies report repair costs | 已给定初译的研究只统计本次诊断与修复费用 | 用对应表注说明，删除泛化的记账句 |
| Failures remain in the task denominator | 失败任务计入总任务数 | 移至附录评分规则 |
| acceptance at each budget scores the current candidate | 评价该预算下实际提交的程序 | 移至附录预算与验收说明 |
| 数值容差、BF16 特例、seed、各类检查数量、时间和输出限制 | 完整复现条件 | 集中在已有协议与种子附录，正文引用一次 |

## 4. 4.2 主结果如何写出优势

### MindSpore

段落围绕“保持完整接受，同时显著降低模型使用成本”展开。主证据为 50/50 和 57.4% token 节省；图 3 说明成本改善覆盖需要修复与初始通过的两组。输入 token 占节省量的 93.0%，用于解释费用差异主要发生在哪一部分。

拟写为：

> LaDiM completes all 50 MindSpore migrations with 57.4% fewer tokens than MatchFixAgent. The savings cover both programs that require repair and programs that pass the initial checks (Figure 3). Reduced input usage accounts for 93.0% of the token savings. LaDiM accepts 46/50 tasks after the first submission and all 50 after the second, retaining full acceptance at four submissions.

调用次数等表中已有细目不再逐一复述。这里比较的是完整接受和 token 成本；预算 1、2、4 用于展示本方法的完成进展。

删除正文中的 27/29 和 7/9。7/9 原本指九个不同的初始失败输入组合中七个在首次提交后修复，并非七类故障。任务标识、不同输入组合与去重记录统一放附录。图 3 保留真实数据点和两组比较，图注解释每个点代表什么，不再把读者带入多个突然变化的分母。

### 跨语言

先说 LaDiM 的接受集合覆盖 MatchFixAgent 的成功程序，并增加一个循环网络实例，再给出与 SWE-agent、MatchFixAgent 相比 11.7% 和 24.2% 的成本节省。分析落在“训练行为引导的修复可以用于同时改变语言与框架的任务”，具体成功程序类型提供支撑。删除关于迁移接口和内部对接方式的枝节。

### 仓库

时间序列段落突出共享模型在训练脚本、notebook 和教学示例中共同完成迁移，以及相同完成结果下的成本优势。正文保留 68.1% 和 80.8% 两个 token 比较，不复述主表每个梯度、更新及入口计数。

推荐段落围绕行为覆盖展开：LaDiM 恢复 reward model inference 和 retrieval，并执行训练命令，两个基线仍未完成前两项。用最高行为覆盖和十个原始测试支撑这一结论。18 项 loss、18 项 gradient、15 项 update 及后续 embedding 差异的拆解放附录，避免将段落写成检查日志。

原始推荐测试继续按已核实结果保留 MatchFixAgent 0/10；其测试收集被未迁移的 PyTorch 导入阻断，原因放简短表注。其他执行失败后确实缺测的数值项按各自实际状态记录。

## 5. 4.3 分析实验如何衔接

采用与 4.2 相同的加粗标签，各部分围绕一个问题形成连贯段落。

Repairing Translation Errors 对应 setup 中十个保存的首次翻译。该研究分别统计失败程序的修复与初始通过程序的保留，直接观察方法修复实际翻译错误的能力。拟写为：

> LaDiM raises acceptance from five to nine of the ten saved translations by repairing four programs that fail the initial checks and preserving the five that already pass. Direct repair, SWE-agent, and MatchFixAgent retain the initial five successes but recover none of the failed programs. In the LSTM case, LaDiM repairs recurrent operations and tensor indexing in the supporting library, restoring agreement in loss, gradients, and parameter updates.

运算注册、dispatch cycle、第几次提交修复哪一步等过程移到附录。该段用一个可理解的例子说明修复延伸到了支持库，保持为一个段落。

Training Signals and Detection Latency 接着解释为何观察训练行为能够发现这些问题。梯度错误可能暂时保持当前损失，更新错误可能暂时保持当前前向值和梯度；后续计算才会受到改变的参数状态影响。成文使用两句：

> Gradient errors can leave the current loss unchanged. Errors in parameter updates can preserve both current forward values and gradients, with their effects appearing in later steps.

接下来给出 LaDiM 第一步检出的结果及损失检测对照。阈值列表、每步同步细节和健康控制的精确误差放附录。

图 4 标记采用 LaDiM detects at step 1 和 Loss check detects at step 31／18，去掉冒号。31／18 来自平均损失曲线的过阈位置，图注交代这一含义；现有数据没有测得 SWE-agent 或 MatchFixAgent 在这两个时刻检出，因此图中对照使用实际测量的 Loss check。

Generalization Across Frameworks 回到原六例，围绕“同一训练行为修复流程可以在 JAX 后端工作”展开。任务为 MLP 和 CNN 各三个带有执行、前向或梯度故障的候选。LaDiM 六例全部在首次提交接受，并通过三个种子的单步 SGD 检查；Direct repair 同样为 6/6。训练信号消融已承担诊断机制的验证，这里用第二个目标框架的实际执行、求导与更新结果说明适用范围。

主文保留 LaDiM 的 6/6 及原生转换对照的结果，完整表采用两个分组，清楚说明各方法做了什么：

| 对照类别 | 方法 | 故障消除后接受 | LLM 调用 | LLM token |
|---|---|---:|---:|---:|
| 给定候选的 LLM 修复 | LaDiM | 6/6 | 76 | 674,009 |
| 给定候选的 LLM 修复 | Direct repair | 6/6 | 57 | 353,311 |
| 给定候选的单次原生转换 | Ivy | 0/6 | 0 | 0 |
| 给定候选的单次原生转换 | torch2jax | 0/6 | 0 | 0 |

两个修复方法共享原始候选、评估协议及最多四次提交、40 次调用、120,000 输出 token 和 1,800 秒预算，保留各自既有流程。表中成本包含调查和修复；转换器的零 token 表示没有使用 LLM，转换本身的运行耗时列在附录。Direct repair 在六例上的 token 更少，正文将这组研究用于支持跨框架适用性，接受与效率差异按实测值呈现。

Ivy 与 torch2jax 的两个 0/6 都包含以下三种结果，每种对应 MLP、CNN 各一例：

| 原候选故障 | 每个转换器的例数 | 实际观测 |
|---|---:|---|
| 执行故障 | 2 | 线性层收到多余实参，转换后仍触发 TypeError；数值测量为 n/a |
| 前向故障 | 2 | 输出缩放错误保留，损失、梯度和更新均未通过阈值 |
| 梯度故障 | 2 | 被截断的求导路径保留；损失通过，梯度和参数更新未通过 |

两个工具各自的 MLP、CNN 健康控制全部通过。这里的 0/6 表示对已含故障的输入做原生转换后，既有错误没有被消除；健康源程序的迁移成功率需要按健康输入任务评价。该定义紧接工具介绍并在表注简述，避免把原生转换和主动修复混为同一种能力。可采用的主文表述为：

> LaDiM repairs all six JAX cases spanning execution, forward-value, and gradient faults in MLP and CNN models. Every case passes verification on three seeds after the first submission. Direct repair also accepts all six cases. Ivy and torch2jax accept none of the faulty candidates after native conversion, while their healthy MLP and CNN controls pass. In these cases, native conversion preserves the supplied execution or numerical faults, and explicit repair restores agreement in training behavior.

新 JAX 研究在附录作为独立的原生计算与多步验收研究保留。十二个来源中，八个共同初译通过，两个非空候选失败，另两次生成耗尽输出预算且未返回代码；后续四方法比较使用冻结规则选出的两个初始失败候选。所有方法都修复时间序列而未接受 ResNet，修复接受均为 1/2；计入八个共同初译成功后，来源层面的接受均为 9/12。它与原六例分别定义任务和验收，不合并分母。

| 附录新 JAX 比较 | 修复接受 | 修复调用 | 修复 token | 两任务端到端 token |
|---|---:|---:|---:|---:|
| LaDiM | 1/2 | 35 | 1,840,066 | 1,871,493 |
| Direct repair | 1/2 | 28 | 760,935 | 792,362 |
| MatchFixAgent | 1/2 | 23 | 258,914 | 290,341 |
| SWE-agent | 1/2 | 66 | 1,013,532 | 1,044,959 |

附录解释三步、三种子的验收与失败原因：时间序列恢复输入切片和输出拼接形状后通过；LaDiM、Direct repair 和 SWE-agent 将 ResNet 的截断初译修成可执行代码，首步数组通过而后续步骤仍有梯度和更新等偏离。MatchFixAgent 在原生语法分析时终止，该例数值为 n/a，四次调用费用保留。两任务端到端成本包含共同初译的 31,427 token；十二次初译的全部 139,724 token 和生成失败留在完整来源账本。这些结果继续支持对连续训练验收的讨论，本轮按已有记录调整论文安排。

## 6. 消融怎样支撑组件

训练信号消融回答“需要观察什么”，程序级和仓库级组件消融回答“如何组织调查与修复”。在现有消融表中按小写面板组织为 (a) 训练信号、(b) 历史初译上的程序级组件、(c) 时间序列上的仓库级组件。四项组件直接加入这张表；面板各自注明任务、接受指标和成本范围。完整的时间序列累计表移至附录，主文采用其中识别仓库上下文整体作用的配对结果。

### 程序级：修复历史与独立证据交接

采用十个保存初译的同一组历史消融。五个候选初始失败、五个初始通过，允许修改候选及支持库。完整参照包含修复历史、独立证据交接和当时启用的编辑格式辅助；三个条件沿用该研究的冻结设置，表注一次说明配置与成本口径。

| 条件 | 初始失败程序修复 | 初始通过程序保留 | 最终接受 | 修复 token |
|---|---:|---:|---:|---:|
| Independent evidence handoff（完整参照） | 4/5 | 5/5 | 9/10 | 15,547,813 |
| Continuous conversation | 3/5 | 5/5 | 8/10 | 14,516,463 |
| Without repair history | 0/5 | 5/5 | 5/10 | 10,851,537 |

正文先指出作用，再用配对差异支撑：保留修复历史时，五个失败程序中修复四个，移除历史后为零；独立证据交接比连续对话多修复一个程序，最终接受由 8/10 提高到 9/10。三个条件均保留全部五个初始成功。这两项组件在该研究中提高修复接受，成本差异由表格同时报告。

这组实验按“程序级修复”命名，能够覆盖支持库编辑。主文不用时间序列累计结果说明这两项的修复收益，也不把它们描述成只能处理单文件的机制。进度提醒、编辑格式辅助及其他集合上的既有消融放在附录。

### 仓库级：整体上下文机制与结构分析

时间序列面板保留两组配对比较：第一组考察加入完整仓库上下文机制，第二组考察移除其中的 Repository Structural Analysis。它们回答整体机制和内部组件两个不同层次的问题。

| 比较对象 | 条件 | 通过检查 | 调查与修复调用 | 端到端 token |
|---|---|---:|---:|---:|
| Repository context management | Without repository context（保留调查与独立交接） | 69/69 | 26 | 6,047,074 |
| Repository context management | With repository context | 69/69 | 22 | 1,936,579 |
| Repository Structural Analysis | Without Repository Structural Analysis | 69/69 | 42 | 2,651,248 |
| Repository Structural Analysis | With Repository Structural Analysis（完整方法） | 69/69 | 30 | 2,126,900 |

两组均在完整通过 69/69 项检查的情况下体现效率收益。加入仓库上下文机制后，端到端 token 从 6,047,074 降至 1,936,579，减少 68.0%，调用从 26 降至 22。保留 Repository Structural Analysis 时，端到端 token 从 2,651,248 降至 2,126,900，减少 19.8%，调用从 42 降至 30。可直接写为：

> On the time-series repository, repository context management reduces total token use by 68.0% while preserving acceptance on all 69 checks. In a separate paired ablation, Repository Structural Analysis reduces total token use by 19.8% and LLM calls from 42 to 30, with the same complete acceptance.

表注说明每个条件运行一次，69 是同一仓库跨三个种子的检查项目数，端到端 token 包含同一初译费用。两组完整条件来自不同的实际运行，分别为 1,936,579 和 2,126,900 token，表内通过分组保留各自参照；百分比在组内计算，整体机制与结构分析的收益不相加。完整链路相对基础 Repair Agent 的 68.4% 是另一比较，留在附录累计表讨论。

### 附录保留完整组件结果

主文消融段明确指向附录中的完整结果，包括两仓库累计消融、Repository Structural Analysis 与 Repair Dependency Graph Planning 独立消融，以及其余历史初译组件。这些结果用于解释任务差异。

推荐仓库的四个累计条件均为 131/145；加入组件后费用上升。独立结构分析消融也都为 131/145，保留结构分析时在第三次提交达到该覆盖，移除时在第四次达到；保留时端到端 token 为 9,961,503，移除时为 7,172,218，前者高 38.9%。因此主文将 68.0% 和 19.8% 的节省明确写在时间序列任务条件内。

修复依赖图规划的完整结果同样保留。时间序列完整方法为 69/69、30 次调用、2,126,900 token，移除规划后为 69/69、21 次调用、1,803,551 token，token 少 15.2%。推荐完整方法为 131/145、80 次调用、9,961,503 token，移除规划后为 130/145、69 次调用、9,213,723 token，token 少 7.5%。两条件都完整接受一个仓库。规划继续作为方法组成介绍，四项主要组件证据中的“仓库上下文整体”不能替代规划的独立效果。

附录过程分析保留推荐移除规划后的 128→103→133→130 轨迹与完整方法的 n/a→122→131→131，最终分别按 130/145、131/145 计数。首次完整条件的八个执行失败标志位于协议检查之外，该次协议数值测量记为 n/a。移除规划的范围包含单元计划、依赖就绪检查、单元文件范围、检查点依赖传播和单元切换整理；结构分析、普通工具、证据及容量触发整理仍保留。精确开关、预算和运行条件集中在协议说明中。

共同 MindSpore 集合上的完整方法 50/50、连续对话 49/50，以及移除历史或提醒仍为 50/50 且 token 更低的结果继续按原研究保留。全文的组件结论分别落在已测任务上的修复收益与效率收益，表格与附录共同呈现完整证据。

## 7. 全文统一的行文处理

每段先给主要判断，再提供支持该判断的机制、比较或例子。结果段围绕接受、效率和行为覆盖分别展开；表格承担完整数值，正文选最有解释力的数字。已有积极结果直接陈述，实质条件在最相关的位置说明一次。

图表标题和讨论写明任务、方法与指标。图 3 可用“Total and per-input token costs for LaDiM and MatchFixAgent on MindSpore migration”，图注给出两方法均 50/50 及 57.4% 总 token 节省。消融表总题采用“Effects of training signals and repair components on acceptance and token use”，三个面板分别用“Training signals”“Repair history and independent evidence handoff on saved initial translations”“Repository context management and Repository Structural Analysis on the time-series repository”。图 4 的标题区分训练信号检测与损失曲线过阈。JAX 表题点明“Repair and native conversion controls on six faulty JAX candidates”，表内分开 LLM 修复与原生转换。

结果句直接指出比较，例如“uses 57.4% fewer tokens than MatchFixAgent”，删除 may help 或 shows potential 一类弱化已测差异的说法。讲跨条件一致性时列出实际共同呈现该规律的研究；成本统一注明端到端或仅修复，接受按各研究的完整协议表述。摘要与结论选择覆盖最强的证据，结果段保留完整的成功、失败和相反趋势。

全文同步检查正文、摘要、标题、图注和表注。删除重复解释控制流、读者没有提出的防御性说明、内部流程记账及无助于段落主张的修复日志。They are not supplied as task inputs 一类句子从正文清理；确有复现用途的信息进入协议附录。

减少临时拼接的连字符修饰语，例如 model-call 改为 LLM calls，tool-execution step 改为 tool execution，target-framework operations 改为 operations in the target framework。迁移方向用 from PyTorch to MindSpore 等自然表达。保留正式方法名称和用户已确认的 state-of-the-art。自动断词通过局部换行处理，不以全局缩字或压缩篇幅解决。

方法中使用已定义的 discrepancy、Verifier Agent、Repair Agent 和 Orchestrator。两个仓库模块统一称 Repository Structural Analysis 和 Repair Dependency Graph Planning，首次出现时解释作用，后文及图表沿用全称，不增加模块缩写。`repository map` 指仓库结构分析提供的结构清单，`work unit` 指修复依赖图中的单元；两者作为具体对象名称保留。

## 8. 应用顺序与交付检查

方案已纳入完整实验结果及本轮主文安排。应用时先统一摘要、引言贡献和结论的主张，再修改方法动机、任务定义及 setup，随后重写结果分析并同步图 3／图 4、表题和表注。消融主表采用历史初译上的两个程序级组件和时间序列上的两个仓库级比较；JAX 主文采用原六例，预先定义 Ivy、torch2jax 与 TorchAX，保留 Direct repair 及两种原生转换对照。新 JAX 多步结果、完整累计消融与独立规划消融在附录各自说明。方法图仍由用户处理。

应用方案时每轮先检查 Git 并保留提交；完成后编译 LaTeX，核对数值、公式、引用和局部排版，更新与昨晚修改前固定基线的逐词对比页面。此轮不以目标页数为依据删减内容。

证据来源：data/paper_figures/unified_results.json；figures/TABLE_natural_components.tex；sections/supplementary_experiments.tex；docs/maintext-results-20260918.md；docs/cumulative-component-ablation-20260922.md；output/cumulative-component-ablation-20260922/summary.json；docs/repository-map-ablation-20260922.md；data/audits/repository-map-ablation-20260922/；docs/work-unit-planning-ablation-20260922.md；data/audits/work-unit-planning-ablation-20260922/；docs/maintext-jax-autonomous-rerun-20260918.md；output/maintext-jax-autonomous-20260918/final_analysis/；output/maintext-jax-autonomous-20260918/maintext_jax_complete_20260918.tar.gz 中的 formal_v5/converter_results.json 与 private_backend/track_c_external.py；docs/jax-expansion-20260922.md；output/jax-expansion-20260922/formal/；scripts/repository_agent_mode.py。工具介绍引用上述官方资料，实验调用以归档实现为准。行文参考 literature/zhekai-du/Academic-Writing-DNA.md 与仓库 humanizer 规则。
