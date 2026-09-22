# 对既有反馈的复查

已阅读对话《修改论文摘要与引言结构》（01a0c294-56ce-7e93-974f-b59c2894a965）的全部四轮记录，包括每轮中的追加意见。对照材料为当前 6 Pro 修改稿、本轮最初的重做方案、6 Pro 修改前的稿件及此前执行记录。本轮只更新方案和本复查文档，论文源文件保持原状。

## 复查结论

用户指出的部分问题确实重现了。两处尤其明确：此前已撤回的 JAX 成本降调要求重新进入了我的方案，用户曾质疑的“未测量量保持缺失”又被写进 Preliminary 的计划。当前稿件还存在组件名替代机制解释、短句罗列过程、主实验连续报数字的问题。

这些问题需要在段落安排与论证中修正。保留用户已经确认的效果、效率和跨框架结论，把核实后的事实用于解释方法及结果。

## 逐项对照

| 此前明确意见 | 本次复查发现 | 已修正的方案 |
|---|---|---|
| 禁止因为尚未出现的问题贬低方法、收缩 claim | 此前对话已明确撤回“JAX 中 Direct 成本更低”的附加降调句。我又在重做方案的摘要依据中写入相同提醒。当前 JAX 正文本身没有该附加句。 | 删除方案里的这一写作要求。JAX 表准确列出成本，正文解释同一方法在 JAX 上的修复与验证，保留跨框架有效性结论。 |
| “leaving unmeasured quantities missing” 为什么要加 | 重做方案 3.1 出现“执行中断后未得到的量记为未测量”。它打断任务与差异的定义。 | 从 Preliminary 的安排中删除。n/a 的实际含义随对应表格或评估口径说明一次。 |
| 没必要就不新造术语，已有术语必须一致 | 当前稿件从摘要、引言到结论反复使用三个大写组件名，方法开头又引入 LD、IEH、DCM。我原方案主要处理缩写，对名称堆积处理不足。 | 首次解释机制，简短名称用于后文指代。摘要和结论用具体动作推进，不逐个报组件名。角色统一为 Translator、Verifier Agent、Repair Agent、Orchestrator。 |
| 少用冒号、分号和密集连字符，逗号列举读起来零碎 | 当前方法概览连续按角色报动作；实验中仍有分号连接，如推荐仓库与检测图注；结论用组件名串联。 | 按一次完整调查或一个结果现象组织句子。条件、原因和后果用自然从句连接，专业术语保留必要拼写。 |
| 不要很多等长短段，允许段落充分展开 | 6 Pro 版将原有解释压缩，主实验有“总节省—两组比例—27/29”的连续报数，机制解释随之变薄。 | 恢复段落内的解释：先说同等迁移效果下的成本优势，再解释错误程序修复与正确程序确认这两个环节，数字和图表支持该判断。 |
| 主实验不要复述表格，找出方法优势 | 主比较仍保留 `MatchFixAgent reaches full acceptance in its first external submission...`，先突出基线的外部提交次数，随后才比较调用量。 | 主文以完整迁移成本和模型调用为比较对象，1、2、4 次预算下的 LaDiM 结果仍按实测呈现。MatchFixAgent 的内部提交过程放附录。 |
| 构造细节和内部记账移到附录 | 当前自然故障 caption 使用 `selected complete runs`。重做方案的 Preliminary 又计划放入较多观测状态细节。 | 正文说明实验对象、方法和成本范围。运行选择、历史中断和输入复用的记录放来源文档或相应附录。 |
| 结论参考 MOST：We introduced → Specifically → 设计作用 → 整体能力 | 6 Pro 结论虽保留开头，后面改成组件名列表，弱化了此前已确认的机制说明和设计作用。 | 恢复此前已确认的连贯结论段落，不重复精确接受率或 token 比例。 |
| 创新组件应在方法中展开，伪代码要像代码 | 我的第一份方案仍用了较多 `context.BeforeCall` 等接口，核心调查逻辑的显式程度需要提高。 | 三份算法分别突出“差异输入和调查动作”“证据交接和候选修改”“依赖状态和上下文更新”。通用管理接口归入仓库算法，前两份聚焦核心过程。算法定稿逐项核对候选更新、预算扣减及退出路径。 |

此前意见中已经落实的内容也核查了。主文未重新出现 `task contract` 或 `Controller`，相关工作仍在引言之后，torch4ms 和 TorchAX 接入细节保留在附录，主表没有恢复 Pass/Failed 状态列。这些安排继续保留。Figure 3 采用用户选择的简洁柱状图，图内放图例、caption 解释数据，方法总览图继续暂缓修改。

关于 29 个输入，主图逐输入成本的分组需要说明柱子对应什么。任务编号与源文件之间的复用映射放附录，图注给出读图所需的分组说明即可。

## 对“避免过度防御”的落实

写作以研究判断及其证据为中心。已经支持的结论直接表达，方法解释具体动作，结果分析解释观察到的现象。像“损失和梯度相同，后续更新与表示仍出现差异”这样的真实结果，直接服务于本文的训练语义问题，可以放在对应分析中。

审查阶段核实实现、费用和数据来源，交付到正文的是核实后的表述。历史运行中断、来源选择、检查状态以及无法用于当前比较的旧记录集中留在执行文档。成本和分母的定义在评估设置或表注交代，不在每个结论后再次重复。

语言修改保留作者的研究立场。删掉空泛句之后，需要补回的是机制和解释，而不是给每个判断再加一条限制。必要条件直接进入对应结论，例如写明在 JAX 的六个候选和三个验证种子上取得的结果，接着解释同一修复流程怎样应用到这个框架。

## 逐句复查：删除论文中没有作用的执行说明

这一轮同时检查了旧底稿、当前 6 Pro 版及附录。重写以旧底稿起步时，下列已确认的冗余也一并清理。论文正文保留问题定义、方法机制及结果分析，附录保留复现和理解实验所需的细节。没有提供新信息的句子直接删除。

### 已明确要求删除的表达

| 表达 | 查到的位置 | 处理 |
|---|---|---|
| `They are not supplied as task inputs.` | 旧底稿 `conference_101719.tex:104` | 直接删除。前文说明 Verifier 怎样调查并得出位置即可。 |
| `A supplied translation can enter directly at the investigation stage.` | 旧底稿 `conference_101719.tex:91` | 按此前明确要求删除。 |
| `and its loss initially agrees with the source` | 旧底稿摘要 `conference_101719.tex:40` | 删除该摘要片段。训练依赖的具体例子在引言和分析实验中说明。 |
| `leaving unmeasured quantities missing` 及“执行中断后未得到的量记为未测量” | 前者来自用户指出的早期稿件，后者曾进入本轮第一份方案 | 方法正文删除这一说明。表中实际 n/a 的含义在表注或评估设置说明一次。 |
| `Section ... specifies the measurements and tolerances for each study.` | 当前 `sections/methods.tex:27` | 方法中的差异定义完整写清。数值设置在 Evaluation protocol 给出，删去方法段末这一转交说明。 |

旧底稿指 `output/paper-6pro-revision-20260921/before/` 下的文件。其行号与当前工作区源码不同。

### 本轮新增的删除项

| 原句 | 位置 | 原因和处理 |
|---|---|---|
| `Addressing this problem requires detecting changes in training behavior and identifying the computations responsible for them.` | 当前摘要 `conference_101719.tex:43` | 重复问题和解决目标，直接用 `To address this problem, we propose LaDiM ...` 进入方法。 |
| `This separation makes the initial diagnosis an explicit input to repair and allows the effect of independent evidence handoff to be compared with investigation and editing in one conversation.` | 旧底稿 `conference_101719.tex:108` | 前半重复交接定义，后半解释实验怎么设置。删去该尾句，在消融小节直接定义比较条件。 |
| `Progress reminders report the remaining allowance.` | 旧底稿 `conference_101719.tex:110` | 从方法正文删除。涉及移除提醒的消融时，在其配置说明中介绍一次。 |
| `Repository events can suspend and resume this state.` | 当前 `sections/methods.tex:55` | 泛泛描述运行时控制，没有解释科学机制，直接删除。 |
| `Other continuation retains the conversation.` | 当前 `sections/methods.tex:84` | 正文已解释修复历史保留及重建时机，删除重复补句。 |
| `Supplied-candidate studies retain their respective protocols.` | 当前 `sections/experiments.tex:19` | 没有说明任何具体协议，删除。必要区别在各研究的设置中直接写清。 |
| `These costs cover investigation and repair across the complete repository.` | 当前 `sections/experiments.tex:60` | 与成本设置重复，删除结果段末的补充声明。 |
| `These observations describe repair of supplied target candidates through JAX.` | 当前附录 `sections/supplementary_experiments.tex:24` | 重述本段已经说明的实验对象，直接删除。 |
| `The corresponding agent and tool backend configurations are documented with the frozen sources and results.` | 当前附录 `sections/supplementary_experiments.tex:77` | 属于内部材料存放说明，移出论文，在来源文档提供具体位置。 |
| `This trajectory belongs to the same LaDiM configuration as the natural fault table.` | 当前附录 `sections/supplementary_experiments.tex:86` | 属于案例与数据一致性的核查结论，留在执行记录，论文删除。 |
| `None of these operations resets accumulated usage.` | 当前附录 `sections/supplementary_experiments.tex:122` | 总预算口径已统一定义，删除此处重复声明。 |

### 压缩为方法含义的内容

`Production files remain read-only.` 和 `Scope and syntax checks guard each edit.` 目前使段落转向工具权限和执行校验。正文通过 Verifier 调查、Repair Agent 修改的分工解释过程，伪代码中的权限约束表示一次。语法校验如需用于复现工具设置，在实现说明集中交代。

仓库章节保留“修改共享实现会影响依赖它的单元，因此需要使相应检查点失效”和“切换文件后仍能使用相关证据”这两个机制。档案放在可编辑目录之外、JSON pointer、字符区间、文件哈希等具体接口与存储约定从方法正文移出。实现文档保存全部细节，附录按复现所需选取。

`selected complete runs`、`complete usage records` 等运行筛选及账本措辞从正文图注移出。图注说明研究对象、统计阶段和读表方式，来源文档保留所用运行及费用核查记录。

自然故障段首仍需按用户要求定义表头。将目前逐个念出四个列名的句子改为解释“修复初始错误程序”和“保留初始正确程序”分别统计什么，再据此分析 LaDiM 的修复与保留结果。

### 候选段落的实际语气

例如，调查过程可以这样组织：

> When a target parameter has no gradient, the Verifier Agent inspects its registration and traces the operations connecting it to the loss. A focused test helps distinguish an unregistered parameter from a disconnected computation. The agent passes the supporting code observations and test results to the Repair Agent, which uses this evidence to select a correction.

这段完成“出现什么问题、怎样调查、证据怎样用于修改”的解释，到此结束。后续段落接着讨论修改后的新测量，形成连续的研究叙述。

## 更新范围

已直接修改 `docs/paper-rebuild-plan-20260922.md` 中的摘要、方法、实验分析和结论安排，加入方法概览、主实验、JAX 与结论的英文候选段落，用于确认实际语气。上一份方案保存在 `output/paper-rebuild-20260922/plan-before-style-review.md`。

论文正文、正式图表及其数据本轮均未修改。新增组件消融由子 agent 继续执行，独立交付运行结果。
