# 论文内容与行文修改方案

本轮交付修改方案，论文正文尚未应用。方法图由用户负责，篇幅压缩暂不处理。实验子代理独立负责新增比较及证据整理；本方案说明这些证据在论文中回答什么问题、如何组织。

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

沿用已确认的摘要结构、跨框架结论和 Generalization Across Frameworks 标题。摘要本轮只统一 Orchestrator 的职责表述；新的 JAX 数字在完整结果返回后更新。

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

初始分组统一为 programs that require repair 和 programs that pass the initial checks。图中采用 Needs repair 和 Passes initial checks。表 1 中 Natural translation faults 改为 Saved initial translations，与包含五个初始通过程序的事实一致；旧 JAX 六例那一行改为新研究的实际模型范围、候选来源和数量。

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

Generalization Across Frameworks 用新的原生 JAX 迁移研究替换旧六例正文比较。共同初译覆盖十二个公开来源工作负载：八个候选通过初始验收，两个非空候选未通过，另两次生成耗尽输出预算且未返回代码。时间序列与 ResNet 的两个初始失败候选进入全部四种方法的修复比较。这一选择在修复运行前确定。

setup 先交代这条任务来源流程。任务表分别写清十二个来源任务、十个取得的候选和两个修复任务；四方法结果表以两个修复任务为分母，报告完整接受、调用和 token。另在同一研究的来源说明中报告八个初始通过和两个生成失败。修复费用与含共同初译的总费用各有明确列名；十二次初译的全部费用在附录留账，生成失败的费用也保留。

正文按“共同初译留下哪些问题 → 各方法修复了什么 → 成本差异及其过程依据”展开，用真实结果确定重点。时间序列的初始问题是输入维度索引错误，ResNet 是非空代码被截断后的语法错误；模型复杂度与初始错误的性质分别介绍。只有后续轨迹确实出现梯度或缓冲状态差异时，才据此分析训练观测如何引导修复。

新研究验证原生 JAX 模型计算在连续训练中的一致性，候选负责前向计算及缓冲状态，外部执行器使用 JAX 独立求导并按合同执行 Optax 更新。前向、梯度、更新、参数与缓冲状态均在三步、三个种子上比较。成文将这一任务范围写入设置，结果围绕原生计算迁移展开。四方法的最终接受和费用由实验子代理完成审计后填入；旧六例及其全部费用保留在实验记录和附录中。

## 6. 消融怎样支撑组件

训练信号消融回答“需要观察什么”，智能体和仓库消融回答“如何组织调查与修复”。沿用一张表内的小写 (a)、(b) 标记，并让每个面板的表头和表注独立说明比较对象。

现有累计智能体消融的最后一项合并了仓库结构分析、修复依赖图规划、证据和上下文机制。正文可解释完整组合的成本变化。仓库结构分析的独立实验则单独说明：时间序列成本下降 19.8%；推荐较早达到同样的检查覆盖，但最终费用更高。它目前适合作为仓库协调中的辅助机制，贡献列表不据此新增“仓库结构分析普遍提升效率”的主张。

修复依赖图规划的独立消融已交由实验子代理执行。复用仓库结构分析消融中已经完成的时间序列与推荐完整方法结果，仅新增两个仓库关闭修复依赖图规划的运行。启动前核对源程序、共同初译、输入、种子、阈值、模型、预算及冻结核心实现一致，保留仓库结构分析。完整条件没有改动，无需重复运行；已有结果来源在实验记录中注明。

修复依赖图规划消融包括移除单元计划及依照计划执行的规则：依赖就绪检查、当前单元的文件范围、检查点依赖传播和单元切换时的上下文整理。关闭该模块时取消计划及依赖该计划的约束，使智能体可以直接跨文件修复；普通代码检查、证据检索和容量触发的上下文重建保留。结果解释为修复依赖图规划这一完整模块的作用。最终接受之外报告各次提交的通过情况及累计成本，结合轨迹分析是否提前完成相关文件的修复；模型调用、种子和检查数量各自保持其实际统计单位。待两项消融结果返回后，再确定该组件在方法贡献与结果分析中的强调程度。

仓库独立消融可合并为一张表：每个仓库列完整方法、关闭仓库结构分析、关闭修复依赖图规划三行，完整方法只出现一次。英文条件名使用 Full LaDiM、Without Repository Structural Analysis 和 Without Repair Dependency Graph Planning。各行保留最终接受、检查通过数、调用和端到端 token，检查数用于描述同一仓库的完成程度。表注说明两个消融共享完整方法结果，每个条件各运行一次；新增调用开销只计两个关闭修复依赖图规划的运行。正文分别解释两个组件的配对差异，并用提交轨迹说明差异产生在哪个修复阶段。累计组件实验仍回答逐步加入整套机制的问题，保留其独立协议。

已有自然翻译上的历史保留、独立交接等实验，可用于解释这些设计的作用。其设置与仓库研究分别交代，结果不拼成同一组累计条件。实验执行和最终证据由子代理负责。

## 7. 全文统一的行文处理

每段先给主要判断，再提供支持该判断的机制、比较或例子。结果段围绕接受、效率和行为覆盖分别展开；表格承担完整数值，正文选最有解释力的数字。已有积极结果直接陈述，实质条件在最相关的位置说明一次。

全文同步检查正文、摘要、标题、图注和表注。删除重复解释控制流、读者没有提出的防御性说明、内部流程记账及无助于段落主张的修复日志。They are not supplied as task inputs 一类句子从正文清理；确有复现用途的信息进入协议附录。

减少临时拼接的连字符修饰语，例如 model-call 改为 LLM calls，tool-execution step 改为 tool execution，target-framework operations 改为 operations in the target framework。迁移方向用 from PyTorch to MindSpore 等自然表达。保留正式方法名称和用户已确认的 state-of-the-art。自动断词通过局部换行处理，不以全局缩字或压缩篇幅解决。

方法中使用已定义的 discrepancy、Verifier Agent、Repair Agent 和 Orchestrator。两个仓库模块统一称 Repository Structural Analysis 和 Repair Dependency Graph Planning，首次出现时解释作用，后文及图表沿用全称，不增加模块缩写。`repository map` 指仓库结构分析提供的结构清单，`work unit` 指修复依赖图中的单元；两者作为具体对象名称保留。

## 8. 应用顺序与交付检查

先修改方法职责、任务定义及 setup，再重写主结果和分析段落，随后统一图 3／图 4 的文字与表注。新增 JAX 及组件结果由子代理交付后，更新相应任务行、结果表和分析。方法图仍由用户处理。

应用方案时每轮先检查 Git 并保留提交；完成后编译 LaTeX，核对数值、公式、引用和局部排版，更新与昨晚修改前固定基线的逐词对比页面。此轮不以目标页数为依据删减内容。

证据来源：data/paper_figures/unified_results.json；sections/supplementary_experiments.tex；docs/maintext-results-20260918.md；docs/cumulative-component-ablation-20260922.md；docs/repository-map-ablation-20260922.md；docs/jax-expansion-20260922.md；scripts/repository_agent_mode.py。行文参考 literature/zhekai-du/Academic-Writing-DNA.md 与仓库 humanizer 规则。
