# 论文重做方案：先确认论证，再修改正文

本方案以 `output/paper-6pro-revision-20260921/before/` 中的稿件为写作基线，综合本任务中的修改意见，并重新核对了对话《修改论文摘要与引言结构》（01a0c294-56ce-7e93-974f-b59c2894a965）的全部四轮记录及其中的追加意见。正式重写从该快照开始，保留已核对正确的数据处理、引用和表格格式。逐项复查结果见 `docs/paper-style-review-20260922.md`。

当前阶段只提交方案。本轮尚未审阅的正文改动已另存为 `output/paper-rebuild-20260922/unreviewed-draft/`，工作区四份正文文件已恢复到本轮开始时的内容。累计组件消融单独运行，结果暂不写入论文。

## 1. 先把论文的论证链固定下来

论文要回答的问题是：**怎样利用训练计算之间的依赖关系，找到迁移程序中的语义差异，并以较少的调查和修复成本恢复正确行为？**

论证按下面的顺序展开。

1. **问题来自训练语义。** 迁移程序在成功执行的同时仍可能计算出错误梯度或参数更新。前向计算、求导和优化器更新相互依赖，后续步骤又依赖更新后的状态。引言用这些具体关系解释问题。
2. **第一项设计是 layered diagnosis。** Verifier Agent 综合执行、前向值、梯度和更新差异，选择值得检查的代码和测试。例如，前向值一致但梯度缺失时，检查参数注册及参数到损失的求导路径。
3. **第二项设计是 independent evidence handoff。** 独立调查得到的代码观察、测试结果和假设进入另一个 Repair Agent 会话。修复之后重新测量，新的差异继续指导后续尝试。
4. **仓库规模引出 repository context management。** 多文件共享接口会让局部修改影响其他入口；调查跨文件推进时又要保留有效证据。因此跟踪工作单元依赖、检查点及代码版本，并在切换上下文时保留和检索相关记录。
5. **实验依次检验结果、观测和组件。** 主比较回答迁移结果与总成本；自然错误案例解释调查和修复过程；检测实验及信号消融解释为什么需要各类训练观测；组件消融检验逐项加入代理组件后的表现；JAX 与跨语言任务提供适用范围证据。

训练计算内部的依赖支持诊断，仓库文件及接口的依赖支持跨文件协调。每一项设计先说明它遇到的具体问题，再解释如何处理，随后衔接相应实验。

## 2. 摘要和引言怎么改

### 摘要

保留旧版本的研究对象和有依据的结论，重排为“迁移问题 → 解决思路 → 角色和组件 → 实验结论”。

- 删除 `and its loss initially agrees with the source`。同样删除当前摘要中 `Addressing this problem requires ...` 这一重复目标的铺垫句，直接用 `To address this problem, we propose LaDiM ...` 引出方法。
- 将角色嵌入一次完整的调查和修复过程：初始翻译交给 Verifier Agent，检查得到的证据进入独立 Repair Agent，提交后由 Orchestrator 返回新观测。用动作和信息传递衔接句子。
- 仓库组件使用普通的描述性名称 `repository context management`，在 3.4 解释工作单元依赖与相关证据如何随修复保留和更新。摘要优先说明它使跨文件调查持续推进的作用。
- 将跨框架、跨语言实验组织成一个总体结论。MindSpore 与 Java→Python 的实测比较支撑相对 MatchFixAgent 的效果和效率优势，JAX 实验支撑同一方法在另一框架上的应用。摘要保留已确认的跨框架与跨语言有效性结论，关键比例直接附着于对应比较。

Layered Diagnosis 和 Evidence Handoff 分别对应调查与证据交接，repository context management 对应仓库上下文管理，在相应方法小节先解释机制。摘要与结论用具体动作展开方法，简短名称负责后文指代；LD、IEH、DCM 删除。

### 引言

从旧版引言保留“训练语义差异 → 利用计算依赖调查 → 证据指导修复”的主线。一个段落完整讲清一个问题及其对应设计，句子通过原因、动作和结果衔接，段落长短由内容决定。介绍仓库需求时，先说明共享实现、多入口和跨文件调查的问题，再介绍相应管理机制。相关工作继续紧接引言。

Figure 1 只保留三个方法的实测横向 token 柱状图，放在引言右侧并使用文字环绕。横轴为完整 token 用量，方法旁标接受数量，数据为 LaDiM 5.159M／50，MatchFixAgent 12.097M／50，SWE-agent 20.831M／44；分母均为 50。caption 说明成本包含共同初始翻译和全部后续调用。删除文字框组成的左图。

引言用这张图展示调查和修复成本上的差异。梯度／更新检测轨迹移到 4.3 对应实验；目前已有记录支持总 token 比较，图中不加入各方法首次检测 token 或基线检测步数。

## 3. Methods 的结构和符号

章标题为 `Methods`，四节固定为：

| 小节 | 标题 | 这一节完成的工作 |
|---|---|---|
| 3.1 | Preliminary | 定义任务、edit、训练差异、代理角色和共享状态 |
| 3.2 | Verifier Agent: Layered Diagnosis | 用 3.1 的差异解释 Verifier 如何选择调查，再给调查伪代码 |
| 3.3 | Repair Agent: Evidence Handoff | 定义交接、编辑、再验证和持续修复，调用 3.2 的调查过程 |
| 3.4 | Repository Coordination | 将同一调查和修复过程用于仓库，补充依赖及上下文事件 |

### 3.1：定义后文真正要用的量

任务用源程序、源／目标语言与框架、允许修改的文件范围定义。一次 edit 是一次成功应用的编辑工具操作，可以含多个文件中的块替换；一次 submission 可以包含多次 edit、阅读和测试。两者在预算和算法中保持区别。删除旧版 `A supplied translation can enter directly at the investigation stage.`，并将实验输入、初始状态及采集规则放入 Evaluation protocol。

随后定义四类差异，直接对应 3.2：

\[
\begin{aligned}
d_{\mathrm{execution},t}&=\mathbf 1[e_t\not\sim\hat e_t],\\
d_{\mathrm{forward},t}&=v_t-\hat v_t,\\
d_{\mathrm{gradient},t}&=g_t-\hat g_t,\\
d_{\mathrm{update},t}&=(\theta_{t+1}-\theta_t)-(\hat\theta_{t+1}-\hat\theta_t).
\end{aligned}
\]

其中前向值包含选定输出和损失，梯度及更新按源、目标映射对齐。执行差异表示未满足所要求的对应执行结果。形状、梯度是否存在等检查放入 Evaluation protocol，与实际采集规则一起说明。

`d ≃ 0` 表示差异满足该比较规定的容差，例如逐元素绝对／相对容差或规定的范数界。这里定义的是诊断使用的量和依赖关系。各数据集究竟采集哪些量、使用什么范数和阈值、如何同步状态，在 4.1 Evaluation protocol 中给出。检测图中的梯度范数差等标量摘要仍按其原有实验定义报告。

删除目前独立摆放、后文没有直接使用的 `d_element`、`d_vector`、`d_relative`。3.2 使用上述四类差异名称，方法推理不依赖读者先去第四章查阈值。

最后用符号定义 Translator、Verifier Agent、Repair Agent 和 Orchestrator，沿初始翻译、调查、交接和修复的过程说明职责。公式中定义的量必须在 3.2 或算法中实际使用。算法需要的候选、观测、证据、会话和预算随其输入一并介绍。

### 3.2：从差异到调查动作

将旧版两段组织为一个连续的解释段，四种 discrepancy 用加粗短标签放在段内。

| 观测 | Verifier 的调查方向 | 应记录的证据 |
|---|---|---|
| Execution discrepancy | 检查异常、调用位置和相关实现，构造最小复现 | 异常、调用路径、复现结果 |
| Forward discrepancy | 追踪产生不同值的算子，并检查下游差异是否随之出现 | 对应输入输出、代码位置、测试结果 |
| Gradient discrepancy，且前向值一致 | 检查参数注册、可训练状态和求导路径 | 缺失或不同的梯度、连接关系、区分假设的测试 |
| Update discrepancy，且前向值与梯度一致 | 检查优化器规则、状态和实际参数变化 | 更新前后参数、优化器设置、局部验证 |

Verifier 根据这些依赖关系和当前证据自主选择代码阅读与测试。算法显式传入差异，展示工具调用、结果记录、分支和终止条件，正文解释不同观测如何引出相应调查。旧版 `They are not supplied as task inputs.` 直接删除，调查过程写到证据及其用途即可。

### 3.3：让证据交接和反馈闭环成为主线

先交代 Repair Agent 如何使用 Verifier 的实际观察、测试和结论选择修改，接着解释 Orchestrator 重新评估候选，以及新观测如何指导下一轮修复。删除旧版“这一分离允许比较独立交接效果”的段末说明，并删除进度提醒、暂停与恢复状态等运行过程句。

修复段落围绕“上一轮改动产生了什么新观测，下一轮怎样继续”展开。候选和调查历史使 Repair Agent 能比较修改前后的行为，所有调用累计计入任务预算。公共检查与确认检查的具体安排集中到 Evaluation protocol。

### 3.4：解释跨文件修复怎样继续

保留旧版关于文件依赖和证据档案的有效解释，标题缩短为 `Repository Coordination`。正文从共享实现的修改会影响多个调用入口讲起，接着解释依赖检查点如何引导工作，再说明相关证据怎样在切换文件后继续使用。

正文解释实际单元切换、角色交接和容量边界为何需要整理上下文，以及代码修改后为何重新检查受影响单元。三份算法呈现触发条件及状态更新。代码哈希、缓存资格、容量数值和计划版本处理等实现细节进入附录。

方法总览图及其可编辑源文件继续保留，本轮不重画。

## 4. 三份伪代码到底怎么写

参考 MatchFixAgent 三份算法在“输入输出、赋值、函数调用、循环、分支、返回值”上的组织方式，保留 LaDiM 自己的真实过程。每行写计算或控制动作，机制解释放正文。以下是待落实的函数结构。

### Algorithm 1：Investigate

输入任务、候选及其观测、调查额度和上下文管理接口；输出带来源的调查证据。

```text
Investigate(task, state, context):
    history ← StartVerifier(task, state.candidate, state.measurements)
    evidence ← []
    while DiagnosisBudgetLeft(state.budget):
        history ← context.BeforeCall(history, state)
        action ← Verifier.Next(history, state.budget)
        if action.type = FINAL:
            return Append(evidence, action.report)
        for call in action.tool_calls:
            result ← Execute(call, production_read_only = true)
            history ← Append(history, call, result)
            evidence ← Append(evidence, call, result)
            context.Record(call, result, state)
    return evidence
```

`Next` 代表一次真实 LLM 调用并计入共享额度；工具输出和模型报告都有明确去向。Scratch tests 可编辑，生产文件只读。具体调查动作由 3.2 的正文及其输入观测解释。

### Algorithm 2：Repair

输入任务、初始候选、共享预算和上下文管理接口；输出当前候选及完整验收结果。

```text
Repair(task, state, context):
    measurements, status ← Evaluate(state.candidate)
    if status = ACCEPTED:
        return state.candidate, status
    evidence ← Investigate(task, state, context)
    history ← StartRepair(task, AttributeToVerifier(evidence))
    context.OnHandoff(history, state)
    while SubmissionBudgetLeft(state.budget):
        stage_budget ← AllocateRepairStage(state.budget)
        while WithinLimits(stage_budget, state.budget):
            history ← context.BeforeCall(history, state)
            action ← RepairAgent.Next(history, state.budget)
            if action.type = FINAL:
                break
            for call in action.tool_calls:
                result ← Execute(call, editable_files = task.scope)
                history ← Append(history, call, result)
                context.Record(call, result, state)
        measurements, status ← Evaluate(state.candidate)
        history ← Append(history, measurements)
        ChargeSubmission(state.budget)
        if status = ACCEPTED:
            return state.candidate, status
    return state.candidate, status
```

算法定稿时对照真实调用轨迹检查循环退出、预算扣减、候选更新和初始验证路径。核查结果记录在执行文档，正文算法保留读者理解方法所需的控制流程。

### Algorithm 3：RepositoryRepair

外层调用 Algorithm 2；内部定义它使用的仓库上下文管理函数。这样 Algorithm 3 包含 Algorithm 2，Algorithm 2 调用 Algorithm 1。

```text
RepositoryRepair(task, candidate, budget):
    state ← Initialize(candidate, budget)
    context ← RepositoryContext(RepositoryMap(task))
    return Repair(task, state, context)

RepositoryContext.Record(call, result, state):
    Archive(call, result)
    if CodeChanged(result):
        MarkOldMeasurementsHistorical()
        InvalidateCheckpoints(ChangedFiles(result), dependent_units = true)
    if PlanChanged(result):
        UpdateDependencyPlan(result)
    UpdateActiveUnitAndCheckpoints(call, result)

RepositoryContext.BeforeCall(history, state):
    if RoleHandoff() or ActualUnitSwitch() or AtContextBoundary(history):
        code ← PreviouslyReadCodeWithMatchingHashes(state.candidate)
        return RebuildContext(plan, findings, measurements, code)
    return history
```

工作单元规划、选择和检查点由代理通过工具执行，事件处理负责更新依赖和证据状态。以上是用于核对数据流的接口草图。正式三份算法分别突出差异与调查、证据与修改、仓库依赖与上下文；`BeforeCall` 等运行时接口整理到第三份算法，前两份保持核心过程清楚。

## 5. 实验章节怎么组织

### 4.1 Experimental Setup

只保留两个加粗段落标签：`Tasks.` 和 `Evaluation protocol.`，不再使用编号小标题。

`Tasks.` 先交代主要迁移任务与公开来源，再用一个表格列本论文正文实际分析的自建程序集合：

| 行名 | 数量 | 模型／程序覆盖 | 源程序平均非空行数 |
|---|---:|---|---:|
| PyTorch to MindSpore migration | 50 | Operators、CNN、MLP、Transformer、language model 等 | 24.0 |
| Natural translation faults | 10 | 含 5 个初始错误与 5 个初始正确程序 | 16.7 |
| Training-signal ablation | 16 | 4 类模型 × 4 类训练错误 | 24.0 |
| JAX repair | 6 | MLP 和 CNN | 27.0 |

平均长度按不同源程序计数，具体去重和任务映射在附录交代。Java/DJL 的 18 个公开程序平均 221.2 行；时间序列和推荐仓库分别为 13／24 个代码文件或 notebook，合计 865／2,086 行，在正文用来源引用和一句统计说明。

删除任务表中的 `Detection trajectories`：24 来自 4 模型 × 3 种子 × 2 类错误的轨迹数量，不是 24 个迁移任务。检测设置在对应实验中说明。

删除任务表中的 `Controlled MindSpore repair`：它来自已有的另一组 50 个注入错误修复记录，验收口径与主比较的 50 个迁移任务不同。保留原有附录中的来源和结果说明，正文不将它重新包装为一个新数据集。12 个源／目标修复任务也保留在原附录中。

`Evaluation protocol.` 汇总共同输入和初始参数、观测采集、状态同步方式、数值比较和容差、预算及 token 口径。说明程序的两步、仓库的三步及固定种子；检测实验的 50 步和同步方式在其研究描述中明确。定义主表中的 `Behavior checks passed`：已声明的数值、执行及源行为检查通过数；时间序列为 69 项，推荐为 145 项，原始测试单列。

### 4.2 Main Results

使用三个加粗段落标签组织 MindSpore、跨语言和仓库结果。每段首先给出现象，再解释差异来自什么工作，选少数数字支持；完整数值留表中。

- 主表保留已经核对正确的引用、列顺序与强调。a／b 的 Accepted 放最右，CodeTransEngine 显示方法名并引用，direct 配置放协议说明。MSAdapter 无模型调用的成本用横杠，c 强调最低 repair calls，d 强调最高检查通过数。保留输入和输出 token、梯度、参数更新、入口或原测试这些已有指标，以数量呈现结果，表中不恢复 Pass/Failed 状态列。
- Figure 3 沿用你已选择的简洁柱状图方案，展示总量和同输入成本差额。图例放图内，分组与排序说明放 caption。正文以“同等接受结果下节省超过一半 token”为中心，继续分析节省发生在错误程序修复及正确程序确认两个环节。实测 1、2、4 次提交结果交代在同一论证中。
- MatchFixAgent 首次外部提交达到完整接受的过程细节移入附录。主文结合完整调用数与 token 分析整个迁移过程的成本。
- 推荐仓库围绕同一现象展开：损失和梯度已经一致，更新与后续表示仍暴露差异。用必要数字解释这一现象与引言的训练状态问题之间的关系。

### 4.3 Analysis Experiments

保留三项科学问题，各自只有一个小节：

1. `Repairing Natural Translation Faults`：首段定义修复初始错误程序和保留初始正确程序这两个统计对象，随结果解释最终接受数与成本。案例按实际三次提交叙述，说明新的测量怎样引出下一项调查。图注说明对象与成本阶段，运行选择和案例来源核查留在来源记录。
2. `Training Signals and Detection Latency`：在此放原检测轨迹图，说明直接检查在 12 次运行中均为第 1 步检测；均值损失曲线的 31／18 步与个别运行的 3/12、4/12 分开解释。
3. `Generalization Across Frameworks`：恢复 JAX 结果表并保留标题。表中准确列出两种方法的 6/6 结果、调用数与成本，正文解释 JAX 通过相同训练观测和修复过程完成验证。保留已经确认的跨框架有效性结论。

### 4.4 Ablation Studies

第一段直接交代实验对象。`Training signals.` 说明 4 类模型 × 4 类错误，共 16 个固定候选；四行逐项累加，最后一行为完整信号。正文定义“初始未检出错误”和“最终接受”，caption 明确累加关系和三种子完整验证。

`Agent components.` 加入正在执行的四档累计消融。旧的逐项移除研究保留在附录，不改写成累计实验。新的正文分析按实际测量决定，组件增加后表现是否单调改善也由结果说明。

## 6. 行文与结论的具体写法

论文内容按其作用取舍。正文解释问题、机制和实验结果，附录补充理解和复现实验所需的信息，执行文档保存运行及核查记录。直接删去重复说明与无信息的尾句。此次逐句删除清单见 `docs/paper-style-review-20260922.md`，同时覆盖旧底稿和当前稿件。

段落按推理组织。读者先知道这一段的判断，随后理解依据、机制及其结果。涉及同一个过程的句子接续展开，细节较多时允许长段，短段只承担独立内容。角色、工具和状态随过程引入，首次定义时列清技术对象，后文使用已建立的指代。

冒号、分号和临时拼接的连字符修饰语改成自然的条件或因果关系。公式、伪代码和用户要求的加粗段落标签按各自用途保留。方法名称用来指代已经解释的设计，创新点通过问题和机制展开。

审查先在来源记录中核实数字、协议及实现，再将确定的内容写成正面论述。成本定义集中说明，真实结果留在相应表格和分析中，历史开发记账保存在执行文档。对已经确认的效果与跨框架结论沿用其表达力度。

以下候选段落用于确认语气和论证方式，尚未写入论文。

**方法概览的写法。**

> LaDiM uses dependencies between training computations to guide the investigation of a translated program. Starting from the Translator's candidate, the Verifier Agent examines the observed discrepancies and tests the code that could explain them. Its findings and supporting observations pass to a separate Repair Agent, which uses this evidence to select and evaluate changes. The Orchestrator returns measurements after each submission, allowing the repair process to follow the errors revealed as execution progresses. For repositories, dependency tracking and retained evidence support this process across shared implementations and multiple entry points.

**主实验的写法。**

> LaDiM completes all 50 MindSpore migrations with less than half the total tokens used by MatchFixAgent. The savings extend to both faulty translations and programs that are already correct. On the former, LaDiM uses the observed training discrepancies to investigate the code and guide corrective edits. On the latter, investigation and confirmation establish acceptance without corrective changes. The cost reductions in both groups show that the efficiency advantage covers these two parts of the migration process.

这段之后再用成本分解和逐输入图解释分布，具体组别节省量保留在图表中。相关机制按实际调查轨迹展开。

**JAX 段落的写法。**

> LaDiM repairs all six JAX candidates within the first submission and satisfies verification on three seeds. The JAX adapter supplies the corresponding training observations, allowing the same investigation and repair procedure to operate with another target framework. These results demonstrate LaDiM's effectiveness across frameworks.

**结论恢复此前已确认的 MOST 推进方式。**

> We introduced LaDiM, a multi-agent framework for migrating deep learning code while preserving training behavior. Specifically, LaDiM uses dependencies between training computations to guide diagnosis and passes the resulting evidence to a separate Repair Agent. Verification after each submission guides subsequent changes, and dependency tracking with evidence retrieval supports repair across files. This design helps detect and repair semantic errors that remain hidden when evaluation checks only execution or loss. Experiments across frameworks and programming languages demonstrate LaDiM's effectiveness in preserving training behavior and its efficiency in diagnosis and repair.

结论保持一个连贯段落，依次说明目标、设计、设计作用和实验支持的整体能力。具体接受数与 token 比例留在结果章节。

## 7. 新增消融的已执行设计

子 agent 已接管运行。正式调度已启动，最多 3 个进程并行，共 8 次新运行：2 个原有仓库 × 4 个条件，每个组合执行一次。

| 条件 | 独立只读调查阶段 | 独立证据交接 | 仓库依赖及上下文管理 |
|---|---|---|---|
| 基础 Repair Agent | — | — | — |
| + Verifier investigation | 有 | —，继续原会话 | — |
| + Independent evidence handoff | 有 | 有 | — |
| + Repository context management | 有 | 有 | 有，完整方法 |

基础条件保留证据驱动的提示、通用工具、语法检查、原有进度提示和编辑格式行为。第一步新增专门的只读调查阶段，后续两步分别增加独立证据交接与仓库管理。正文围绕这三个流程组件的增量作用分析，已有训练信号消融解释观测覆盖的作用。

四档使用相同源程序、初始候选、完整训练信号、评估输入、初始状态、种子、容差和总预算。每次最多 80 次调用、480,000 输出 token、3,600 秒和 4 次外部提交。启用的调查阶段最多 6 次调用，计入总额。最后一步包含现有仓库工作单元、依赖检查点、证据检索和上下文重建这个完整组件。

报告两个仓库各自的 69／145 项检查通过数、完整验收、模型调用和总 token。完整成本包含共同初始翻译一次以及所有新调查和修复调用；失败调用计入成本，未测量项保留 n/a。旧的主实验结果保持独立，不混入这 8 次新运行。

协议、56 项通过的离线检查、代码与输入冻结记录均已保存。运行结束后由子 agent 汇总 JSON、CSV 和执行报告，先交付可核对结果，再决定正文中的分析句和表格。正文设置说明每个仓库、每种条件各运行一次，表格报告这次统一比较的实测值。

## 8. 后续落实顺序与交付

方案确定后按以下顺序改稿，每一步的修改都能单独核对：

1. 从修改前快照恢复工作底稿，先完成 3.1–3.4 的概念、符号、角色和三份算法，逐项对照真实运行代码。
2. 根据已经明确的方法逻辑修改摘要与引言，让问题、设计和结论对应。
3. 重排 4.1，修正任务统计表，保留已有准确的主表和分析数据。
4. 整合新增消融的实际结果，写结果分析，再处理结论的整体表述。
5. 最后完成 Figure 1 文字环绕、检测图位置、表格位置和整篇排版，不通过随意缩小模板字体压页数。
6. 使用仓库 humanizer 和作者写作 DNA 复核全文，包括标题、图注与表注；运行相关现有数据及布局检查，编译并逐页检查 PDF，核对正文 9 页的版面目标。

届时交付修订稿 PDF、LaTeX／图表源文件，以及记录修改、实验结果和验证范围的执行文档。本轮交付的是这份方案。
