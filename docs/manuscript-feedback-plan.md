# 2026-09-22 论文综合修改方案

当前入口已更新为[2026-09-23 全文逐句审查后的修改方案](manuscript-review-20260923/00-revision-plan.md)。本文件保留9月22日的决定与执行经过；最新要求及冲突处理以[持久意见清单](manuscript-feedback-register.md)为准。

2026-09-22。依据[持久意见清单](manuscript-feedback-register.md)，已检查 `04a66f8` 版本。本文件给出核验后的具体改法。摘要局部修复已完成。用户现已明确要求落实所有剩余意见，本轮已完成执行，并采用最新的数据集表安排。清单持续维护，本方案按最新意见更新实施范围。

## 1. 已确认的问题与时间优先关系

确有持续遗漏和改写回退。Verifier 段仍用 narrow，以 discrepancy 为主语描述“指向哪里”，没有完整写出 Verifier 如何处理；四种错误类型的加粗在改写中丢失。算法 1 的分层诊断逻辑仍主要隐在角色指令里。数据集表按最新要求移至附录且不补平均长度，行为检查的表头与已有定义需要直接对应，时间序列修复调用数的粗体在横排中丢失。摘要的问题到方法连接及仓库机制目的已在此前摘要修订中落实，本轮保留该版本。

前后冲突采用用户最新意见或最后确认的方案。以下安排已经按时间整理，避免把新版改回旧版。

| 旧意见 | 后来确认的安排 | 本方案采用 |
|---|---|---|
| 早期要求数据集平均长度 | 后续要求删除，最新再次确认不加回且表移附录 | 保留四列表，移至附录；主文只保留任务定义。 |
| 摘要曾采用两至三个主要结果并概括跨框架适用性 | 最新要求删除自然故障结果、不写 baseline 名称，基于原稿简洁修复 | 只保留主要成本比较和跨框架/语言结论，优先执行最新意见。 |
| 结论不再重复精确数字，参考 MOST | 后来要求结果在结论更突出，并确认包含主要定量结果的方案 | 保留必要实证；使用 MOST 式“方法—机制—作用—整体发现”的推进。 |
| TorchAX 等名称全部进附录 | 后来要求在 JAX 结果前定义方法，并确认转换器/执行后端的区分 | 保留简短角色定义，具体接口和接入细节进附录。 |
| JAX 不额外追加 Direct 更便宜的降调句 | 最新确认方案明确按实测呈现接受和效率差异 | 保留真实成本比较，不把事实本身当成过度防御，不削弱跨框架有效性结论。 |
| Evaluation Protocol 独立小节 | 后来要求 4.1 不增加多级标题，用加粗段首 | 用 **Evaluation Protocol.** 段首，短正文配协议附录。 |
| 所有 agent 组件像信号一样累计加到主表 | 后来指定程序组件用十份初译，仓库组件用时间序列 | 保持主文四项组件按任务分组，完整累计结果留附录。 |
| 新 JAX 四方法比较承担泛化论证 | 后来明确主文回到原六例 | 六例保留主文；12 来源、2 个待修复任务独立在附录。 |
| 引言图兼有检测时刻和成本信息 | 后来要求只保留简洁横向成本图并环绕正文 | 保持现有成本图，检测轨迹位于分析实验。 |

代理自己的建议不会覆盖用户要求。以后出现冲突时，同样在清单中记录采用哪个较新的决定。

## 2. 摘要、引言与结论

对应 A01–A15、W01/W02。摘要按最新意见，基于固定基线的原摘要局部修复，保留问题、方法流程、仓库作用、主要结果的顺序。用 To address this problem 承接，不加回 loss initially agrees。删除自然故障四/五及对照零修复句，不再列 baseline 名称，不把方法各个组件堆进摘要。末句前半部分按最后一条意见保留，后半部分直接陈述训练行为保持的有效性。

以下摘要已实际写入论文并编译检查；具体基线与完整实证继续在正文和表格中说明。state of the art 采用无连字符的名词短语，摘要共 135 词：

> Migrating deep learning code across frameworks enables the reuse of training programs in new software and hardware environments. Framework differences can silently change gradients and parameter updates even when a translated program runs successfully. To address this problem, we propose LaDiM, a framework with multiple agents that uses dependencies between training computations to guide diagnosis and repair. The Verifier Agent investigates discrepancies and passes supporting evidence to a separate Repair Agent. The Orchestrator schedules their work and returns verification results after each submission. Repository context management preserves relevant evidence to coordinate repair across dependent files. On 50 migrations from PyTorch to MindSpore, LaDiM matches the state of the art in acceptance with 57.4% fewer total tokens, including initial translation. Evaluation across framework migration, language migration, and repository tasks demonstrates LaDiM's effectiveness in preserving training behavior.

仓库句以保存证据来协调依赖文件的修复，具体组成留方法。初译角色已在方法中定义，摘要不为列齐名称增加篇幅。

引言保留现在的成本横柱图和三个主要贡献，在首次介绍方法时明确使用 Layered Diagnosis 名称。四项组件先说明其解决的问题，再接历史初译和时间序列的对应证据；贡献不把整个仓库包的效果写成包内每个组件都有同样收益。

结论按最新强化方向保留一组主要定量比较，同时采用用户要求的机制推进。正式稿为：

> We introduced LaDiM, a framework with multiple agents for preserving training behavior during code migration. Layered Diagnosis uses dependencies among execution, forward values, gradients, and parameter updates to guide investigation. Independent evidence handoff and repair history connect the resulting evidence to corrective edits and their verification results. Repository context management carries this process across shared implementations and multiple entry points. LaDiM completes all 50 MindSpore migrations with 57.4% fewer tokens than MatchFixAgent, and the translation error study demonstrates repairs that all three repair baselines leave unresolved. Results across framework, language, and repository migration establish the effectiveness of this approach in preserving training behavior and reducing repair costs.

这保留最新方案要求的结果力度，同时避免将摘要中的全部数字和每个任务重念一遍。

## 3. 方法与三个算法

对应 M01–M14。Methods、Preliminary、Verifier Agent、Repair Agent、Repository Coordination 的短标题保持。3.1 保留任务和四差异公式，仅用一句定义对 W 内代码的修改；编辑计数留附录。容差与具体评价设置不回填方法正文。

3.2 将错误线索与具体调查动作合在同一段，四种 discrepancy 加粗。拟按以下逻辑组织，已落实到正文及算法：

> The Verifier Agent uses Layered Diagnosis to focus its investigation on the computations responsible for the observed discrepancies. For an **execution discrepancy**, it inspects the exception and the calls that produced it. For a **forward discrepancy**, it traces the operators that produce different values and tests the suspected computation. When forward values agree but a **gradient discrepancy** remains, it examines parameter registration and the path from the parameters to the loss. When both forward values and gradients agree, it investigates an **update discrepancy** through the optimizer's rule and state. The agent selects code inspections and distinguishing tests under its diagnosis instructions, then records the observations supporting each hypothesis. Independent evidence handoff transfers this evidence to a separate Repair Agent for correction and verification.

正式稿在对应短语旁沿用 3.1 的 discrepancy 符号。把“为什么这些观测帮助定位”和“agent 实际做什么”连起来，而非让异常自己执行动作。

算法的改法围绕实际实现展开：

| 算法 | 保留什么 | 本轮显式补充 |
|---|---|---|
| LayeredDiagnosis | 输入任务、候选及测量、LLM、预算和上下文；工具调用循环；证据输出 | 展开 A_V 对四种差异的诊断指导，让读者看见观测怎样影响 LLM 选择的检查/测试。 |
| Repair | 独立接收 Verifier 证据、保留历史、编辑后测试、提交和反馈 | 清楚呈现候选与历史怎样更新；保留 AgentStep 复用，压缩 flags/提示消息的低层细节。 |
| RepositoryMigrate 与上下文操作 | 调用前两算法、依赖失效、证据有效性及必要上下文重建 | 将结构分析和依赖规划如何进入工具过程讲清；通用归档接口的实现细节放附录。 |

诊断由 LLM 根据 A_V 和工具证据作选择。伪代码需要展示这层选择，不能为了好看把现有实现写成额外运行的固定 if/else 路由器。实施时对照冻结实现和已有 MatchFixAgent 算法参考，核对函数输入、候选修改、预算扣减、退出路径。仓库初查通过的返回路径与程序研究中初查后的调查/确认过程分别核对，不强行写成同一规则。

3.4 保持两个已确认正式名称，先说明共享修改与跨文件证据问题，再展开结构分析、依赖图规划，以及 notebook 工具、版本化证据、上下文重建的共同作用。文件哈希、容量数字、工具接口和事务细节集中到附录。正文保留“代码更新使哪些证据或检查失效”这一机制。

## 4. 实验定义、评价协议与结果

对应 E01–E10、R01–R14。4.1 继续采用三个加粗段首 Tasks、Compared methods、Evaluation Protocol。只补理解主表所需定义，详细数值阈值、种子和状态同步保持在协议附录。

任务表保留候选构造、模型覆盖和数量这四列，整体移至附录。**不加回平均长度**，这项最新用户要求覆盖原方案中的补列建议。公开 Java/DJL 和两仓库的来源、模型和规模仍在 Tasks 段交代。检测研究补一句“四种模型、三种子、50 步，用于比较直接训练信号与 loss 的检测时机”，不新增未定义的集合名。

Evaluation Protocol 已定义接受条件、训练观测和预算；本轮只补三列表头与统计对象的对应：accepted programs 是完成该任务所有规定检查的程序数；behavior checks passed 是仓库规定行为检查的通过数；entry points/original tests 分别是执行入口和仓库已有测试的通过数。行为检查包括执行及适用的数值、接口检查，不能把 69/69 误读成 69 个独立任务。完整分解仍在附录。

主表保留横排，恢复时间序列 35 次修复调用的粗体，`Checks passed` 改为完整 `Behavior checks passed`。Accepted 仍最右，CodeTransEngine 简名与 setup 首次引用保持，MSAdapter 无 LLM 用量保留横杠。自然修复表突出 LaDiM 的 4/5 和 9/10，相关段落解释从初始五个通过提升到九个通过的关系。

主结果继续分析完整接受、上下文输入成本、增加的 Java 接受、仓库多入口覆盖，保留 93.0% 与 1/2/4 提交证据。JAX 保持原六例表，Ivy/torch2jax 解释原生转换为何保留输入错误，Direct repair 成本按最新确认方案准确呈现。新 12 来源研究中的 SWE-agent/MatchFixAgent 结果保留附录。

## 5. 消融及排版收尾

对应 B01–B07、F01–F08。开头用一句话对应三组研究：16 个固定错误候选检验训练信号；十个保存初译检验历史与交接；时间序列检验仓库上下文与结构分析。信号 caption 写明每行继承上一行信号，最后为完整四种反馈。程序面板的 Accepted (repaired) 仍在 caption 明确定义，避免无说明的括号。

主文继续用两组独立配对呈现仓库效果。上下文机制为 6,047,074→1,936,579 token，节省 68.0%；结构分析为 2,651,248→2,126,900，节省 19.8%。均保持 69/69 检查通过，两个参照不合并。完整累计和规划消融保留附录。

内容修改后已执行此前批准的三项局部版式调整：修复第 10 页大块留白和末页短尾；对齐 Parameter updates 换行；统一表 3/5 关键修复数、最终接受和两项节省比例的强调。保留横向信息组织和模板字号。图 3 三方法总量柱、右侧图例及横轴保持；检测图仍在分析附近。方法图由用户负责。

## 6. 修改后的验收

实施时按清单 ID 登记每项改动。完成后重新检查**全部有效意见**，包括已落实和后续调整项，避免本轮修复制造另一轮回退。核对数值与公式、生成脚本和资产一致性，运行相关既有图表检查，编译并检查 PDF，刷新固定基线逐词比较。检查记录写回同一份持久清单，并保留实际版本和未解决项。

本轮已按用户授权落实方法、实验叙述、表格和结论的剩余修改。已确认的摘要保持不变。25 项既有检查通过，全文 23 页已编译并检查，固定基线比较已刷新。逐项核验和最新决定见持久清单；没有运行新实验或改用户方法图。
