# 论文内容与行文修改方案

JAX 正式比较与修复依赖图规划消融均已完成，费用、最终验收和原始证据已通过审计。本方案结合完整结果，明确全文的贡献、结果表达与证据范围。论文正文尚未应用；方法图由用户负责，篇幅压缩暂不处理。

全文改写采用用户确认的方向：在现有证据支持下坚定陈述方法解决的问题和取得的结果，突出比较对象、指标、评价条件及量化差异，并充分表达已覆盖的任务和模型范围。摘要、引言、方法动机、实验分析、图表标题与结论共同落实这一方向。

## 1. 全文的论证顺序

论文的核心问题是：迁移后的程序即使能够运行，训练行为也可能改变。方法章围绕训练计算之间的依赖解释如何诊断和修复；实验章先展示迁移成功与成本，再解释新增成功来自哪里、哪些观测和组件发挥了作用。

| 部分 | 读者应得到的结论 | 本轮改法 |
|---|---|---|
| 方法概述 | 谁调查、谁修复、谁调度和验证 | 恢复 Orchestrator 的调度职责，以实际动作串起流程 |
| 3.1 | 后文使用哪些 discrepancy | 保留执行、前向值、梯度、参数更新的定义，移出编辑计数和运行细节 |
| 3.2、3.3 | 训练差异怎样缩小调查范围，证据怎样帮助修复 | 用依赖关系解释判断，保留 LLM 与工具调用的伪代码，删除逐行复述算法的正文 |
| 3.4 | 多个文件如何组织，修改共享代码后如何继续检查 | 依次介绍仓库结构分析与修复依赖图规划，说明依赖检查及相关证据的保存 |
| 4.1 | 比较哪些任务、方法，以及什么算成功 | 先定义任务和初始状态分组，简述协议，复现细节集中到附录 |
| 4.2 | LaDiM 在迁移接受、成本或功能覆盖上有什么优势 | 每段围绕一个比较结论，用少量数字和具体行为支撑 |
| 4.3 | 新增成功和更早检测分别来自什么能力，能否迁移到 JAX | 分别讨论真实翻译错误、训练信号及新的 JAX 比较 |
| 消融 | 哪项设计改变了接受结果或修复成本 | 区分组件的独立作用与组合效果，补充每次提交的修复进展 |

沿用已确认的摘要结构、跨框架结论和 Generalization Across Frameworks 标题。摘要同时强化研究定位、方法动作和核心定量结果；JAX 的跨框架适用证据与两任务修复比较分别解释。

### 摘要、引言和结论的主张

研究定位直接写为“以训练行为引导代码迁移与修复”。方法创新围绕训练计算依赖展开：用执行、前向值、梯度和参数更新确定调查方向，由独立智能体形成证据并据此修复，再用提交后的测量继续定位问题。仓库结构分析与修复依赖图规划说明这一流程如何组织跨文件工作，其各自作用由独立消融解释。

| 证据 | 可直接突出的问题与结果 | 全文安排 |
|---|---|---|
| MindSpore 共同迁移集合 | LaDiM 与 MatchFixAgent 都接受 50/50，LaDiM 的端到端 token 少 57.4% | 摘要、引言和结论的主要效率证据 |
| Java/DJL 到 Python/PyTorch 的 18 项任务 | LaDiM 接受 9/18，SWE-agent 与 MatchFixAgent 各 8/18；token 分别少 11.7% 和 24.2% | 支持同时改变语言与框架的任务范围 |
| 十个保存的初译 | LaDiM 修复 4/5 个初始失败并保留 5/5 个初始通过；三个修复对照各修复 0/5 | 突出真实翻译错误及支持库修复能力 |
| 四模型、16 实例的训练信号消融 | 执行反馈、加入前向值、再加入梯度、再加入更新时，完整验收为 4/16、8/16、12/16、16/16 | 解释训练观测对触发和引导修复的作用 |
| 时间序列主比较 | 三种智能体均通过 69/69；LaDiM 比 SWE-agent、MatchFixAgent 少用 68.1%、80.8% 的端到端 token | 支持共享模型与多个仓库入口的实际意义 |

摘要保留两至三个最能支撑主张的结果，避免把所有研究压进数字列表。可采用的核心结果句为：

> LaDiM completes all 50 MindSpore migrations with 57.4% fewer tokens than MatchFixAgent. On saved initial translations, it repairs four of five failed programs, while Direct repair, SWE-agent, and MatchFixAgent repair none. Evaluation across framework migration, language migration, and repository tasks demonstrates its ability to preserve training behavior across distinct migration settings.

引言先用前向一致却梯度错误、当前观测一致却后续更新偏离的具体机制建立动机，再介绍 LaDiM 的调查与修复流程。贡献陈述分别对应训练行为诊断、独立证据交接与验证流程、以及共同协议下的迁移比较。每项写清提出了什么、处理哪种困难，并把最有力的结果紧接在相应主张后。全文保留可直接核对的比较，创新性通过机制与已有工作的具体差异表达。

适用范围按已测条件展开：从 PyTorch 到 MindSpore 的框架迁移、从 Java/DJL 到 Python/PyTorch 的语言与框架迁移，以及共享代码跨训练脚本、notebook 和其他入口的仓库迁移。新 JAX 研究补充原生模型计算和连续训练验收的证据。计算机视觉、语言、时间序列和推荐等名称用于说明所测模型与工作负载的覆盖，整应用能力按实际执行的入口和功能说明。

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

接着用一段说明上下文保留当前计划、相关代码和已有观测，以支持跨文件调查。完整历史和旧代码版本对应的测量留在可检索记录中。这里说明具体保留什么、何时需要取回，避免再造缩写或给实现机制起新名字。

删除以下控制流复述：

> Otherwise, the initial measurements support diagnosis, and the resulting evidence starts the repair loop.

这句话重复算法中的“初始检查失败后诊断，再进入修复”。同段“算法先验证，已通过就立即返回”“这些上下文操作服务于算法 1 和 2”等重复说明一起清理。

代码核对还发现，仓库结构分析由 `repository_map` 工具调用触发，初始化及上下文重建不会自动执行该扫描。因此算法 3 的 `RepositoryContext(Map(T))` 拟改为 `RepositoryContext(T)`，结构分析结果通过共享工具调用取得。正文和伪代码统一为实际实现的行为，代码中的工具标识保持不变。

方法核心流程已经稳定。仓库结构分析与修复依赖图规划在方法图中的强调程度，根据各自实验确定；图由用户修改。

## 3. 4.1 缩短 setup，先把比较对象讲清楚

保留加粗标签，按 Tasks、Compared methods、Evaluation 三部分组织，不增加小标题层级。

Tasks 交代主迁移集合、两个仓库、十个保存的首次翻译和训练信号研究分别用于什么问题。十个保存的翻译中，五个需要修复，五个已通过初始检查；该比较允许修改候选及其支持库。这一定义放在结果之前。

初始分组统一为 programs that require repair 和 programs that pass the initial checks。图中采用 Needs repair 和 Passes initial checks。表 1 中 Natural translation faults 改为 Saved initial translations，与包含五个初始通过程序的事实一致。原生 JAX 研究的任务行明确区分 12 个来源、10 个非空候选和 2 个初始失败修复任务；旧六例的协议与结果移至附录单独说明。

Compared methods 区分主表的 Direct LLM 初次翻译与分析实验中的 Direct repair，避免两个 Direct 被读成同一种流程。说明 LaDiM、SWE-agent 和 MatchFixAgent 的比较角色，以及相同的 LLM 后端；各研究包含的方法由相应表格直接列明。

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

Generalization Across Frameworks 保留为主文中的跨框架分析，重点说明原生 JAX 计算和多步训练验收。完整结果表及失败分析放附录。这轮只有两个修复任务，没有达到扩大修复比较规模的目标，原方案中把它安排为扩大后的主要修复比较这一判断予以撤回。

共同初译覆盖十二个公开来源工作负载：八个通过初始验收，两个非空候选未通过，另两次生成耗尽输出预算且未返回代码。时间序列与 ResNet 的两个初始失败候选按修复前冻结的规则进入四方法比较。四种方法都修复时间序列、未接受 ResNet，最终均为 1/2。共享初译加后续修复后，各方法在十二个来源上均有九个通过；该结果包含共同初译已经通过的八个。

| 方法 | 修复接受 | 修复调用 | 修复 token | 两任务端到端 token |
|---|---:|---:|---:|---:|
| LaDiM | 1/2 | 35 | 1,840,066 | 1,871,493 |
| Direct repair | 1/2 | 28 | 760,935 | 792,362 |
| MatchFixAgent | 1/2 | 23 | 258,914 | 290,341 |
| SWE-agent | 1/2 | 66 | 1,013,532 | 1,044,959 |

时间序列的成功修复主要恢复输入切片和输出拼接形状，随后通过三个种子的三步训练检查。ResNet 初译为截断代码。LaDiM、Direct repair 和 SWE-agent 将其改为可执行实现，三个种子的首步数组均通过，第二或第三步出现梯度和更新等偏离，最终均未接受。主文可据此明确说明多步验收发现了首步检查会遗漏的差异；数值偏离的具体原因仍未唯一定位。

MatchFixAgent 在 ResNet 的原生语法分析阶段因截断候选提前终止，保留全部四次调用费用，数值测量为 n/a。附录同时呈现各方法的接受、停止原因和成本，解释其较低 token 中包含提前终止的影响。LaDiM 在这两例中没有修复数量或 token 优势。

任务设置明确候选负责原生 JAX 前向计算及缓冲状态，可信外部执行器负责独立求导与 Optax 更新；前向值、梯度、更新、参数和缓冲状态在三步、三个种子上比较。两任务端到端成本在修复费用上加入对应的共同初译 31,427 token；十二次初译的全部 139,724 token 及生成失败留在完整来源账本中。旧六例按其 TorchAX 协议单列于附录，与新任务分别计数。

若后续需要有代表性的 JAX 修复比较，证据缺口是更多独立的初始失败候选，尤其是可执行但梯度、状态或多步训练行为错误的程序。后续方案应先固定来源池、覆盖机制、初译预算和所需最小失败任务数，再统一初译并纳入全部符合条件的失败。这一建议只列为后续实验设计，本轮未新增运行。

## 6. 消融怎样支撑组件

训练信号消融回答“需要观察什么”，智能体和仓库消融回答“如何组织调查与修复”。沿用一张表内的小写 (a)、(b) 标记，并让每个面板的表头和表注独立说明比较对象。

现有累计智能体消融的最后一项合并了仓库结构分析、修复依赖图规划、证据和上下文机制，用于分析整套机制逐步加入后的变化。两个独立消融已经完成，以同一组完整方法结果分别考察仓库结构分析和修复依赖图规划。每个仓库每个条件各一次，完整方法和共同初译均未重跑。

| 仓库 | 条件 | 完整接受 | 检查 | 调用 | 端到端 token |
|---|---|---|---:|---:|---:|
| 时间序列 | Full LaDiM | 是 | 69/69 | 30 | 2,126,900 |
| 时间序列 | Without Repository Structural Analysis | 是 | 69/69 | 42 | 2,651,248 |
| 时间序列 | Without Repair Dependency Graph Planning | 是 | 69/69 | 21 | 1,803,551 |
| 推荐 | Full LaDiM | 否 | 131/145 | 80 | 9,961,503 |
| 推荐 | Without Repository Structural Analysis | 否 | 131/145 | 80 | 7,172,218 |
| 推荐 | Without Repair Dependency Graph Planning | 否 | 130/145 | 69 | 9,213,723 |

这张表用于独立仓库消融，完整方法每个仓库只列一次。表注说明共享参照和每格一次运行，69 与 145 是同一仓库的检查项目数。主方法与其他智能体的仓库比较采用其原有运行，保留原数值和独立协议。

Repository Structural Analysis 在时间序列上减少 19.8% 的端到端 token。在推荐上，保留结构分析于第三次提交达到 131/145，移除时到第四次达到；最终两者相同，而保留结构分析的 token 多 38.9%。正文用这两个任务的具体差异解释其作用。

Repair Dependency Graph Planning 的完整条件和移除条件都接受一个仓库。时间序列移除规划后首次提交通过，调用由 30 降为 21，token 少 15.2%。推荐移除规划后最终为 130/145，完整条件为 131/145，token 少 7.5%。因此本轮未显示修复依赖图规划提高完整接受数或降低 token；方法章保留其组织修复的机制，贡献陈述以训练行为诊断和证据交接为重点。

提交轨迹保留为过程分析：推荐移除规划后为 128→103→133→130，最终使用 130/145；完整条件为 n/a→122→131→131。移除条件有两次回退，完整条件在第三次提交达到的覆盖保持到末次。首次完整条件返回的八个执行失败标志位于 145 项协议检查之外，该次协议测量为 n/a。该轨迹描述本次修复过程，规划对稳定性的作用仍需更多独立运行验证。

消融边界说明一次：移除修复依赖图规划同时移除单元计划、依赖就绪检查、单元文件范围、检查点依赖传播和单元切换整理；仓库结构分析、普通工具、证据与容量触发整理保留。精确开关、复用核对与资源放置进入附录。关闭规划运行的耗时还受不同 CPU 放置和工具执行轨迹影响，正文的成本比较使用实际调用与 token。

已有自然翻译上的历史保留、独立交接等实验继续按各自设置解释。各研究的条件和结果分别保留，组合消融与独立消融共同说明哪些设计在什么任务上改变了修复表现。

## 7. 全文统一的行文处理

每段先给主要判断，再提供支持该判断的机制、比较或例子。结果段围绕接受、效率和行为覆盖分别展开；表格承担完整数值，正文选最有解释力的数字。已有积极结果直接陈述，实质条件在最相关的位置说明一次。

图表标题和讨论写明任务、方法与指标。图 3 可用“Total and per-input token costs for LaDiM and MatchFixAgent on MindSpore migration”，图注给出两方法均 50/50 及 57.4% 总 token 节省。训练信号表题点明“Effect of verification signals on full acceptance”；图 4 的标题区分训练信号检测与损失曲线过阈。独立仓库消融表采用“Effects of Repository Structural Analysis and Repair Dependency Graph Planning”，让接受、成本和提交进展承担结果解释。

结果句直接指出比较，例如“uses 57.4% fewer tokens than MatchFixAgent”，删除 may help 或 shows potential 一类弱化已测差异的说法。讲跨条件一致性时列出实际共同呈现该规律的研究；成本统一注明端到端或仅修复，接受按各研究的完整协议表述。摘要与结论选择覆盖最强的证据，结果段保留完整的成功、失败和相反趋势。

全文同步检查正文、摘要、标题、图注和表注。删除重复解释控制流、读者没有提出的防御性说明、内部流程记账及无助于段落主张的修复日志。They are not supplied as task inputs 一类句子从正文清理；确有复现用途的信息进入协议附录。

减少临时拼接的连字符修饰语，例如 model-call 改为 LLM calls，tool-execution step 改为 tool execution，target-framework operations 改为 operations in the target framework。迁移方向用 from PyTorch to MindSpore 等自然表达。保留正式方法名称和用户已确认的 state-of-the-art。自动断词通过局部换行处理，不以全局缩字或压缩篇幅解决。

方法中使用已定义的 discrepancy、Verifier Agent、Repair Agent 和 Orchestrator。两个仓库模块统一称 Repository Structural Analysis 和 Repair Dependency Graph Planning，首次出现时解释作用，后文及图表沿用全称，不增加模块缩写。`repository map` 指仓库结构分析提供的结构清单，`work unit` 指修复依赖图中的单元；两者作为具体对象名称保留。

## 8. 应用顺序与交付检查

方案已纳入两组新实验的最终审计结果。应用时先统一摘要、引言贡献和结论的主张，再修改方法动机、任务定义及 setup，随后重写结果分析并同步图 3／图 4、表题和表注。JAX 作为跨框架与多步验收分析，仓库独立消融如实呈现任务差异。方法图仍由用户处理。

应用方案时每轮先检查 Git 并保留提交；完成后编译 LaTeX，核对数值、公式、引用和局部排版，更新与昨晚修改前固定基线的逐词对比页面。此轮不以目标页数为依据删减内容。

证据来源：data/paper_figures/unified_results.json；sections/supplementary_experiments.tex；docs/maintext-results-20260918.md；docs/cumulative-component-ablation-20260922.md；docs/repository-map-ablation-20260922.md；data/audits/repository-map-ablation-20260922/；docs/work-unit-planning-ablation-20260922.md；data/audits/work-unit-planning-ablation-20260922/；docs/jax-expansion-20260922.md；output/jax-expansion-20260922/formal/；scripts/repository_agent_mode.py。行文参考 literature/zhekai-du/Academic-Writing-DNA.md 与仓库 humanizer 规则。
