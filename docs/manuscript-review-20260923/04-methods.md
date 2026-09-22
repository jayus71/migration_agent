# 方法正文、图注及三个算法逐句审查报告

审查版本：`d1d6a53`。本报告仅提出修改方案，未修改论文、脚本、图表、结果或 PDF，未运行工具或实验。依据为本轮直接提供的源码、意见清单、humanizer 规则、Academic-Writing-DNA 和实现片段。

本节最需要调整的是三个算法的组织：算法一删除正文已经解释的四类 discrepancy；共享步骤显式标出 LLM 调用；算法二保留真正影响修复行为的条件，尤其是“最后一次编辑后执行测试”；算法三把仓库整体评估、算法一和二的复用，以及按需发生的跨文件协调连起来。正文总体逻辑完整，主要需要消除重复、解释少数内部状态词，并准确区分诊断线索与固定路由。

## 一、审查范围与覆盖数

| 对象 | 准确来源 | 本轮覆盖 |
|---|---|---:|
| 方法概述 | `sections/methods.tex:4` | 6 句 |
| Preliminary | `sections/methods.tex:15–26` | 16 个文字单元，其中包括公式引导句 |
| 四种 discrepancy 公式 | `sections/methods.tex:19–22` | 4 个公式单元 |
| Verifier Agent | `sections/methods.tex:31` | 9 句 |
| Repair Agent | `sections/methods.tex:70–72` | 8 句 |
| Repository Coordination | `sections/methods.tex:97–101` | 15 句 |
| 方法图图注 | `sections/methods.tex:9` | 4 个文字单元，包括开头标题短语 |
| 算法一 | `sections/methods.tex:34,37–63` | 1 个标题、27 行内容 |
| 算法二 | `sections/methods.tex:75,78–90` | 1 个标题、13 行内容 |
| 算法三 | `sections/methods.tex:104,107–131` | 1 个标题、25 行内容 |

合计：正文 54 个文字单元、公式 4 个、图注 4 个、算法标题 3 个、算法内容 65 行。算法内容行包括输入输出、说明行、函数声明、控制结构及结束行；一行内有多个操作时分别说明。

四个小节标题 `Preliminary`、`Verifier Agent`、`Repair Agent`、`Repository Coordination` 均建议保留，符合 M01。LaTeX 环境、标签和排版命令核对到引用关系层面，不计入句子或算法步骤数量。

本节没有表格。方法图的实际内部文字和生成器源码未包含在快照中，因此本轮覆盖其图注、资产引用与已给出的维护规则，不将图内标签记为已审查。

### 证据使用范围

- `output/maintext-ablations-20260918/frozen_v4_agent.py:27–73,558–620,853–1049` 支持独立调查、证据交接、持续修复会话、按最后一次编辑判断测试状态等行为。
- `scripts/repository_agent_mode.py:183–410,419–608` 支持按需结构检查、代理提出依赖计划、工作单元选择、检查失效、证据检索和会话重建。
- `data/paper_figures/README.md` 明确当前主方法采用冻结的 slim-v4，而部分研究采用较早配置。本轮提供的 `frozen_v4_agent.py` 可用于核对所展示的具体行为，但不能据此宣称已核对当前主实验全部实现。
- 主控程序、完整预算处理和仓库最终验收调用代码未提供。有关这些部分的实现判断在下文列为主代理核对项。

下文使用现有意见 ID。`S13` 指 2026-09-23 最新要求；未为代理建议擅自登记新的正式意见 ID。

## 二、正文逐句台账

### 2.1 方法概述与 Preliminary

| 局部编号 | 原句短引与行号 | 建议 | 理由及意见 ID |
|---|---|---|---|
| M-01 | “LaDiM uses dependencies between training computations…”；L4 | 保留 | 直接交代核心诊断依据，没有夸大，也没有无信息铺垫。A08、W02 |
| M-02 | “The Translator first produces a candidate in the requested framework.”；L4 | 改写 | 本节任务元组同时包含语言与框架；这里只写 framework 与整体适用范围不一致。改为 requested language and framework。M02、W03 |
| M-03 | “The Verifier Agent investigates discrepancies…”；L4 | 保留 | 清楚连接调查对象、证据和接收角色，概述层面必要。M09 |
| M-04 | “The Repair Agent tests these hypotheses…”；L4 | 保留 | 说明接收者会检验假设，独立交接并非直接照抄诊断。M13 |
| M-05 | “The Orchestrator schedules their work…”；L4 | 保留 | 职责及提交后的反馈闭环明确。A03、M11 |
| M-06 | “Figure…shows this process.”；L4 | 保留 | 简短图引用，不构成重复总结。P04 |
| M-07 | “A migration task \(\mathcal T=(P,L_s,F_s,L_t,F_t,W)\)…”；L15 | 保留 | 任务、环境和可编辑范围定义完整。M02 |
| M-08 | “Migration produces a target program…that preserves…”；L15 | 保留 | 这是任务目标定义，保持肯定表达，无需添加防御性限定。W02 |
| M-09 | “The scope can include the translated program…”；L15 | 保留 | 解释 \(W\) 可覆盖支持库和仓库，是理解后续修复的重要条件。M02 |
| M-10 | “An edit modifies code within \(W\).”；L15 | 保留 | 满足 edit 的基本定义；计数规则继续留附录。M04 |
| M-11 | “At step \(t\), the source produces…”；L17 | 改写 | 发生执行异常时并非所有数值都可观测，原句将完整四元组写成每一步必然产生。建议以记录的观测定义四元组，明确数值项在可获得时记录。M03、W07 |
| M-12 | “Here \(e_t\) records the execution outcome…”；L17 | 保留 | 符号逐项对应；无需把自然的四项定义当成列举冗余。M03 |
| M-13 | “After aligning corresponding tensors and parameters, we define”；L17 | 保留 | 张量和参数对齐是公式的必要条件，不能为压缩删除。M03 |
| M-14 | “For a numerical comparison \(d=x-\hat x\)…”；L24 | 保留 | 容差含义、绝对与相对项及范数形式均有作用，具体数值留协议。M03、M05 |
| M-15 | “These discrepancies follow the training computation.”；L24 | 删除并由后文直接展开 | 下一句已经具体说明依赖关系，本句没有新增机制信息。W01、W06、S13 |
| M-16 | “Forward values determine the loss…”；L24 | 保留 | 具体说明前向、梯度和优化器状态的关系，是分层诊断的机制依据。M03 |
| M-17 | “The updated parameters then affect subsequent forward computations.”；L24 | 保留 | 解释跨步传播，支撑后文“首次出现差异的步骤”。M03 |
| M-18 | “The LLM \(M\) performs translation…”；L26 | 保留 | 统一模型符号与角色指令，供三个算法复用。M02 |
| M-19 | “The Orchestrator \(\mathcal O\) evaluates candidates…”；L26 | 保留 | 共享调查与修复预算是必要设定；不擅自把初译计入该预算符号。M02、W07 |
| M-20 | “In the algorithms, \(S\) holds…\(C\) manages retained evidence.”；L26 | 改写 | `S.m`、`S.\hat P` 后文直接出现，但这里未对应说明；\(C\) 在算法三还管理计划、单元与检查状态。需要一次准确的符号定义。M02、W03 |
| M-21 | “A submission sends the candidate for external verification…”；L26 | 保留 | 明确 submission 与 LLM call、test、edit 的区别，关系到预算结果的解释。W07 |
| M-22 | “Each \(\textsc{Query}\)…invokes \(M\)…”；L26 | 改写 | 名称改为 `LLMCall`，保持阶段额度与共享预算含义，使算法本身可见 LLM 调用。M10、S13 |

### 2.2 四种 discrepancy 公式

| 局部编号 | 原式与行号 | 建议 | 理由及意见 ID |
|---|---|---|---|
| EQ-01 | \(d_{\mathrm{execution},t}=\mathbf1[e_t\ne\hat e_t]\)；L19 | 保留 | 用指示函数表达执行结果差异，与正文一致。异常结果如何编码属于实现或协议，本轮不重定义。M03 |
| EQ-02 | \(d_{\mathrm{forward},t}=v_t-\hat v_t\)；L20 | 保留 | 保留有符号差值及后续容差定义，不擅自换成范数。M03、W07 |
| EQ-03 | \(d_{\mathrm{gradient},t}=g_t-\hat g_t\)；L21 | 保留 | 与前向及参数更新分别定义，机制清楚。M03 |
| EQ-04 | \(d_{\mathrm{update},t}=(\theta_{t+1}-\theta_t)-(\hat\theta_{t+1}-\hat\theta_t)\)；L22 | 保留 | 比较的是参数变化量，不能简写成更新后参数差。M03、W07 |

这四个公式保留在 Preliminary。算法一删除其重复解释，既不删除定义，也不减少方法的科学内容。

### 2.3 Verifier Agent

| 局部编号 | 原句短引与行号 | 建议 | 理由及意见 ID |
|---|---|---|---|
| M-23 | “The Verifier Agent uses Layered Diagnosis…”；L31 | 保留 | 正式方法名、主体和用途明确。A08、M07 |
| M-24 | “For an execution discrepancy…exception and the calls…”；L31 | 保留 | 观测与对应调查动作在同一句，符合 M08/M09。 |
| M-25 | “For a forward discrepancy…it traces the operators…”；L31 | 保留 | 明确查什么及怎样检验，不是单独罗列故障名。M08、M09 |
| M-26 | “When forward values agree but a gradient discrepancy…”；L31 | 保留 | 描述训练依赖提供的调查线索；与后文 LLM 自行选择动作合读，不应改成硬编码分支。M08、M10 |
| M-27 | “When both forward values and gradients agree…”；L31 | 保留 | 优化器规则和状态均有机制含义。保留条件，不添加“唯一原因”等结论。M03、M08 |
| M-28 | “The first affected step further guides this investigation…”；L31 | 最小改写 | `first affected step` 可明确为首次观测到差异的训练步骤，避免读者将 affected 理解成已定位故障发生时刻。W03、W07 |
| M-29 | “The LLM selects code inspections and tests…”；L31 | 保留 | 清楚说明动作由 LLM 根据证据选择，并输出位置与支持观测。是避免固定路由误读的重要句子。M10、S13 |
| M-30 | “Independent evidence handoff transfers these findings…”；L31 | 与 M-31 合并 | 与概述和 Repair Agent 开头重复。保留组件名及其含义，但集中在 Repair Agent 首句定义。M13、W01 |
| M-31 | “Algorithm…connects the observed discrepancies…defines the shared AgentStep…”；L31 | 改写 | 删除重复 discrepancy 列表后，“connects”不再准确概括算法内容。应说算法组织调查工具循环并提供共享 LLM 步骤。M10、M11、S13 |

### 2.4 Repair Agent

| 局部编号 | 原句短引与行号 | 建议 | 理由及意见 ID |
|---|---|---|---|
| M-32 | “The Repair Agent receives…through independent evidence handoff.”；L70 | 最小改写 | 在此完整定义组件最自然，并说明证据带有 Verifier 来源；算法无需另设难懂的归属函数名。M13、B03 |
| M-33 | “It reassesses this evidence, runs further tests…”；L70 | 保留 | 重评估、测试和允许的支持库修改均必要，不能为了删三项列举而丢失机制。M02、M13 |
| M-34 | “The agent tests its changes before submission.”；L70 | 保留 | 说明正常修复流程的关键步骤；算法应更精确表达最后一次编辑后的测试要求。M10 |
| M-35 | “The Orchestrator then verifies…further investigation and repair.”；L70 | 最小改写 | 将末尾动作主体写成 Repair Agent，避免“further investigation”被误读为每次重新启动 Verifier。M11、S13 |
| M-36 | “Repair history preserves earlier edits…”；L72 | 保留 | 定义后文消融使用的正式组件，不能因抽象概述而删除。M13、B03 |
| M-37 | “The continuing conversation includes failed tests…”；L72 | 保留 | 具体解释历史如何帮助比较修改前后结果，信息密度合适。M13 |
| M-38 | “The current candidate also persists…”；L72 | 保留 | 对话持久化和代码持久化不同，本句补充了后者。M13 |
| M-39 | “Algorithm…reuses AgentStep…”；L72 | 保留 | 为渐进复用提供明确指向。M11 |

### 2.5 Repository Coordination

| 局部编号 | 原句短引与行号 | 建议 | 理由及意见 ID |
|---|---|---|---|
| M-40 | “A change to a shared implementation can affect several callers…”；L97 | 保留 | 由具体跨文件问题引出设计，符合 DNA 的问题到机制顺序。M13 |
| M-41 | “Repository context management carries the plan…”；L97 | 改写 | `carries` 没有说明实际行为。改为保存依赖计划、相关代码观测和调查证据。W01、W03、M14 |
| M-42 | “It combines Repository Structural Analysis…”；L97 | 保留 | 五部分完整且各有用途，不是为凑列表而列举；两个正式名称保持不变。M12、M13 |
| M-43 | “Repository Structural Analysis exposes files…through a tool call.”；L99 | 最小改写 | 保留按需调用这一真实机制，删 `exposes` 式接口措辞，直接说代理可以检查什么。M12、M14 |
| M-44 | “The agent uses Repair Dependency Graph Planning…”；L99 | 保留 | 清楚说明单元、目标与 DAG 由代理建立，符合代码证据。M12、M13 |
| M-45 | “It selects a unit whose prerequisites have current checkpoints…”；L99 | 改写 | `current checkpoints` 未解释，跨领域读者容易理解为模型权重检查点。用“前置单元检查仍有效”表达。W03、S13 |
| M-46 | “Local syntax checks and selected tests establish each unit's current status.”；L99 | 改写 | `current status` 模糊，直接写记录语法检查和选定测试结果。M14、W06 |
| M-47 | “When an edit changes a shared implementation…affected units and their dependents…”；L99 | 改写 | 实现按修改文件所属单元及声明依赖图传播失效，并非自动解析所有实际调用者。候选保留跨文件作用，写清传播依据。M13、W07 |
| M-48 | “The Orchestrator evaluates the complete repository…”；L99 | 保留 | 仓库整体验收是本节关键机制，应进入算法三主流程。M11、M13 |
| M-49 | “Notebook tools let the agent inspect and revise code cells…”；L101 | 保留 | 与普通文件编辑有实质区别，源码支持单元格读取和语法校验。M13 |
| M-50 | “The evidence archive retains code observations…”；L101 | 保留 | 版本关联与检索直接支持跨会话修复，不应与无用记账一起删除。M13、M14 |
| M-51 | “At independent evidence handoff, a switch…or a context capacity boundary…”；L101 | 最小改写 | 用 `when the conversation approaches its capacity` 解释容量条件；保留交接和工作单元切换。其他控制边界见后文算法核对项。W03、M13 |
| M-52 | “It retains relevant code observations when…files remain unchanged.”；L101 | 保留 | 解释哪些读到的代码仍可复用；与实现中文件内容校验一致，无需在正文写哈希。M13、M14 |
| M-53 | “These operations extend the program repair history…”；L101 | 改写 | 现句有总结性重复。可改成具体的“恢复工作时沿用计划和先前发现”，自然连接下一句算法。W01、M11 |
| M-54 | “Algorithm…combines repository verification…”；L101 | 改写并与 M-53 合并 | 需要指出一次调查、持续修复和共享仓库上下文之间的关系，使读者进入算法前知道整体结构。M11、S13 |

## 三、方法图图注逐项台账

来源均为 `sections/methods.tex:9`。

| 编号 | 原文 | 建议 | 理由及意见 ID |
|---|---|---|---|
| FIG-01 | “LaDiM's migration workflow.” | 保留 | 简短指明图的对象。 |
| FIG-02 | “The Translator generates a candidate, the Verifier Agent investigates code and training observations, and the Repair Agent receives the evidence and revises the candidate.” | 保留 | 三个角色对应实际信息流，列举有必要。M09 |
| FIG-03 | “The Orchestrator schedules their work, checks submissions, and returns measurements.” | 保留 | 图注应自足，这里的角色说明与正文重复合理。A03 |
| FIG-04 | “Execution adapters obtain observations from MindSpore and JAX.” | 移附录 | 属于后端与观测采集说明，按最新 S13、E10 和 M05 移到附录对应协议。此句本身未出现 TorchAX，不应误报为主文出现了 TorchAX 名称。 |

建议图注候选：

> LaDiM's migration workflow. The Translator generates a candidate, the Verifier Agent investigates code and training observations, and the Repair Agent receives the evidence and revises the candidate. The Orchestrator schedules their work, checks submissions, and returns measurements.

图中若仍有执行适配器模块，图注删去这句后是否需要保留一句不含后端名称的功能解释，由主代理结合用户维护的图判断。本轮没有图内文字，不提出假定的标签替换。

## 四、三个算法逐行台账

### 4.1 算法一：Layered Diagnosis

标题 `sections/methods.tex:34`：“Layered Diagnosis”建议保留，保持贡献名称。以下逐行覆盖 L37–63。

| 编号／源码行 | 原步骤短引 | 建议 | 冗余、必要性及实现一致性 |
|---|---|---|---|
| A1-01／L37 | `Require Task…, candidate and measurements…, context C` | 保留并统一说明 | 输入必要；\(C\) 应称 context state，而不只表示证据档案。M02 |
| A1-02／L38 | `Ensure Evidence E: code observations…` | 保留 | 输出内容具体，支撑独立交接。 |
| A1-03／L39 | `Dependencies guiding the LLM's investigation:` | 删除 | 删除重复 discrepancy 块后不再需要引导行。S13 |
| A1-04／L40 | execution discrepancy 对应 exception/calls | 删除 | 正文 M-24 已解释，不删除科学定义。S13 |
| A1-05／L41 | forward discrepancy 对应 operators | 删除 | 正文 M-25 已解释。S13 |
| A1-06／L42 | forward agreement + gradient discrepancy | 删除 | 正文 M-26 已解释；无需把条件再排成类似路由表。S13 |
| A1-07／L43 | forward/gradient agreement + update discrepancy | 删除 | 正文 M-27 已解释。S13 |
| A1-08／L44 | `Function LayeredDiagnosis` | 保留 | 为算法三复用提供入口。M11 |
| A1-09／L45 | `StartConversation…; DiagnosisAllowance` | 保留，必要时拆行 | 独立调查会话与阶段额度均必要；删除其中任何一项都会损失机制或预算含义。 |
| A1-10／L46 | `While WithinLimits(b,B)` | 保留 | 阶段与共享预算共同限制，源码 L879–888 支持此结构。 |
| A1-11／L47 | `AgentStep(M,A_V,…); (H,a,R)` | 最小改写 | 保留复用；此处未使用 \(R\)，写为 `_`，降低无效状态负担。 |
| A1-12／L48 | `if a.complete then break` | 保留 | 调查结束条件必要；`complete` 应表示有效的阶段完成，而非任意不带工具的回答。解析细节留实现说明。 |
| A1-13／L49 | `EndWhile` | 保留 | 对应循环结构。 |
| A1-14／L50 | `E ← PublicEvidence(H,C.archive)` | 与 L51 合并 | 提取证据必要；临时变量只赋值后返回，可直接返回。证据不能擅自缩成最后一句摘要。 |
| A1-15／L51 | `Return E` | 与 L50 合并 | 无需独立占一行。 |
| A1-16／L52 | `EndFunction` | 保留 | 函数边界。 |
| A1-17／L53 | `Function AgentStep` | 保留 | 是算法一、二共享的动作循环，不再在算法二重复实现。M11 |
| A1-18／L54 | `H ← C.BeforeCall(H,S)` | 保留并改名 | 用 `PrepareContext` 表达作用；连接算法三的按需会话重建。 |
| A1-19／L55 | `a ← Query(M,A,H,b,B)` | 改为 `LLMCall` | 用户要求 LLM 显式出现。注释可保留“选择检查、测试或编辑”，不增加额外分类调用。S13 |
| A1-20／L56 | `H ← H∥a; R ← []` | 保留 | 记录模型回答及初始化本轮工具结果，后续有实际用途。 |
| A1-21／L57 | `ForAll c in a.toolCalls` | 保留 | 一次 LLM 调用可能请求多个工具；不能把工具调用次数当作 LLM 调用次数。W07 |
| A1-22／L58 | `Execute(c,S,productionReadOnly=(A=A_V))` | 保留语义，简化表达 | 诊断期间候选和支持库只读，但允许编写临时测试。不能直接改成“所有工具只读”。源码 L49–51 支持。 |
| A1-23／L59 | `append (c,r) to H and R` | 保留 | \(H\) 用于后续推理，\(R\) 用于修复测试状态，两者作用不同。 |
| A1-24／L60 | `C.Record(c,r,S)` | 保留并改为语义名称 | 可写 `C.UpdateAfterTool`，由算法三展开仓库状态更新；注释无需再次说“for subsequent reasoning”。 |
| A1-25／L61 | `EndFor` | 保留 | 工具批次边界。 |
| A1-26／L62 | `Return (H,a,R)` | 保留 | 三个返回对象均在共享调用处有用途。 |
| A1-27／L63 | `EndFunction` | 保留 | 函数边界。 |

算法一的精简应集中在删除 L39–43、合并证据返回，以及替换接口式名称。独立会话、预算、LLM 调用、工具结果和只读调查约束都有科学或执行含义，不宜一并压掉。

### 4.2 算法二：Repair

标题 `sections/methods.tex:75` 当前直接把完整签名放进 caption。建议标题改为 **Repair with independent evidence and history**，把签名放入函数声明，使算法三的调用有明确对应。

| 编号／源码行 | 原步骤短引 | 建议 | 冗余、必要性及实现一致性 |
|---|---|---|---|
| A2-01／L78 | `StartConversation(A_R,T,AttributeToVerifier(E))` | 改写 | 保留独立修复会话和来源归属，用注释说明 “E is attributed to the Verifier”，无需再造归属函数。 |
| A2-02／L79 | `C.handoff ← true` | 移附录／封装 | 必须保留交接触发上下文重建的行为，但布尔字段无需独占主文算法一行，可并入启动修复会话。M14 |
| A2-03／L80 | `While SubmissionsLeft(B) ∧ BudgetLeft(B)` | 保留 | 表达上限而非固定执行次数；不得改成固定四轮。W07、S13 |
| A2-04／L81 | `append S.m; F←(false,false); RepairAllowance` | 改写 | 三个动作均必要。将未定义二元组改成明确的 `edited`、`testedAfterLastEdit`；新阶段开始时重置。 |
| A2-05／L82 | `While WithinLimits(b,B)` | 保留 | 一个 submission 前可有多个 LLM 调用与工具操作。 |
| A2-06／L83 | `AgentStep…; UpdateFlags(F,R)` | 改写 | 保留复用，补一句更新语义：生产代码发生新编辑时重置测试标记，之后执行测试才置真。源码 L988–995 直接支持。 |
| A2-07／L84 | `complete ∧ edited ∧ tested` | 改写 | `tested` 必须改成“最后一次编辑后已测试”，否则“测试后再编辑”也可能被读作可提交。 |
| A2-08／L85 | `if complete then PendingAction(F)` | 保留语义、缩短名称 | 该提醒会让模型继续完成缺失编辑或测试，源码 L957–970 支持，不能当纯接口冗余删除。 |
| A2-09／L86 | `EndWhile` | 保留 | 阶段结束；预算耗尽也可能到达此处，不应把正常完成条件写成所有退出的保证。 |
| A2-10／L87 | `O.Verify; submissions++` | 保留 | 验收归主控，计数关系到预算结果。预算耗尽后是否仍调用验收须核对主控代码。 |
| A2-11／L88 | `if accepted then Return` | 保留 | 接受后提前结束，防止误写成所有允许次数均已执行。 |
| A2-12／L89 | `EndWhile` | 保留 | 提交循环边界。 |
| A2-13／L90 | `Return candidate,status` | 保留 | 未接受或预算耗尽时也返回当前候选及已有状态。 |

这里最重要的精度问题是测试与编辑的先后关系。`testedAfterLastEdit` 是源码已有语义，不是本轮新增验证要求。

### 4.3 算法三：Repository migration and context operations

标题 `sections/methods.tex:104` 建议改为 **Repository migration and repair coordination**。原算法只有 L107–113 展现总体流程，其余 18 行主要解释状态维护；应把正文已经说明的仓库协调机制放进读者可见的算法结构。

| 编号／源码行 | 原步骤短引 | 建议 | 冗余、必要性及实现一致性 |
|---|---|---|---|
| A3-01／L107 | `Function RepositoryMigrate` | 保留 | 仓库级入口必要。 |
| A3-02／L108 | `Translate(M,A_T,T); RepositoryContext(T)` | 改写 | 显式写 `LLMTranslate`，将初始化说成提供结构分析、规划、单元格编辑和证据检索能力；不自动执行结构扫描或规划。 |
| A3-03／L109 | `O.Verify(candidate)` | 改写名称／注释 | 明确这是完整仓库的验收，包含声明入口和训练检查。M11 |
| A3-04／L110 | `if accepted then Return` | 保留 | 表达初次翻译后的程序首次评估通过便无需修复。不得为展示修复而删除。 |
| A3-05／L111 | `LayeredDiagnosis(T,S,M,B,C)` | 保留 | 显式标注复用算法一；同一个仓库候选、上下文和预算。 |
| A3-06／L112 | `Return Repair(…)` | 保留并补说明 | 显式标注算法二持续执行修复与仓库验收。不得外加“每单元运行一次 Verifier”的循环。 |
| A3-07／L113 | `EndFunction` | 保留 | 总体入口边界。 |
| A3-08／L114 | `Function C.Record` | 改为 `C.UpdateAfterTool` | 该函数除归档还更新计划及检查状态；原名未说明协调作用。 |
| A3-09／L115 | `archive ← archive∥(c,r)` | 改写 | 使用语义动作“保留结果及其代码版本”；不在主文展开档案路径、哈希和索引。 |
| A3-10／L116 | `if CodeChanged(r)` | 改写 | 精确到目标代码内容变化；临时测试文件变化不应被自动描述为全部仓库观测失效。源码 L370–372 支持。 |
| A3-11／L117 | `MarkHistorical(measurements)` | 改写 | 原测量保留，但不再作为当前代码的有效测量。`historical` 不等于删除、不等于失败。 |
| A3-12／L118 | `Invalidate(AffectedUnitsAndDependents)` | 改写 | 明确按修改文件和声明的依赖图找单元；保留传递失效，不宣称自动获得完整动态调用图。 |
| A3-13／L119 | `EndIf` | 保留 | 代码变化分支边界。 |
| A3-14／L120 | `Update(c,r,C)` | 展开为具体条件动作 | 原行隐藏了结构检查、计划修订、单元选择和局部检查的核心协调。必须显现这些动作是响应 LLM 选定工具，而非固定顺序。 |
| A3-15／L121 | `EndFunction` | 保留 | 工具后状态更新边界。 |
| A3-16／L122 | `Function C.BeforeCall` | 改为 `C.PrepareContext` | 函数名直接说明用途。 |
| A3-17／L123 | `handoff ∨ UnitSwitched ∨ AtCapacity` | 保留核心条件并核对遗漏 | 源码还包含初始阶段、生成边界和显式主控边界。主文可归为待处理重建请求，但不能宣称只存在三个触发。 |
| A3-18／L124 | `Archive(C,H)` | 与重建操作合并表述 | 保留旧会话可检索这一语义，减少接口行数。 |
| A3-19／L125 | `CurrentReadCode(unit,candidate)` | 改写 | 必须表示已读取且文件仍未改变的代码观测，不能被理解为会话重建时自动扫描或读取所有当前代码。源码 L107–144 支持。 |
| A3-20／L126 | `PublicFindings(H,archive)` | 与重建输入合并 | 保留 Verifier 发现与后续调查发现，不只提取当前角色的最后一次回答。 |
| A3-21／L127 | `Rebuild(role,plan,E,S.m,K)` | 改写 | 重建输入应覆盖当前及已过期测试结果的状态；原 `S.m` 不能掩盖本地测试及有效性信息。 |
| A3-22／L128 | `handoff←false; previousUnit←unit` | 移附录／封装 | 状态复位细节放入语义操作，无须占主文算法；源码主要使用 pending rebuild 状态。 |
| A3-23／L129 | `EndIf` | 保留 | 条件重建边界。 |
| A3-24／L130 | `Return H` | 保留 | 返回当前或重建后的同角色会话。 |
| A3-25／L131 | `EndFunction` | 保留 | 函数边界。 |

## 五、需调整文字：原文、问题与英文候选

以下均为待审候选，没有实施。

### C-01：方法概述覆盖语言迁移

- 位置：`sections/methods.tex:4`，M-02。
- 原句：

> The Translator first produces a candidate in the requested framework.

- 问题：与任务元组及全文语言迁移范围不一致。
- 候选：

> The Translator first produces a candidate in the requested language and framework.

- 对应：M02、W03。无需新增定义或改变方法范围。

### C-02：观测定义允许执行异常后的缺测

- 位置：`sections/methods.tex:17`，M-11。
- 原句：

> At step \(t\), the source produces \((e_t,v_t,g_t,\theta_{t+1}-\theta_t)\), and the target produces \((\hat e_t,\hat v_t,\hat g_t,\hat\theta_{t+1}-\hat\theta_t)\).

- 问题：异常可能使后续前向、梯度或更新观测不可获得。提供的实现说明明确测试结果可能因错误而不完整。
- 候选：

> At step \(t\), we record the source and target execution outcomes \(e_t\) and \(\hat e_t\), together with the available forward values, gradients, and parameter updates.

下一句保留现有符号定义，四个公式保持原样。若主代理认为删去显式四元组影响紧凑性，也可保留四元组并用一句说明数值项仅在可观测时定义；不把缺测赋零。

- 对应：M03、W07。

### C-03：删除依赖解释前的空泛引导

- 位置：`sections/methods.tex:24`，M-15。
- 原句：

> These discrepancies follow the training computation.

- 问题：下一句已具体说明相同内容。
- 候选：删除本句，容差定义后直接接：

> Forward values determine the loss, differentiation produces the gradients, and the optimizer uses those gradients and its state to update parameters. The updated parameters then affect subsequent forward computations.

- 对应：W01、W06、S13。

### C-04：一次定义算法真正使用的状态

- 位置：`sections/methods.tex:26`，M-20。
- 原句：

> In the algorithms, \(S\) holds the candidate and observations, \(q\) is its verification status, \(H\) is a conversation, and \(C\) manages retained evidence.

- 问题：字段未对应；\(C\) 的定义小于算法三的实际职责。
- 候选：

> In the algorithms, \(S.\hat P\) is the current candidate, \(S.m\) contains its verification observations, \(q\) is its verification status, and \(H\) is the agent's conversation. The context state \(C\) retains evidence and, for repository tasks, the dependency plan and local check results.

- 对应：M02、W03、M14。这里是必要符号定义，不另造术语表。

### C-05：显式标出 LLM 调用

- 位置：`sections/methods.tex:26,55`，M-22、A1-19。
- 原句：

> Each \(\textsc{Query}(M,A,H,b,B)\) invokes \(M\) with instructions \(A\) and conversation \(H\), charging its usage to the stage allowance \(b\) and shared budget \(B\).

- 候选：

> Each \(\textsc{LLMCall}(M,A,H,b,B)\) invokes \(M\) with role instructions \(A\) and conversation \(H\), accounting for its usage against both the stage allowance \(b\) and the shared budget \(B\).

算法中的 `Query` 同步改为 `LLMCall`。算法三初译调用使用 `LLMTranslate`，但不能在没有主控证据时将其强行简化成一次调用。

- 对应：M10、S13、W07。

### C-06：首次出现差异的时间及算法一衔接

- 位置：`sections/methods.tex:31`，M-28、M-30、M-31。
- 原句一：

> The first affected step further guides this investigation because a changed update can alter later forward computations.

- 候选：

> The first training step with an observed discrepancy also guides the investigation because a changed update can alter later forward computations.

- 原句二、三：

> Independent evidence handoff transfers these findings to a separate Repair Agent for assessment and correction. Algorithm~\ref{alg:diagnose} connects the observed discrepancies to this investigation and defines the shared \textsc{AgentStep} for selecting actions, executing tools, and retaining evidence.

- 合并候选：

> Algorithm~\ref{alg:diagnose} organizes this investigation through a shared \textsc{AgentStep}, which makes an LLM call, executes the selected tools, and retains their results.

独立交接保留在下一节首句定义。四类 discrepancy 的正文解释和加粗名称均保留。

- 对应：M08–M11、M13、W01、S13。

### C-07：独立交接和失败后的调查主体

- 位置：`sections/methods.tex:70`，M-32、M-35。
- 原句一：

> The Repair Agent receives the Verifier Agent's code observations, test results, and hypotheses through independent evidence handoff.

- 候选：

> Independent evidence handoff gives the Repair Agent the Verifier Agent's recorded code observations, test results, and hypotheses, identified as the Verifier Agent's findings.

- 原句二：

> The Orchestrator then verifies the candidate and returns the remaining discrepancies, which guide further investigation and repair.

- 候选：

> The Orchestrator then verifies the candidate and returns the remaining discrepancies to guide the Repair Agent's next investigation and edits.

- 对应：M11、M13、S13。第二项澄清控制流，不增加“不会重启”等防御性尾句。

### C-08：仓库机制的具体动作

- 位置：`sections/methods.tex:97`，M-41。
- 原句：

> Repository context management carries the plan, code context, and evidence needed to investigate these relationships across files.

- 候选：

> Repository context management retains the dependency plan, relevant code observations, and investigation evidence across files and conversations.

- 对应：M13、M14、W01、W03。

### C-09：结构分析与有效的局部检查

- 位置：`sections/methods.tex:99`，M-43、M-45、M-46。
- 原句一：

> Repository Structural Analysis exposes files, imports, function and class definitions, and notebook cells for the agent to inspect through a tool call.

- 候选：

> Through Repository Structural Analysis, the agent can inspect the repository's files, imports, function and class definitions, and notebook structure on demand.

这里用 `notebook structure` 对应结构工具提供的单元格结构；实际单元格源码读取仍由 L101 的 notebook tools 说明。

- 原句二：

> It selects a unit whose prerequisites have current checkpoints, then edits the files assigned to that unit.

- 候选：

> The agent selects a work unit whose prerequisite units have valid local checks, then edits the files assigned to it.

- 原句三：

> Local syntax checks and selected tests establish each unit's current status.

- 候选：

> For each work unit, LaDiM records the results of syntax checks and the tests selected in the plan.

- 对应：M12–M14、W03、S13。

### C-10：按声明依赖传播检查失效

- 位置：`sections/methods.tex:99`，M-47。
- 原句：

> When an edit changes a shared implementation, LaDiM invalidates the checks for affected units and their dependents, prompting the agent to check the relevant callers again.

- 问题：`affected units` 容易被理解为系统自动识别所有调用关系；代码实际根据修改文件及声明图传播。
- 候选：

> When target code changes, LaDiM invalidates the local checks for units containing the changed files and for their dependents in the plan. Changes to shared implementations therefore prompt the agent to recheck the corresponding dependent units.

该候选不引入额外依赖解析功能，也不删去跨文件协调的贡献。

- 对应：M13、W07、S13。

### C-11：会话重建与整个仓库修复衔接

- 位置：`sections/methods.tex:101`，M-51、M-53、M-54。
- 原句一：

> At independent evidence handoff, a switch between work units, or a context capacity boundary, LaDiM rebuilds the conversation around the current plan, findings, and measurements.

- 候选：

> LaDiM rebuilds the conversation around the current plan, findings, and measurements when evidence passes to the Repair Agent, work shifts to another unit, or the conversation approaches its capacity.

- 原句二、三：

> These operations extend the program repair history to investigations that span multiple files and conversations. Algorithm~\ref{alg:repository} combines repository verification with the diagnosis and repair procedures.

- 合并候选：

> Algorithm~\ref{alg:repository} uses this context throughout the investigation in Algorithm~\ref{alg:diagnose} and the continuing repair process in Algorithm~\ref{alg:repair}, while the Orchestrator evaluates the complete repository after each submission.

- 对应：M11、M13、M14、S13。

初始阶段、生成边界和显式主控重建请求可放进附录实现说明；正文这句不必穷举全部内部触发字段。算法使用一般性的“有待处理的重建请求”时应在注释中列出主要来源。

### C-12：后端说明移附录

- 位置：`sections/methods.tex:9`，FIG-04。
- 原句：

> Execution adapters obtain observations from MindSpore and JAX.

- 移动目标：附录对应 MindSpore／JAX 的执行与观测采集协议。若附录已有相同内容，合并而不重复追加。
- 对应：M05、E10、S13。

本节源码没有 Ivy、torch2jax 或 TorchAX 的实际定义句。本报告不审改其他章节，只保留边界：实际对比方法 Ivy／torch2jax 的定义继续留在实验主文；TorchAX 执行后端说明移附录。

## 六、三个算法的精简与衔接候选

以下是供主代理选择的英文伪代码方案，不是已实施源码，也不把新函数名视为项目已有接口。语义操作可在最终 LaTeX 中采用现有宏实现。

### 6.1 算法一候选：只保留调查过程与共享 LLM 步骤

```text
Algorithm 1: Layered Diagnosis

Require: task T, candidate and observations S, LLM M,
         shared budget B, context C
Ensure: recorded code observations, test results,
        supported locations, and hypotheses

function LayeredDiagnosis(T, S, M, B, C):
    H ← StartConversation(A_V, T, S)
    b ← DiagnosisAllowance(B)
    while WithinLimits(b, B):
        (H, a, _) ← AgentStep(M, A_V, H, S, b, B, C)
        if a.complete:
            break
    return PublicEvidence(H, C.archive)

function AgentStep(M, A, H, S, b, B, C):
    H ← C.PrepareContext(H, S)
    a ← LLMCall(M, A, H, b, B)
    Append a to H
    R ← []
    for each tool call c selected in a:
        r ← Execute(c, S, A)
        # During investigation, candidate and library code remain
        # unchanged; scratch tests may be created and run.
        Append (c, r) to H and R
        C.UpdateAfterTool(c, r, S)
    return (H, a, R)
```

该方案删除四种 discrepancy 的重复块。正文解释训练依赖如何指导调查，算法显示 LLM 如何据此选择工具并形成证据，不新增分类器或固定分支。

`PublicEvidence` 应保留可交接的调查记录及工具观测。实现显示 Repair Agent 接收带来源的调查记录，因此不能仅因篇幅将其重新定义成一个短摘要。

### 6.2 算法二候选：持续修复、最后一次编辑后的测试和预算

```text
Algorithm 2: Repair with independent evidence and history

function Repair(T, S, E, q, M, B, C):
    H ← StartRepairConversation(A_R, T, E, C)
    # E is attributed to the Verifier Agent.

    while SubmissionsLeft(B) and BudgetLeft(B):
        Append S.m to H
        edited ← false
        testedAfterLastEdit ← false
        b ← RepairAllowance(B)

        while WithinLimits(b, B):
            (H, a, R) ← AgentStep(M, A_R, H, S, b, B, C)
            Update edited and testedAfterLastEdit from R
            # A new production edit resets testedAfterLastEdit.
            # A subsequent executed test sets it to true.

            if a.complete:
                if edited and testedAfterLastEdit:
                    break
                Append the missing edit or test requirement to H

        (S.m, q) ← O.Verify(S.candidate)
        Record one submission in B
        if q = accepted:
            return (S.candidate, q)

    return (S.candidate, q)
```

`StartRepairConversation` 封装现有独立交接及仓库上下文重建请求；并未取消交接。测试状态按工具实际发生顺序更新，不能把同一批工具结果当作无序集合。

候选保留原算法阶段结束后验收的位置。主代理需用主控源码核对预算耗尽、无有效最终回答或工具错误时的验收条件，再确定最终版本；本轮提供的 `_stage` 片段不足以裁定这一外层行为。

### 6.3 算法三候选：仓库整体流程及贯穿算法一、二的协调

算法三建议分为“仓库主流程”和两个精简的共享上下文操作。共享操作明确由算法一的 `AgentStep` 调用，因此整个调查与修复过程中均有效。

```text
Algorithm 3: Repository migration and repair coordination

function RepositoryMigrate(T, M, B):
    S.candidate ← LLMTranslate(M, A_T, T)
    C ← RepositoryContext(T)
    # C provides Repository Structural Analysis,
    # Repair Dependency Graph Planning, notebook tools,
    # evidence retrieval, and context reconstruction.

    (S.m, q) ← O.VerifyRepository(S.candidate)
    if q = accepted:
        return (S.candidate, q)

    E ← LayeredDiagnosis(T, S, M, B, C)          # Algorithm 1
    return Repair(T, S, E, q, M, B, C)          # Algorithm 2
    # Repair uses the same repository context and budget.
    # O.Verify evaluates the complete repository.


function C.UpdateAfterTool(c, r, S):
    Retain r with its code version.

    Update the dependency plan, active unit, or local check results
    when the selected tool performs the corresponding operation.
    # The LLM selects these operations through AgentStep.
    # Production edits require an active unit whose prerequisites
    # have valid local checks.

    If target code changed:
        Mark earlier measurements as belonging to an earlier version.
        Invalidate local checks for units containing changed files
        and their dependents in the declared plan.

    If the plan changed:
        Invalidate affected local checks and dependent checks.


function C.PrepareContext(H, S):
    if a context rebuild is pending or H approaches capacity:
        Archive H.
        Rebuild H for the current role using:
            the dependency plan and active unit;
            the Verifier's findings and subsequent investigation;
            recorded measurements and their validity;
            relevant prior code reads whose files remain unchanged.
    return H
```

本候选的配套解释应限定为两句：

> The LLM requests structural inspection, planning, unit selection, tests, and evidence retrieval through the shared tool loop. Context reconstruction preserves the current role and remaining budget as work moves across files.

这一结构有四个优点，均直接对应当前缺口：

1. 主流程明确处理初译、首次完整仓库评估、算法一调查和算法二持续修复。
2. 结构分析与依赖规划作为 LLM 按需使用的能力出现，不虚构初始化时必做扫描。
3. 局部检查失效与会话重建贯穿共享工具循环，仓库协调不再隐藏在泛化的 `Update` 里。
4. 单元切换只重建当前角色的上下文，算法没有按单元重新运行 Verifier。

`VerifyRepository` 是表述性名称。最终可继续写 \(\mathcal O.\textsc{Verify}\)，但须在算法入口明确它在此处评估整个仓库。

## 七、实现一致性与需核对事项

### 7.1 本轮片段直接支持的行为

| 行为 | 证据位置 | 审查结论 |
|---|---|---|
| 调查依据公开代码和观测，不读取预设故障路由 | `frozen_v4_agent.py:1–5,27–36` | 保留 LLM 选择检查和测试；删除算法重复条件块后，不补固定分类分派。 |
| Verifier 可写临时测试，候选和支持库不可修改 | 同文件 L49–51、L854、L987 | 算法不能把诊断简写为“完全只读工具”。 |
| 独立证据交接保留实际调查记录及来源 | 同文件 L570–619 | 交接是机制，不是无用接口；实现字段可精简。 |
| 修复会话跨尝试持续 | 同文件 L66–73、L857、L871 | Repair 会话应在提交循环外初始化。 |
| 生产代码最后一次编辑后需要执行测试 | 同文件 L957–970、L988–995 | `testedAfterLastEdit` 必须显式表达。 |
| 结构检查由工具请求触发 | `repository_agent_mode.py:183–201,226–245` | `RepositoryContext` 初始化不应被改写成自动全仓库分析。 |
| 工作单元及依赖由代理提出 | 同文件 L1–5、L213–219、L259–295 | 保留正式模块名，不赋予其隐藏故障知识或自动完备依赖图。 |
| 目标代码编辑受活动单元约束 | 同文件 L298–308 | 是仓库协调的重要逻辑，算法三应可见。 |
| 代码变化导致本单元及图中后继检查失效 | 同文件 L370–380 | 写清声明依赖传播，不扩张成自动发现所有调用者。 |
| 计划变化也可能使后继检查失效 | 同文件 L273–292 | 原算法 L120 隐藏此行为，候选予以展开。 |
| 局部检查包含语法及计划中的测试 | 同文件 L383–410 | 保留检查机制，避免写成模糊 status。 |
| 会话重建复用此前真正读到且仍未改变的代码 | 同文件 L107–144、L556–559 | `CurrentReadCode` 应改成先前有效读记录，不新增自动读取。 |
| 单元切换安排上下文重建 | 同文件 L246–255、L446–448 | 不等于重新启动 Verifier。 |
| 重建保留角色、计划、发现、测量与预算语义 | 同文件 L496–574 | 状态位和档案实现可放附录，科学机制保留主文。 |

### 7.2 主代理需要核对或裁定的具体点

**当前主方法与所附冻结实现的对应。** README 指出不同研究使用不同配置。主代理应核对当前 slim-v4 中与本报告候选有关的阶段完成、测试要求和交接行为。这里不建议增加论文免责声明，也不建议重跑实验；只需查当前实现或既有映射记录。

**阶段耗尽后的验收调用。** 算法二 L87 无条件位于内部循环后，而提供的 `_stage` 可以因预算、格式或 API 错误退出。主控是否在这些情况下评估当前候选，没有直接证据。候选暂保留原算法结构，最终以主控逻辑为准。

**初译是一次还是多次 LLM 调用。** 算法三可以显式标为 `LLMTranslate`，但没有证据支持将翻译抽象强制替换为一次 `LLMCall`，也没有证据支持把初译加入 \(B\) 所定义的共享调查与修复额度。

**局部检查点通过条件。** 提供的 `_checkpoint` 到 L410 为止，后续如何最终设置单元状态未展示。`focus_unit` 确实要求前置单元状态为 `checked`，因此“valid local checks”候选合理；最终若写得更细，应核对状态赋值代码。

**上下文重建的触发范围。** 原算法只列交接、切换和容量；实现还允许初始阶段、生成和主控边界。建议主文抽象为“待处理的重建请求或容量条件”，附录列出实现触发，不在主文堆所有字段。

## 八、图表、生成器与资产同步位置

| 对象 | 当前引用／来源 | 方案及同步要求 | 本轮状态 |
|---|---|---|---|
| 方法图图注 | `sections/methods.tex:9` | 后端采集说明移附录；其余角色与信息流保留 | 仅提出方案 |
| 方法图 PDF | `figures/hierarchical_feedback_architecture.pdf`，由 L8 引入 | 本轮无图内内容证据，不认定需要修改资产 | 未读取、未修改 |
| 用户维护的 PowerPoint、SVG、PNG | README 说明存在，未提供具体路径 | 遵守 P04，交由用户维护；不猜测文件名 | 未读取、未修改 |
| 方法图历史脚本 | README 点名 `make_overview.mjs`、`make_slim_v4_overview.py`、`update_overview_labels.py` | README 明确本轮内容修订不运行这些脚本；不能将它们自动认定为用户当前资产的权威生成源 | 未运行 |
| 三个算法 | `sections/methods.tex:33–133` | 在同一源文件中同步函数名、调用、符号定义和正文交叉引用 | 仅提出方案 |
| 附录后端说明 | 目标为 `sections/supplementary_experiments.tex` 的相关执行协议 | 确切插入行未提供，主代理定位后合并已有说明 | 未审改附录 |

算法调整不涉及定量表格或实验图生成器。不得因修改算法名字顺带重新生成结果图表。

## 九、范围内的最新意见落实判断

- 四类 discrepancy：正文解释保留；算法一 L39–43 删除候选已给出。
- 三个算法的 LLM 调用：算法一 `LLMCall`、算法三 `LLMTranslate` 显式标出；算法二通过共享 `AgentStep` 复用。
- 仓库整体协调：算法三候选包含首次仓库评估、一次独立调查、持续修复、依赖计划、局部检查失效及上下文恢复。
- 后端移附录：方法图图注中的执行适配器说明列为移动项。TorchAX 的具体句子不在分配源码中，交其他章节审查整合。
- 不虚构修复次数：算法二保留预算上限及接受后提前返回，没有固定“四次修复”循环。
- 实验中的 `1/2/4`、`3/12`、`4/12`、`31/18`、健康控制和十份初译等句子不在本节，未越界审查，也未将旧清单状态当成本轮核验结果。
- 两个正式模块名完整保留。方法组件仍在消融之前定义。
- 未提出收缩贡献、添加重复免责声明或扩大实验的方案。

## 十、最重要发现与主代理裁定清单

1. **算法一重复正文四类 discrepancy 是明确应删项。** 删除 L39–43 后保留正文定义、公式和训练依赖解释，算法集中呈现 LLM 调查与工具循环。对应 S13、M10。

2. **算法二的 `tested` 应明确为“最后一次编辑后已执行测试”。** 这是源码支持的真实行为，也是本轮最具体的算法语义修正。是否在预算或错误退出后仍执行外部验收，需要主代理核对主控。对应 M10、W07。

3. **算法三需要显现仓库协调，但不能增加逐单元诊断循环。** 建议保留算法一和二的直接复用，通过共享上下文操作展开计划、活动单元、失效传播和会话重建。对应 M11、M13、S13。

4. **正文少数内部词应换成实际动作。** `current checkpoints`、`current status`、`carries` 和 `CurrentReadCode` 分别改为有效局部检查、具体检查结果、保存证据，以及此前读取且仍有效的代码观测。两个正式模块名保持不变。对应 W03、W06、M14。

5. **后端说明移动与用户方法图维护存在边界。** 图注最后一句可移附录；图内标签未提供且由用户维护，主代理应裁定是否仅调整图注或另向用户汇总图内同步需求。本轮不修改资产。对应 E10、M05、P04、S13。

6. **最终方案须核对实现版本映射，不能把历史片段当成当前全实现。** 需确认的仅是阶段结束后验收、初译调用及预算关系、局部检查状态和重建触发；不需要重跑实验，也不应据此在方法正文增加防御性限制。对应 W02、W07、B07。
