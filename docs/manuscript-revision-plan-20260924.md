# 论文修改方案：架构图、交叉引用、图表与页数

2026年9月25日补充：已按用户要求实际试排0924架构图及Task 1–29，并重算loss阈值敏感性。具体尺寸、截图、结果及对第1、6、7、10项的修正见[补充方案](manuscript-revision-plan-20260925.md)。下文保留9月24日提案记录，正式论文修改仍待审核。

本方案供用户审核，尚未实施论文修改。依据用户本轮十项意见、随后“先给论文修改方案”的要求，以及最后将图源纠正为 `figures/架构图0924.svg` 的消息。0914版不再作为本轮图源。

当前分支为 `codex/iclr-2027-template`。已有暂存的架构图工作保存为检查点 `f781fc0`；用户正在编辑的PPT及其他个人文件保留。检查对象包括主稿、方法、实验、附录、全部有效反馈、相关图表生成器与数据来源，以及现有PDF第3–10页。当前PDF共24页，正文和结论结束在第10页，参考文献也从第10页开始。本文档中的替换文字均为候选稿。

## 1. 以0924版替换架构图，并同步解释

已确认指定SVG存在，尺寸为5006×3035，包含可编辑矢量元素，没有SVG image位图元素。SHA-256为 `8d465411eabc0daa28b168c6505b8485b7b89aa0665416028f0c0901e51ec3dc`。图中包含Orchestrator、Translator Agent、Verifier Agent、Repair Agent、Evidence Handoff，以及底部三个仓库模块；MindSpore、JAX和语言迁移示意均保留。

批准后的操作：从指定SVG直接导出独立矢量PDF `figures/architecture_0924.pdf`，核对字体、箭头和边界，再修改 `sections/methods.tex` 的图源。原SVG与旧PDF保留。方法开头说明Orchestrator与三个Agent的关系；图注重点解释分层检查、证据交接、迭代修复及仓库上下文。图中的波形与sum/mean补丁按机制示意描述，不为它们新增实验结果。按实际论文宽度检查小字可读性。

建议图注：

> LaDiM's migration workflow. The Orchestrator coordinates translation, diagnosis, repair, and verification. The Verifier compares source and target computations in training order and passes code observations, test results, locations, and hypotheses to the Repair Agent. Repository context management supports this process through structural analysis, dependency planning, and evidence retrieval and context reconstruction. MindSpore and JAX illustrate target frameworks, and Java illustrates language migration.

图源的长宽比约0.606，当前包含的架构图更扁。替换后可能增加占高，因此页数比较必须包含新图，不能只依据算法和表格节省量推断。

## 2. 伪代码字号与全宽／环绕试排

当前算法1、2采用55%正文宽度的左置环绕，算法3全宽。前两个算法的长调用和注释产生额外换行。现有历史试排记录表明，采用环绕曾节省48.09pt、约四行正文；这属于旧版结果，本轮修改后的净收益需要重新测量。

用户希望稍微缩小字号，建议试排目标为局部9pt（`\small`），并与当前10pt比较。需要审核的实际冲突是：[ICLR官方模板 Final instructions](https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2027/iclr2027_conference.tex#L318-L323)明确写有“do not change font sizes”，没有给算法或表格列出例外。因此建议正式稿保留10pt，9pt仅作为独立排版候选，不能将它标为符合当前官方要求的投稿稿。

批准试排后比较四种组合：10pt全宽、10pt环绕、9pt全宽、9pt环绕。先以算法1、2为主要候选，算法3的长函数名较多，优先保留全宽。保持算法内容和预算条件相同，比较方法结束位置、正文最终页数、代码换行数与旁侧正文可读性。采用整页净节省较好的布局，不只比较算法框自身高度。字号决定单独记录，不能通过整体缩放算法图像绕过字体要求。

## 3. 表格字号及异常空白

表格当前为10pt，局部9pt的建议与上项共享同一格式决定。可以先通过单位简化、列宽和表格组织减少拥挤。

已定位的空白来源：

| 位置 | 已核对原因 | 拟处理 |
|---|---|---|
| 表4(a)标题下方 | 两个子表均使用固定高度 `\parbox[t][2\baselineskip]`，左标题一行、右标题两行，左侧因此保留一行 | 表4(b)改短标题后，两个标题均采用自然的一行高度 |
| 表格与正文之间 | LaTeX浮动体间距和模板的 `\flushbottom` 可能伸展竖直间距 | 对照分页与浮动体位置逐页检查；不将正常浮动体间距直接清零 |
| 子表／表注之间 | 源码中主动加入 `\smallskip`、`\medskip`、局部 `\vspace` | 只保留分组、表注所需的间隔，删除重复占位 |
| 方法部分分页 | `\Needspace{16\baselineskip}`、`18\baselineskip` 等分页保护与环绕算法共同影响位置 | 按试排结果调整局部预留，避免正文被不必要地提前移页 |

官方模板规定了段落间距和齐底排版，但没有要求每个表格前人为插入一整行。源码中的逻辑空行也不能直接等同于PDF中的多余空白。本轮现有PDF的突出问题是表4标题的固定高度和部分浮动体间距，需分别处理。

## 4. 附录及图号自动引用

主稿已经加载 `cleveref`，直接统一使用它。当前发现10处 `Appendix~\ref{...}` 和5处 `Figure~\ref{...}`，另有已使用的 `\cref`。

将正文和附录的章节引用统一改为 `\cref{...}`／句首 `\Cref{...}`，由目标标签类型决定显示Section或Appendix；保留现有 `\appendix` 分界。检查本地cleveref实现，已经支持appendix、subappendix等类型。编译验收时需逐项确认附录A、A.1、A.6等链接均正确，不能只替换字符串后假定有效。

图引用在导言区集中定义：

```tex
\crefname{figure}{Fig.}{Figs.}
\Crefname{figure}{Fig.}{Figs.}
```

这样正文显示 `Fig. 1`、`Fig. 2`，以后修改前缀只需改一处。图注前的 `Figure 1:` 暂沿用模板；本项针对正文交叉引用。文献引用继续使用 `\citep` 等现有命令。附录交叉引用当前实际是 `\ref`，与文献引用各自处理。

## 5. 重写3.4：首次出现时定义组件

直接删除指定句子“A change to a shared implementation can affect several callers in a repository.”，并取消紧随其后的组件名称清单。按“结构信息—修复计划—证据和上下文—算法符号”的顺序组织。每个组件首次出现时说明输入、功能及后续使用方式，保留两个已确认的正式名称。

候选正文如下：

> Repository context management keeps the dependency plan and diagnostic evidence available as agents work across files and conversations. Repository Structural Analysis provides on-demand inspection of files, imports, function and class definitions, and notebook structure. These observations help the agent identify related implementations and the entry points that use them.

> Repair Dependency Graph Planning groups related target files into work units, assigns each unit a repair goal and selected tests, and represents prerequisites as a directed acyclic graph. The agent selects a unit whose prerequisites have valid local checks. LaDiM records syntax and test results for each unit; changes to files or the plan invalidate checks for affected units and their dependents. The Orchestrator verifies the complete repository, including its entry points and training computations, to determine acceptance.

> Notebook tools support code-cell inspection and editing with syntax validation. An evidence archive stores code observations, measurements, hypotheses, and conversations with their code versions. Context reconstruction retrieves relevant evidence and rebuilds the conversation around the current plan and measurements when evidence passes to the Repair Agent, work moves to another unit, or the conversation approaches its capacity. Earlier code observations are restored when the corresponding files remain unchanged.

> Algorithm 3 connects these tools to Layered Diagnosis and repair. Context C contains the dependency graph C.G, local check results C.Q, and evidence archive C.E. UpdateDependencyGraph applies Repair Dependency Graph Planning; PrepareContext performs context reconstruction. Execute handles unit selection, file and notebook operations, tests, and evidence retrieval, returning observations o and the affected units U. All work units share the repository files, repair history, and total budget.

正式实施时以上符号保持原有LaTeX数学格式，算法编号采用自动引用。此稿与新架构图底部三个模块对应，也保留notebook工具、版本相关证据和检查失效机制。

## 6. Fig. 3(b)增加逐输入标签

横轴每根柱增加 `Task 1` 至 `Task 29` 的展示标签，删除 `Migration inputs`。保留20个初始通过输入、9个初始失败输入及组内按token节省排序的规则。采用竖排标签进行首轮试排，分组名称移至图内合适位置或用分组括线标识，避免同一位置堆三层文字。

29根柱对应50个任务标识中的29个不同输入。Task标签用于图内展示；生成时保存与冻结输入标识的对应表，验收分母继续是50。保留全部柱、两根负值柱、左图三个方法及其成本分层。图注同时修正 `signicantly` 的拼写。

图3(b)当前以thousands计量，(a)以millions计量。按全文单位统一要求，(b)改为millions，坐标和数据一同除以1000，保持原始token差值不变。

## 7. Fig. 4阴影、loss判据与现有工作

阴影是每个训练步12次运行的最小值到最大值，12次来自四个模型、三个种子。它表达跨模型和种子的离散范围，不是置信区间或标准差。建议保留阴影，在图注中就近写明 `Shaded bands show the minimum–maximum range across four models and three seeds.`，需要时添加简短图内说明。原图的step 1箭头、均值在31／18步越阈、图内子图标题及Loss difference标签保持。

已直接复算冻结CSV：两类故障各600条独立训练观测，step 1的loss差值范围均为0至1.9073×10⁻⁶；对应梯度／更新检查各12/12在step 1越阈。按现有0.02 loss阈值，50步内分别3/12和4/12运行越阈，均值首次越阈仍为31和18。这是已有数据核对，未执行训练或LLM实验。

loss比较存在其他合理判据，例如绝对与相对容差结合、参考正常运行波动确定误差范围。降低阈值可能使后续loss变化更早被发现；若故障发生在本步forward之后，该步已计算出的loss仍可能与正常程序一致。具体31／18步只对应当前测量和固定阈值。

已有工作提供了明确依据：

- [MindSpore官方精度指南](https://www.mindspore.cn/mindformers/docs/en/r1.7.0/advanced_development/precision_optimization.html#benchmark-error-confirmation)使用loss差异和正常运行误差范围进行精度判断，并讨论梯度范数及更新后权重的比较。它支持以这些训练信号开展诊断；本研究的0.02阈值来自自身实验协议，不能归于该文档。
- [MatchFixAgent §2.2.3与§2.3](https://arxiv.org/html/2509.16187v3#S2.SS2.SSS3)分析输入输出、库API和其他语义，并生成和执行等价性测试。将它概括成“只看运行有没有error”不准确；现有文献核对未发现其使用本文相同的loss阈值协议。
- [NablaFuzz](https://arxiv.org/abs/2302.04351)对输出和自动微分的梯度进行差分测试，可用于说明检查梯度本身已有研究基础。

建议把该段明确写为“在相同训练轨迹上比较不同检测信号”，用它解释Layered Diagnosis的动机；与具体Agent的优劣继续由共同任务比较和组件消融支撑。补一处直接来源，并将对应解释连到表4(a)的训练信号消融。保留具体故障、阈值和检测比例，避免从这张图推导未测量的基线检测延迟。

如要检验阈值选择的敏感性，可另行提出对冻结轨迹重算多个阈值下的检出率及误报率；这需要单独确定分析范围，本方案不把尚未进行的敏感性分析写成结论。

## 8. Table 3改为窄表并尝试正文环绕

ICLR当前为单栏版式，此处按“约半页宽的表格，另一侧正文环绕”实现。建议将现有方法列转为方法行，使用 `Method / Accepted / Calls / Tokens` 四列；以分组行保留LLM repair与Native conversion的区别。建议展示数据如下，token单位为millions：

| Method | Accepted | Calls | Tokens |
|---|---:|---:|---:|
| LaDiM | 6/6 | 76 | 0.674 |
| Direct repair | 6/6 | 57 | 0.353 |
| Ivy | 0/6 | 0 | 0 |
| torch2jax | 0/6 | 0 | 0 |

将表放在Generalization Across Frameworks段落起始附近，试排约55%–60%正文宽度，优先采用左表右文。图注保留六个故障候选、LLM修复预算、原生转换一次及计费范围。验收时比较整段占高；若窄图注和旁侧断行抵消表格收益，则把全宽版与环绕版并列交给用户，而不以横向变窄直接宣称省页。

## 9. Table 4(b)标题与全文token单位

标题建议改为单行 `(b) Repair components`。图注和相邻正文继续使用完整的repair history及independent evidence handoff名称；不把长术语缩成含义不明的缩写。取消两个子表固定两行标题高度，保持标题和表头对齐。

建议全文论文的token成本统一为millions（10⁶ tokens）。表格表头保留Tokens／Total tokens，单位在图注或表注中统一说明；图轴明确写 `(millions)`；正文写 `x.xxx million tokens`。与现有主表一致，成本数值显示三位小数；严格预算按换算后的精确值表达，例如120,000 tokens可写0.120 million tokens。原始CSV、JSON、账本和预算均保持原始整数。

改动范围包含表3、表4的三个子表、附录成本表、正文中的具体token数，以及图3(b)。同步更新 `figures/make_unified_results.py`、`figures/make_cumulative_components.py` 等实际生成器及其输出，避免下一次生成恢复旧单位。零LLM消耗、缺测n/a、不适用的横杠分别保留。

## 10. 页数控制顺序与验收

[ICLR 2027 Author Guidelines](https://iclr.cc/Conferences/2027/AuthorGuidelines#paper-formatting)规定初次投稿正文最多9页，参考文献与附录不计入。当前24页PDF的正文结束在第10页，因此还超出正文页数要求；本轮尚未试排，不给出未经编译的新页数。

先完成确定的内容与引用修改，再做以下版面比较：

1. 用0924架构图纳入真实占高；测试算法1、2的全宽／环绕净收益，算法3优先全宽。
2. 调整表3环绕、表4一行子标题及多余占位，统一token单位后重新分配列宽。
3. 消除浮动体插入造成的明显阅读断裂，例如算法3现在进入实验setup中间，以及表4把消融分析的句子拆至两页。
4. 若正文仍超过9页，优先精简3.4中已由定义承担的重复解释、图注和表注对setup的重复计费说明、算法后对显然操作的复述。保留组件定义、公式、验收协议、实际结果、泛化小节和关键机制。
5. 若仍需整段删除、移动实验或改变主文证据范围，先另列具体删改文字，不将其视为此次一般排版授权。

实施验收包括：图表数据和现有布局检查；逐一核对单位换算；`latexmk`编译与实际尺寸PDF检查；报告主文结束页、总页数及试排收益；刷新固定基线逐词HTML与需要的LaTeX差异稿；复核全部有效反馈。所有步骤均在用户批准方案之后执行。正文段落保持一段一行，官方样式文件保持原字节。

## 本轮记录与待审核项

本轮仅做只读核查、临时渲染及方案／反馈记录。没有更改主稿、章节、包含的图表或生成器，没有重新编译正式论文，也没有运行新实验。需要用户审核的核心取舍是：正式稿字号与9pt试排的关系、3.4候选正文、表3环绕候选、表4短标题，以及统一million token单位的显示规则。其余项目依本方案执行，最终以编译结果报告页数。
