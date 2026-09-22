# 全文逐句审查后的修改方案

2026-09-23。审查基准 `d1d6a53`，分支 `codex/iclr-2027-template`。本轮只审查、形成方案并更新持久意见清单；论文源码、算法、生成脚本、图表、实验结果及 PDF 不做修改。所有章节审查统一使用 `gpt-6-astra`、`high`。本文件由主代理整合，各章节逐句台账保留为独立文档。

## 本次检查标准及对上轮的纠正

上轮把关键词出现、定义存在、数字正确当成了许多条目的充分验收，没有逐句判断大同行能否直接理解对象、动作和结果。四类差异在正文与算法重复、仓库算法隐藏主要动作、TorchAX 放置和初译/消融标签的问题因此被错误标为已落实。本轮将这些条目重开，方案完成与论文落实分别记录。

每句只在它能够解释问题、机制、比较条件或结果时保留。通用词也按语境检查，不能因为 controls、retains、checkpoints 是英文常见词就免于解释。已有正式模块名保留，第一次出现时说明它做什么。实验事实和有证据的贡献力度保持，用明确对象和条件表达真实边界，删除重复防御句。

## 三个算法的修改安排

正文 §3.2 保留四种 discrepancy 与对应调查动作。算法 1 删除重复的四条关系及其引导行，方法段不再把算法里的初始化、列表追加、计数操作重述一遍。

当前 §3.1 已定义 M 是 LLM，算法 1 的 Query(M,...) 是实际模型调用，算法 2 经 AgentStep 复用，算法 3 的 Translate 也使用 M。修改时保留模型符号 M，将实际请求函数写成 LLMCall，共享工具步骤写成 LLMToolStep；普通验证、工具执行和文件检查不冠以 LLM。

| 算法 | 主文保留的过程 | 合并或移出主文的细节 |
|---|---|---|
| 1：Verifier 的调查 | 接收程序和测量；LLM 选择代码检查或测试；执行工具并把结果纳入证据；输出位置、观察和假设 | 删除四类差异复述；合并 E 赋值与返回；将逐个消息/工具结果追加与权限字段收束到共享执行步骤 |
| 2：Repair Agent 的修复 | 独立接收证据；延续修复历史；LLM 调查、修改并测试；提交完整候选；用反馈继续或返回 | 不单列 handoff 布尔开关、F 的初值、UpdateFlags、PendingAction 和提交计数加一；用一个已定义的“修改完成且已测试”判定表达同一条件，预算仍生效 |
| 3：仓库整体协调 | 展示同一仓库上下文如何连接结构分析、依赖规划、相关文件修复、依赖失效与完整仓库验证，并显式调用算法 1、2 | 原 C.Record / C.BeforeCall 的档案追加、临时字段和重建标志移附录；保留科学机制及必要触发条件 |

算法 3 的主线改为：建立仓库上下文与可用工具 → 初次翻译和整个仓库的评估 → 调用算法 1 调查 → 通过同一仓库上下文调用算法 2 修复 → 整个仓库接受或预算结束。算法 1、2 共用的工具执行步骤显式接入算法 3 的仓库操作，使结构分析、依赖规划、工作单元选择、编辑后相关检查失效、局部测试与上下文重建出现在调用链中。

结构扫描和规划仍由 LLM 调用工具触发，不能写成每个仓库必先执行的一次固定扫描。独立 Verifier 仍在修复前运行一次，不能为表现“仓库级”而改成每个工作单元重启一个 Verifier 或重开一套完整修复预算。所有单元使用共同仓库文件、依赖关系、历史与总预算。附录保留具体实现对应，主文只显示解释方法所需的操作。

## 实验文字与图表的统一修改

| 原表达 | 采用的具体处理 |
|---|---|
| TorchAX...is the execution backend... | 从主文 Compared methods 移至附录 A.5 的 JAX 执行协议，保留引用。主文继续定义真正参与表格比较的 Ivy 和 torch2jax。 |
| The main migration comparisons check consecutive training steps. | 删除主文这句。附录 A.2 已明确程序连续两步、仓库三步，保留其具体状态演进与比较方式。 |
| retaining full acceptance at four submissions | 改为直接预算结果：`With submission limits of one, two, and four, LaDiM accepts 46/50, 50/50, and 50/50 tasks, respectively.` 不暗示每个任务都实际执行四次修复。 |
| Individual loss trajectories cross...3/12 and 4/12 | 主文保留最早检测及机制解释；图注明确：`Within 50 training steps, the loss difference exceeds its threshold in 3 of 12 runs with gradient errors and 4 of 12 runs with update errors.` 同处说明四模型×三种子；均值曲线31/18仍单独标清。 |
| while their healthy MLP and CNN controls pass | 改为具体句子：`Both converters pass evaluation on the corresponding MLP and CNN programs without these faults.` 保留其实际作用：转换器能运行正确程序，但不会自动修复输入程序中的错误。 |
| Passes initial checks | 图 3 标签建议 `Passes before repair`，与 `Needs repair` 配合；正文写 `programs that pass evaluation before repair`。任务定义说明这些是第一次翻译得到的程序，不引入另一套分类名。 |
| Ten saved translations | 任务定义写 `ten programs produced by the initial translation, of which five fail evaluation and five pass before repair`。后文使用 `the ten translated programs`；去掉暗示存档来源的 saved。 |
| Independent pairs on time series | 写 `Comparisons with and without each component on the time series repository`。表注保留两个组件各自的完整方法参照来自分别执行的实验这一事实，直接交代为何有两个成本值。 |
| complete reference / final coverage / public evaluation | 分别按语境写明“使用所有组件的 LaDiM”“通过多少项检查”“修复期间可见的评价及后续种子验证”；不机械全局替换或另造缩写。 |

消融表注 (b) 的候选为：`Repair history and evidence handoff on ten translated programs. The parentheses report how many of the five failing programs are repaired. All three settings also pass evaluation on the five programs that pass before repair.` (c) 的候选为：`Comparisons with and without each repository component on the time series repository. Every setting passes all 69 behavior checks across three seeds.`

两项仓库消融的完整方法是分别执行的参照，仍分别报告 1,936,579 和 2,126,900 tokens。用清楚的实验说明替代 independent pairs，不把两个结果合并，不相加 68.0% 与 19.8%。四组件的任务分组、六例 JAX、正文预算、每个底层数值均保持。

图表文字必须与源码生成器同步：图 3 的修复前通过标签、自然修复表、程序消融表及 JAX 表由 `figures/make_unified_results.py` 生成；仓库消融和附录表由 `figures/make_cumulative_components.py` 生成；数据集表标签由 `scripts/summarize_paper_collections.py` 生成；检测图标签由 `figures/make_gradient_drift.py` 生成。修改 caption 时对照实际图的比较量、图例、阈值和分母。

## 逐章节安排

14 份独立审查均已完成。下表是主代理整合后的采用范围；各报告保留逐句的原文、保留理由和英文候选，报告中未列入本方案的建议不自动进入修改范围。报告入口见[审查索引](README.md)。

| 章节 | 修改方向 |
|---|---|
| 摘要 | 8句逐句核对，保留已确认的135词版本。 |
| 引言 | 用具体训练计算替代空泛铺垫；说明初译及修复前通过；明确两项仓库节省的基线对应；贡献与机制对应，保留结果力度。 |
| 相关工作 | 分别对应 DeepXplore/DeepGauge 的作用；明确 LaDiM 调查对象和角色交接；共同输入与成本口径留实验现有定义处。 |
| 方法 | 保留四差异正文、精简三个算法、显式 LLM 请求、贯通仓库流程；解释工作单元实际由哪些文件构成。 |
| 实验 | 按上表统一对象与条件；结果段先说发现再选数字支撑；消融表注说清任务和比较。 |
| 结论 | 保留主要比较和贡献力度，删抽象拼接与重复范围，不追加免责式结尾。 |
| 附录 A：实验协议 | TorchAX 说明集中到 A.5，并去掉 A.3 的重复；删掉仍残留的 221.2 平均长度及脱离表格的长度定义；澄清预算单位、每次调用与累计预算；修正 Java/DJL 应用类别的错误叙述。 |
| 附录 B：证据交接与 agent 集成 | 将 native host 写成具体 baseline agent；说明“修复了几个程序”，避免 repair count 被理解为调用数；保留两个程序集合各自结果，解释编辑格式辅助与成本范围，删除主文选了哪些行的编辑过程说明。 |
| 附录 C：其他修复集合 | 将两个集合分别定义：50 项受控故障和12组源/目标程序。共享工具明确是 Direct repair 与 LaDiM，SWE-agent 仍使用原生工具。保留这两组研究各自的指标与预算。 |
| 附录 D：初译错误修复 | 将 ten saved translations 统一为十份初次翻译程序；明确五份首次评估失败、五份通过；保留 LSTM 支持库机制案例和三种子验证，清理 dispatch 等内部操作叙述。 |
| 附录 E：仓库结果 | 表注解释时间序列的9项训练检查来自三步×三种子，推荐的18项来自六条模型执行路径×三步；区分前向 loss 和训练返回 loss；缺测及测试收集失败按真实含义说明。 |
| 附录 F：上下文管理 | 用“旧代码版本的测量”“仍与当前文件一致的先前读取内容”“依赖文件的检查失效”等实际对象解释机制；JSON 定位指针、归档接口及内部字段移来源文档。保留独立交接、按需重建和共享预算。 |
| 附录 G：仓库组件 | 明确累计加入与每次移除一个组件的不同设计；complete references 改成各实验中启用全部组件的运行；保留推荐任务的成本上升及规划移除后少通过一项检查。 |
| 附录 H：原生 JAX | 明确十二来源中八份首次通过、两份没有生成代码、两份进入修复；预算按方法和任务说明；ResNet 首步数值一致只指三份可执行候选，MatchFixAgent 的缺测单独交代；删重复三步/优化器/接受数导览句。 |

## 主代理对候选方案的取舍

**采用实际问题的修正，保留已经清楚的句子。** 摘要8句全部保留。引言和结果中的完整迁移、57.4% 成本优势、4/5自然错误修复、跨语言和跨框架有效性，以及四组件在指定任务上的实测效果，继续明确表达。结论中的 `completes all 50 MindSpore migrations` 保留，不采用为了显得谨慎而改成 `achieves 50/50 acceptance` 的建议。

**算法采用精简结构，不直接复制子 agent 的长候选。** 报告给出了核对用的完整循环，其中消息追加、布尔变量和两段上下文回调仍然偏长。最终算法1只保留调查与一个共享 `LLMToolStep`；算法2用已经解释的完成条件收束低层标志；算法3的仓库操作通过该共享步骤实际被调用。正文说明机制，伪代码显示流程，两处各承担自己的作用。

**保留模型符号 M，函数名称直接标出 LLM。** Preliminary 已清楚定义 M，没有必要为显眼而把全文数学符号全部替换成 LLM。采用 `LLMCall(M, …)`、`LLMTranslate(M, …)` 和共用 `LLMToolStep`，算法2调用同一个步骤。翻译可能包含多次模型请求，不能把它改写成必然一次调用。

**图3采用短且一致的分类文字。** 使用 `Passes before repair` 与 `Needs repair`，在 caption 说明前者是初次翻译后首次评估通过的程序，色块表示后续调用成本。不采用 `Later calls: initially passed` 等冒号串列标签。保留全部三方法、全部阶段及右图正负柱，不新增29的正文细账。

**检测图继续用一般故障名称。** 保留图内 `(a) Incorrect gradients`、`(b) Incorrect parameter updates`；具体的梯度缩放和部分更新抑制留 caption 与协议，避免把图读成只针对某个代码操作。31/18的箭头文字写清 `Mean loss difference crosses threshold at step …`，LaDiM的 step 1 标注保留。梯度图例可准确写成 `Gradient norm difference`，不改其底层量。

**表头适度精简，不用更长标签重新撑高表格。** 程序组件完整行用 `LaDiM`，正文说明启用修复历史和独立证据交接，另外两行分别改动一个组件。避免再加 `(reference)` 或堆完整组件清单。表中短写 `Tokens`、`LLM calls` 时，caption 必须交代统计阶段；已经定义的 `Accepted` 不机械全改为 `Final accepted`。保留完整术语和当前横向布局，不缩字号。

**数字只在需要解释时出现。** 正文检测段突出第一步发现差异和训练依赖机制；四模型×三种子、50步内3/12与4/12的明确对应集中在图注及附录。保留评价指标现有定义，只修正不清楚的表头对应；不另添一套指标或冗长 evaluation protocol。

**主文与附录各自承担清楚的任务。** 用支持库修复案例解释实际意义，保留主文六例JAX结果及 Direct repair 的真实成本比较。其他协议的完整结果继续留附录。移出的是项目内部记账和接口定位细节，不能把未定义的名词简单搬到附录后不解释。

## 已核出的事实问题与实施前的证据定位

主代理核对冻结逐任务记录后确认：Java/DJL 中 LaDiM 和 MatchFixAgent 通过的是水果分类迁移学习应用，SWE-agent 通过的是 MNIST LSTM 应用。当前附录的 `the same application` 有误。`initially accepted application` 也有误：已通过的初译对应教材示例，不能写成应用。方案删除这句不必要的概括，改为直接报告各方法实际接受的程序构成。主文 `LaDiM accepts all programs completed by MatchFixAgent and an additional recurrent network example` 与记录一致，保留。详见[证据核对补记](15-evidence-decisions.md)。

同一补记记录了已解决的检查项：六例JAX的四次提交上限、信号消融中 basic checks 的实际内容、仓库修改后测试与完整验收的调用关系，以及上下文证据的版本判定。这些核对不需要重跑实验。

少量可选细化依赖更具体的冻结定义，例如 BF16 相对容差、原生 JAX 每次运行的累计预算、推荐表中 file coverage 和 training return loss 的精确含义。当前方案不新增未经核实的定义；实际实施前定位原记录，已有数值及原条件原样保留。这个核对只决定这些局部句子的最终写法，不阻塞已经明确的文字和算法调整。

## 实施与验收

用户审阅本方案后再改论文。执行时先方法与算法，再实验及图表标签，再引言/相关工作/结论及附录的一致性；摘要保持。逐条核对持久清单，不能以关键词存在替代语义和可读性检查。保留有效定量事实与比较范围；不运行新实验。

涉及图表生成器时同步资产并运行对应既有检查；重新编译、检查算法和横排表格实际大小，更新固定基线逐词比较；记录哪些意见真正落实、哪些仍待处理。当前审查轮只验证审查文档和被保护文件未变，不把此前25项测试或PDF检查算成本轮执行。
