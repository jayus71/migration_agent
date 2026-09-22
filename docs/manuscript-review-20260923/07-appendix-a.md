# 附录 A 逐句审查报告

审查版本：`d1d6a53`。本报告仅依据传入的源码、意见清单、Humanizer 规则、Academic Writing DNA 和图表来源说明形成。所有修改均为方案，未修改论文、脚本、图表、结果或 PDF，未调用工具、运行实验或提交 Git。

本轮采用最新意见 S13，重点检查可读性、统计口径、预算表述和实现一致性。TorchAX 的执行说明应集中到附录；50 项主比较、十份初次翻译程序、六例 JAX 研究及各独立研究的分母保持不变。

## 1. 审查范围与覆盖数量

| 对象 | 精确来源 | 本轮覆盖 |
|---|---|---|
| 附录 A 标题及全部六个子节 | `sections/supplementary_experiments.tex:1–87` | 全部提供内容 |
| 正文句子 | 同上，第 16–86 行 | 116 句 |
| 表注句子 | 同上，第 8、28 行 | 4 句 |
| 公式 | 同上，第 80–86 行 | 3 个公式及 1 个引导单元；公式后的 3 句计入正文 |
| 数据集表 | `figures/TABLE_task_collections.tex:1–10` | 1 组表头、4 个数据行 |
| 完整程序成本表 | `figures/TABLE_program_costs.tex:1–21` | 1 组表头、2 个分组标题、12 个数据行 |
| 标题 | 附录标题、六个子节标题、六个随机种子段首 | 13 个标题单元 |
| 图 | 本范围没有直接插入图，仅引用 `fig:gradient-drift` | 已审查全部相关解释；图注和实际图内标签未提供 |
| 算法 | 本范围没有算法环境 | 0 个；不重复审查主文算法 |

下文局部编号固定对应当前快照。表内“保留”“改写”“删除”“移来源记录”均表示建议处置，未实施。“待核对”表示现有材料不足以确定英文定稿，不表示已经发现实现错误。

## 2. 逐句台账

### A.1 Task Construction and Accounting

来源：`sections/supplementary_experiments.tex:4–34`。

| 编号 | 行号与短引文 | 建议 | 理由／修改方案 |
|---|---|---|---|
| A1.C01 | 8 “Program collections for migration and repair…” | 保留 | 准确说明表格内容，没有增加平均长度。 |
| A1.01 | 16 “contains 50 task identifiers” | 保留 | 50 是主表评价分母，需要与后续 29 个不同输入区别。 |
| A1.02 | 16 “Twelve entries reuse existing native source programs…” | 改写 | `native` 未说明所属框架；“entries”可明确为任务。见 C01。 |
| A1.03 | 16 “29 distinct combinations…24 source files” | 保留 | 清楚解释 50、29、24 的不同含义。 |
| A1.04 | 16 “Conditions with identical source…are executed once…” | 保留 | 去重执行规则直接影响成本解释，附录中有必要保留。 |
| A1.05 | 16 “Acceptance…all 50 identifiers…actual calls” | 保留 | 分母与成本口径明确，不能删成笼统的“公平比较”。 |
| A1.06 | 16 “share the same initial translation…” | 保留 | 明确三种方法的共同输入。 |
| A1.07 | 16 “Production edits are restricted…” | 改写 | `Production edits` 容易被理解为生产部署修改；应直接说明候选程序和临时测试。见 C02。 |
| A1.08 | 16 “Sources and task specifications remain fixed.” | 保留 | 说明可编辑范围之外的评价条件固定，信息独立。 |
| A1.09 | 18 “ten DJL application programs…averaging 221.2…” | 改写 | 保留十加八的任务构成，删除平均长度；最新要求明确不加平均长度。见 C03。 |
| A1.10 | 18 “LaDiM accepts one application and all eight examples.” | 保留 | 与 9/18 一致，说明新增接受来自何种程序。 |
| A1.11 | 18 “SWE-agent and MatchFixAgent…test-guided repair accepts seven examples” | 保留，关联核对 | 本句分别对应 8/18、8/18、7/18；与下一句发生冲突，先保留数值来源支持的句子。 |
| A1.12 | 18 “All repair methods preserve the initially accepted application.” | 改写，待核对 | 若包括 test-guided repair，则其七个例子加一个应用应为 8/18，与成本表 7/18 冲突。见 C04。 |
| A1.13 | 18 “The saved initial translations…are shared…” | 改写 | `saved` 是存档状态；读者需要知道各方法接收相同的初次翻译程序。见 C05。 |
| A1.14 | 18 “InterTrans uses its direct Java-to-Python path…” | 保留 | 两条搜索路径及原生搜索过程是实际比较设置，信息具体。 |
| A1.15 | 18 “2,286,034 tokens include 574,304…1,711,730…” | 保留 | 交代失败生成计入成本，数字相加一致。 |
| A1.16 | 18 “final evaluation compares…over two consecutive training steps” | 保留 | 具体列出比较对象和连续两步；正好承接主文抽象句移来的细节。 |
| A1.17 | 20 “initial translations cost 429,109 tokens” | 保留 | 是完整成本分解的起点。 |
| A1.18 | 20 “included once in each repair method's total” | 保留 | 防止把初译重复计费，不能删掉。 |
| A1.19 | 20 “inputs that pass the initial checks…require repair” | 改写 | 明确为首次评估通过或未通过的初次翻译程序，避免暗示前者没有后续调用。见 C06。 |
| A1.20 | 20 “corresponding MatchFixAgent totals…” | 保留 | 上句分组改清后，本句承接自然，两个数值保持。 |
| A1.21 | 20 “median ratio…0.588” | 保留 | 指标和比较方向明确。 |
| A1.22 | 20 “19/20 initially passing inputs and 8/9 initially failing inputs” | 改写 | 说明 20 和 9 是按初次翻译首次评估结果划分的输入组。见 C07。 |
| A1.23 | 20 “Seven of the nine failing inputs…” | 改写 | 缺少执行修复的方法主语，应明确 LaDiM。见 C08。 |
| A1.24 | 20 “Shared initial translation costs cancel…” | 保留 | 解释配对 token 差值为何不受共同初译成本影响，属于有效方法说明。 |
| A1.25 | 20 “first external submission…internal analysis and repair orchestration” | 改写 | `external` 和 `orchestration` 过于内部化；需区分一次提交和内部多次分析／修复。见 C09。 |
| A1.26 | 22 “All failed tasks remain…all failed calls…” | 保留 | 明确失败任务和失败调用的统计归属。 |
| A1.27 | 22 “scores the current candidate…regression…” | 保留 | 准确保留当前候选评分规则，不能改成“预算内曾通过即接受”。 |
| A1.28 | 22 “An edit counts one successfully applied editing operation…” | 保留 | 定义编辑计数，并说明一次操作可以修改多个代码块和文件。 |
| A1.29 | 22 “share cumulative call, output, and time budgets…” | 改写 | `output` 应明确为 output token；累计预算规则保留。见 C10。 |
| A1.30 | 25 “Source lengths count nonblank physical lines…” | 移来源记录 | 当前表没有长度列，正文无需保留孤立的长度计算规则。见 C11。 |
| A1.31 | 25 “50…24 source files…signal…four…JAX…two” | 保留，调整位置 | 四份和两份源程序有助于理解任务构造；24 与前文重复，可合并。见 C11。 |
| A1.32 | 25 “Repository lengths include…” | 移来源记录 | 属于仓库长度统计方法；当前子节缺少对应长度值，移到来源说明更合适。见 C11。 |
| A1.C02 | 28 “Complete input and output token costs for individual migrations.” | 改写 | 表格按方法和集合汇总，并非逐个程序列成本。见 C12。 |
| A1.C03 | 28 “Costs include initial translation and every subsequent call.” | 保留 | 完整成本口径明确。 |
| A1.C04 | 28 “Acceptance uses the declared task denominator…” | 保留 | 表中分母为 50 和 18，句子与表一致。 |

### A.2 Numerical Comparisons and Migration Settings

来源：`sections/supplementary_experiments.tex:36–41`。

| 编号 | 行号与短引文 | 建议 | 理由／修改方案 |
|---|---|---|---|
| A2.01 | 39 “absolute/relative tolerances…” | 改写 | 斜杠压缩了绝对／相对容差的对应关系，建议展开。见 C13。 |
| A2.02 | 39 “BF16…absolute tolerance \(10^{-2}\)” | 保留，待核对 | 绝对容差明确；是否沿用一般相对容差，现有材料未说明。见 V01。 |
| A2.03 | 39 “Shapes, data types, initial values, and trainability must match.” | 保留 | 验收对象具体，四项各有独立意义。 |
| A2.04 | 39 “Parameter and optimizer tasks test…” | 保留 | 特定任务的行为检查有必要保留，不能统一改为 loss 检查。 |
| A2.05 | 39 “retain their own state over two…three…” | 改写 | 指明连续训练期间分别保留状态，避免 `individual migration` 泛指附录所有研究。见 C14。 |
| A2.06 | 39 “source program and task requirements…each method” | 保留 | 说明方法可用输入，有助于理解比较条件。 |
| A2.07 | 39 “target framework executes the required computations” | 保留 | 是验收条件，避免仅生成目标框架外壳。 |
| A2.08 | 41 “SWE-agent retains its native tools and controller.” | 保留 | 此处小写 `controller` 指基线自身机制，不是新造 LaDiM 模块名。 |
| A2.09 | 41 “shared DeepSeek tool backend” | 改写 | `shared` 的共享对象及“工具后端”作用不清楚；可保留已明确的 DeepSeek 调用事实。见 C15。 |
| A2.10 | 41 “CodeTransEngine…native direct path…MSAdapter…” | 保留 | 两个原生基线的实际使用方式明确。 |
| A2.11 | 41 “Individual migration allows 40…four submissions” | 改写 | 标明这些数值是上限，并避免将该预算误套到所有附录研究。见 C16。 |
| A2.12 | 41 “Repository limits are 80…four submissions” | 保留 | 用 `limits` 明确上限，没有声称全部用满。 |
| A2.13 | 41 “eight calls per investigation or repair stage…” | 保留 | 是 LaDiM 的阶段预算；不能由此推导每个工作单元重新启动 Verifier。 |
| A2.14 | 41 “Agent calls…16,384…complete candidate…131,072…” | 改写，待核对 | 需直接命名整文件修复基线，并解释单次上限与累计 120,000 的关系。见 C17、V02。 |
| A2.15 | 41 “The latter has four repair rounds.” | 改写 | 代词距离远；应写具体方法及最多四轮，不虚构每次都执行。见 C17。 |
| A2.16 | 41 “Repository calls…32,768 output tokens” | 保留 | 仓库单次调用上限清楚。 |
| A2.17 | 41 “Output budgets include reasoning tokens…” | 保留 | reasoning 计入输出预算、输入使用被统计，均影响成本解释。 |

### A.3 Random Seeds and Initial States

来源：`sections/supplementary_experiments.tex:43–62`。

| 编号 | 行号与短引文 | 建议 | 理由／修改方案 |
|---|---|---|---|
| A3.01 | 47 “seed 101 for public evaluation…202 and 303…” | 改写 | 首次解释 `public` 是修复过程中可见的评价，而非公开数据集；主代理核对其可见性。见 C18。 |
| A3.02 | 47 “NumPy's random generator…inputs and training targets” | 保留 | 随机性来源清楚。 |
| A3.03 | 47 “hash of each parameter name…fixed across…seeds” | 保留 | 参数固定、输入种子变化的设置影响实验含义；分号在此连接两个紧密事实，可保留或自然拆句。 |
| A3.04 | 47 “Discrete inputs, masks…task-specific settings” | 保留 | 说明不由通用随机输入生成过程替代的输入类型。 |
| A3.05 | 47 “original initial parameters and two preprocessed batches” | 保留 | 连续两步的输入和初始化具体。 |
| A3.06 | 47 “component comparisons on these programs…” | 改写，待核对 | `these programs` 指代不清，容易误指十份初译的组件实验。见 C19。 |
| A3.07 | 50 “All ten natural translation tasks…” | 改写 | `natural translation tasks` 不能直接说明已有初译程序这一实验对象。见 C20。 |
| A3.08 | 50 “16 training-signal candidates use 4101…” | 保留 | 16 个候选及三个种子准确；`public` 在 A3.01 解释一次即可。 |
| A3.09 | 50 “sets the Python, NumPy, and PyTorch random states…” | 保留 | 初始化及状态复制步骤具有复现价值。 |
| A3.10 | 50 “CPU PyTorch generator seeded with \(s+101\)” | 保留 | 数据随机性与模型初始化分离，描述具体。 |
| A3.11 | 50 “all three seeds…fault construction…final candidate…” | 保留 | 清楚说明三种子用于构造核验和最终全信号评分。 |
| A3.12 | 50 “additional repair collections…original unit probes…” | 改写，待核对 | 未明确所指集合，`unit probes` 又是内部化表达。见 C21。 |
| A3.13 | 53 “MLP and CNN programs…6701…6702…6703” | 保留 | 与 JAX 协议一致。 |
| A3.14 | 53 “initializes PyTorch's random state…before constructing…” | 保留 | 明确初始化时机。 |
| A3.15 | 53 “Inputs and class labels…\(s+101\)” | 保留 | 与模型随机性分离，信息完整。 |
| A3.16 | 53 “TorchAX transfers…native differentiation and Optax…” | 删除本处，合并到 A.5 | 与第 71 行重复；TorchAX 应在附录 JAX 协议集中说明。见 C22。 |
| A3.17 | 56 “Seeds 300, 301, and 302…” | 保留 | 三个重复轨迹的设置准确。 |
| A3.18 | 56 “initial state is shared across…executions” | 保留 | 明确起始状态一致。 |
| A3.19 | 56 “batch order…\(s+5000\)…\(s+6000\)…\(s+7000\)” | 保留 | 三项对应真实不同数据输入机制，不属于为节奏硬凑三项。 |
| A3.20 | 56 “share the same initial state and 50-step batch sequence” | 保留 | 是比较故障与同步条件的控制设置。 |
| A3.21 | 59 “main comparison and component ablation…101…202…303” | 保留 | 时间序列仓库的实验对象和种子清楚。 |
| A3.22 | 59 “source model…parameters…copied to the target” | 保留 | 初始化对应关系明确。 |
| A3.23 | 59 “\(s+47\)…training batches…\(s\)…price series” | 保留 | 随机数据来源和种子分工明确。 |
| A3.24 | 59 “target MindSpore random state also uses \(s\)” | 保留 | 目标框架内部随机性设置不可从前句推知。 |
| A3.25 | 59 “training script, notebook, and teaching examples…” | 保留 | 公共评估范围与确认阶段数值检查范围不同，应保留；分号可拆句。 |
| A3.26 | 62 “seed 101…user identifiers, features, histories…” | 保留 | 推荐任务输入类型具体，无需为了缩短删除其中某类。 |
| A3.27 | 62 “source parameters and retrieval corpus…supplied…” | 保留 | 说明目标端收到的初始状态与检索数据。 |
| A3.28 | 62 “confirmation after all public checks pass…finish at the public evaluation” | 改写 | 后半句应直接说明本次结果没有进入确认阶段，防止误读为三种子均已完成。见 C23。 |
| A3.29 | 62 “original tests use seed 42…” | 保留 | 原始测试与数值评价使用不同种子，必须保留。 |
| A3.30 | 62 “exact-value history-encoder checks…” | 改写 | 连字符堆叠，直接说明对 history encoder 输出作精确值检查。见 C24。 |
| A3.31 | 62 “one-epoch training command uses seed 101” | 保留 | 具体训练入口的种子设置，信息独立。 |

### A.4 Training Signal Study

来源：`sections/supplementary_experiments.tex:64–66`。

| 编号 | 行号与短引文 | 建议 | 理由／修改方案 |
|---|---|---|---|
| A4.01 | 66 “same investigation and evidence handoff procedure…editing examples…” | 改写 | 必须保留早期实验使用编辑示例和格式纠正的真实设置；`same` 应说明信号与 JAX 两项研究之间一致。见 C25。 |
| A4.02 | 66 “four controlled modifications to four model classes” | 改写 | 明确每种模型各有四种故障，共 16 个候选。见 C26。 |
| A4.03 | 66 “invalid optimizer keyword…constant loss offset…” | 保留 | 四种实际故障机制具体，且与 JAX 前向故障不同，不能混写。 |
| A4.04 | 66 “Each setting retains the initial investigation, current workspace…” | 改写，待核对 | `setting` 和 `retains` 的跨阶段含义不清；保留调查、工作文件及累计预算设置。见 C27。 |
| A4.05 | 66 “Its visible checks determine whether repair starts and stops.” | 改写 | 需指明反馈条件决定可见检查，并保留其控制启动／停止修复的真实逻辑。见 C28。 |
| A4.06 | 66 “Final acceptance uses all training signals on three seeds.” | 保留 | 清楚区分运行时可见反馈与最终全信号评价。 |
| A4.07 | 66 “torch4ms forward and backward bridge…” | 保留，可拆句 | 桥接后端和参数更新属于附录实现设置；不得把 `torch4ms` 自动改成 TorchAX。 |

### A.5 JAX Repair and Native Conversion Controls

来源：`sections/supplementary_experiments.tex:68–73`。

| 编号 | 行号与短引文 | 建议 | 理由／修改方案 |
|---|---|---|---|
| A5.01 | 71 “six JAX candidates comprise…” | 改写 | 明确是每个模型的三个故障版本，避免被读成每个候选同时含三种故障。见 C29。 |
| A5.02 | 71 “same source programs and original candidates…” | 改写 | `original candidates` 指代不够直观，应直接说相同的含故障候选程序。见 C30。 |
| A5.03 | 71 “Each allows four submissions, 40 LLM calls…” | 改写 | 标明每个任务的最多预算；否则下句总调用数 76／57 容易与 40 被误读为冲突。见 C31。 |
| A5.04 | 71 “accept every task at the first submission…” | 保留 | 清楚报告实际首次提交即 6/6，不应改成执行了四次修复。 |
| A5.05 | 71 “76 calls and 674,009 tokens;…57…353,311” | 改写 | 拆分分号，明确为六项任务合计，保留全部成本。见 C32。 |
| A5.06 | 71 “TorchAX executes…JAX…Optax…” | 保留，作为集中说明位置 | 三个后端各自承担的动作具体，适合作为主文迁入内容的落点。见 C22。 |
| A5.07 | 71 “Loss absolute difference, gradient norm absolute difference…” | 改写 | 改用“损失的绝对差”“梯度范数的绝对差”等清楚的数学对象。见 C33。 |
| A5.08 | 71 “match the reference initial parameters exactly” | 保留 | 是实测结果与验收状态，不应削弱为近似相同。 |
| A5.09 | 71 “maximum final loss, gradient norm…differences…” | 保留 | 三项最大误差和科学计数法保持不变。 |
| A5.10 | 73 “Ivy uses ivy.transpile…” | 保留 | 原生转换方法及目标实现具体。 |
| A5.11 | 73 “samuela/torch2jax…t2j…” | 保留 | 正式实现标识与调用方式明确，有助于避免与 TorchAX 混淆。 |
| A5.12 | 73 “single native conversion…already faulty candidate” | 保留 | 解释为何原生转换不会自动消除源候选中的错误，且不将其伪装为迭代修复。 |
| A5.13 | 73 “extra argument…TypeError…n/a” | 保留 | 故障原因和缺测含义明确，n/a 不能改为零。 |
| A5.14 | 73 “output scaling error…fail loss, gradient, and update checks” | 保留 | 三种检查确实各提供信息；不得替换为信号实验的恒定 loss 偏移。 |
| A5.15 | 73 “interrupted differentiation path: loss passes…” | 保留 | 具体解释梯度故障的可观测结果，冒号有实际说明作用。 |
| A5.16 | 73 “healthy MLP and CNN controls pass” | 改写 | 明确对照输入是已知正确的程序，且转换后通过检查。见 C34。 |
| A5.17 | 73 “Ivy spends 561.935…healthy controls; torch2jax…” | 改写 | 按转换器拆句，明确各时间对应六个故障候选或两个正确对照程序。见 C35。 |
| A5.18 | 73 “Their LLM calls and tokens are zero.” | 保留 | 两个原生转换器均无 LLM 使用；与接受数 0/6 不是同一指标。 |

### A.6 Detection Measurements

来源：`sections/supplementary_experiments.tex:75–86`。

| 编号 | 行号与短引文 | 建议 | 理由／修改方案 |
|---|---|---|---|
| A6.01 | 78 “four models, three seeds, and 50 training steps” | 保留 | 直接定义模型、重复次数和观测窗口。 |
| A6.02 | 78 “Gradient scaling and partial update suppression…” | 保留 | 两种故障及同步／独立演进两种设置都需要保留。 |
| A6.03 | 78 “With synchronization…starts…from the source state” | 保留 | 解释同步机制，避免把同步和独立轨迹混为一谈。 |
| A6.04 | 78 “Loss, gradient norm, and relative update thresholds…” | 改写 | 必须说成相应“差值”的阈值，而非 loss／梯度范数自身的阈值。见 C36。 |
| A6.05 | 78 “separate state…mean and range across 12 runs per fault” | 改写 | 明确独立状态演进，12 来自四个模型乘三个种子。见 C37。 |
| A6.06 | 78 “crossings at steps 31 and 18 refer to mean curves” | 改写，待核对 | 需说明 loss difference 越过 0.02，并补充每个步数对应的故障。快照未提供映射证据。见 C38。 |
| A6.07 | 78 “Direct gradient or update checks detect all respective faults…” | 改写 | 明确梯度检查对应梯度缩放，更新检查对应局部更新抑制。见 C39。 |
| A6.08 | 78 “Healthy translations…maximum loss difference…” | 改写 | 改为已知正确的翻译程序，保留最大误差。见 C40。 |
| A6.F00 | 80 “The scalar summaries are” | 改写 | 与前文检测阈值连接，明确下面定义的是检测研究中的三个标量差异。见 C41。 |
| A6.F01 | 82 \(\Delta_{\mathrm{loss}}\) | 保留公式 | 计算源与目标 loss 的绝对差，符合文字说明。 |
| A6.F02 | 83 \(\Delta_{\mathrm{grad}}\) | 保留公式 | 计算两个梯度范数的绝对差；不能改成梯度差的范数。 |
| A6.F03 | 84 \(\Delta_{\mathrm{param}}\) | 保留公式，待核对定义 | 相对更新差公式不改；需核对 \(\epsilon\) 数值是否在其他处已定义。见 V03。 |
| A6.09 | 86 “updates…epsilon prevents division by zero” | 保留，可补定义 | 更新向量含义明确；如全文没有 \(\epsilon\) 数值，补真实值，不能猜。 |
| A6.10 | 86 “divides each difference by its detection threshold” | 保留 | 解释图上的归一化量，支持阈值线为 1 的标签。 |
| A6.11 | 86 “main migration comparison uses…tensor comparisons…” | 保留 | 本句区分标量检测量与主比较张量验收，属于必要科学口径，不是防御性降调。 |

### 标题台账

| 编号 | 位置 | 建议 | 理由 |
|---|---|---|---|
| H01 | 1 `Additional Experimental Protocols` | 保留 | 与附录内容一致。 |
| H02 | 4 `Task Construction and Accounting` | 保留 | 同时涉及任务构造和真实成本统计，`Accounting` 在此有具体内容。 |
| H03 | 36 `Numerical Comparisons and Migration Settings` | 保留 | 阈值、原生配置和预算均在本节。 |
| H04 | 43 `Random Seeds and Initial States` | 保留 | 准确。 |
| H05 | 64 `Training Signal Study` | 保留 | 准确。 |
| H06 | 68 `JAX Repair and Native Conversion Controls` | 保留 | `controls` 是实际实验角色，正文解释正确程序后即可理解。 |
| H07 | 75 `Detection Measurements` | 保留 | 准确。 |
| H08 | 46 `Individual migration.` | 保留 | 当前段落覆盖主程序迁移比较；正文须明确范围。 |
| H09 | 49 `Natural faults and training signals.` | 改写 | 建议 `Initial translations and training signals.`，与十份初译程序的真实对象一致。 |
| H10 | 52 `JAX repair.` | 保留 | 准确。 |
| H11 | 55 `Detection trajectories.` | 保留 | 是具体的轨迹实验。 |
| H12 | 58 `Time series repository.` | 保留 | 指向明确仓库任务。 |
| H13 | 61 `Recommendation repository.` | 保留 | 指向明确仓库任务。 |

保留期刊／会议模板中的标题格式和加粗段首，不将 Humanizer 的通用排版建议解释为统一取消学术结构格式。

## 3. 图表逐项台账

### 3.1 数据集表

来源：`figures/TABLE_task_collections.tex`；表注位于 `sections/supplementary_experiments.tex:8`。

| 编号 | 行号／对象 | 建议 | 核查结论及候选 |
|---|---|---|---|
| T1.H | 3，四列表头 | 保留 | `Collection / Candidate construction / Model or operation coverage / Tasks` 各有明确作用；不增加平均长度列。 |
| T1.R1 | 5，PyTorch to MindSpore | 保留 | 50 对应任务标识；模型／操作范围和生成候选方式保留。 |
| T1.R2 | 6，Saved initial translations | 改写标签 | 集合名改为 `Initial translations`；构造说明改为 `Five fail and five pass their first evaluation`。10 和模型覆盖不变。 |
| T1.R3 | 7，Training-signal ablation | 小幅改写标签 | 改为 `Training signal ablation`；保留 `Controlled training faults`、四类模型和 16。 |
| T1.R4 | 8，JAX repair | 保留 | 六个含故障候选、MLP 与 CNN 范围明确；不混入附录另一项十二来源 JAX 研究。 |

表格四行不是全文所有任务的完整清单。当前表注仅称“Program collections”，没有声称穷尽全部实验，因此无需为了对称添加检测轨迹、额外注入故障集合或独立 JAX 扩展研究。

“Five fail and five pass their first evaluation”只说明初始状态；不能改成“五次修复失败和五次修复成功”。

### 3.2 完整程序成本表

来源：`figures/TABLE_program_costs.tex`；表注位于 `sections/supplementary_experiments.tex:28`。

| 编号 | 行号／对象 | 建议 | 核查结论 |
|---|---|---|---|
| T2.H | 3，六列表头 | 保留，补表注说明 | LLM calls、输入／输出／总 token 和 Accepted 均明确；可补充 token 按百万显示并独立舍入。 |
| T2.P1 | 5，PyTorch to MindSpore | 保留 | 分组名称准确。 |
| T2.R1 | 6，Direct LLM | 保留全部数值 | 29 calls；0.018／0.411／0.429；29/50。调用次数与 50 个标识的差异由 A.1 去重说明解释。 |
| T2.R2 | 7，CodeTransEngine | 保留全部数值 | 29 calls；0.022／0.257／0.280；31/50。三项 token 显示值不要求舍入后严格相加。 |
| T2.R3 | 8，MSAdapter | 保留 | LLM 成本横杠与 15/50 分开；不能把接受结果改成横杠或零。 |
| T2.R4 | 9，SWE-agent | 保留全部数值 | 1,097 calls；19.845／0.987／20.831；44/50。来源说明中的不可用最终结果仍在 50 分母内。 |
| T2.R5 | 10，MatchFixAgent | 保留全部数值和结果强调 | 619 calls；10.750／1.347／12.097；50/50。 |
| T2.R6 | 11，LaDiM | 保留全部数值和结果强调 | 326 calls；4.298／0.861／5.159；50/50。与 MatchFixAgent 并列最好。 |
| T2.P2 | 13，Java/DJL to Python/PyTorch | 保留 | 分组名称准确。 |
| T2.R7 | 14，Direct LLM | 保留全部数值 | 18 calls；0.142／0.552／0.694；1/18。 |
| T2.R8 | 15，InterTrans | 保留全部数值 | 89 calls；0.680／1.606／2.286；1/18。总成本包括不完整生成。 |
| T2.R9 | 16，Test-guided repair | 保留数值，核对正文 | 71 calls；1.594／2.881／4.475；7/18。与“All repair methods preserve…”存在明确文本冲突。 |
| T2.R10 | 17，SWE-agent | 保留全部数值 | 682 calls；23.063／1.258／24.321；8/18。 |
| T2.R11 | 18，MatchFixAgent | 保留全部数值 | 524 calls；26.335／2.020／28.355；8/18。 |
| T2.R12 | 19，LaDiM | 保留全部数值和结果强调 | 345 calls；19.470／2.009／21.479；9/18，为本组最好。 |

表中有些显示值相加相差 0.001 million，例如 CodeTransEngine 的 0.022 + 0.257 与总计 0.280。输入、输出和总量分别从原始计数舍入即可产生这种情况，不能据此改动任何数值。建议在表注补充：

> Token counts are reported in millions and rounded independently.

第 7–10、15 行重复出现基线引用，而来源说明采用“在实验设置首次介绍处引用一次”的安排。建议删除这些表内重复引用，保留实验设置中的首次引用。对应 E09、W06；不改变方法名称或行数据。

## 4. 具体修改方案

以下候选均未实施。没有充分证据支持的补充使用明确的待核对说明，不将猜测写入英文定稿。

### C01–C12：任务构造、成本与长度记录

**C01｜A1.02，原文件第 16 行**

原句：

> Twelve entries reuse existing native source programs, and the remaining entries use programs authored from public interfaces and declared semantics.

问题：`native` 没有明确框架，且对当前构造说明没有额外作用。

英文候选：

> Twelve tasks reuse existing source programs; the remaining tasks use programs written from public interfaces and declared semantics.

若希望同步减少分号，可写成两句：

> Twelve tasks reuse existing source programs. The remaining tasks use programs written from public interfaces and declared semantics.

对应意见：W01、W03、W04、S13 第 7 项。

---

**C02｜A1.07，第 16 行**

原句：

> Production edits are restricted to the candidate program, with separate temporary tests available for investigation.

英文候选：

> Repair edits are restricted to the candidate program. Agents can create separate temporary tests during investigation.

保留候选程序可编辑范围和临时测试权限，不引入支持库可编辑等其他研究设置。

对应意见：M04、M14、W03、W07。

---

**C03｜A1.09，第 18 行**

原句：

> The comparison across languages contains ten DJL application programs and eight textbook examples, averaging 221.2 nonblank source lines.

英文候选：

> The comparison across languages contains ten DJL application programs and eight textbook examples.

221.2 的长度统计留在来源文件。本轮不增加任何新的平均长度位置。

对应意见：E02、S12、最新第 9 项。

---

**C04｜A1.12，第 18 行，需主代理裁定**

原句：

> All repair methods preserve the initially accepted application.

问题：同段称 test-guided repair 接受七个教材例子，表中也是 7/18；若再保留一个应用，则应为 8/18。三者不能同时成立。

由现有文本支持的最小候选：

> LaDiM, SWE-agent, and MatchFixAgent preserve the application that passes the initial evaluation.

该候选与上一句所列三种方法结果相容。主代理应核对冻结的逐任务结果，确认 test-guided repair 是否确实丢失了初始通过应用，或七个接受任务的类别描述是否需要纠正。不得先改表格 7/18。

对应意见：W07、R07、E08。

---

**C05｜A1.13，第 18 行**

原句：

> The saved initial translations and their generation costs are shared by the repair conditions.

英文候选：

> All repair methods receive the same initially translated programs, and each method's total cost includes their generation cost once.

共同初译成本计入一次的规则由来源说明及第 20 行支持。若本段希望避免重复成本规则，可仅将原句中的 `saved initial translations` 改成 `initially translated programs`，将计费定义统一放在 A1.18。

对应意见：E08、W03、W06、最新第 6 项。

---

**C06｜A1.19，第 20 行**

原句：

> Subsequent LaDiM calls use 1,409,686 tokens on inputs that pass the initial checks and 3,320,339 on inputs that require repair.

英文候选：

> After translation, LaDiM uses 1,409,686 tokens on inputs whose initial translations pass the first evaluation and 3,320,339 tokens on inputs whose initial translations fail it.

不把“首次评估通过”写成“没有后续调查调用”。两组 token 均保留。

对应意见：E08、F04、W07、最新第 6 项。

---

**C07｜A1.22，第 20 行**

原句：

> LaDiM uses fewer tokens on 19/20 initially passing inputs and 8/9 initially failing inputs, giving 27/29 overall.

英文候选：

> LaDiM uses fewer tokens on 19 of the 20 inputs whose initial translations pass the first evaluation and on eight of the nine whose initial translations fail, for 27 of 29 inputs overall.

这段保留在附录，主文不重新堆入 29、20、9 的细账。

对应意见：R12、F04、E08、W07。

---

**C08｜A1.23，第 20 行**

原句：

> Seven of the nine failing inputs are repaired at the first submission.

英文候选：

> LaDiM repairs seven of the nine initially failing translations by its first submission.

需要核对这里的“七个”确实为 LaDiM 的九个不同输入，而非 50 个任务标识中的计数。当前段落结构和来源说明支持这一解释，但没有提供逐输入记录。

对应意见：W01、W07、R07。

---

**C09｜A1.25，第 20 行**

原句：

> MatchFixAgent reaches full acceptance within its first external submission through its internal analysis and repair orchestration.

英文候选：

> MatchFixAgent reaches 50/50 acceptance at its first submission to the evaluator, after running its internal analysis and repair process.

明确 submission 是向评价器提交候选，不等于一次 LLM 调用或一次内部编辑。`internal analysis and repair process` 保留原有机制，不补造内部轮数。

对应意见：E06、W03、W06、R07。

---

**C10｜A1.29，第 22 行**

原句：

> Investigation and repair share cumulative call, output, and time budgets across submissions.

英文候选：

> Investigation and repair share cumulative budgets for calls, output tokens, and elapsed time across submissions.

对应意见：W01、W07。

---

**C11｜A1.30–A1.32，第 25 行**

原文：

> Source lengths count nonblank physical lines, including comments. The 50 MindSpore identifiers use 24 source files, the signal study uses four, and the JAX study uses two. Repository lengths include all source Python files and notebook code cells, including original tests and excluding the external evaluation harness.

方案：

- 第一、第三句移至 `data/paper_figures/README.md` 中现有 `scripts/summarize_paper_collections.py` 的统计说明。该文件已经包含基本相同的信息，执行时应合并，避免重复追加。
- 24 个源文件在第 16 行已经解释，不再重复。
- 保留能解释任务构造的后两项源程序数：

> The training signal study uses four source programs, and the JAX repair study uses two.

将此句放在数据集表附近，或分别并入 A.4、A.5。不要把四／二改成独立研究次数。

对应意见：E02、W06、W07、最新第 9 项。

---

**C12｜A1.C02，第 28 行**

原句：

> Complete input and output token costs for individual migrations.

英文候选：

> Aggregate input and output token costs for the program migration comparisons.

后两句保留，并可追加表内独立舍入说明：

> Token counts are reported in millions and rounded independently.

对应意见：E05、R06、W01。

### C13–C17：数值验收与预算

**C13｜A2.01，第 39 行**

原句：

> The main MindSpore collection uses absolute/relative tolerances of \(10^{-4}/10^{-4}\) for forward values, \(10^{-4}/10^{-3}\) for gradients, and \(10^{-5}/10^{-3}\) for updates.

英文候选：

> For the main MindSpore collection, the absolute and relative tolerances are \(10^{-4}\) and \(10^{-4}\) for forward values, \(10^{-4}\) and \(10^{-3}\) for gradients, and \(10^{-5}\) and \(10^{-3}\) for parameter updates.

所有阈值保持不变。

对应意见：M03、E05、W07。

---

**C14｜A2.05，第 39 行**

原句：

> Source and target programs begin from corresponding initial states and retain their own state over two consecutive steps for individual migration and three for repositories.

英文候选：

> In the main program migration comparisons, the source and target start from corresponding initial states and each retains its own state over two consecutive training steps. Repository comparisons use three consecutive steps.

这里的范围应与 MindSpore、Java/DJL 主比较一致，不能把 JAX 的一个 SGD 步改成两步。

对应意见：E04、W07、最新第 3 项。

---

**C15｜A2.09，第 41 行**

原句：

> MatchFixAgent retains its analysis and repair orchestration through a shared DeepSeek tool backend.

英文候选：

> MatchFixAgent retains its own analysis and repair procedure and uses DeepSeek for LLM calls.

该候选适用于 `DeepSeek tool backend` 确实指 LLM 调用后端的情况。若还包括特定工具调用兼容层，应将其准确名称及作用放在来源记录，不用 `shared` 代替解释。

对应意见：E07、M14、W03、W06。

---

**C16｜A2.11，第 41 行**

原句：

> Individual migration allows 40 investigation and repair calls, 120,000 output tokens, 1,800 seconds, and four submissions.

英文候选：

> Each task in the main program migration comparisons allows up to 40 investigation and repair calls, 120,000 output tokens, 1,800 seconds, and four submissions.

保留所有预算；`up to` 表示上限，不表示每项任务都用了四次提交。

对应意见：W07、R07、最新第 4 项。

---

**C17｜A2.14–A2.15，第 41 行，部分待核对**

原文：

> Agent calls allow at most 16,384 output tokens, while initial translation and the repair loop that rewrites the complete candidate allow at most 131,072 per call. The latter has four repair rounds.

建议先确认整文件修复循环是否就是表中 `Test-guided repair`。若一致，候选为：

> Calls made by LaDiM, SWE-agent, and MatchFixAgent allow at most 16,384 output tokens each. Initial translation and test-guided repair allow at most 131,072 output tokens per call. Test-guided repair allows up to four repair rounds.

须核对：

1. 16,384 是否确实适用于上述全部方法。
2. 131,072 是模型/API 单次配置上限，还是实验中实际允许使用的 token 额度。
3. 它如何受累计 120,000 输出 token 预算约束。
4. 初译是否属于该累计调查／修复预算。

现有材料可以确认这些数字存在，不能确认上述预算执行关系，因此不添加“自动取剩余额度最小值”等实现细节。

对应意见：E06、E07、W03、W07、最新第 4 项。

### C18–C24：随机种子与确认阶段

**C18｜A3.01，第 47 行**

原句：

> The main MindSpore and Java/DJL comparisons use seed 101 for public evaluation and seeds 202 and 303 for confirmation of a passing candidate.

英文候选：

> The main MindSpore and Java/DJL comparisons use seed 101 for the evaluation available during repair. A candidate that passes this evaluation is checked again with seeds 202 and 303.

主代理需确认 `public evaluation` 的确表示修复期间可见的评价。若仅表示主评价而不涉及可见性，应采用更保守的候选：

> The main MindSpore and Java/DJL comparisons first evaluate candidates with seed 101 and confirm passing candidates with seeds 202 and 303.

对应意见：E04、W03、W07。

---

**C19｜A3.06，第 47 行，需核对所指研究**

原句：

> The component comparisons on these programs use the same settings.

问题：`these programs` 可以指 Java/DJL，也可以回指整个主比较；它还容易与主文十份初译程序上的交接／历史比较混淆。后者在下一段使用 42、1042、2042，不能自动套用 101、202、303。

若仅指主 MindSpore 集合的程序组件比较：

> Component comparisons on the main MindSpore collection use the same evaluation settings.

若也覆盖 Java/DJL，需逐项写明对应集合。若本句没有独立研究需要说明，可删除重复句，不能为消除歧义修改真实种子。

对应意见：B02、B04、W07、最新第 9 项。

---

**C20｜A3.07，第 50 行**

原句：

> All ten natural translation tasks use seed 42 for public evaluation and 1042 and 2042 for confirmation.

英文候选：

> The study of ten initially translated programs uses seed 42 for the initial evaluation and seeds 1042 and 2042 for confirmation.

段首对应改为：

> Initial translations and training signals.

如这里的 `public` 特指修复期间反复调用的评价，最终应沿用 C18 核实后的统一名称，避免把“每轮公开评价”误缩成“仅首次评价”。

对应意见：E08、B02、W03、最新第 6 项。

---

**C21｜A3.12，第 50 行，需确定具体集合**

原句：

> The additional repair collections retain their original unit probes and apply their task-specific acceptance checks without an additional multi-seed confirmation stage.

问题：本句没有指明哪些集合；`unit probes` 也没有具体检查对象。不能让读者误以为所有附加实验都不做多种子确认。

英文结构候选：

> [Names of the specific repair collections] use their original tests and acceptance criteria, without an additional confirmation stage across random seeds.

方括号须用冻结来源确认后的集合名替换。若所指研究在后续附录各自已有完整协议，优先把此句移动到对应研究段落。

对应意见：E01、E04、W03、W06、W07。

---

**C22｜A3.16 与 A5.06，第 53、71 行**

重复原句：

> TorchAX transfers the candidate to JAX, where native differentiation and Optax perform the checked training step.

集中保留位置：A.5 第 71 行。

推荐集中表述：

> TorchAX executes the candidate with JAX arrays, JAX computes gradients, and Optax applies one SGD step.

处理方案：

- 删除第 53 行重复句。
- 主文移来的 TorchAX 执行后端说明与第 71 行合并。
- 主文保留 Ivy／torch2jax 作为实际比较方法的定义。
- 不给 TorchAX 新增 0/6 基线行。

对应意见：E10、R10、W06、最新第 2 项。

---

**C23｜A3.28，第 62 行**

原句：

> The protocol assigns seeds 202 and 303 to confirmation after all public checks pass; the reported recommendation runs finish at the public evaluation.

英文候选：

> Confirmation with seeds 202 and 303 is triggered only after all checks with seed 101 pass. The reported recommendation runs do not reach this confirmation stage.

该改写直接说明实际执行范围，保留已有事实，不附加新的限制性结论。

对应意见：W07、E04。

---

**C24｜A3.30，第 62 行**

原句：

> For their exact-value history-encoder checks, the public task supplies the source parameters initialized with PyTorch seed 42.

英文候选：

> For checks that require exact history encoder outputs, the task supplies source parameters initialized with PyTorch seed 42.

主代理核对原测试确实检查输出的精确值；若检查对象还含内部状态，应保留更宽的表述：

> For exact comparisons involving the history encoder, the task supplies source parameters initialized with PyTorch seed 42.

对应意见：W01、W04、W07。

### C25–C28：训练信号实验

**C25｜A4.01，第 66 行**

原句：

> The training signal and JAX studies use the same investigation and evidence handoff procedure with editing examples and format-correction feedback in their tool prompts.

英文候选：

> Both the training signal study and the JAX repair study use the investigation and evidence handoff procedure with editing examples and feedback for correcting tool call formats.

此处应保留配置差异，不删除成“采用相同的 LaDiM 方法”。来源说明明确这些研究使用编辑示例及格式纠正，主比较使用冻结的另一配置。内部版本号继续留在来源记录。

对应意见：B07、W02、W06、W07。

---

**C26｜A4.02，第 66 行**

原句：

> The signal experiment applies four controlled modifications to four model classes.

英文候选：

> The signal experiment introduces each of four faults into each of four model classes, producing 16 candidates.

对应意见：E01、B01、B04、W07。

---

**C27｜A4.04，第 66 行**

原句：

> Each setting retains the initial investigation, current workspace, and cumulative call budget.

最低限度候选：

> All feedback conditions retain the initial investigation and current working files and use a cumulative call budget.

本句仍需主代理核对：`retains` 指在整个修复过程中保留，还是四个反馈条件均保留某项机制。若是后者，应直接写保留的机制；若是前者，再补 `across submissions`。不能据本句推导跨实验共用可变工作目录，也不能推导每个工作单元重启 Verifier。

对应意见：B04、M14、W03、W07。

---

**C28｜A4.05，第 66 行**

原句：

> Its visible checks determine whether repair starts and stops.

英文候选：

> In each feedback condition, the checks visible to the agent determine whether repair begins and when it stops.

后接原句：

> Final acceptance uses all training signals on three seeds.

两句共同说明运行中反馈与最终评价的区别，无需另造“反馈门控”等新名词。

对应意见：B01、B04、W03、W07。

### C29–C35：JAX 修复和原生转换

**C29｜A5.01，第 71 行**

原句：

> The six JAX candidates comprise an execution, forward, and gradient fault in each of an MLP and a CNN.

英文候选：

> The JAX repair study uses three faulty versions of an MLP and three of a CNN. For each model, the versions contain an execution fault, a forward fault, or a gradient fault.

对应意见：R09、R11、E01、W07。

---

**C30｜A5.02，第 71 行**

原句：

> LaDiM and Direct repair receive the same source programs and original candidates and retain their respective procedures.

英文候选：

> LaDiM and Direct repair receive the same source programs and faulty candidates and use their respective repair procedures.

对应意见：E07、E08、W03。

---

**C31｜A5.03，第 71 行**

原句：

> Each allows four submissions, 40 LLM calls, 120,000 output tokens, and 1,800 seconds, including investigation.

英文候选：

> For each task, both methods allow up to four submissions, 40 LLM calls, 120,000 output tokens, and 1,800 seconds, including investigation.

保留其后“所有任务首次提交即通过”的真实结果。

对应意见：W07、最新第 4 项。

---

**C32｜A5.05，第 71 行**

原句：

> LaDiM uses 76 calls and 674,009 tokens; Direct repair uses 57 calls and 353,311 tokens.

英文候选：

> Across the six tasks, LaDiM uses 76 LLM calls and 674,009 tokens. Direct repair uses 57 calls and 353,311 tokens.

不删除 Direct repair 成本较低的事实，也不以此自动削弱 JAX 修复有效性的主张。

对应意见：R14、W02、W04、W07。

---

**C33｜A5.07，第 71 行**

原句：

> Loss absolute difference, gradient norm absolute difference, and relative parameter update thresholds are 0.02, 0.05, and 0.03.

英文候选：

> The thresholds are 0.02 for the absolute loss difference, 0.05 for the absolute difference between gradient norms, and 0.03 for the relative difference between parameter updates.

如 A.5 与 A.6 确实共用第 82–84 行公式，可增加公式引用，避免重复定义；是否共用相同 \(\epsilon\) 需先核对。

对应意见：M03、E05、W07。

---

**C34｜A5.16，第 73 行**

原句：

> Each converter's healthy MLP and CNN controls pass.

英文候选：

> Both converters pass the checks when given known-correct MLP and CNN programs.

为遵循减少非必要连字符的偏好，可采用：

> Both converters pass the checks when given MLP and CNN programs known to be correct.

对应意见：R10、E08、W03、最新第 6 项。

---

**C35｜A5.17，第 73 行**

原句：

> Ivy spends 561.935 seconds on the six faulty candidates and 191.663 seconds on its healthy controls; \texttt{torch2jax} spends 39.234 and 15.930 seconds.

英文候选：

> Ivy takes 561.935 seconds for the six faulty candidates and 191.663 seconds for the two correct control programs. The corresponding times for \texttt{torch2jax} are 39.234 and 15.930 seconds.

不把这些时间改称为“每项任务平均耗时”，也不从时间值推导未给出的转换吞吐。

对应意见：W04、W07、E08。

### C36–C41：检测量、阈值与轨迹

**C36｜A6.04，第 78 行**

原句：

> Loss, gradient norm, and relative update thresholds are 0.02, 0.05, and 0.03.

英文候选：

> The detection thresholds for the absolute loss difference, the absolute difference between gradient norms, and the relative parameter update difference are 0.02, 0.05, and 0.03, respectively.

这是检测差值阈值，不是要求 loss 本身小于 0.02 或梯度范数小于 0.05。

对应意见：M03、E05、F05、W07、最新第 5 项。

---

**C37｜A6.05，第 78 行**

原句：

> Figure~\ref{fig:gradient-drift} uses trajectories with separate state and reports the mean and range across 12 runs per fault.

英文候选：

> Figure~\ref{fig:gradient-drift} shows trajectories in which the source and target retain their own states. For each fault, it reports the mean and range over 12 runs, comprising four models with three seeds each.

对应意见：F05、W03、W07、最新第 5 项。

---

**C38｜A6.06，第 78 行及相关图注，需冻结数据确认映射**

原句：

> The loss threshold crossings at steps 31 and 18 refer to mean curves.

现有材料能够确认：

- 测量对象是源与目标的 loss difference。
- 检测阈值为 0.02。
- 31 和 18 是均值曲线越过阈值的步数。
- 每种故障有 12 条轨迹，即四模型乘三种子。
- 这些步数不是 SWE-agent 或 MatchFixAgent 的首次检测时刻。

现有快照没有明确给出：

- 31、18 分别对应哪一种故障；
- 用户指出的 3/12、4/12 分别对应哪一种故障。

可直接采用的最小候选：

> The mean absolute loss differences cross the 0.02 threshold at steps 31 and 18 in the two fault conditions.

该句仍不能完全满足“分别对应何故障”的要求。主代理核对后应采用具名完整形式：

> For [fault corresponding to step 31], the mean absolute loss difference crosses 0.02 at step 31. For [fault corresponding to step 18], it crosses the threshold at step 18.

相关图注中的个体轨迹说明应写成：

> Within the 50 training steps, the absolute loss difference crosses 0.02 in 3 of 12 runs with [verified fault] and 4 of 12 runs with [verified fault]. Each group contains four models evaluated with three seeds each.

以上方括号是审查方案中的待核对位置，不是可直接提交的论文文本。不要根据句子先后顺序猜测对应关系，也不要把均值跨越时刻用于概括全部个体轨迹。

对应意见：F05、W07、最新第 5 项。

---

**C39｜A6.07，第 78 行**

原句：

> Direct gradient or update checks detect all respective faults at step~1.

英文候选：

> Gradient checks detect gradient scaling at step~1 in all 12 runs, and parameter update checks detect partial update suppression at step~1 in all 12 runs.

该对应关系由本段两种故障和 `respective` 所述直接检测机制支持。执行时仍应与生成数据中的两个故障标签逐项核对。

对应意见：F05、R13、W07。

---

**C40｜A6.08，第 78 行**

原句：

> Healthy translations pass the recorded checks, with maximum loss difference \(3.815\times10^{-6}\).

英文候选：

> Translations known to be correct pass all recorded checks, with a maximum absolute loss difference of \(3.815\times10^{-6}\).

保留 `recorded checks` 的真实范围，不扩展为未执行的所有测试。

对应意见：E08、W02、W07、最新第 6 项。

---

**C41｜A6.F00，第 80 行**

原文：

> The scalar summaries are

英文候选：

> The detection study uses the following scalar differences:

三个公式不变。公式后的主迁移张量比较说明保留，避免把范数差验收误写成所有实验共用的张量级验收。

对应意见：M03、E05、W07。

## 5. 公式专项核查

| 对象 | 当前含义 | 审查结论 |
|---|---|---|
| \(\Delta_{\mathrm{loss}}=|L(P)-L(\hat P)|\) | 源与目标的 loss 绝对差 | 保留；检测图和正文应统一写 absolute loss difference。 |
| \(\Delta_{\mathrm{grad}}=\left|\|\nabla_\theta L(P)\|_2-\|\nabla_{\hat\theta}L(\hat P)\|_2\right|\) | 两个梯度向量各自取二范数后再求绝对差 | 保留；不能改写成 \(\|\nabla L(P)-\nabla L(\hat P)\|_2\)。 |
| \(\Delta_{\mathrm{param}}=\|\Delta\theta-\Delta\hat\theta\|_2/(\|\Delta\theta\|_2+\epsilon)\) | 以源更新范数归一化的参数更新差 | 保留；归一化方向不能改成目标范数或对称平均。 |
| \(\Delta\theta,\Delta\hat\theta\) | 源与目标参数更新 | 第 86 行已有定义。 |
| \(\epsilon\) | 防止分母为零 | 作用已有说明；具体值未出现在快照，需核对已有定义或冻结实现。 |
| 图中归一化 | 每个差值除以对应检测阈值 | 文本自洽；图内阈值若显示为 1，应明确是归一化后的阈值。 |
| 主比较验收 | 按任务使用张量比较及绝对／相对容差 | 第 86 行的区别说明必要，保留一次即可。 |

没有建议修改任何公式计算逻辑，也没有建议重新计算阈值或运行实验。

## 6. 生成器与资产同步位置

| 调整内容 | 已知同步位置 | 同步要求 |
|---|---|---|
| 数据集表 `Saved initial translations` 等标签 | `scripts/summarize_paper_collections.py` → `figures/TABLE_task_collections.tex` | 修改生成标签来源，保留四列及所有任务数；不新增平均长度。 |
| 数据集表图注／表注 | `sections/supplementary_experiments.tex:8` | 当前表注可保留。 |
| 源长度定义移出正文 | `sections/supplementary_experiments.tex:25`、`data/paper_figures/README.md` 中集合统计说明 | 与已有来源说明合并，保留 `collection_statistics.json` 中统计，不重复追加同义段落。 |
| 成本表内重复基线引用 | `figures/make_unified_results.py` → `figures/TABLE_program_costs.tex` | 修改生成器对应附录表输出分支；不删除实验设置中的首次方法引用。 |
| 成本表表注、独立舍入说明 | `sections/supplementary_experiments.tex:28` | 修改正文 caption；所有数值单元格不动。 |
| `initially passing/failing inputs` 的统一解释 | 第 20 行；如主文成本图标签同步调整，则涉及 `figures/make_unified_results.py` 输出的 `repair_comparison.pdf/.png/.svg` | 图中仍保留 20／9 分组和全部 29 个输入，不改排序、差值或三根总量横柱。 |
| TorchAX 说明移入附录 | `sections/supplementary_experiments.tex:53,71`；主文原句位置未提供 | 集中到第 71 行附近，避免附录内再次重复；不新增 TorchAX 比较行。 |
| JAX 正确程序对照措辞 | `sections/supplementary_experiments.tex:73` | 本轮仅正文需要明确修改；`TABLE_jax_repairs.tex` 未提供源码，不声明已审查其全部标签。 |
| 检测均值曲线、个体轨迹和阈值说明 | 第 78、86 行；`fig:gradient-drift` 对应图注及 `gradient_drift.pdf` 等资产 | 生成器确切路径未在快照给出，留主代理定位；必须同步核对故障名称、31／18、3/12／4/12 和阈值 0.02。 |

来源说明确认 `figures/make_unified_results.py` 还生成多个其他表和结果 JSON。后续仅为标签修改运行该生成器时，应核对数值单元格没有变化；本审查没有运行生成器。

JAX 原生转换记录的已知来源是压缩包中的 `formal_v5/converter_results.json` 与 `private_backend/track_c_external.py`。它们可供主代理核对转换器故障、正确程序对照和时间口径，不能因修改文字而改变冻结记录。

## 7. 需要主代理核对的证据缺口

| 编号 | 位置 | 需要核对的具体问题 | 对方案的影响 |
|---|---|---|---|
| V01 | 第 39 行 BF16 容差 | \(10^{-2}\) 绝对容差是否仍与一般相对容差共同使用 | 决定是否补充 relative tolerance；现有数值不改。 |
| V02 | 第 41 行预算 | 16,384／131,072 的适用方法、累计 120,000 的执行方式、初译是否计入累计修复预算 | 决定 C17 的方法命名及预算说明。 |
| V03 | 第 84–86 行 | \(\epsilon\) 的真实值，以及 JAX 与检测研究是否使用同一实现 | 决定是否补值和共享公式引用。 |
| V04 | 第 47、50 行 | `component comparisons`、`additional repair collections` 分别指哪些冻结研究 | 防止把主比较种子套到十份初译组件实验或其他附加集合。 |
| V05 | 第 66 行 | `retains the initial investigation, current workspace` 的实际时间／条件范围 | 防止虚构共享可变工作目录、固定诊断路径或 Verifier 重启机制。 |
| V06 | 第 78 行及检测图 | 31／18、3/12／4/12 与两种故障的准确对应，以及个体跨阈值统计窗口 | 完成具名英文候选；不得凭列举顺序推断。 |
| V07 | 第 18 行与成本表 | test-guided repair 是否保留初始通过应用，七个接受任务的实际类别 | 解决“all repair methods”与 7/18 的直接冲突。 |

## 8. 最重要发现与裁定事项

1. **Java/DJL 段存在需要优先解决的结果描述冲突。** “所有修复方法都保留初始通过应用”与 test-guided repair 的七个教材例子、表中 7/18 无法同时成立。建议先把保留应用的主语限定为已有文本支持的 LaDiM、SWE-agent 和 MatchFixAgent，最终依据逐任务冻结结果确认；表格数值不先动。

2. **检测段仍未达到最新可读性要求。** 需要明确 loss difference 越过 0.02、12 是四模型乘三种子，并分别标明 31／18、3/12／4/12 对应故障。快照不足以确认故障映射，主代理必须核对原数据。均值跨阈值步数始终不能写成基线 agent 检测时刻。

3. **TorchAX 已有合适的附录落点，但附录内部重复。** 第 71 行清楚区分 TorchAX 执行、JAX 求导和 Optax 更新，建议集中保留；删除第 53 行重复句，并吸收主文迁来的后端说明。Ivy／torch2jax 的主文方法定义继续保留。

4. **预算需要同时说明单位、范围和实际执行次数。** JAX 的 40 次调用是每任务上限，76／57 是六任务合计；四次提交是上限，所有六项任务实际首次提交即接受。第 41 行单次 131,072 与累计 120,000 的执行关系需要核对，不能靠行文自行补出实现。

5. **十份初译程序及正确对照程序应直接命名。** 数据集表的 `Saved initial translations`、种子段的 `natural translation tasks`、JAX 的 `healthy controls` 和检测段的 `healthy translations` 都有具体、可替换的普通表述。三个研究的初始状态和分母保持独立，程序组件实验仍用十份初译。

6. **平均长度和孤立长度定义可从论文叙述中清理，实验事实保持完整。** 删除第 18 行 221.2 平均长度，长度计数方法留在来源说明；保留四／二个源程序对任务构造的解释。三条检测公式、所有阈值、成本、接受数和有证据支持的结果力度均不需要修改。
