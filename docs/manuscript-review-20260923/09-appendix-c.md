# 附录 C 逐句审查报告

## 1. 审查范围与状态

本报告审查快照 `d1d6a53` 中 `sections/supplementary_experiments.tex` 第 122–128 行，即附录 C “Additional Repair Collections”。

覆盖情况：

| 对象 | 数量 | 覆盖情况 |
|---|---:|---|
| 章节标题 | 1 | 已审查 |
| 正文句子 | 10 | 全部逐句登记；第 125 行 6 句，第 127 行 4 句 |
| 公式、算法 | 0 | 本节没有 |
| 图、表、图注、表注 | 0 | 本节没有 |
| LaTeX 标签 | 1 | 保留 `sec:additional-repair` |

审查依据为用户提供的 AGENTS.md、Humanizer 规则、Academic-Writing-DNA、意见清单和图表来源说明。以下均为修改方案，没有修改文件、生成资产、编译论文或重跑实验。

本节最需要处理的是：让读者看清两个集合分别提供什么输入；明确提交预算与累计接受数；消除没有具体内容的协议概述。两个集合的结果、成本和比较力度均应保留。

## 2. 逐句台账

“保留”表示本轮没有发现足以支持改写的问题；不代表已独立核实底层实验记录。

| 编号 | 位置与短引文 | 建议 | 具体理由 |
|---|---|---|---|
| C-H01 | L122，“Additional Repair Collections” | 保留 | 简洁说明本节收录补充修复集合。无需为标题增加新分类，也无需机械改动论文统一的标题大小写。 |
| C-S01 | L125，第 1 句，“We also evaluate supplied faulty target programs under their respective acceptance criteria.” | 改写 | `supplied` 没有明确这些程序是修复方法的输入；`their respective acceptance criteria` 又提前泛述后文的集合协议。开头应直接说明本节评估的是对已有错误目标程序的修复。 |
| C-S02 | L125，第 2 句，“A controlled MindSpore collection contains 50 injected faults with task-specific acceptance checks.” | 保留 | 给出了框架、故障构造、数量与验收依据，信息有效。`controlled` 和 `task-specific` 在这里具有实验含义，不应机械禁用。须保留“50 injected faults”的计数对象，不能自行改成 50 个不同程序或源文件。 |
| C-S03 | L125，第 3 句，“LaDiM accepts 45/50 within four submissions … using shared tools.” | 改写；工具条件待核对 | `accepts` 容易让 LaDiM 看起来同时承担评价裁决；可改为方法达到验收的结果表达。将四次提交明确写成预算。`shared tools` 缺少共享对象，本快照不能确定其具体含义。 |
| C-S04 | L125，第 4 句，“LaDiM's cumulative accepted counts are 29, 41, and 45 at one, two, and four submissions.” | 最小改写 | 保留真实的 1/2/4 三个预算点，并显式写出各自分母。原文使用 `cumulative`，不能仅依据主实验说明将其改成“预算末次候选通过数”。 |
| C-S05 | L125，第 5 句，“Total token use is 39,982,844, 42,579,064, and 12,459,013 …” | 保留 | 明确报告三种方法的总 token，顺序与前一句一致。三个数是实际比较项，并非为了节奏凑成三项。即使 LaDiM 成本高于 direct repair，也应完整保留。 |
| C-S06 | L125，第 6 句，“The source and target inputs required by MatchFixAgent are supplied in the paired collection below.” | 改写并并入下一段 | 这句话解释另设集合的输入原因，具有实质信息；但 `paired collection` 含义不够直接，也与下一段的 `source and target repair tasks` 重复。宜将“MatchFixAgent 需要源程序和目标程序”与第二个集合的介绍合并。 |
| C-S07 | L127，第 1 句，“In a separate collection of twelve source and target repair tasks, LaDiM accepts 12/12 …” | 与 C-S06 合并改写 | `source and target repair tasks` 容易被读成两类任务。应明确每项任务提供源程序和含错误的目标程序。保留 12/12 与 11/12，不添加未经提供的任务类型、框架或预算。 |
| C-S08 | L127，第 2 句，“They use 6,642,603 and 14,505,833 tokens, respectively.” | 保留 | `They` 的先行对象明确，`respectively` 的顺序清楚。直接陈述成本即可，无需为了加强结果而额外添加百分比或重复总结。 |
| C-S09 | L127，第 3 句，“Both receive the complete source, candidate, task specification, and target library.” | 最小改写 | 这句说明双方获得相同输入，是有效比较条件。将 `source` 和 `candidate` 明确为程序，便于不熟悉系统接口的读者理解；保留任务说明和目标库。 |
| C-S10 | L127，第 4 句，“Each repair collection uses its specified editable code scope and acceptance checks.” | 用具体协议替换；核对后删除泛述句 | `specified` 没有实际给出任何可编辑范围或检查内容，也没有指向相应说明。可编辑范围与验收协议确实重要，但需要在相关比较处具体交代一次。不能通过重排词语保留一个仍然空泛的句子，也不能在未找到协议时直接删除唯一的范围提示。 |

逐句建议统计：直接保留 3 句，改写或合并 6 句，需查明协议后处理 1 句。标题与标签保留。

## 3. 需调整项及英文候选

### C-R01：开头明确修复输入

对应句子：C-S01，L125。

原句：

> We also evaluate supplied faulty target programs under their respective acceptance criteria.

问题：`supplied` 的作用没有展开；开头泛述验收规则，末尾又泛述一次，读者仍不知道两项补充实验的具体区别。

候选：

> We evaluate repair methods on faulty target programs supplied as inputs in two additional collections.

该句交代已有错误目标程序作为输入，并引出下面两个集合。各集合的验收条件放在所属段落说明。

对应意见：W01、W03、W06、E08；最新意见 6、7。

状态：仅提出方案。

### C-R02：明确四次提交是预算，澄清 direct repair 的工具条件

对应句子：C-S03，L125。

原句：

> LaDiM accepts 45/50 within four submissions, compared with 29/50 for SWE-agent and 35/50 for a direct repair agent using shared tools.

可直接采用的最小候选：

> LaDiM achieves acceptance on 45/50 cases with a budget of four submissions, compared with 29/50 for SWE-agent and 35/50 for a direct repair agent using shared tools.

这项局部调整保留原句全部信息，将预算说清楚，也不暗示每个案例实际执行了四次修复。

`using shared tools` 仍需主代理核对。若记录确认三种方法使用同一套工具，可以另写：

> All three methods use the same tools.

该句是有条件候选，当前材料不足以采用。若只有 direct repair 与 LaDiM 共享工具，则应准确写出这两个方法，不能扩展到 SWE-agent。

本次也不能把 `with a budget of four submissions` 移到整个比较句最前面，从而默认所有方法具有同一预算；需先核对两个基线的预算记录。

对应意见：W07、E07、W03；最新意见 4、6、8。

状态：预算措辞为可执行建议；共享工具和基线预算待主代理核对。

### C-R03：保留累计口径，显式给出分母

对应句子：C-S04，L125。

原句：

> LaDiM's cumulative accepted counts are 29, 41, and 45 at one, two, and four submissions.

候选：

> LaDiM's cumulative acceptance is 29/50, 41/50, and 45/50 at submission budgets of one, two, and four, respectively.

保留 `cumulative`、全部数值及三个预算点，不添加第三次提交结果，也不将预算写成每个案例的实际执行次数。

来源说明中，当前主实验的预算统计按“预算下最后一个候选”评分；本节原文却明确使用累计接受表述。两者属于不同集合，不能直接套用。主代理应核对本节冻结记录后决定是否保留 `cumulative`。

对应意见：W07、R07；最新意见 4、8。

状态：仅提出方案；累计口径待来源核对。

### C-R04：合并第二个集合的输入说明和结果

对应句子：C-S06、C-S07，L125、L127。

原句：

> The source and target inputs required by MatchFixAgent are supplied in the paired collection below.

> In a separate collection of twelve source and target repair tasks, LaDiM accepts 12/12 and MatchFixAgent accepts 11/12.

推荐合并候选：

> A separate collection contains twelve repair tasks, each providing the source program and faulty target program required by MatchFixAgent. LaDiM achieves acceptance on 12/12 tasks and MatchFixAgent on 11/12.

将两句一起放入第二段开头，形成“输入条件 → 接受结果 → 成本 → 双方完整输入”的顺序。

此候选保留另设集合的原因和全部接受数，去掉含义不明的 `paired collection`。这里的十二项任务不能据提供的 README 直接认定为另一项十二来源的 JAX 研究，更不能引入那项研究的 8、2、2 分组。

对应意见：W01、W03、W06、E07、E08、W07；最新意见 6、7、8。

状态：仅提出方案。

### C-R05：将双方输入写成读者能辨认的对象

对应句子：C-S09，L127。

原句：

> Both receive the complete source, candidate, task specification, and target library.

候选：

> Both methods receive the complete source program, faulty target program, task specification, and target library.

该句明确 `candidate` 指含错误的目标程序，保留完整输入条件。无需额外解释接口字段、文件组织或内部运行标识。

对应意见：W03、E07、E08；最新意见 6、7。

状态：仅提出方案。

### C-R06：用实际协议处理末句

对应句子：C-S10，L127。

原句：

> Each repair collection uses its specified editable code scope and acceptance checks.

问题：这句话只声称存在规则，没有给出规则的内容。两项实验的可编辑范围和验收方式又可能影响结果比较，不能靠删除一句话解决证据缺口。

处理方案：

1. 主代理先查明两个集合各自的可编辑范围及验收检查。
2. 若相应协议已在附录其他位置完整定义，在本节相关比较处增加准确回指，删除此句。
3. 若尚未说明，在本节两个段落中分别补入必要条件，再删除此句。运行标识、归档路径及哈希等内容放来源记录。

当前快照没有给出具体范围和检查内容，因此不提供带有猜测的英文协议句。第一段已经明确 `task-specific acceptance checks`，不能自动扩展为四种 discrepancy 全部通过、三种子训练验收或其他集合使用的标准。

对应意见：W06、W07、M14、E06；最新意见 7、8。

状态：处理方案；待主代理核对具体协议，尚不能直接定稿。

## 4. 数值、分母及来源口径核对

本轮候选保留以下全部数值：

| 集合 | 项目 | 原文数值及顺序 |
|---|---|---|
| 受控 MindSpore 修复集合 | 故障数量 | 50 injected faults |
| 同上 | 接受结果 | LaDiM 45/50；SWE-agent 29/50；direct repair 35/50 |
| 同上 | LaDiM 累计接受结果 | 1/2/4 次提交预算对应 29/41/45，分母均为 50 |
| 同上 | 总 token | LaDiM 39,982,844；SWE-agent 42,579,064；direct repair 12,459,013 |
| 十二项源程序与目标程序修复任务 | 接受结果 | LaDiM 12/12；MatchFixAgent 11/12 |
| 同上 | token | LaDiM 6,642,603；MatchFixAgent 14,505,833 |

提供的 README 没有明确映射到这两组数值的冻结文件或生成器。因此，本轮完成的是原文、候选与给定来源说明之间的口径检查，未独立验证这些结果的底层记录。

主代理需要集中核对四项会影响表述的事实：

- 第一集合的累计接受，是否统计预算内曾通过的案例，或统计预算末次候选的结果。
- 三种方法分别具有什么提交预算，`shared tools` 具体涉及哪些方法。
- 两个集合的可编辑范围和验收规则。
- 两组 token 的统计阶段及是否包含全部失败尝试。

这些信息应在相应比较处说明一次，不需要把核查过程或防御性提醒写进论文。

## 5. 图表、生成器与资产同步

本节没有图表、算法、`\input` 或图表引用。本次文字方案的直接修改位置仅为：

- `sections/supplementary_experiments.tex:125`
- `sections/supplementary_experiments.tex:127`

标题和 `sec:additional-repair` 标签无需修改。

提供的来源说明列出了主比较生成器 `figures/make_unified_results.py`，但没有证明它生成本节的 45/50 或 12/12 结果。因此，不能将该脚本指定为本节数值的同步位置，也不能用主比较的 50/50、46/50 等结果替换这里的结果。

若主代理在冻结来源中找到对应表格或生成标签，应同步检查其中的集合名称、预算含义和方法名称；本轮没有依据指定某个图表资产必须改动。来源路径和统计口径可登记在 `data/paper_figures/README.md`，具体修改待主代理确认真实映射后执行。

## 6. 最重要发现与待裁定事项

1. **两个集合应以输入条件区分。** 第一集合评估给定错误目标程序的修复；第二集合明确提供 MatchFixAgent 所需的源程序和错误目标程序。建议合并 C-S06、C-S07，删除含义不明的 `paired collection`。

2. **保留全部 1/2/4 预算结果，并核实累计口径。** 29/50、41/50、45/50 可以直接写清；这些数不能被解释为每个案例都执行了对应次数的修复，也不能套用主实验的末次候选评分规则。

3. **`shared tools` 是当前最明显的比较条件缺口。** 主代理需查明共享对象和基线预算，再决定条件句如何覆盖各方法。当前候选没有替实验补设统一条件。

4. **末句应由具体协议取代。** 可编辑范围与验收检查具有科学意义，但 `its specified ...` 没有向读者提供这些信息。是否删除该句，取决于主代理能否找到并准确回指已有协议。

5. **结果力度保持。** LaDiM 在两个集合的接受数优势、相对 SWE-agent 和 MatchFixAgent 的 token 情况，以及 direct repair 在第一集合的更低成本，都应完整保留。此次审查不增加防御性结尾，也不因行文调整自动收缩主张。
