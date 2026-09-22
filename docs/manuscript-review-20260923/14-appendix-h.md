# 附录 H 逐句与表格审查报告

本报告依据用户提供的 `d1d6a53` 完整文本快照，采用本轮 AGENTS.md、Humanizer、Academic-Writing-DNA 和意见清单的审查要求。所有修改均为候选方案，未实施任何修改，未调用工具、读取其他文件、运行实验或编译论文。

附录 H 的实验分组、接受数和表内成本算术一致。主要问题集中在预算适用单位、ResNet 数值结果的指代，以及少量重复说明。应完整保留十二个来源、两项修复任务、三个种子和三步训练的区别。

## 一、审查范围与覆盖数

| 对象 | 准确源文件与行号 | 覆盖范围 |
|---|---|---|
| 章节标题 | `sections/supplementary_experiments.tex:221–222` | 1 个标题及章节标签 |
| 正文 | `sections/supplementary_experiments.tex:224,235,237,239` | 4 段、24 个句子，全部登记 |
| 表注 | `sections/supplementary_experiments.tex:227` | 3 个句子，全部登记 |
| 表格引入 | `sections/supplementary_experiments.tex:226–233` | 表格标签、输入资产及排版设置 |
| 表格内容 | `figures/TABLE_native_jax.tex:5–10` | 5 个表头、4 个方法行、16 个数值单元格 |
| 表格来源与结构 | `figures/TABLE_native_jax.tex:1–4,11–12` | 来源路径、SHA256 注释、表格结构 |
| 生成关系 | 所提供的 `data/paper_figures/README.md` | 生成器、冻结输入及输出资产的对应关系 |

本章没有算法、独立公式或图形。逐句台账共覆盖 27 句，另列标题与表格台账。正文编号为 H-S01 至 H-S24，表注编号为 H-C01 至 H-C03，表格编号为 H-T01 至 H-T11。

后文意见 ID 沿用主清单；S13 指本轮最新逐句审查要求。报告中的局部编号仅用于定位，不表示已向意见清单新增条目。

## 二、逐句台账

### 2.1 标题及任务构成

| 编号 | 短引文与位置 | 建议处理 | 具体理由及对应意见 |
|---|---|---|---|
| H-H01 | “Native JAX Migration with Consecutive Training Steps”，221 行 | 保留 | 标题准确体现本研究的目标框架与连续训练检查。这里的连续训练有下文三步协议和 ResNet 结果支撑，具有具体信息。W01、R11 |
| H-S01 | “This study uses twelve public model workloads from PyTorch examples, minGPT, and torchvision.”，224 行第 1 句 | 保留；核对来源引用 | 十二个来源和三个公开来源名称清楚。所给句子未显示引用，主代理需核对是否已有明确覆盖本研究的来源引用。无需新增数据集表或平均长度。E01、E03、E02 |
| H-S02 | “They cover image classification, super-resolution, … GPT, and ResNet.”，224 行第 2 句 | 保留 | 列举提供具体覆盖范围，并与后文八个初次通过、两个无代码输出、两个需要修复的来源对应。任务类型与模型名称虽混排，仍能理解，无需为了形式整齐重新分类。W01、W07 |
| H-S03 | “Each workload executes three optimization steps.”，224 行第 3 句 | 删除独立句，信息由 H-S08 承接 | H-S08 已说明三步、种子、微分与优化器。此处还容易被读成所有初译程序都完成了三步，与随后两项未返回代码的情况产生阅读冲突。删除该句不删除三步协议。W06、W07、S13 |
| H-S04 | “The shared initial translation produces ten nonempty candidates: eight pass the three-seed evaluation, and two fail.”，224 行第 4 句 | 改写 | `shared initial translation` 和 `nonempty candidates` 偏记录术语。应直接说明四种方法共用初译程序，其中八份首次评估通过、两份失败。保留十、八、二及三个种子。E08、W03、W07 |
| H-S05 | “The image generator and Transformer language model exhaust their initial output budget without returning code.”，224 行第 5 句 | 改写 | 目前语法主语是待迁移模型，实际耗尽代码生成输出预算的是初译过程。尤其 `image generator` 容易与生成代码的模型混淆。W01、W03、W07 |
| H-S06 | “The failed nonempty candidates, a time series model and ResNet, form the common repair collection for all four methods.”，224 行第 6 句 | 改写 | 用“所有四种方法修复相同的两份初译程序”直接说明比较对象，去掉 `failed nonempty candidates` 与 `common repair collection` 的叠加抽象。R11、E08、W03 |

### 2.2 表注

| 编号 | 短引文与位置 | 建议处理 | 具体理由及对应意见 |
|---|---|---|---|
| H-C01 | “Repair of two initially failing native JAX translations from twelve source workloads.”，227 行第 1 句 | 保留 | 明确十二个来源中只有两份初译进入修复比较，符合两份 JAX 研究分开报告的要求。R11、W07 |
| H-C02 | “End-to-end tokens for the two repair tasks include 31,427 shared translation tokens; costs for all twelve sources include all 139,724 translation tokens.”，227 行第 2 句 | 改写 | 两种统计范围必须保留。可拆成两句，并说明共享初译成本在每种方法的合计中计入一次。无需依靠分号承载两套分母。W04、W07、R06 |
| H-C03 | “All four methods accept 1/2 repair tasks and 9/12 sources after repair.”，227 行第 3 句 | 改写 | 两个分母准确。`methods accept sources` 不够自然，宜表达每种方法的通过数及覆盖范围。该结果置于表注有助于直接阅读成本表，应保留。W01、W07、R11 |

### 2.3 执行与验收协议

| 编号 | 短引文与位置 | 建议处理 | 具体理由及对应意见 |
|---|---|---|---|
| H-S07 | “Candidates implement the forward computation and explicit buffer state in native JAX.”，235 行第 1 句 | 改写 | `explicit buffer state` 对大同行仍不够具体。可用模型状态的含义解释 buffer，并保留 native JAX 与前向计算这两个关键事实。W03、E08 |
| H-S08 | “The evaluator independently invokes JAX differentiation and the specified Optax optimizer for three consecutive steps on seeds 8101, 8102, and 8103.”，235 行第 2 句 | 保留 | 主体、执行位置、优化器、步数和种子完整，能够解释何为连续训练检查。`independently` 在此表达评估器执行微分和优化器的职责，有技术作用。W07、M05 |
| H-S09 | “Source parameters, buffers, and batches are supplied to each method.”，235 行第 3 句 | 保留 | 这是方法所获输入及公平比较条件，不属于可直接删除的无用接口记录。不得无依据改成只向评估器提供这些内容。W07、E07 |
| H-S10 | “Initial states match exactly, and full outputs, losses, gradients, updates, parameters, and buffers are compared elementwise in float64 with absolute/relative tolerances \(10^{-7}/10^{-5}\).”，235 行第 4 句 | 改写 | 明确比较双方为源程序和 JAX 程序；展开斜杠对应关系。完整保留六类比较对象、float64、精确初始状态及两个容差。W01、W07 |
| H-S11 | “Tensor names, shapes, and data types must also match.”，235 行第 5 句 | 保留 | 补充结构与类型检查，未与数值容差检查重复。没有依据将该条件弱化或移除。W07 |
| H-S12 | “The optimizer executes in the evaluator.”，235 行第 6 句 | 删除 | H-S08 已明确由评估器调用 Optax 优化器，本句完全重复。保留 H-S08 即保留实现边界。W06、W01 |
| H-S13 | “Each repair condition has at most 40 calls, four submissions, 120,000 output tokens, and 1,800 seconds; each initial translation has one call with at most 16,384 output tokens.”，235 行第 7 句 | 改写；预算单位待主代理核对 | `repair condition` 未明确指一种方法的两项任务合计，还是每种方法在每项任务上的一次运行。表内 SWE-agent 为 66 calls，说明读者必须知道统计与预算单位。保留所有预算数值，明确这是上限。W03、W04、W07、S13 |

### 2.4 两项修复结果

| 编号 | 短引文与位置 | 建议处理 | 具体理由及对应意见 |
|---|---|---|---|
| H-S14 | “All four methods repair the time series candidate's input slicing and output concatenation shapes and pass all three steps on all three seeds.”，237 行第 1 句 | 改写 | `input slicing and output concatenation shapes` 的修饰关系不顺。应明确修复的是输入切片和输出拼接中的形状错误，并让通过训练检查的主体落在程序上。W01、W07 |
| H-S15 | “LaDiM, MatchFixAgent, and SWE-agent pass at their first submission, and Direct repair passes at its second.”，237 行第 2 句 | 保留 | 首次与第二次提交清楚区分实际完成过程与四次提交上限，不存在冗余预算叙述。W07、S13 |
| H-S16 | “LaDiM, Direct repair, and SWE-agent also turn the truncated ResNet candidate into executable code.”，237 行第 3 句 | 保留 | 说明三种方法恢复了可执行性，为随后“执行成功但后续训练不一致”的具体结果提供必要前提。不得把可执行等同于最终接受。W02、W07 |
| H-S17 | “All first-step arrays pass, but later steps contain gradient and update differences, followed by further output and buffer differences.”，237 行第 4 句 | 改写 | `All` 的适用对象需要明确为上一句的三份可执行 ResNet 程序；`arrays pass` 应展开为通过相应数值检查。保留后续梯度、更新、输出和 buffer 的时序观察，不自行补成固定第 2/3 步或因果链。W01、W03、W07 |
| H-S18 | “MatchFixAgent terminates when its native analysis parses the truncated candidate and encounters a syntax error; its numerical results are n/a, and its four completed calls remain in the costs.”，237 行第 5 句 | 改写 | `native analysis` 缺乏定义，直接说明解析截断的 ResNet 程序时遇到语法错误即可。数值缺测及四次已完成调用计入成本具有解释比较的作用，应保留。W03、W04、W07 |
| H-S19 | “All four methods therefore finish at 1/2 repair acceptance.”，237 行第 6 句 | 删除 | 表注已给 1/2，下一段又说明总通过数 9/12。此句只重复刚述两项任务的结局，可删除而不损失结果。W01、W06 |

### 2.5 十二个来源的总体结果与成本

| 编号 | 短引文与位置 | 建议处理 | 具体理由及对应意见 |
|---|---|---|---|
| H-S20 | “The eight initially passing sources are CNN classification, super-resolution, … graph attention, and GPT.”，239 行第 1 句 | 改写 | 通过检查的是这些来源对应的初译程序。应明确八份程序首次评估即通过、无需修复；模型名单全部保留。E08、R11、W07 |
| H-S21 | “Adding the repaired time series model gives 9/12 accepted sources for every method.”，239 行第 2 句 | 保留 | 解释 9/12 如何由八个初次通过加一个修复成功构成，具有分母解释作用。不能与 H-S19 一并作为“重复数字”删除。W07、R11 |
| H-S22 | “The complete initial translation ledger contains 29,455 input and 110,269 output tokens, totaling 139,724, including both generation failures.”，239 行第 3 句 | 改写 | 删除内部记账对象 `ledger`，直接报告十二次初译的输入、输出和总成本。两次未返回代码的生成仍计费，必须说明。W06、W07 |
| H-S23 | “Table… distinguishes this source-level cost from the 31,427 translation tokens for the two repair tasks.”，239 行第 4 句 | 删除 | 表注 H-C02 和两个完整表头已解释两个统计范围。本句再次介绍表格组织方式，没有新增成本事实。W06、W01 |
| H-S24 | “The ResNet results show why consecutive training checks remain necessary after the first step agrees; the final three-seed evaluation retains the later discrepancies.”，239 行第 5 句 | 改写 | 前半句具有具体结果支撑，应保留。后半句 `retains the later discrepancies` 不清楚，像记录系统动作，可改成检查揭示后续差异的直接结论。不要增加降调或防御性限制。W01、W02、W04、W06 |

## 三、需调整项与具体英文候选

以下均为未实施候选。除明确标注须核对的预算单位外，候选只重组快照中已有事实。

### 3.1 清楚区分初次通过、未返回代码和需要修复

**位置：H-S03 至 H-S06，224 行。**

原句：

> Each workload executes three optimization steps. The shared initial translation produces ten nonempty candidates: eight pass the three-seed evaluation, and two fail. The image generator and Transformer language model exhaust their initial output budget without returning code. The failed nonempty candidates, a time series model and ResNet, form the common repair collection for all four methods.

问题：三步协议与后文重复；`nonempty candidates` 偏内部分类；耗尽初译输出预算的动作主体不准。

候选：

> Initial translation returns code for ten of the twelve workloads. Eight translations pass the initial evaluation on all three seeds, and two fail. Initial translations of the image generation and Transformer language modeling workloads exhaust the output budget without returning code. All four methods receive the same two failing translations, for the time series model and ResNet, for repair.

“三个连续优化步”的完整定义由 H-S08 保留。该段明确两项修复任务，不能将十二个来源改称十二项修复任务。

对应意见：E08、R11、W03、W06、W07、S13。

### 3.2 表注保留两个成本范围与两个接受分母

**位置：H-C02、H-C03，227 行。**

原句：

> End-to-end tokens for the two repair tasks include 31,427 shared translation tokens; costs for all twelve sources include all 139,724 translation tokens. All four methods accept 1/2 repair tasks and 9/12 sources after repair.

候选：

> For each method, total tokens for the two repair tasks include the shared initial translation cost of 31,427 tokens once. Totals for all twelve sources include the full initial translation cost of 139,724 tokens once. Each method achieves acceptance on 1/2 repair tasks and 9/12 source workloads overall.

这两列是替代性的统计范围，不能相加。共同初译只执行一次，表内每种方法的完整成本各计入其相应份额。

对应意见：W04、W07、R06、R11。

### 3.3 解释 buffer，并明确数值比较对象

**位置：H-S07、H-S10，235 行。**

原句：

> Candidates implement the forward computation and explicit buffer state in native JAX.

候选：

> The translated programs implement the forward computation in native JAX and explicitly represent model buffers, which store state other than trainable parameters.

该解释说明 buffer 的通常技术含义，不新增具体模型层或状态更新机制。

原句：

> Initial states match exactly, and full outputs, losses, gradients, updates, parameters, and buffers are compared elementwise in float64 with absolute/relative tolerances \(10^{-7}/10^{-5}\).

候选：

> The source and JAX programs start from exactly matching states. The evaluator compares their complete outputs, losses, gradients, parameter updates, parameters, and buffers elementwise in float64, using an absolute tolerance of \(10^{-7}\) and a relative tolerance of \(10^{-5}\).

不将两个容差擅自改成两个须独立满足的不等式，也不添加未提供的比较公式或数据类型转换规则。

对应意见：W01、W03、W07、M05。

### 3.4 删除优化器执行位置的重复句

**位置：H-S12，235 行。**

原句：

> The optimizer executes in the evaluator.

方案：删除。H-S08 已明确由评估器调用 JAX differentiation 和指定 Optax optimizer，职责信息完整保留。

对应意见：W01、W06。

### 3.5 明确预算针对哪个运行单位

**位置：H-S13，235 行。**

原句：

> Each repair condition has at most 40 calls, four submissions, 120,000 output tokens, and 1,800 seconds; each initial translation has one call with at most 16,384 output tokens.

问题：`condition` 无法让读者判断 40 次调用是每个任务的上限，还是两项修复任务的合计上限。表内 66 次调用使这个区别直接影响结果理解。

**若主代理核对冻结协议确认预算按“每种方法、每项修复任务”设置，采用：**

> For each of the two repair tasks, each method is allowed up to 40 LLM calls, four submissions, 120,000 output tokens, and 1,800 seconds. Each initial translation uses one LLM call with an output limit of 16,384 tokens.

`LLM calls` 还须确认与冻结记录的 call 计数一致。若原记录包含其他调用类别，应使用真实名称。

候选明确“允许上限”，不会把四次提交写成所有方法实际进行了四轮修复。本章已经记录时间序列任务的实际提交次数，须原样保留。

对应意见：W03、W04、W07、S13。

### 3.6 明确时间序列修复对象

**位置：H-S14，237 行。**

原句：

> All four methods repair the time series candidate's input slicing and output concatenation shapes and pass all three steps on all three seeds.

候选：

> All four methods correct shape errors in the time series translation's input slicing and output concatenation. The repaired programs pass the checks at all three optimization steps on all three seeds.

对应意见：W01、W07。

### 3.7 明确 ResNet 首步结果仅属于三份可执行程序

**位置：H-S17，237 行。**

原句：

> All first-step arrays pass, but later steps contain gradient and update differences, followed by further output and buffer differences.

候选：

> For these three repaired ResNet programs, all arrays pass the numerical checks at the first optimization step. Later steps show gradient and parameter update discrepancies, followed by output and buffer discrepancies.

此处 `these three` 对应上一句的 LaDiM、Direct repair 和 SWE-agent。MatchFixAgent 的数值结果为 n/a，不属于该首步通过结论。

快照没有给出各项差异的精确首次出现步数，也未给出逐种子明细，因此候选保留原句时序，不补成“第 2 步梯度失败、第 3 步输出失败”。`followed by` 表达观察顺序，不扩写成已经证实的因果机制。

对应意见：W01、W03、W07。

### 3.8 清理 MatchFixAgent 失败描述，保留缺测与成本解释

**位置：H-S18，237 行。**

原句：

> MatchFixAgent terminates when its native analysis parses the truncated candidate and encounters a syntax error; its numerical results are n/a, and its four completed calls remain in the costs.

候选：

> MatchFixAgent terminates after encountering a syntax error while parsing the truncated ResNet translation. Its numerical results are n/a, and its four completed calls are included in the reported costs.

这里的四次调用是实际完成量，不等同于四次提交。n/a 必须保持缺测含义，不能改成零或“数值检查失败”。

对应意见：W03、W04、W07。

### 3.9 删除重复的修复接受数总结

**位置：H-S19，237 行。**

原句：

> All four methods therefore finish at 1/2 repair acceptance.

方案：删除。1/2 保留在表注，时间序列通过和 ResNet 未接受的具体结果保留在本段。

对应意见：W01、W06。

### 3.10 明确八份初译无需修复

**位置：H-S20，239 行。**

原句：

> The eight initially passing sources are CNN classification, super-resolution, the variational autoencoder, the recurrent language model, both policy learning models, graph attention, and GPT.

候选：

> The initial translations for CNN classification, super-resolution, the variational autoencoder, the recurrent language model, both policy learning models, graph attention, and GPT pass the first evaluation and require no repair.

随后保留原句：

> Adding the repaired time series model gives 9/12 accepted sources for every method.

两个句子共同说明八加一的构成，不把初次通过记作修复成功。

对应意见：E08、R11、W07、S13。

### 3.11 成本直接落在初译过程，删除记账措辞与表格导览

**位置：H-S22、H-S23，239 行。**

原句：

> The complete initial translation ledger contains 29,455 input and 110,269 output tokens, totaling 139,724, including both generation failures.

候选：

> Initial translation across all twelve workloads uses 29,455 input tokens and 110,269 output tokens, totaling 139,724 tokens, including the two attempts that return no code.

原句：

> Table~\ref{tab:native-jax} distinguishes this source-level cost from the 31,427 translation tokens for the two repair tasks.

方案：删除第二句。31,427 与 139,724 的对应范围已由表注和表头清楚保留；输入、输出分解仍留在正文，无需移走实质成本信息。

对应意见：W01、W06、W07。

### 3.12 保留连续训练检查的具体结论

**位置：H-S24，239 行。**

原句：

> The ResNet results show why consecutive training checks remain necessary after the first step agrees; the final three-seed evaluation retains the later discrepancies.

候选：

> The ResNet results show why checking consecutive optimization steps is necessary: agreement at the first step leaves later gradient, parameter update, output, and buffer discrepancies undetected.

该句由本章具体结果支持，保留原有结论力度。删除的是 `evaluation retains discrepancies` 这一不清楚的记录动作，不增加无证据的普遍性主张或额外降调。

对应意见：W01、W02、W04、W06。

## 四、表格逐项台账

### 4.1 表头、方法行与结构

| 编号 | 源位置与内容 | 建议处理 | 审查结果 |
|---|---|---|---|
| H-T01 | 5 行：`Method` | 保留 | 完整清楚，无需改名。 |
| H-T02 | 5 行：`Repair calls` | 核对统计范围后改清 | 需要明确是否包含调查调用，以及是否只计 LLM calls。表内是两项任务合计；不能直接拿 66 与单任务 40 比较。 |
| H-T03 | 5 行：`Repair tokens` | 核对统计范围后改清 | 明确是否包含完整调查与修复阶段的输入和输出。表格算术能确认其不含共同初译，但不能单靠算术确认内部调用分类。 |
| H-T04 | 5 行：`Two repair tasks / end-to-end tokens` | 可改写表头 | 建议 `Two repair tasks / total tokens`，并由表注定义包含初译与后续过程。范围保留。 |
| H-T05 | 5 行：`All twelve sources / end-to-end tokens` | 可改写表头 | 建议 `All twelve sources / total tokens`，与前一列保持一致。范围保留。 |
| H-T06 | 7 行：LaDiM，35；1,840,066；1,871,493；1,979,790 | 全部保留 | 两种总成本都满足表注所述初译加法。 |
| H-T07 | 8 行：Direct repair，28；760,935；792,362；900,659 | 全部保留 | 方法名称明确，数值算术一致。 |
| H-T08 | 9 行：MatchFixAgent，23；258,914；290,341；398,638 | 全部保留 | 成本包括失败任务已完成的调用；较低成本须结合语法分析提前终止的正文事实理解。无需新增评价性标签。 |
| H-T09 | 10 行：SWE-agent，66；1,013,532；1,044,959；1,153,256 | 全部保留 | 两项任务合计数不得改为单任务计数；66 本身不能证明违反 40 次上限。 |
| H-T10 | 1–2 行：冻结输入与 SHA256 | 保留在资产来源注释 | 已位于正确的来源记录位置，无须进入论文正文。本轮没有重新核验哈希。 |
| H-T11 | 3–4、11–12 行及正文 226–233 行：表格结构、标签与输入 | 保留 | 横向表格符合现有安排。未渲染，不能声称列宽、换行和页面位置已通过视觉检查。 |

普通技术复合词不作机械替换。这里将 `end-to-end tokens` 改为 `total tokens` 的理由是表注已经精确定义起止范围，短表头可减少排版负担；这项属于可选措辞调整。

若冻结记录确认两列统计完整的调查与修复过程，可采用：

> `Investigation and repair calls`
> `Investigation and repair tokens`

若确认调用均为 LLM 调用，且表注明确排除初译，也可用更短的：

> `LLM calls`
> `Input + output tokens`

两种方案择一即可，不能在未核对记录时直接认定现有 `Repair calls` 统计错误。

### 4.2 数值与分母核对

以下核对仅依据传入表格和正文进行算术检查。

| 方法 | 后续过程 tokens | 加两项初译 31,427 | 加全部初译 139,724 |
|---|---:|---:|---:|
| LaDiM | 1,840,066 | 1,871,493，一致 | 1,979,790，一致 |
| Direct repair | 760,935 | 792,362，一致 | 900,659，一致 |
| MatchFixAgent | 258,914 | 290,341，一致 | 398,638，一致 |
| SWE-agent | 1,013,532 | 1,044,959，一致 | 1,153,256，一致 |

其余关系均一致：

- 初译结果：8 份首次通过＋2 份返回代码但失败＋2 份未返回代码＝12 个来源。
- 修复结果：时间序列通过、ResNet 未接受，因此每种方法均为 1/2。
- 来源总体结果：8 份初次通过＋1 份修复通过＝9/12。
- 全部初译成本：29,455 输入＋110,269 输出＝139,724 tokens。
- 两种总成本列之差均为 108,297 tokens，对应其余十个来源的初译成本。

表注统一报告接受数、表内比较成本的安排可以保留。没有必要为四个完全相同的接受结果额外扩展两列。

## 五、生成器与资产同步位置

本节仅列后续方案的同步范围，本轮未修改或生成任何文件。

| 候选调整 | 应同步的位置 | 冻结来源与处理边界 |
|---|---|---|
| 标题、正文、协议与结果措辞 | `sections/supplementary_experiments.tex:221–239` | 数字、预算、种子及容差全部保留。 |
| 表注两种总成本的定义 | `sections/supplementary_experiments.tex:227` | 31,427 与 139,724 均只按所属范围计入一次。 |
| 表头名称或换行 | `figures/make_cumulative_components.py` 中生成 native JAX 表的部分；输出 `figures/TABLE_native_jax.tex:5` | 所给 README 确认此生成关系，但未提供生成器具体行号，不编造定位。 |
| 调用与 token 范围说明 | 上述生成器、表注；若与现有来源说明存在差异，再同步 `data/paper_figures/README.md` 的对应段落 | 先核对实际字段含义，不重解释或重算冻结实验结果。 |
| 表格源数据 | `output/jax-expansion-20260922/formal/formal_report.json` | 只作为后续核对预算单位与指标定义的来源，不修改。 |

当前表格记录的 SHA256 为：

`82b1279075e730dee90e47ade1c3d9a342c1028670ae1f8dbaa903121d502165`

这只是快照中的来源标记，本轮未重新计算哈希。

本章不包含 TorchAX。最新 E10 要求将其执行后端说明移至附录，但仅凭本章的 native JAX 协议，不能确定这里就是合适的接收位置。主代理应将 TorchAX 放入其所服务的六例 JAX 修复评估协议，保持其与本章十二来源研究的边界。

## 六、最重要发现及需主代理裁定之处

1. **十二个来源、两项修复任务与 9/12 总体接受数关系正确。** 建议清理 `nonempty candidates`、`initially passing sources`，明确八份初译首次通过、两份没有返回代码、两份进入修复。保留本章与主文六例 JAX 研究各自的分母。

2. **预算单位是本章最需要核对的协议问题。** `Each repair condition` 未定义清楚，表内 SWE-agent 的 66 次调用又是两项任务合计。主代理需确认 40 calls、四次提交、120,000 output tokens 和 1,800 秒是否均按每种方法的每项任务设置，再采用明确候选；不能从现有表格直接判定预算违规。

3. **ResNet 首步通过的指代应明确限定为三份可执行程序。** LaDiM、Direct repair 和 SWE-agent 的数值结果与 MatchFixAgent 的 n/a 必须分开表达。保留后续差异的观察顺序，不补造具体出现步数或已经证实的因果关系。

4. **成本数字和加法全部一致，表头的调用范围仍需核对。** 主代理需确认 `Repair calls`、`Repair tokens` 是否包含调查阶段，以及 calls 是否均为 LLM 调用。已完成的失败调用必须继续计入，两个不同覆盖范围的总成本列不得相加。

5. **可删除三类重复，保留具体科学结论。** 删除独立的三步说明、重复的优化器执行位置、重复的 1/2 总结和表格导览句；三步协议、预算、成本及接受结果仍完整保留。ResNet 对连续训练检查必要性的支持应直接表达，不追加防御性降调。

6. **来源引用及 TorchAX 移入位置由主代理统筹。** 所给 H 首句没有引用标记，需要核对已有文献是否覆盖三个公开来源。TorchAX 应进入相应六例研究的执行协议；现有材料不足以支持把它写成本章十二来源 native JAX 研究的后端。

以上均为审查方案；论文、生成器、图表资产、冻结结果、PDF 和意见清单均未改动。
