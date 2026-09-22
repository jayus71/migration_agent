# 附录 F 逐句审查报告

## 1. 范围、依据与覆盖

审查版本为用户提供的 `d1d6a53` 文本快照。范围是 `sections/supplementary_experiments.tex` 第 169–176 行，章节标题为 **Repository Context and Evidence**。

本报告按提供的 AGENTS.md、意见清单、humanizer 技能和 Academic-Writing-DNA 审查表达，并以 `scripts/repository_agent_mode.py` 第 419–608 行核对能够直接确认的实现关系。来源说明仅使用本轮提供的 `data/paper_figures/README.md`。未调用工具、读取额外文件、修改文件或重跑实验。

| 覆盖对象 | 数量 | 审查结果 |
|---|---:|---|
| 章节标题 | 1 | 保留 |
| 正文句子 | 16 | 全部逐句登记 |
| 保留句 | 5 | F-02、F-03、F-05、F-07、F-11 |
| 改写句 | 10 | F-01、F-04、F-06、F-09、F-10、F-12 至 F-16 |
| 移来源记录句 | 1 | F-08 |
| 公式、图、表、算法 | 0 | 本节没有这些对象 |

以下均为审查方案，尚未实施。涉及实现证据缺口的候选列明采用条件，交主代理核对。

本节值得保留的内容包括：测试结果随代码版本失效、失败的新结果替换旧结果、局部检查与最终仓库验收的关系、上下文重建保留的信息、缓存上限及整个仓库共享的预算。主要调整集中在内部接口描述、上下文触发条件的准确措辞，以及预算中 `calls` 和 `submissions` 的可读性。

## 2. 逐句台账

同一源码行包含多个句子，以下按原文出现顺序编号。

| 编号 | 原文件位置及短引文 | 建议 | 理由与对应意见 |
|---|---|---|---|
| F-H01 | 第 169 行，`Repository Context and Evidence` | 保留 | 标题准确涵盖上下文保留和证据有效性，长度适当。W01。 |
| F-01 | 第 172 行第 1 句，`separates the version of its dependency plan...` | 改写 | `separates the version` 表达生硬，`repository extension` 未直接说明主体。明确分别跟踪依赖计划和候选文件的版本，保留原机制。W01、W03、M14。 |
| F-02 | 第 172 行第 2 句，`Every recorded test stores the candidate version...` | 保留 | 清楚说明测试记录如何对应执行时的代码，是后文判定证据是否过期的必要前提。W02、M14。 |
| F-03 | 第 172 行第 3 句，`An actual change to candidate code...even when the new test fails.` | 保留 | 两个分句分别说明失效条件和同一测试的结果替换规则，信息均有用途。末尾明确失败结果也替换旧结果，属于真实规则，保留。W02、W07、M14。 |
| F-04 | 第 172 行第 4 句，`Work-unit checkpoints additionally depend...` | 改写 | `work-unit`、`file scopes` 连续堆叠实现术语；应说明依赖计划中的修复单元及检查点有效性。W01、W03、M14。 |
| F-05 | 第 172 行第 5 句，`A checkpoint without a selected test records syntax validation only.` | 保留 | 具体说明未选测试时记录了什么，能够帮助理解局部完成状态。`only` 在这里有明确技术含义。W02、M14。 |
| F-06 | 第 172 行第 6 句，`The final acceptance decision uses the complete repository evaluation.` | 改写 | `uses` 较弱且抽象。实现指导明确要求完整仓库验证及所有声明入口的实际执行，可以直接写出。S13、M11、M14。 |
| F-07 | 第 174 行第 1 句，`Full tool observations, file reads, and conversations are archived...` | 保留 | 说明上下文重建后原始证据如何保留，与后文检索及缓存形成机制关系。三项对象各有实际含义，无须机械合并。W01、M13。 |
| F-08 | 第 174 行第 2 句，`Records carry content hashes...JSON pointer, and character range.` | 移来源记录 | 检索参数主要服务接口复现；文件哈希对缓存有效性的作用已在 F-10 说明。本句可移到实现来源记录，正文保留按需检索完整记录的能力。W06、M14、S13。 |
| F-09 | 第 174 行第 3 句，`When the context is rebuilt...complete structured hypotheses...` | 改写 | 枚举内容必要，但 `it`、`generation status`、`last tool batch` 可更明确；`complete` 所修饰内容需与完整记录、摘要及结构化最终消息的保留方式核对。W01、W02、M13、M14。 |
| F-10 | 第 174 行第 4 句，`Cached code consists only of content returned by earlier reads...` | 改写 | 保留“此前读取、哈希仍匹配、与当前单元相关”三个筛选条件，改为主体明确的主动表达。W01、M13。 |
| F-11 | 第 174 行第 5 句，`The cache contains at most 120,000 characters.` | 保留 | 数字是明确上限。源码还会按可用上下文空间进一步缩减，因此 `at most` 准确。W07、M13。 |
| F-12 | 第 174 行第 6 句，`Reconstruction is triggered by...75\%...` | 改写 | 三类主要事件应保留；源码还包含初始化、生成状态更新和显式检查点等触发路径，不能将此句理解为完整触发清单。75% 按序列化消息长度计算，应写清。S13、M11、M14。 |
| F-13 | 第 174 行第 7 句，`Ordinary stage continuation and the first selection...retain...` | 改写 | 普通阶段延续仍可能遇到容量触发或已安排的重建。应说明这些动作自身是否触发重建，避免绝对承诺始终保留原对话。首次单元选择还需核对回调调用条件。S13、M11、M14。 |
| F-14 | 第 176 行第 1 句，`diagnosis allows up to six calls and 64,000 output tokens.` | 改写 | 数字保留，将 `calls` 明确为 LLM 调用。给定实现片段未包含这两个预算的配置来源，须核对冻结配置。S13、W07。 |
| F-15 | 第 176 行第 2 句，`remaining repair calls...remaining external submissions...16 calls...` | 改写 | 明确为剩余允许提交次数，区分预算分配与实际执行次数；保留首次修复阶段最多 16 次调用，不添加均分规则。S13、W03、W07、E06。 |
| F-16 | 第 176 行第 3 句，`The cumulative limits apply to the whole repository.` | 改写 | 全仓库累计预算是必要条件，保留并明确覆盖诊断和修复；与前两句保持同一预算单位。S13、W07、M11。 |

## 3. 需调整项与具体英文候选

### F-01：分别跟踪计划与代码版本

**原句，第 172 行：**

> The repository extension separates the version of its dependency plan from the version of the candidate files.

**问题：** 原句机制有用，动词结构不自然；`repository extension` 也偏向软件扩展说明。

**英文候选：**

> Repository context management tracks the dependency plan and candidate files with separate versions.

此候选沿用已定义的仓库上下文机制，不改动两个正式模块名。给定代码显示依赖计划和测试证据进入重建上下文，但未展示两类版本的维护实现；实际版本规则见第 4 节待核对项。

**对应意见：** W01、W03、M13、M14。
**状态：** 方案，未实施。

### F-04：解释检查点有效性所依赖的对象

**原句，第 172 行：**

> Work-unit checkpoints additionally depend on their declared file scopes, test selections, and prerequisite units.

**问题：** `depend` 没有明确说明所依赖的是检查点有效性；`work-unit` 和 `file scopes` 对非项目读者不够直观。

**英文候选：**

> For each repair unit in the dependency plan, checkpoint validity also depends on the files it covers, its selected tests, and prerequisite units.

候选保留文件范围、测试选择、前置单元三项条件。`repair unit` 应与方法章节最终采用的称呼统一，不新增一套分类或缩写。

**对应意见：** W01、W03、M14、S13。
**状态：** 方案，未实施。

### F-06：明确完整仓库验收包含实际入口执行

**原句，第 172 行：**

> The final acceptance decision uses the complete repository evaluation.

**问题：** `uses` 没有充分表达必须完成整个仓库评估的要求。

**英文候选：**

> Final acceptance requires the complete repository evaluation, including execution of all declared entry points.

**依据：** `scripts/repository_agent_mode.py` 第 419 行直接规定完整仓库 verifier，并要求所有声明入口实际执行。本候选保留原有验收力度，也解释局部检查点之后仍需完成的整体验证。

**对应意见：** W02、M11、M14、S13。
**状态：** 方案，未实施。

### F-08：将检索参数移到实现来源记录

**原句，第 174 行：**

> Records carry content hashes and can be retrieved by identifier, JSON pointer, and character range.

**问题：** 标识符、JSON pointer 和字符范围属于检索接口细节。论文需要说明原始记录可重新读取，但无需在此逐项列出调用参数。

**移动目标：**

建议移入已有实现映射文档 `docs/paper-6pro-execution-20260921.md` 的仓库上下文实现说明小节。该文档在提供的来源说明中已有明确定位；本轮没有其正文，小节的具体插入位置由主代理确定。

正文可将检索能力并入 F-07：

> Full tool observations, file reads, and conversations are archived outside the editable workspace and remain available for retrieval.

文件哈希对缓存新鲜度的作用仍由 F-10 说明。来源记录保留原句涉及的检索参数及其实现对应。

**对应意见：** W06、M14、S13。
**状态：** 移动方案，未实施。

### F-09：明确重建后保留的信息，核对 `complete`

**原句，第 174 行：**

> When the context is rebuilt, it retains the current dependency plan and generation status, the complete structured hypotheses and next steps, the latest measurements, and the last tool batch.

**问题：**

- `it` 指代不够直接。
- `generation status` 需说明是代码生成状态。
- `last tool batch` 对读者而言应明确为最近一批工具响应。
- `complete structured hypotheses and next steps` 是实质性完整保留主张，应核对其对应的数据结构。

**保留原完整性主张的英文候选：**

> The rebuilt context retains the current dependency plan and code generation status, the complete structured hypotheses and next steps, the latest test results, and the most recent batch of tool responses.

**实现核对依据：**

第 533–544 行保存依赖计划、生成状态、诊断信息、近期代理记录、结构化最终消息、最近工具响应和测试状态。其中部分内容经 `evidence_summary` 处理，部分结构化对象完整复制。给定片段没有该摘要函数的定义，也未展示 hypotheses 和 next steps 的完整结构。

因此，主代理应确认这里的 `complete` 指哪些字段。若这些字段确实完整保留，采用上述候选；若完整内容仅在归档中保留，则应准确区分当前上下文和归档，候选为：

> The rebuilt context retains the current dependency plan and code generation status, summaries of diagnostic findings, structured agent notes, the latest test results, and the most recent batch of tool responses. Complete records remain available in the archive.

第二版仅在核对支持该信息组织方式时采用，不因本轮材料有限直接缩小原主张。

**对应意见：** W01、W02、M13、M14。
**状态：** 两个有条件候选，未实施。

### F-10：用直接表达保留缓存筛选条件

**原句，第 174 行：**

> Cached code consists only of content returned by earlier reads, with matching current file hashes and relevance to the active unit.

**问题：** `with matching...and relevance...` 连接不自然，读者需要自行恢复两个筛选条件。

**英文候选：**

> The code cache retains previously read content only when its file hash still matches the current file and the content is relevant to the active repair unit.

候选保留原句全部条件，不把缓存扩大为自动读取或扫描整个仓库。第 558 行调用 `working_set`，但具体过滤实现未包含在快照中，须由主代理核对。

**对应意见：** W01、M13、M14。
**状态：** 方案，未实施。

### F-12：区分主要重建事件与完整实现触发清单

**原句，第 174 行：**

> Reconstruction is triggered by an independent role handoff, an actual work-unit switch, or messages exceeding 75\% of the configured context capacity.

**问题：** 主要机制可以保留，但表述容易被理解为穷尽清单。源码另外展示：

- 第 474–475 行安排初始阶段重建；
- 第 450–460 行允许生成状态更新和显式上下文检查点安排重建；
- 第 577–578 行根据待处理标记或容量条件执行重建。

**英文候选：**

> Context reconstruction supports independent role handoffs and switches between repair units. It also occurs when the serialized conversation exceeds 75\% of the configured context capacity.

这里将角色交接和单元切换写成重建所支持的机制，避免把三项写成全部触发路径。75% 的判断对象明确为序列化对话长度，不改成 token 使用率。

初始化、生成状态更新和显式检查点等完整触发规则，建议与 F-08 一同记入 `docs/paper-6pro-execution-20260921.md` 的实现说明，保留对应源码位置。

**对应意见：** W01、W06、M11、M14、S13。
**状态：** 方案，未实施。

### F-13：将“保留对话”改为动作自身不触发重建

**原句，第 174 行：**

> Ordinary stage continuation and the first selection of a work unit retain the existing conversation.

**问题：** 原句没有区分阶段延续、已有待处理标记和容量触发。普通延续期间仍可能因上下文容量而重建。

**英文候选：**

> Ordinary stage continuation and the first selection of a repair unit do not themselves trigger context reconstruction.

该候选保留原句关于两个动作的机制主张，并允许容量条件独立生效。

**需核对：** 第 471–473 行支持普通修复阶段延续保留已有上下文；第 446–448 行只显示 focus 回调会安排边界重建，未显示首次选择是否调用该回调。主代理应检查调用方后决定能否保留“首次选择”分句。

若调用方不支持首次选择的原主张，采用：

> Ordinary stage continuation does not itself trigger context reconstruction.

首次选择的实际规则随后记录到实现来源说明，不编造“每个修复单元重新启动 Verifier”的流程。

**对应意见：** M11、M14、S13。
**状态：** 有条件候选，未实施。

### F-14：明确诊断预算的调用类型

**原句，第 176 行：**

> For the repository experiments, diagnosis allows up to six calls and 64,000 output tokens.

**问题：** `calls` 可能被理解为工具调用、测试调用或 LLM 请求，需要明确单位。

**英文候选：**

> In the repository experiments, diagnosis is limited to six LLM calls and 64,000 output tokens.

六次和 64,000 均保持原值。此处分别给出调用数上限和输出 token 上限，不暗示两者都会实际用满。

**对应意见：** W01、W07、S13。
**状态：** 方案，未实施；数值配置待主代理核对。

### F-15：说明分配的是剩余预算

**原句，第 176 行：**

> The remaining repair calls and output budget are allocated over the remaining external submissions, with at most 16 calls in the first repair stage.

**问题：** `external submissions` 偏接口用语，`output budget` 的计量单位省略；还需避免将剩余允许次数写成实际发生的修复轮数。

**英文候选：**

> The remaining LLM calls and output token budget are allocated across the remaining allowed submissions for evaluation, with at most 16 LLM calls in the first repair stage.

候选保留原有预算分配关系，没有添加“平均分配”，也没有引入本节未给出的提交次数。若前文已统一使用 `candidate submissions`，此处可沿用该称呼。

**对应意见：** W03、W07、E06、S13。
**状态：** 方案，未实施；分配实现及 16 次上限待主代理核对。

### F-16：明确累计预算覆盖整个仓库

**原句，第 176 行：**

> The cumulative limits apply to the whole repository.

**问题：** 这是解释预算口径的必要句，不应作为重复结尾删除；可明确承接调用数和输出 token 两类限额。

**英文候选：**

> The cumulative call and output token limits apply to the entire repository across diagnosis and repair.

**依据：** 第 419 行说明生命周期预算覆盖所有单元的调查、编辑和验证；第 457 行注明上下文检查点不重置用量；第 544 行保留完整生命周期预算。本句有助于避免将单元切换或上下文重建解释为预算重置。

**对应意见：** W02、W07、M11、S13。
**状态：** 方案，未实施。

## 4. 实现证据与主代理核对事项

本节没有算法，提供的代码用于核对叙述，不作为另一个章节逐行审查。以下集中列出影响候选采用的证据边界。

| 核对对象 | 给定证据 | 主代理需要核对的具体内容 |
|---|---|---|
| 计划版本、候选版本及测试失效规则 | 第 459、466 行记录测试；第 540、544 行保留测试状态并说明过期证据 | 版本如何生成；新失败是否替换同一测试的旧通过结果；依赖计划与文件版本是否独立维护。 |
| 局部检查点与语法验证 | 第 419 行要求声明局部测试，并说明上游变化使依赖检查点失效 | 文件范围、测试选择和前置单元如何影响有效性；未选测试时是否确实只记录语法验证。 |
| 归档及缓存过滤 | 第 500、515、528 行归档记录；第 556–558 行计算容量并建立代码工作集 | 归档是否位于可编辑工作区之外；`working_set` 是否同时执行此前读取、哈希匹配、单元相关性三个筛选。 |
| 完整结构化假设与下一步 | 第 508–544 行同时使用摘要、结构化记录和完整复制 | hypotheses 和 next steps 对应哪些字段；是否在当前上下文完整保留，还是需从归档检索。 |
| 首次修复单元选择 | 第 446–448 行 focus 回调安排重建 | 回调是否仅在实际切换单元时触发，首次选择是否例外。不能仅凭回调函数推断调用条件。 |
| 诊断和修复预算 | 第 419、457、544 行支持全仓库累计预算 | 冻结配置中的六次调用、64,000 输出 token、首次修复最多 16 次调用，以及剩余预算分配规则。 |

这些核对项用于选择准确表述，不构成本轮新增实验要求。无需重跑实验即可先检查对应冻结配置和实现。

## 5. 图表、算法及来源记录同步位置

本节没有图表、图注、表注、公式或生成标签，因此没有可确认必须同步的图表生成器或图形资产。

后续实施建议涉及以下位置：

| 位置 | 建议同步内容 | 本轮状态 |
|---|---|---|
| `sections/supplementary_experiments.tex:169–176` | 按逐句候选调整附录 F | 未修改 |
| `docs/paper-6pro-execution-20260921.md` | 承接检索接口参数、完整上下文触发规则及实现映射；具体插入位置由主代理确定 | 未修改 |
| `docs/manuscript-feedback-register.md` | 记录本节对 W01/W03/W06、M11/M13/M14、W07 及 S13 的审核结果；未核对项不能标为已落实 | 未修改 |
| `sections/methods.tex` 中仓库协调算法及相关叙述 | 主代理整合时核对上下文重建、证据交接、完整仓库验收和全局预算含义；本报告不重复审查该章节 | 仅提出交叉核对 |
| `scripts/repository_agent_mode.py` | 作为实现证据保留；本轮没有代码修改建议 | 未修改 |

本节不涉及 TorchAX、JAX 对比表、损失阈值图或 1/2/4 提交预算结果，也不建议因本节审查改动那些资产。

## 6. 最重要发现与待裁定事项

1. **本节的核心机制有保留价值。** 版本对应、旧证据失效、新失败替换旧结果、完整仓库验收和全局预算均直接影响方法含义。建议保留这些内容，只将检索参数等接口细节移到来源记录。

2. **上下文触发叙述需要修正表达范围。** 当前文本列出三类事件，代码还包含其他安排重建的路径。正文可说明主要作用和容量条件，完整触发清单进入实现记录。

3. **“首次选择单元保留对话”需要核对调用方。** 提供的 focus 回调不足以证明该规则。无论最终如何措辞，都不能推导出每个修复单元会重新启动 Verifier。

4. **`complete structured hypotheses and next steps` 需核对具体保留结构。** 代码同时使用完整复制和摘要。主代理应据实际字段选择候选，保留有证据支持的完整性主张。

5. **预算需要明确 LLM 单位与允许提交次数。** 六次调用、64,000 输出 token、首次修复最多 16 次调用全部保留，配置来源待核对。预算分配不能写成所有允许修复轮次都实际执行。

6. **需主代理裁定来源记录位置及术语统一。** 建议由已有实现映射文档承接接口细节，并将本节 `repair unit` 与方法章最终措辞统一；两个正式模块名称 Repository Structural Analysis / Repair Dependency Graph Planning 保持不变。
