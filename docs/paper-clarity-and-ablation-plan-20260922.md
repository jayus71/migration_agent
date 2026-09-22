# 论文清晰度与仓库模块消融修改方案

本轮以 `10e3710` 为检查点。先验证自动结构映射模块，并给出可审阅的修改方案；本文件尚未应用到论文正文、图表或方法图。

方案初稿已保存为 `37220f1`。本轮只更新方案与独立实验文件，论文正文继续保留在原版本。

当前主要问题是：实验设置承载了过多评估器细节，结果段夹杂修复日志，部分分组出现时没有定义，仓库组件的独立作用也没有被现有累计消融区分。下一版围绕“迁移是否成功、成功需要多少成本、哪些设计带来改进”组织实验论证。

## 1. 优先验证自动结构映射

现有累计消融最后一级同时加入结构映射、依赖规划、检查点、notebook 单元编辑、证据检索和上下文重建。时间序列上的成本改善属于这一整组组件，尚不能归因给结构映射。

子代理负责独立实验目录 `experiments/repository_map_ablation_20260922/`，使用原远端的冻结运行时。首轮固定比较完整 LaDiM 与移除自动结构映射的 LaDiM，在时间序列和推荐两个现有仓库各新运行一对，共四次运行。

| 项目 | 固定设计 |
|---|---|
| 唯一移除项 | 工具自动提供的文件、导入、函数/类、notebook 单元结构，以及自动未分配文件清单 |
| 保留能力 | 普通列目录、搜索、读取，智能体自行规划工作单元，依赖约束，局部检查，notebook 编辑，证据保存与上下文重建 |
| 共同条件 | 同一源仓库、初始翻译、任务要求、LLM、输入、初始参数、评价种子、阈值和完整验收 |
| 每次预算 | 80 次模型调用、480,000 输出 token、3,600 秒、最多四次提交 |
| 主要结果 | 完整仓库是否通过、各类功能和训练检查的覆盖、总 token 与调用次数 |
| 机制证据 | 映射是否被实际读取，规划了哪些关联文件，每次提交的通过情况及累计成本，依赖修改后的复查情况 |

需同时核对初始提示、工具输出和上下文重建，确保移除的信息没有从其他入口自动返回。普通工具仍能读取相同源代码，因此两组比较的是结构整理的作用。

首轮用于取得完整配对证据。建议随后预先固定追加两轮，在两个仓库都完成相同重复，报告三轮的配对结果及波动。重复 LLM 运行与评价程序使用的随机种子是两件事，不能用三个评价种子代替三次独立运行。追加重复和更大的组件矩阵列为后续实验方案，当前先执行上述四次运行。

首轮四次运行已完成，129 项最终审计通过。时间序列两条件都通过完整验收，均在第二次外部提交后接受：完整方法使用 30 次调用和 2,126,900 总 token；移除自动映射后使用 42 次调用和 2,651,248 总 token，完整方法节省 19.8%。推荐两条件均用完 80 次调用，最终均为 131/145、未完整接受；完整方法使用 9,961,503 总 token，移除映射后为 7,172,218，前者多 38.9%。完整方法在推荐的第三次提交达到 131，移除映射后在第四次达到。费用核查、轨迹与小型可提交证据见 `docs/repository-map-ablation-20260922.md` 和 `data/audits/repository-map-ablation-20260922/`。

当前结果适合将自动映射呈现为仓库调查与规划的辅助机制，并分别解释时间序列的成本改善及推荐的修复进展；它尚未提高两个仓库的最终接受结果，成本效应也随仓库不同。映射与依赖规划的组合价值需要另设“保留映射、关闭依赖规划”的对照来区分。现阶段保留仓库协调方法的位置，单独验证规划后再确定该模块在贡献和方法图中的权重。

## 2. 方法章恢复职责与因果关系

Orchestrator 的主句采用：

> The Orchestrator schedules their work and returns verification results after each submission to guide further repair.

对应正文、摘要和图注统一“调度、验证、反馈”的职责。方法章先说明训练差异如何引导调查，再说明调查证据如何帮助修复，最后说明多个文件之间如何协调。

仓库映射部分用具体动作解释：程序分析汇总文件、导入、函数和类、notebook 单元；智能体据此把相关文件组织成工作单元并记录依赖；共享实现被修改后，相关调用方需要重新检查。把结构信息、智能体制定的计划以及依赖检查分清，避免一句话堆叠多个未解释名词。

删除重复讲解伪代码控制流的句子，包括 “Otherwise, the initial measurements support diagnosis, and the resulting evidence starts the repair loop.”。它的实际含义只是“初始程序未通过检查后，先调查失败原因，再交给修复智能体”，算法已经表达了这一顺序。

继续检查方法正文中的工具记账：edit 的操作计数、阶段 flags 的更新细节、预算变量如何扣减等，分别放在伪代码或附录。正文保留其作用，例如修复智能体测试修改后的代码，外部验证结果指导后续修改。

## 3. 缩短 setup，把任务先讲清楚

沿用加粗标签，不增加多级标题。正文保留任务来源及用途、初态分组、比较方法、核心接受标准、主要调用预算和成本范围。数值容差、BF16 特例、seed、状态同步细节、各类检查的计数分解、输出 token/时间限制及停止处理统一放入附录。

在 Tasks 中明确说明十个修复实例来自保存的首次翻译结果，其中五个需要修复、五个已通过初始检查；该研究允许修改候选程序及其支持库。这样读者在结果段看到修复与保留两列时已经知道比较对象。实际模型列表和详细运行条件仍在附录。16 个注入故障用于训练信号消融，JAX 六例用于检查另一目标框架上的适用性，各自用途在首次出现时交代。

初态分组统一使用普通描述：`programs that require repair` 与 `programs that pass the initial checks`。图中可用 `Needs repair` 与 `Passes initial checks`。正文不再把源输入称作 faulty inputs，也不把通过有限检查直接写成绝对正确。

| 当前句子 | 实际含义 | 修改位置 |
|---|---|---|
| individual programs retain their own state over two consecutive steps, and repositories use three | 源和目标从相同参数开始，各自连续训练两步或三步，中途不把目标参数重新替换成源参数，从而检查更新误差是否传播 | 连续训练是评价设计；具体两步/三步与初态规则放附录，正文概括检查训练行为 |
| A submission can follow several model calls and edits | 一次交给外部验证器检查之前，智能体可能多次读代码、调用模型和修改代码 | 从 setup 删除，必要的提交定义放方法或附录一次 |
| Supplied-candidate studies report repair costs | 给定初始翻译的修复研究不把此前生成翻译的费用算入本次修复成本 | 对应表注说明 token 范围，详细成本规则放附录 |
| Failures remain in the task denominator | 失败任务仍计入总任务数 | 附录的评分规则 |
| acceptance at each budget scores the current candidate | 在某个预算下，评估当时的代码，而不是取历史上最好的版本 | 附录的预算与验收规则 |

上述规则继续用于实验和数据统计。正文用一句附录引用承接完整复现信息。

Evaluation protocol 的拟替换核心段落如下，比较方法与共同预算另保留一小段：

> We compare methods on common source programs, evaluation inputs, and corresponding initial parameters. Repair methods also receive the same initial translations. Acceptance requires agreement in execution, forward values, gradients, and parameter updates, together with the task's optimizer and interface checks. Repository evaluation also covers shared entry points and the original tests. Candidates that pass the initial evaluation are checked on additional seeds. The appendix gives the numerical tolerances, training schedules, and detailed checks.

此处的附录编号在应用方案时由 LaTeX 引用生成。训练步数、每类检查数量和停止规则不再挤在这段定义中。

## 4. 主结果围绕优势展开

MindSpore 段落按“完整接受 → 成本优势 → 优势来源”组织：50/50 接受，较 MatchFixAgent 少用 57.4% token；46/50 在首次提交后通过，第二次达到 50/50；调用减少到 326 次，输入 token 的减少占总节省的 93.0%。解释效率优势同时出现在需要修复和初始检查已通过的程序中。图 3 为这种分解提供证据。

主文删除 27/29、7/9 这组突然切换分母的叙述。7/9 指九个不同的、初态未通过的源程序与评价设置组合中，七个在首次提交后修复成功，既不是七类故障，也不是主表中的七个任务。50 个任务标识与不同组合的对应关系、实际调用去重方式保留在附录。图 3 的数据点保持真实，不扩充成 50 个独立运行；图注说明分组含义，精确计数与去重说明放附录。

跨语言段落解释新增成功案例所体现的训练语义修复能力，并结合相同预算下的接受与成本比较。仓库段落分别解释“共享模型在多个入口中完成迁移”和“推荐任务的训练、推理、检索覆盖”，用最相关的数值支撑，不重复整行表格。

## 5. 修复分析突出结果，案例细节进附录

将 `Repairing Natural Translation Faults` 改为更直接的 `Repairing Translation Errors`，并与 setup 中十个保存的初始翻译对应。

本段的主张是：LaDiM 修复了五个失败翻译中的四个，同时保留五个已通过检查的程序；三个对照方法保留原已通过的程序，但未修复这五个失败翻译。新增成功全部来自错误修复，可以直接支撑整个诊断与修复流程的有效性。独立调查这一组件的贡献由对应消融解释。

拟替换段落先用下面两句表达实质结果，再根据修复记录选取一个能解释训练语义的例子：

> LaDiM raises acceptance from five to nine of the ten saved translations by repairing four programs that fail the initial checks and preserving the five that already pass. Direct repair, SWE-agent, and MatchFixAgent retain the initial five successes but recover none of the failed programs.

将 LSTM 的运算注册、张量索引递归、dispatch cycle、三次提交日志全部移到附录。正文如保留案例，只用一句说明“修复涉及支持库中的运算实现与调用关系”，并连接到训练行为恢复这一结果。删除段末重复总结修复流程的句子。

## 6. 图 4 与 JAX 各自回答明确的问题

图 4 的科学问题是：直接检查梯度和参数更新，能否比只检查损失更早发现差异。梯度错误可暂时不改变当前损失，更新错误可暂时不改变当前损失和梯度；在成文中用两句说明，去掉分号。阈值、状态同步对照及详细健康检查转入附录。

图中文字拟用 `LaDiM detects at step 1` 和 `Loss check detects at step 31/18`，在对应文字或图注明确后者是均值曲线的检测位置。31/18 的现有数据来自损失曲线，不是 SWE-agent、MatchFixAgent 或笼统“common methods”的实测检测时间，因此不能替换成这些方法名称。

JAX 的当前正式修复比较运行了 LaDiM 与直接修复，两者都是 6/6，后者成本更低。另有 Ivy 和 torch2jax 的原生转换结果，但它们接收带故障的候选，测量的问题不同。当前六例没有 SWE-agent 或 MatchFixAgent 的修复运行。

用户随后要求扩大 JAX 实例并研究提升方法表现。当前六例的最终补丁全部只改一行，分别修正多余函数参数、输出缩放或梯度截断，且只涉及 MLP/CNN 和单步 SGD。新研究应增加真实迁移中的模型结构、连续训练状态和优化器语义，并用开发实例改进方法。正式比较前固定未用于调试的任务、方法版本与预算，再让 LaDiM、直接修复、MatchFixAgent 和 SWE-agent 接收同一初始候选。旧六例及其成本保留为原有实验，不把新旧协议混成同一表。

JAX 子代理负责独立目录 `experiments/jax_expansion_20260922/`，先推进两个受控开发任务：残差 MLP 的连续 momentum SGD 更新，以及 attention 的连续 Adam 更新。每例运行三个训练步和三个评价种子，比较完整的逐参数梯度、更新与参数状态，同时检查前向值、损失和对应初态。启动前必须验证健康实现在两框架间通过、目标故障确实被检出。

开发研究先运行 LaDiM 与共享工具的直接修复，共四个条件，每个条件最多 40 次模型调用、四次提交，单 worker 执行。它用于发现诊断、证据交接或修复流程中的具体改进点，所有版本和结果留档。初始注意力健康检查暴露的近零梯度数值问题已在离线阶段处理；第二版十二个健康/故障检查全部通过。四个开发条件现已全部完成，两方法均在首个提交后通过两例；LaDiM 使用 352,624 token，直接修复使用 278,439，前者多 26.6%。这一组尚未体现独立诊断收益，后续从轨迹检查额外开销，并继续完成下面的自然迁移研究。

正式扩展的来源池已经冻结为 PyTorch 官方示例的八个原始文件、九个模型训练任务：MNIST CNN、超分辨 CNN、VAE、DCGAN Generator、RNN 语言模型、Transformer 语言模型、时间序列 LSTM、Actor-Critic 与 REINFORCE Policy。固定上游版本为 `acc295dc7b90714f1bf47f06004fc19a7fe235c4`，来源和逐文件哈希保存在 `experiments/jax_expansion_20260922/formal_source_pool/manifest.json`。该池在开发 API 结果出现前选定，九任务各三个种子的源端连续训练检查已全部通过。原生 JAX 验收及基线接入继续准备。

用户进一步要求增加初始就存在问题的程序或更复杂的程序，并彻底替换旧六例。按此扩充来源准备，优先新增官方 GAT、minGPT 的三层因果语言模型以及带 BatchNorm 状态和跨阶段残差连接的 ResNet，目标为十二个模型任务的来源池。新增源码和许可证已下载，固定版本与哈希保存在 `output/jax-complex-source-review-20260922/manifest.json`；接入时保留原九任务准备记录，另写扩充后的任务清单。

十二任务的扩充清单现已另行保存为 `formal_source_pool/manifest_12_tasks.json`，36/36 项源端三步训练检查通过。新增模型参数量分别为 GAT 214、GPT 86,928、ResNet 4,908,357；后者在远端 CPU 上每种子的三步源训练约 0.44 秒。源码结构、状态和完整梯度的检查范围共同描述任务复杂度，不以参数量独自代表难度。

新修复组在任何修复方法运行前，由共同首次翻译的初始验收确定：纳入来源池中全部未通过检查的候选，让四种方法修复相同的问题程序。保留整个来源池的初始通过与失败记录，已通过的候选单独用于确认能力分析。这个设计直接测量修复成功率，能观察复杂程序中的分层诊断效果；不会将初始已通过的程序计作成功修复。

通过一次共同翻译得到每例的原生 JAX/Optax 初始候选，固定任务和候选后运行四种修复方法。任务测量给定模型的连续训练，不声称迁移源文件中的数据下载、环境交互和整个应用。Dropout 模式、VAE 采样及 BatchNorm 缓冲状态在所有方法共用的任务要求中预先声明。正式任务不使用上述两个开发程序，也不依据已经观察到的方法输赢选择实例。MatchFixAgent 与 SWE-agent 的原生算法、提示和工具流程保持一致，新增工作集中在共同的 JAX 执行和验收接入。最终报告接受率、达到接受所用的提交次数、调用及完整 token 成本，并用多步训练中的失败类型解释差异。

验收脚本的独立审阅还要求核对参数形状、从更新前快照计算参数变化，并验证梯度确实由 JAX 对当前计算求导。开发运行保留已冻结判定，最终候选另做这三项离线复验；正式验收内置相应检查。

正式候选实现原生 JAX 的模型计算及缓冲状态更新，外部执行器对当前损失求导并执行合同指定的 Optax 优化过程。正文将其表述为模型迁移后的训练一致性比较。十二次共同初译和完整初始验收已在独立进程启动；修复集合据此确定。真实候选中的语法错误也进入修复组，API 无返回或没有任何候选程序的情况另记生成失败及费用。

JAX 主文将以这组新程序及共同协议比较替换旧六例，保持 `Generalization Across Frameworks` 标题。结果段围绕修复成功、成本及复杂结构中的差异展开，旧六例及转换器结果保留在历史记录和附录，新的分母与其分开。此轮先完成实验与修改方案，正文在方案执行时更新。

新表统一列出 LaDiM、Direct、MatchFixAgent 和 SWE-agent 的修复成功数、调用次数与完整 token 成本。setup 先交代程序来源、自然初译及初始失败这一选择条件；结果段先比较修复能力，再用实际记录解释注意力、循环计算或缓冲状态等结构中解决了什么问题。通过预算 1、2、4 的结果只选必要数字写入分析，其余完整进展放附录。新的任务数量和成本都由冻结结果生成。

## 7. 增强智能体消融的解释力

现有累计消融在两个仓库上最终结果均相同，每格只运行一次，且最后一级合并了多个组件。它适合报告这次运行的成本变化，对单个组件的因果贡献支持较弱。

下一组主消融建议以完整方法为共同参照，分别移除初始调查、独立证据交接、自动结构映射、依赖规划或上下文重建，每个对照清楚对应一个研究问题。优先完成当前已授权的映射对照，再决定后续矩阵。使用相同预算、相同初态的配对重复，完整报告两个仓库。

从已有记录提取每次提交时的通过情况与累计 token，呈现修复进展和达到相同完成程度所需的成本。这样既看最终接受，也能看相同最终分数背后的修复效率。跨文件的入口通过情况、共享实现修改后的复查可辅助解释作用。以独立仓库运行作为比较单位，不把同一次运行中的 69 项检查当作 69 个独立实验。

现有自然翻译的修复历史与独立交接消融也可辅助说明智能体机制，分别保留各自任务和实现设置。正式矩阵预先固定仓库、分母和预算，并汇总所有运行。

## 8. 行文和方法图

全文逐段检查每个句子与段落主张的关系。能帮助理解设计、解释结果或明确关键比较条件的内容留在正文；复现步骤和案例日志进附录；已经由算法、表格或前文充分表达的重复句删除。

减少用连字符临时拼出的修饰语，例如 `model-call` 改为 `LLM calls`，`tool-execution step` 改为 `tool execution`，`target-framework operations` 改为 `operations in the target framework`，`loss-difference curves` 改为 `curves of the loss difference`，框架迁移方向用 `from PyTorch to MindSpore`。保留 SWE-agent 等正式名称，以及用户已经指定的 state-of-the-art。同步检查 PDF 自动断词，改善局部换行。

方法的核心流程已稳定：初始翻译 → 调查训练差异 → 证据交接 → 修复 → 外部验证，验证后的反馈返回修复智能体。Orchestrator 明确承担调度和验证；各智能体使用 LLM。仓库协调支持调查与修复，包含结构映射、工作单元依赖和证据上下文。框架执行端包含 MindSpore 和 JAX。

方法图由用户负责修改。待文件映射与工作单元规划的作用得到验证后，方法结构和该模块的贡献表述即可确定；本任务不修改或生成方法图。内容方案应用后，统一检查正文、图注、表头和伪代码，并更新固定基线的逐词对比页。

## 核查来源

- `docs/cumulative-component-ablation-20260922.md` 与对应冻结 runner：累计组件和已有八次运行。
- `scripts/repository_agent_mode.py`：自动结构分析、工作单元、依赖约束、检查点和上下文行为。
- `docs/maintext-jax-autonomous-rerun-20260918.md`：JAX 方法范围与正式结果。
- `docs/autonomous-verifier-experiment-20260917.md`、`sections/supplementary_experiments.tex`：十个保存的初始翻译与可编辑范围。
- `data/paper_figures/README.md`、`data/paper_figures/unified_results.json`：主比较任务、成本和不同初态分组。
