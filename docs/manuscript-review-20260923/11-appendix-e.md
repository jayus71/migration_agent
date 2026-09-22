# 附录 E 逐句及表格审查报告

本报告依据主代理提供的 `d1d6a53` 文本快照，审查附录 E 的全部正文、两张表的表注、表头和数据行。所有修改均为候选方案，尚未实施。未调用工具、读取其他文件、修改文件、编译论文或重跑实验。

审查采用所附 AGENTS.md、humanizer 规则、Academic-Writing-DNA 和意见清单，以 2026-09-23 最新要求为准。以下实现或统计口径问题，凡快照不足以确定，均明确留主代理核对。

## 1. 范围与覆盖数量

| 对象 | 准确源文件与原行号 | 覆盖数量 |
|---|---|---:|
| 章节标题 | `sections/supplementary_experiments.tex:138–139` | 1 个标题 |
| 正文 | 同文件 `141、152、154、156、158` | 31 句 |
| 两张表的表注 | 同文件 `144、161` | 6 句 |
| 仓库成本表 | `figures/TABLE_repository_costs.tex:1–15` | 1 组表头、2 个分组标签、6 行数据 |
| 推荐仓库检查表 | `figures/TABLE_repository_checks.tex:1–22` | 1 组表头、14 行数据 |
| 算法、独立公式、图 | 本节无 | 0 |

共覆盖 **37 个句子单元、20 行表格数据、2 组表头和2个分组标签**。LaTeX 布局命令另作结构检查，不计作句子。

本节数值之间的加总关系成立。主要问题集中在检查对象的表述、缺测与测试收集失败的解释，以及若干仍需冻结来源才能说明的表头含义。

## 2. 正文逐句台账

“改写”和“删除”均表示建议；“保留”表示本轮未发现需要修改的实质问题。

### 2.1 共同输入与成本口径：原文件第 141 行

| 编号 | 短引文 | 处置 | 理由及对应意见 |
|---|---|---|---|
| E-S01 | “All methods receive byte-identical source repositories…” | 改写 | 相同输入和评价条件必须保留；可用自然语言表达文件一致性，减轻技术记录语气。W01、W04、W07。 |
| E-S02 | “The time series translation has three generation calls totaling 163,661 tokens.” | 保留 | 明确给出初译调用数及成本，支撑后文总成本口径。W07。 |
| E-S03 | “The recommendation translation uses 20 calls totaling 368,368 tokens.” | 保留 | 与上一句构成必要并列，两类仓库各自的初译成本清楚。W07。 |
| E-S04 | “Generation proceeds from the public import structure and includes failed or truncated attempts.” | 改写，部分待核对 | 应明确“包含失败或截断尝试”修饰成本统计；`public import structure` 的具体含义仍需来源核对。W01、W03、W06。 |
| E-S05 | “Each method's reported total contains one complete copy…” | 改写 | `one complete copy of this generation cost` 带账本语气；直接说明初译计一次、随后修复成本全部计入。W01、W06、W07。 |
| E-S06 | “Table… separates input and output usage in repair.” | 删除并合并表引用 | 只复述清楚可见的表头。将表引用并入 E-S05，保留信息定位。W06。 |

### 2.2 时间序列协议：原文件第 152 行

| 编号 | 短引文 | 处置 | 理由及对应意见 |
|---|---|---|---|
| E-S07 | “The time series protocol compares the core model…” | 改写 | 应明确比较源程序与翻译后程序，保留三步 Adam、对应参数、关闭 dropout 和输入形状。W01、W03、W07。 |
| E-S08 | “Preprocessing and prediction absolute tolerances are…” | 保留 | 两个对象与两个阈值对应明确，属于有用的复现实验条件。W07。 |
| E-S09 | “Loss absolute difference, gradient vector L2 difference…” | 改写 | 当前名词串把差值与容差混在一起；改成每个差值对应一个容差。W01、W07。 |
| E-S10 | “Learning rate behavior is checked around its schedule boundaries.” | 保留 | 检查对象及位置明确；无需仅因出现 `behavior` 就机械换词。 |
| E-S11 | “The public evaluation executes the 100-epoch training workflow…” | 保留 | 交代真实执行覆盖及源代码顺序，有独立信息。`100-epoch` 是正常修饰结构，不属于复杂术语堆叠。W07。 |
| E-S12 | “Each entry point must… execute native differentiation.” | 改写 | `execute native differentiation` 不够自然；说明通过目标框架的原生自动微分计算梯度。W01、W03。 |
| E-S13 | “The notebook and snippets provide execution coverage…” | 改写 | 这一分工重要，应把 `paired numerical training measurements` 展开为源程序与翻译后程序的训练数值比较。W03、E05。 |
| E-S14 | “All three methods pass 23 behavior checks per seed…” | 改写 | 将 69 的分母展开为三个种子各23项，说明 public seed 与两个 confirmation seeds。W01、W07。 |

### 2.3 推荐仓库协议：原文件第 154 行

| 编号 | 短引文 | 处置 | 理由及对应意见 |
|---|---|---|---|
| E-S15 | “The recommendation protocol covers six model paths…” | 改写，路径定义待核对 | 需要明确源程序与翻译后程序的比较关系；六条路径具体指什么，快照未给出。不能自行改称六个模型。W03、W07。 |
| E-S16 | “Source exceptions and empty returns are checked…” | 改写 | 当前句没有清楚说出检查的是翻译后程序是否复现源程序行为。W01、W03。 |
| E-S17 | “Both the numerical worker and training command…” | 改写 | `numerical worker` 是执行实现称谓；保留数值评价与训练命令均使用候选程序优化器工厂的事实。W06、M14。 |
| E-S18 | “The source Adam settings use decay coefficients…” | 保留 | 超参数明确，有复现价值，无需为主动语态强行重写。W07。 |
| E-S19 | “Representation absolute tolerance is \(10^{-4}\).” | 保留 | 简洁给出阈值，与表中表示比较相关。W07。 |
| E-S20 | “Loss absolute/relative tolerances are…” | 改写 | 两组斜杠数值加一个相对容差，阅读负担较大；展开绝对与相对的对应关系。W01、W07。 |
| E-S21 | “The evaluation includes all ten original tests…” | 保留 | 测试数、训练轮数和合成样本数明确。W07。 |

### 2.4 推荐仓库检查与缺测：原文件第 156 行

| 编号 | 短引文 | 处置 | 理由及对应意见 |
|---|---|---|---|
| E-S22 | “Table… reports the declared checks on the public seed.” | 改写 | `declared checks` 带内部清单语气；直接说报告推荐仓库在公开评价种子上的检查结果。W01、W06。 |
| E-S23 | “The 114 numerical comparisons comprise 108 checks…” | 保留 | \(6\times3\times6+6=114\)，完整解释关键分母，且与表格相符。W07。 |
| E-S24 | “Twenty-four execution, step count, and native differentiation checks…” | 保留，类别边界待核对 | \(114+24+7=145\) 正确。24项和7项的具体覆盖，以及与表尾各行的包含关系，仍需来源映射。W03、W07。 |
| E-S25 | “SWE-agent and MatchFixAgent each lack one retrieval measurement…” | 保留 | 明确指出两个方法、各一个缺测及其原因，不把缺测伪装成数值失败。W07。 |
| E-S26 | “That entry remains n/a in both the 114 and 145 denominators.” | 改写 | `n/a in… denominators` 混淆单项状态与计数分母；还应包括检索的6项分母。W01、W07。 |
| E-S27 | “MatchFixAgent passes 0/10 original tests: an unmigrated PyTorch import…” | 改写 | 实际为测试收集被阻断，0/10表示确认通过数。应避免被读成十个测试全部执行后失败。W07、E05。 |
| E-S28 | “No method reaches the two confirmation seeds…” | 改写 | `reaches` 隐含未说明的流程门槛；直接陈述这两个种子未执行评价，不编造停止条件。W03、W06。 |

### 2.5 推荐仓库结果：原文件第 158 行

| 编号 | 短引文 | 处置 | 理由及对应意见 |
|---|---|---|---|
| E-S29 | “LaDiM passes all 18 loss and 18 gradient checks…” | 改写 | 表中存在 Forward loss 和 Training return loss 两组各18项检查；单写 `18 loss` 无法唯一对应。W03、W07。 |
| E-S30 | “Later item embeddings diverge in all six model paths…” | 改写 | `Later` 重复后面的步数；`embeddings` 与表中 `representations` 不统一；`diverge` 应说明未通过表示容差。W01、W03、W07。 |
| E-S31 | “These failures remain alongside the successful…” | 改写 | `remain alongside` 只描述结果并存；直接说明 LaDiM 完成了哪些推理、检索、训练及原始测试。W01、W02。 |

## 3. 表注逐句台账

| 编号 | 来源 | 短引文 | 处置 | 理由及对应意见 |
|---|---|---|---|---|
| E-C01 | `supplementary_experiments.tex:144` | “Training checks and complete costs for repository migration.” | 保留 | 准确概括两组训练检查及完整成本。 |
| E-C02 | 同上 | “Gradient and parameter update checks cover three training steps on all evaluated seeds.” | 改写 | 时间序列9项与推荐18项使用不同乘数；表注应直接解释两种分母。W07、E05。 |
| E-C03 | 同上 | “Total tokens include repair input and output plus common initial translation.” | 保留 | 独立阅读表格时需要总成本定义；与正文重复有明确用途。W07。 |
| E-C04 | `supplementary_experiments.tex:161` | “Recommendation repository checks passed on the public seed.” | 保留 | 明确仓库、计数含义和种子范围。 |
| E-C05 | 同上 | “The numerical checks are a subset of behavior checks…” | 改写 | 应明示检查层级，说明下方六行是108项训练检查的分解，避免把上下行相加。W03、E05。 |
| E-C06 | 同上 | “One unmeasured retrieval check remains in each baseline's denominator.” | 改写 | `each baseline` 指向可更清楚；明确两个方法及保留分母的范围。W07。 |

## 4. 需调整句子的具体英文候选

下列候选均保留已有主张与定量结果。标注“待核对”的候选，不应在实现语义未确定时直接采用。

### E-S01：共同输入

原句：

> All methods receive byte-identical source repositories, common initial translations, task requirements, and acceptance procedures.

候选：

> All methods receive identical copies of the source repositories and the same initial translations, task requirements, and acceptance procedures.

理由：保留文件一致性和共同条件，减少 `byte-identical` 的实现记录感。对应 W01、W04、W07。

### E-S04：生成过程与计费对象

原句：

> Generation proceeds from the public import structure and includes failed or truncated attempts.

候选：

> Generation follows the public import structure, and its cost includes failed or truncated attempts.

理由：明确失败或截断尝试计入生成成本。对应 W01、W06、W07。

待核对：`public import structure` 是否指源仓库的公开导入接口、模块依赖结构或其他具体组织方式。当前候选只修复句法，不把这一未定义短语判为已解决。

### E-S05、E-S06：总成本与表引用

原句：

> Each method's reported total contains one complete copy of this generation cost together with every repair call. Table~\ref{tab:repository-costs} separates input and output usage in repair.

候选：

> In Table~\ref{tab:repository-costs}, each method's total includes the common initial translation once and all input and output tokens used during the subsequent repair process.

处置：用一句替换 E-S05，删除 E-S06 的独立表头复述。对应 W06、W07。

待核对：`repair process` 的计费范围是否包含 Verifier 的调查调用。快照不足以确认主比较表的调用分类，不能自行将列名扩成 “Investigation and repair calls”。

### E-S07：时间序列训练比较

原句：

> The time series protocol compares the core model for three consecutive Adam steps from corresponding source parameters, with dropout disabled and input shape $4\times20\times1$.

候选：

> For the time series repository, we compare the source and translated core models over three consecutive Adam steps, starting from corresponding parameter values, with dropout disabled and an input shape of $4\times20\times1$.

理由：明确比较双方，保留参数对应关系，不改写成未经支持的初始化方式。对应 W01、W03、W07。

### E-S09：时间序列容差

原句：

> Loss absolute difference, gradient vector L2 difference, and relative parameter update tolerances are 0.02, 0.05, and 0.03.

候选：

> The tolerances are 0.02 for the absolute loss difference, 0.05 for the L2 norm of the gradient difference, and 0.03 for the relative parameter update difference.

理由：清楚表达每种差值与容差的对应。对应 W01、W07。

### E-S12：原生自动微分

原句：

> Each entry point must produce the required predictions and plots and execute native differentiation.

候选：

> Each entry point must produce the required predictions and plots and compute gradients using the target framework's native differentiation.

理由：把不自然的操作描述改成明确的计算行为。对应 W01、W03。

### E-S13：执行覆盖与数值比较

原句：

> The notebook and snippets provide execution coverage, while the core model supplies paired numerical training measurements.

候选：

> The notebook and snippet evaluations check execution, while numerical comparisons between the source and translated programs use the core model.

理由：保留两类评价的实际分工，解释 `paired` 的对象。对应 W03、E05。

### E-S14：69项的分母

原句：

> All three methods pass 23 behavior checks per seed, giving 69/69 across the public and two confirmation seeds.

候选：

> All three methods pass all 23 behavior checks on each of three seeds, comprising the public evaluation seed and two confirmation seeds, for a total of 69/69.

理由：明确23、3和69之间的关系，保留三方法全部通过的结果力度。对应 W02、W07。

### E-S15：推荐仓库比较对象

原句：

> The recommendation protocol covers six model paths that execute in the source framework with three sequential Adam updates.

候选：

> For the recommendation repository, we compare the source and translated programs over three consecutive Adam updates on six model paths that execute in the source framework.

理由：明确比较双方及三步更新范围。对应 W03、W07。

待核对：补充六条路径的具体含义。主代理应从冻结评价来源取得面向读者的名称或描述，再嵌入本段；不能把路径推断为六种架构，也不建议新增项目代号表。

### E-S16：异常和空返回值

原句：

> Source exceptions and empty returns are checked against the corresponding source behavior.

候选：

> We also check whether the translated program reproduces the source program's exceptions and empty returns.

理由：说明谁应复现谁的行为，消除“源异常与源行为比较”的循环表述。对应 W01、W03。

### E-S17：优化器调用

原句：

> Both the numerical worker and training command invoke the candidate's optimizer factory with learning rate 0.001.

候选：

> The numerical evaluation and the training command both invoke the translated program's optimizer factory with a learning rate of 0.001.

理由：删除内部执行单元称谓 `worker`，保留优化器工厂这一影响评价的真实机制。对应 W06、M14、W07。

### E-S20：推荐仓库容差

原句：

> Loss absolute/relative tolerances are $0.002/10^{-4}$, gradient tolerances are $10^{-4}/0.005$, and relative parameter update tolerance is 0.03.

候选：

> The absolute and relative tolerances are 0.002 and $10^{-4}$ for loss, and $10^{-4}$ and 0.005 for gradients. The relative parameter update tolerance is 0.03.

理由：只展开数字配对，不自行添加绝对与相对阈值的组合判定公式。对应 W01、W07。

### E-S22：表格引导句

原句：

> Table~\ref{tab:repository-checks} reports the declared checks on the public seed.

候选：

> Table~\ref{tab:repository-checks} reports the recommendation repository results on the public evaluation seed.

理由：删除无助理解的 `declared`。对应 W01、W06。

### E-S26：缺测状态与分母

原句：

> That entry remains n/a in both the 114 and 145 denominators.

候选：

> For each baseline, the missing retrieval measurement is recorded as n/a and remains in the denominators of six retrieval checks, 114 numerical checks, and 145 behavior checks.

理由：区分单项缺测标记和汇总计数，保留全部分母。对应 W07、E05。

### E-S27：原始测试收集失败

原句：

> MatchFixAgent passes 0/10 original tests: an unmigrated PyTorch import in its history-encoder test prevents collection under the native MindSpore requirement.

候选：

> MatchFixAgent has 0/10 confirmed original test passes because a remaining PyTorch import in its test for the history encoder prevents test collection under the native MindSpore requirement.

理由：与 README 所述“确认通过数、原始测试结果为空、收集退出码为2”一致，不将收集失败描述成十次已执行的测试失败。对应 W07、E05。

### E-S28：确认种子范围

原句：

> No method reaches the two confirmation seeds on this repository.

候选：

> No method was evaluated on the two confirmation seeds for this repository.

理由：准确陈述实际评价范围，不增添未给出的触发或停止规则。对应 W03、W06、W07。

### E-S29：两种 loss 检查

原句：

> LaDiM passes all 18 loss and 18 gradient checks and 15/18 parameter update checks in the main recommendation comparison.

候选：

> In the main recommendation comparison, LaDiM passes all 18 forward loss checks, all 18 checks of the loss returned during training, all 18 gradient checks, and 15 of 18 parameter update checks.

理由：两组 loss 检查均由表格明确支持。展开后消除歧义，也保留完整成功结果。对应 W02、W03、W07。

### E-S30：表示比较失败

原句：

> Later item embeddings diverge in all six model paths at steps two and three.

候选：

> Item representations fail the representation tolerance of $10^{-4}$ in all six model paths at steps two and three.

理由：统一 `Item representations`，将 `diverge` 对应到本段已给出的表示绝对容差。对应 W01、W03、W07。

实施前核对：冻结记录中的这些失败确实对应所述表示容差，而非执行失败或缺测。文本和表格支持当前解释，但快照没有逐项结果可供独立核验。

### E-S31：成功结果的直接陈述

原句：

> These failures remain alongside the successful reward model inference, retrieval, training command, and ten original tests.

候选：

> LaDiM completes reward model inference, passes all six retrieval checks and all ten original tests, and runs the training command successfully.

理由：直接报告具体结果，删除抽象的“失败与成功并存”描述；不削弱前句的失败结果。对应 W01、W02、W07。

### E-C02：成本表的检查分母

原句：

> Gradient and parameter update checks cover three training steps on all evaluated seeds.

候选：

> For each signal, the time series repository has nine checks across three training steps and three seeds, while the recommendation repository has 18 checks across six model paths and three steps on the public seed.

理由：表格脱离正文时仍可解释9和18，避免把推荐18项理解成跨三个种子的总数。对应 E05、W07。

### E-C05：检查表的层级

原句：

> The numerical checks are a subset of behavior checks, and the six training signal rows break down the training checks.

候选：

> Training checks are a subset of numerical checks, which are a subset of behavior checks. The six rows from User representations to Parameter updates break down the 108 training checks.

理由：说明上下层关系及分解范围，防止读者将汇总行与分项再次相加。对应 E05、W03、W07。

### E-C06：缺测表注

原句：

> One unmeasured retrieval check remains in each baseline's denominator.

候选：

> One retrieval measurement is missing for both SWE-agent and MatchFixAgent and remains in each method's retrieval, numerical, and behavior check denominators.

理由：明确涉及的方法和分母，保留缺测处理。对应 W07。

## 5. 仓库成本表逐项台账

源文件：`figures/TABLE_repository_costs.tex`。

| 编号 | 行号 | 表头、标签或完整数据行 | 处置与理由 |
|---|---:|---|---|
| E-T01-H | 3 | Method；Gradients；Parameter updates；Repair calls；Submissions；Repair input tokens；Repair output tokens；Total tokens | 建议将两个信号列明确为通过计数；调用及提交口径待核对，其余保留。 |
| E-T01-G1 | 5 | Time series | 保留。任务分组清楚。 |
| E-T01-R1 | 6 | LaDiM；9/9；9/9；35；2；2,345,473；105,096；2,614,230 | 全部数值保留。修复输入、输出加初译163,661，恰为总成本。 |
| E-T01-R2 | 7 | SWE-agent；9/9；9/9；80；1；7,984,797；51,367；8,199,825 | 全部保留。成本加总成立。 |
| E-T01-R3 | 8 | MatchFixAgent；9/9；9/9；69；2；13,306,003；128,114；13,597,778 | 全部保留。成本加总成立。 |
| E-T01-G2 | 10 | Recommendation | 保留。任务分组清楚。 |
| E-T01-R4 | 11 | LaDiM；18/18；15/18；80；4；8,147,846；295,032；8,811,246 | 全部保留。修复输入、输出加初译368,368，恰为总成本；4的提交定义须与来源一致。 |
| E-T01-R5 | 12 | SWE-agent；17/18；12/18；80；1；7,889,936；58,248；8,316,552 | 全部保留。成本加总成立；不因成本低于 LaDiM 而省略该结果。 |
| E-T01-R6 | 13 | MatchFixAgent；18/18；16/18；80；1；8,215,327；95,385；8,679,080 | 全部保留。成本加总成立；16/18优于 LaDiM 的15/18，保留真实差异。 |

### 表头候选与未决口径

| 原表头 | 候选或处置 | 意见 ID |
|---|---|---|
| `Gradients` | `Gradient checks passed`，允许分行 | E05、F07 |
| `Parameter updates` | `Parameter update checks passed`，允许分行 | E05、F07 |
| `Repair calls` | 暂保留。核对是否计入调查调用，不能仅凭全文机制改变统计标签。 | W07、M14 |
| `Submissions` | 暂保留。核对是否为实际评价提交次数、是否包含首次提交，再在表注定义。 | W07、E06 |

若冻结定义确认计数是实际提交次数，可采用表注候选：

> Submissions counts the candidates actually submitted for evaluation.

这句目前是**条件候选**。本节的 `4` 不能自动解释为四次修复都执行，也不能与程序级1/2/4预算实验混写。

表格结构使用横向分组，无需改变数据布局。新增完整表头后的宽度由后续渲染检查决定，本轮没有核验 PDF，也不建议预先缩小字号。

## 6. 推荐仓库检查表逐项台账

源文件：`figures/TABLE_repository_checks.tex`。以下数值顺序均为 LaDiM、SWE-agent、MatchFixAgent。

| 编号 | 行号 | 原标签与完整数值 | 处置与理由 |
|---|---:|---|---|
| E-T02-H | 3 | Check；LaDiM；SWE-agent；MatchFixAgent | 保留。表注已说明各列是通过数。 |
| E-T02-R1 | 5 | Behavior checks passed；130/145；104/145；129/145 | 保留。总分母145已在正文分解；与数值检查相减后分别为31、30、30项非数值检查通过。 |
| E-T02-R2 | 6 | Numerical checks；99/114；74/114；99/114 | 保留。分别等于训练检查加检索检查。 |
| E-T02-R3 | 7 | Training checks；93/108；69/108；94/108 | 保留。三方法均与下方六种信号行加总一致。 |
| E-T02-R4 | 8 | Inference retrieval；6/6；5/6；5/6 | 数值保留；标签建议改为 `Retrieval during inference`。两个5/6各包含一个缺测，不得改分母。 |
| E-T02-R5 | 10 | User representations；18/18；16/18；18/18 | 保留。信号名称自然，18项来自六路径乘三步。 |
| E-T02-R6 | 11 | Item representations；6/18；6/18；6/18 | 保留。正文 E-S30 应与此统一；三个方法的结果均须保留。 |
| E-T02-R7 | 12 | Forward loss；18/18；18/18；18/18 | 保留。须在正文与下一行明确区分。 |
| E-T02-R8 | 13 | Training return loss；18/18；0/18；18/18 | 标签改写候选为 `Loss returned during training`；全部数值保留。具体返回位置或返回值含义待核对。 |
| E-T02-R9 | 14 | Gradients；18/18；17/18；18/18 | 保留。已处于训练信号分解区，无需每行重复 `checks passed`。 |
| E-T02-R10 | 15 | Parameter updates；15/18；12/18；16/18 | 保留。与成本表一致。 |
| E-T02-R11 | 17 | Original tests；10/10；10/10；0/10 | 保留。0/10通过正文解释为测试收集失败后的确认通过数，不写成十次测试失败。 |
| E-T02-R12 | 18 | Training command；1/1；1/1；1/1 | 保留。正文已定义为16个合成样本上的一轮训练。 |
| E-T02-R13 | 19 | File coverage；1/1；1/1；0/1 | 数值保留，标签含义待核对。1/1显然不能直接解读为迁移了一个文件；需要明确这个整体检查判定什么。 |
| E-T02-R14 | 20 | Documentation and dependencies；1/1；1/1；0/1 | 数值保留，检查标准待核对。不能推断为文档完整性、依赖安装成功或禁止源框架依赖。 |

### 可以直接提出的标签候选

| 原标签 | 英文候选 | 原因与意见 ID |
|---|---|---|
| `Inference retrieval` | `Retrieval during inference` | 展开压缩名词组合，不改变任务含义。W01、W03。 |
| `Training return loss` | `Loss returned during training` | 更自然地表达原有信号名称；与 `Forward loss` 的精确定义仍需核对。W03、E05。 |

### 需要先核对来源的两行

`File coverage` 和 `Documentation and dependencies` 目前缺少足够证据来给出准确的最终替换词。单纯改成更长的 “checks” 标签仍不能解决语义问题。

主代理应核对：

1. `File coverage` 的1项检查具体判断文件存在、迁移完整性、可编辑范围遵守，还是其他条件。
2. `Documentation and dependencies` 的1项检查是组合条件还是单独评价，失败依据是什么。
3. 表尾四行与145项行为检查之间的包含关系。

这些核对只需读取已有冻结定义及结果，不构成重跑实验建议。获得定义后，应在相关行标签或同一处表注解释一次，不新增内部术语表。对应 W03、W06、E05、W07。

## 7. 数值、分母与证据一致性检查

本轮完成的是快照内的文字与算术核对。

| 项目 | 核对结果 |
|---|---|
| 时间序列信号分母 | 3步 × 3种子 = 9，与成本表的9/9一致。 |
| 时间序列行为检查 | 23项 × 3种子 = 69，与正文69/69一致。 |
| 推荐单种训练信号 | 6路径 × 3步 = 18，与六个信号行一致。 |
| 推荐训练检查 | 6信号 × 18项 = 108。 |
| 推荐数值检查 | 108项训练检查 + 6项检索检查 = 114。 |
| 推荐行为检查 | 114项数值检查 + 24项执行等检查 + 7项源行为检查 = 145。 |
| LaDiM训练通过数 | 18 + 6 + 18 + 18 + 18 + 15 = 93。 |
| SWE-agent训练通过数 | 16 + 6 + 18 + 0 + 17 + 12 = 69。 |
| MatchFixAgent训练通过数 | 18 + 6 + 18 + 18 + 18 + 16 = 94。 |
| 三方法数值通过数 | 93 + 6 = 99；69 + 5 = 74；94 + 5 = 99。 |
| 六行完整成本 | 每行修复输入 + 修复输出 + 对应仓库初译成本均等于 Total tokens。 |
| 推荐缺测处理 | 两个基线各一个检索缺测，保留6、114、145三个分母；不能将缺测写成实测数值零。 |
| 原始测试 | MatchFixAgent 的0/10与“确认通过数”一致，不能据此声称十个测试均已执行。 |

没有发现需要修改的数值单元格。尚未核验逐项冻结记录、调用分类、提交事件定义及阈值判定实现。

## 8. 生成器与资产同步位置

本轮未修改以下任何文件；此表说明未来方案获准实施时的同步范围。

| 修改对象 | 论文或资产位置 | 生成器及证据位置 | 应同步内容 |
|---|---|---|---|
| 正文与表注 | `sections/supplementary_experiments.tex:141–161` | 手写章节源码 | 比较对象、检查分母、缺测、测试收集失败及成功结果的表述。 |
| 成本表表头 | `figures/TABLE_repository_costs.tex:3` | `figures/make_unified_results.py` | 在生成器修改显示标签，再生成表格；保留所有数值。 |
| 推荐检查表标签 | `figures/TABLE_repository_checks.tex:8、13、19–20` | `figures/make_unified_results.py` | 同步面向读者的名称，保留原始数据字段及结果。 |
| 时间序列梯度和更新来源 | README 指出的 `repository_training_check_details.json` | 原始归档成员及其哈希记录 | 核对三种子、三步的检查范围；当前快照未提供完整文件路径。 |
| 仓库评价定义、缺测及测试状态 | `output/repository-migration-20260921/` 下的冻结 summary、paired checks 和 final integrity audit | README 已说明来源目录，未给出全部文件名 | 核对六路径、表尾检查、两种 loss、提交和调用口径。 |
| 汇总来源说明 | `data/paper_figures/README.md` | 现有来源文档 | 若最终确认并调整统计名称，同步说明；不改变冻结实验事实。 |
| 汇总结果导出 | `data/paper_figures/unified_results.json` | 同一生成器 | 仅核对是否含需同步的展示名称；不手改结果数值或输入哈希。 |

本节没有图、算法或 TorchAX 后端说明，不涉及图形资产和算法生成标签。主文后端内容移附录的最终落点应由主代理协调，不应无依据塞入本节仓库协议。

## 9. 最重要发现与主代理待裁定事项

1. **推荐结果中的 loss 指代不唯一。** 表中有两组各18项 loss 检查，正文只说“18 loss checks”。建议明确同时报告 forward loss 和训练返回 loss 的通过结果，并核对二者的定义。相关编号：E-S29、E-T02-R7–R8。

2. **缺测与测试收集失败需要准确落到计数含义。** 保留两个基线的5/6、全部固定分母和 MatchFixAgent 的0/10；将“缺测留在分母”与“零项确认通过”分别解释，避免形成已执行失败的错误印象。相关编号：E-S26–27、E-C06。

3. **两个仓库的训练检查分母应在成本表注中展开。** 时间序列是三步乘三个种子，推荐是六路径乘三步、仅公开种子。现有表注不能独立说明这一差异。相关编号：E-C02。

4. **四类定义仍需冻结来源裁定。** 六条 model paths、`Training return loss`、`File coverage`、`Documentation and dependencies` 不能靠语言润色准确补全。还需确定表尾各行与145项检查的包含关系。当前报告保留全部数值，没有虚构检查规则。

5. **调用和提交列的含义不能由表中数字反推。** 主代理需确认 Repair calls 是否包括调查调用，以及 Submissions 的事件定义。推荐 LaDiM 的4不能被改写成“四次修复全部执行”，也不能与程序级预算实验合并解释。

6. **全部已给出的成本和检查加总一致，实测优势与失败均应保留。** 建议只调整读者理解所需的表述和标签；保留三方法时间序列69/69、LaDiM推荐130/145及成功推理和测试结果，也保留推荐成本、更新检查和表示检查中的真实差异。无需新增防御性结尾或缩窄已有贡献。
