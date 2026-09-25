# LaDiM 论文修改方案 r5：图注、方法节导读、§3.4 压缩、标题间距

2026-09-25（第 7、8 节 2026-09-26 更新）。针对 `migration_agent_overleaf0925修改版本2.pdf` 提出的 4 个问题，加上 Tanh 案例（第 7 节）和全文语气强化（第 8 节）。

- **改动位置**：只改了 `sections/methods.tex` 和 `conference_101719.tex` 两个文件，已直接写入。
- **未编译**：修改时没有编译环境，所有版面效果都要在 Overleaf 编译后确认（见第 6 节）。
- **合规检查**：已联网查过 ICLR 2027 官方要求（见第 5 节）。

| # | 问题 | 改哪里 | 结果 |
|---|---|---|---|
| 1 | Fig. 2 图注太短 | methods.tex 图注 | 删掉 3 句无关说明；(a) 按流程写清楚，(b) 补全 |
| 2 | 方法节开头导读句没有信息量 | methods.tex 第 3 行 | 整句删除；另在 3.2、3.4 正文各加一处图引用 |
| 3 | §3.4 偏长 | methods.tex §3.4 | 删除重复和次要细节，约缩短 1/4，技术内容不变 |
| 4 | 同级标题前后空白不一致 | conference_101719.tex 导言区 | 加 `\raggedbottom`，不再按整页拉伸标题间距 |
| 7 | 4.3 第二段换成 Tanh 修复案例图 | experiments.tex 第 42、70 行，附录 A 节 `sec:natural-protocol` | **未改 tex**。数据已按 `D:\705file\coworker` 的实验记录逐项核实，图中数字全部一致；给出定稿的图注、正文段、附录段和图的修改建议（见第 7 节） |
| 8 | 全文语气偏保守，结果没有突出 | 摘要、引言、§3.2–3.4 开头、实验各段、Fig. 1/3 与 Table 2/3 图注、结论 | **未改 tex**。给出可直接粘贴的替换 LaTeX，每段结论先行、写明比较对象，数字全部保持原值；逐项核对表和删减顺序见第 8 节 |

---

## 1. Fig. 2 图注

### 1.1 删除的内容

以下三句全部删除，不放到正文其他地方：

- `$A_T$, $A_V$, and $A_R$ denote agent instructions.`（3.1 节已经定义了 $A_T,A_V,A_R$）
- `Code and traces are illustrative.`
- `Java/DJL experiments migrate in the reverse direction, to Python/PyTorch.`（迁移方向在 4.1 Tasks 段已经写明）

### 1.2 原图注

> Overview of LaDiM. (a) The Orchestrator coordinates translation, diagnosis, repair, and validation. The Verifier investigates the first divergent stage and hands evidence to the Repair Agent. (b) Repository context management combines structural analysis, dependency planning, and evidence retrieval with context reconstruction. $A_T$, $A_V$, and $A_R$ denote agent instructions. Code and traces are illustrative. Java/DJL experiments migrate in the reverse direction, to Python/PyTorch.

### 1.3 新图注

```latex
\caption{Overview of LaDiM. (a) The Translator Agent produces an initial candidate, and the Orchestrator executes it alongside the source program to measure execution, forward values, gradients, and parameter updates. If the candidate is not accepted, the Verifier Agent applies Layered Diagnosis: it compares these stages in training order and investigates the first one that diverges (gradients in this example), so later stages are not reached. Its code observations, test results, code locations, and hypotheses are handed to the Repair Agent, which tests and edits the candidate and submits it to the Orchestrator. The Orchestrator returns the remaining discrepancies to the Repair Agent until the candidate is accepted or the budget is exhausted. (b) For repositories, repository context management analyzes the repository structure, orders repairs over a dependency graph of work units, and stores evidence outside the conversation so that a compact context can be reconstructed when the agent switches units.}
```

### 1.4 新图注和图中模块的对应

| 图注内容 | 图中模块 |
|---|---|
| Translator 产生初始候选 | Translator Agent |
| Orchestrator 同时运行源程序和候选，测量四个阶段 | Orchestrator（Execute / Coordinate Agents） |
| 按训练顺序比较，只查第一个出现差异的阶段；后面的阶段不再检查 | Verifier Agent 的 Layered Diagnosis 阶段表，以及图例 “Stages not reached” |
| 四类证据交给 Repair Agent | Evidence Handoff（Code observations / Test results / Locations / Hypotheses） |
| Repair Agent 测试、修改、提交；Orchestrator 返回剩余差异，直到通过或预算用完 | Repair Agent（Patch and Validate）、Verified Output |
| (b) 分析结构、按工作单元依赖图排序、证据存档与上下文重建 | Repository Structural Analysis、Dependency Graph Planning、Evidence Retrieval & Context Reconstruction |

**需要核对**：图注里写的是 “gradients in this example”。请对照图中阶段表，确认图里标红的首个差异阶段确实是梯度；如果不是，把括号里的阶段名改成图中实际标出的那一个。

**图内名称**：如果图中 (b) 仍写 “Dependency Graph Planning”，最好改成与正文一致的 “Repair Dependency Graph Planning”（r4 方案第 0.1 节已提过）。

---

## 2. 删除方法节开头的导读句

### 2.1 删除的句子（methods.tex 原第 3 行）

```latex
\cref{fig:architecture} overviews LaDiM; \cref{sec:hierarchy,sec:repair-agent,sec:repository-method} describe diagnosis, repair, and repository coordination.
```

删除后，`\section{Methods}` 和 `\label{sec:method}` 后面直接是 Fig. 2 的 `figure` 环境，然后是 3.1 节。

### 2.2 补上的图引用

删掉这句以后，正文里就没有引用 Fig. 2 的地方了。所以在两处各加了一个很短的引用，不增加行数：

- **3.2 节第一句**：
  `... and the Orchestrator's measurements (\cref{fig:architecture}a). It uses ...`
- **3.4 节第一段末尾**：
  `... through three components (\cref{fig:architecture}b).`

---

## 3. §3.4 压缩

### 3.1 改了什么

| 段落 | 删除或合并的内容 | 理由 |
|---|---|---|
| 首段 | “files that depend on each other” 改为 “interdependent files”；“described below” 改为图引用 | 同样意思，更短 |
| Structural Analysis | 删去 “showing which parts of the repository remain unplanned”，以及 “it is not run at initialization or when the context is rebuilt” | 前一句是对上一句的重复；后一句是实现细节，“on demand” 已经表达了 |
| Dependency Graph | 删去 “may edit only the files assigned to that unit”；“which must then be checked again” 并入失效那句；Orchestrator 那句去掉 “including its entry points and training computations” | 第一处和 “editable files” 重复；后两处前文已经说过 |
| Evidence archive | 触发条件那句和对话内容那句合成一句；notebook 工具那句移到最后一段 | 原来是两句话讲同一个动作 |
| 算法说明段 | 删去 “\textsc{UpdateDependencyGraph} applies Repair Dependency Graph Planning” 和 “Each operation updates the shared state $S$ and context $C$” | Algorithm 3 的代码已经表达了这两点 |

保留的内容：三个组件的全部功能、$C.G$、$C.Q$、$C.E$ 的定义、版本号标记、失效传播到依赖单元、75% 上下文阈值、Orchestrator 负责最终验收，以及 $o$ 和 $U$ 的含义。Algorithm 3 没有改动。

### 3.2 新的 §3.4 正文

```latex
Repository migration raises two problems that single-program migration does not: a repair may span several interdependent files, and evidence gathered on one file must remain available while the agent works on others. Repository context management addresses both through three components (\cref{fig:architecture}b).

\textbf{Repository Structural Analysis.} This tool returns an inventory of the target repository: its files, the imports among them, the functions and classes each file defines, and the cells of each notebook. It also lists files not yet assigned to any work unit. The agent invokes it on demand.

\textbf{Repair Dependency Graph Planning.} Based on this inventory, the agent partitions the target files into \emph{work units}. Each unit specifies its editable files, a repair goal, its tests, and the units it depends on; together, the units form a directed acyclic graph $C.G$. A unit may start only when the checks of its prerequisites remain valid, so shared implementations are repaired before the units that use them. $C.Q$ stores each unit's syntax check and test results with the code version on which they ran; when a file or the plan changes, the results of the affected units and their dependents are invalidated. Unit checks only guide the agent; the Orchestrator decides acceptance by verifying the complete repository.

\textbf{Evidence archive and context reconstruction.} Tool observations, code read by the agent, measurements, hypotheses, and conversations are stored in an archive $C.E$ outside the editable workspace, each tagged with the code version it describes. At evidence handoff, when the agent switches work units, or when the conversation exceeds 75\% of the context capacity, \textsc{PrepareContext} replaces the conversation with a compact one containing the current plan and progress, the structured findings, the latest measurements, and previously read code that is relevant to the active unit and unchanged since it was read.

\cref{alg:repository} connects these components to \cref{alg:diagnose,alg:repair}. \textsc{Execute} handles unit selection, file and notebook-cell operations, tests, and evidence retrieval, and returns an observation $o$ with the set $U$ of units affected by file or plan changes. All units share the repository files, the repair history, and the total budget.
```

### 3.3 如果还需要再压缩

按对理解的影响从小到大排列，可以依次删掉：

1. 最后一句 “All units share the repository files, the repair history, and the total budget.”
2. Structural Analysis 段中的 “It also lists files not yet assigned to any work unit.”
3. Evidence archive 段中列举对话内容的部分，从 “containing the current plan …” 到句末，改为 “with a compact one built from the archive”。

---

## 4. 同级标题之间空白不一致

### 4.1 原因

问题出在样式文件里的 `\flushbottom` 设置，不是正文写法造成的。ICLR 样式文件 `iclr2027_conference.sty` 中写的是 `\flushbottom \sloppy`。它的作用是要求每一页的最后一行必须对齐到版心底边。

一页正文不满的时候，LaTeX 会把页面上所有可伸缩的竖直空白一起拉长，把差额填满。导致正文不满的情况有：

- 页顶有浮动图表；
- 有 `wrapfigure` 环绕的算法块；
- `\Needspace` 提前换页；
- 某个标题不能单独留在页底。

样式里标题前后的间距本身就是可伸缩的：`\section` 前是 `-2.0ex plus -0.5ex`，`\subsection` 前是 `-1.8ex plus -0.5ex`。所以每页被拉长的量不同，同一级标题的前后空白也就不同。截图里的 “2 Related Work”、“3.4”、“4 Experiments / 4.1” 都属于这种情况。

### 4.2 改法

在 `conference_101719.tex` 导言区 `\usepackage{xurl}` 之后加了下面这段：

```latex
% The ICLR style sets \flushbottom, which stretches the glue around section
% headings on pages that are not exactly full (floats, wrapfigures, \Needspace),
% so same-level headings get visibly different gaps. Leave unused space at the
% page bottom instead.
\raggedbottom
```

改后，标题前后都回到样式规定的基本间距，多出来的空白放到页面底部。

### 4.3 如果不想加 `\raggedbottom`

只要删掉这 5 行，就恢复原样。这时空白只能通过调内容来减少：

- 调 `\Needspace` 的数值，或者删掉不必要的 `\Needspace`；
- 移动图表和算法块的位置，让各页尽量接近写满。

这样做可以减轻，但没法完全消除标题间距不一致。

### 4.4 3.3 与 3.4 之间的空白

如果编译后这里还有明显空白，多半是 Algorithm 2 的环绕块比旁边的正文高，环绕结束后留下了空行。可以试这几种办法：

1. 调小 `\Needspace{15\baselineskip}`（methods.tex 第 69 行）的数值，改成算法块实际占的行数。数值偏大会导致提前换页，在上一页底部留下空白。
2. 把 Algorithm 2 的 `wrapfigure` 挪到 3.3 节第一段（“Independent evidence handoff …”）之前。这样环绕的正文就包括 3.3 节全部三段，更容易和算法块一样高。
3. 如果旁边的正文还是比算法块短，可以把 Algorithm 2 改成全宽：去掉 `wrapfigure` 和 `minipage`，写成 `\begin{algorithm}[t] … \end{algorithm}`。

---

## 5. 合规检查：这些操作会不会被 desk reject

### 5.1 ICLR 2027 官方明确会 desk reject 的情况

ICLR 2027 Author Guidelines 里写明会 desk reject 的有：

- **正文超过 9 页**。页数限制严格执行；参考文献、AI 使用声明、伦理声明和可复现性声明不计入页数。
- **泄露作者身份**。
- **没有任何作者注册为审稿人**。
- **单个作者超过投稿数量上限**，超出的部分会被随机 desk reject。
- **作者属于美国制裁名单上的机构**。
- **OpenReview 资料信息不实**。

指南里没有列出与“竖直间距”“浮动体位置”有关的 desk reject 条款。

### 5.2 模板中关于格式的要求

ICLR 官方模板的说明文字（2024–2026 年版本措辞相同）要求：

- “Authors are required to use the ICLR style files … **Tweaking the style files may be grounds for rejection.**”
- “**Do not change any aspects of the formatting parameters in the style files.** In particular, do not modify the width or length of the rectangle the text should fit into, and do not change font sizes (except perhaps in the References section).”
- 版心 5.5 × 9 英寸，正文 10pt、行距 11pt。一级标题前空一行、后空半行。二级和三级标题前空一行、后空半行。

### 5.3 逐项判断

| 操作 | 是否改了样式文件或版心、字号 | 判断 |
|---|---|---|
| 改图注、删导读句、压缩 §3.4 | 否，只改内容 | 没有风险 |
| 调 `\Needspace` 的数值 | 否。它只决定在哪里换页，不改任何格式参数 | 没有风险。数值太大时会在页底留下空白，占用页数 |
| 移动 Algorithm 2 的位置，或改为全宽 `algorithm` | 否。属于正常的浮动体排版 | 没有风险 |
| 加 `\raggedbottom` | 没有改 `.sty` 文件，版心宽高、边距、字号、行距、标题间距的基本值都没有变。但它确实覆盖了样式文件里的 `\flushbottom` 这个设置 | 风险很低，但严格来说属于灰区，见下文 |

**关于 `\raggedbottom`**：

- **为什么说风险很低。** 官方要防止的是“改格式挤出版面”。`\raggedbottom` 的效果正好相反：它不会让一页多放内容，只会让某些页的底部留白。它也不改变版心大小，所以不会给论文带来版面上的好处。审稿人看到的只是某些页底部略空，和标题间距是否一致一样，都不容易被注意到。

- **为什么仍算灰区。** 模板原文是 “Do not change any aspects of the formatting parameters in the style files”。`\flushbottom` 是样式文件里写明的设置，按字面理解，覆盖它也算改了格式参数。我没有检索到有人因为 `\raggedbottom` 被 desk reject 的先例或公开说法，但也没有官方文字明确允许这样做。

- **建议。**
  - 如果你们希望完全按字面合规，就不加 `\raggedbottom`（删掉那 5 行即可），只用 4.3 和 4.4 的内容调整来减少空白。
  - 如果更在意版面观感，加上它的风险很低。最终怎么选，由你们根据合作者和导师的偏好决定。

### 5.4 顺带看到的其他问题

下面这几处不在这次的修改范围内，但也属于“改动格式”的范畴，一并列出供参考：

- **表格和算法用了 `\small`。** 模板说不要改字号，但在图表和算法里用 `\small` 在 ICLR 录用论文中很常见，正文仍然是 10pt，实际风险很低。**不要**在正文段落里缩小字号。
- **Introduction 中的 `\hyphenpenalty=10000\emergencystretch=1em`。** 这两个设置只影响断行，不改版心和字号，风险很低。
- **正文页数必须 ≤ 9 页。** 这是唯一一条明确“严格执行”的格式红线。加入或删除 `\raggedbottom`、移动算法块，都可能让分页略有变化。编译后务必确认 Conclusion 结束在第 9 页以内（AI use statement 不计入页数）。
- **截止时间。** 全文截止为 2026-09-25 11:59 PM AOE，即北京时间 **9 月 26 日 19:59**。截止后不能再修改。

---

## 6. 编译后检查清单

- [ ] Fig. 2 图注在图下方完整显示，没有被截断；图注中的阶段名和图一致。
- [ ] 3.2 和 3.4 中的 “Fig. 2a / Fig. 2b” 引用编译正确，不是 “??”。
- [ ] 同一级标题前后的间距一致（加 `\raggedbottom` 的情况）。
- [ ] 3.3 与 3.4 之间没有大块空白；如果有，按 4.4 处理。
- [ ] Algorithm 1、2 没有跨页，环绕文字没有和算法块重叠。
- [ ] 正文（到 Conclusion 为止）≤ 9 页。
- [ ] 页面左侧有行号，页眉为 “Under review as a conference paper at ICLR 2027”，作者为匿名。

---

## 7. 4.3 第二段换成 Tanh 修复案例图

### 7.1 要解决的问题

4.3 第二段现在是 “Training Signals and Detection Latency”。这段原来靠一张检测曲线图支撑（现在的 `fig:gradient-drift`，已移到附录 A.6）。那张图对比的是 “gradient/update 检查” 和 “只看 loss”，而 “只看 loss” 是我们自己构造的对照条件，没有一个有名字的 baseline 方法。所以图移走以后，这段只剩数字，说服力不足。

新图想说明的其实是同一件事：LaDiM 靠逐层比对训练信号，能又准又快地定位 loss 看不出来的错误。区别在于，新图用一个真实的修复案例来说明，对比对象换成了 SWE-agent 和 MatchFixAgent 这两个有名字的 baseline。

### 7.2 判断：合适，而且应该成为 4.3 的核心证据

这个案例数据扎实（全部可追溯到实验记录，见 7.3），而且能同时撑起 “准”“快”“省” 三点：

- **准：只凭分层测量就把错误定位到一个算子。** 程序能运行，前向值和源程序一致，loss 只差 $1.43\times10^{-6}$，连梯度范数检查（0.046 < 0.05）都通过了。常规检查全部看不出问题，Layered Diagnosis 却能用 “Linear 2 梯度正确、Linear 1 梯度为零” 把错误锁定在两者之间的 Tanh。这正是 3.2 节的方法完整走一遍，也是全文第一个具体实例。
- **快：从测量直接收敛到一个可检验的假设。** LaDiM 的 Verifier 在第 8 次调用（累计 0.141M token）就把 Tanh 列为唯一与测量一致的假设，并在第 17 次调用用针对性测试证实了它。两个 baseline 的记录里，对 Tanh 的怀疑与其他假设反复交替（例如 MatchFixAgent 在第 2 次调用提到 Tanh，第 3 次又转向把 encoder.0 本身当作断点），一直到第 40 次调用还在读源码。注意：不要写 “LaDiM 最先想到 Tanh”，MatchFixAgent 第 2 次调用就提过；能写的是 “LaDiM 从测量出发，最早形成并证实了这个诊断”，最硬的对比是 “第 23 次调用通过 vs 40 次用满未修”。
- **诊断变成修复：这是最有说服力的一点。** 两个 baseline 最后也怀疑到了 Tanh，MatchFixAgent 甚至写出了同样的注册代码，但都没有把它变成经过测试的修改。LaDiM 的独立证据交接，加上修复阶段 “必须有已应用的修改和修改后的测试” 这个完成条件（3.3 节），把同一个诊断变成了通过验收的补丁。这直接说明了 3.3 节设计的价值。
- **省：修好所用的资源，比 baseline 没修好时用掉的还少。** 调用次数 24 对 40。token 为 1.488M，SWE-agent 是 1.606M，MatchFixAgent 是 2.341M。
- **给表 2(a) 的 “4/5 vs 0/5” 补上过程**，并和原第二段的检测实验自然衔接：这个错误在 loss 上看不出来，正是检测实验说的 “梯度和更新错误发生在 loss 计算之后”。
- **对比对象都有名字。** 对比的是表 1 和表 2 里的 SWE-agent 和 MatchFixAgent，不再是自己构造的 loss-only 对照。

**写法要点**（都是准确且有利的表述）：

| 事实 | 推荐写法 |
|---|---|
| baseline 最终也怀疑到了 Tanh | “also suspect Tanh but never turn the diagnosis into a tested patch within 40 calls”，对比重点放在 “诊断收敛并被证实” 和 “诊断落实为修复” |
| 总 token | “repairs the program with fewer calls and tokens than either baseline spends without a repair” |
| 快 | 按调用次数和 token 讲（第 8 次调用给出唯一假设、第 17 次调用证实、第 23 次调用通过 vs 40 次用满）。不讲墙钟时间，本例三者耗时相近 |
| 案例的代表性 | 案例说明机制，跨程序的结论由表 2(a) 的 4/5 vs 0/5 支撑 |
| 内部信息 | 任务编号、配置名、服务器路径不进论文 |

### 7.3 核实结果

证据在 `D:\705file\coworker\tanh-case-evidence\`，共 1,363 个文件，SHA-256 全部通过校验（仓库提交 `4a9b9dd`）。下表 “来源” 一列是该目录下的相对路径。

| 项目 | 核实结果 | 来源 |
|---|---|---|
| 程序 | 自编码器式分类器 `AutoencoderHead`：encoder 为 Linear(15→10)–Tanh–Linear(10→4)，decoder 为 Linear(4→10)+ReLU，head 为 Linear(14→5)，AdamW + 交叉熵。**不是两层 MLP** | `code/source.py` |
| 是否表 2(a) 的失败程序 | 是。5 个失败程序之一，也是 LaDiM 修好的 4 个之一；没有注入故障 | `audit/summary.json` |
| 出错原因 | 支撑库只注册了底层的 `aten.tanh`，**没有注册**高层的 `torch.tanh` 和 `F.tanh`。未注册的调用会回退到 PyTorch，在拷贝出的张量上执行：前向值正确，但 MindSpore 的求导图在 Tanh 处断开 | `README_五项核对.md`；`torch4ms/tensor.py` 的回退分支 |
| 补丁 | 只改了 `torch4ms/ops/mtorch.py`，在 ReLU 注册前**新增** 4 行：两行 `@register_function`，函数体 `return mops.tanh(input)`。翻译出的程序本身没有改 | `audit/repair.patch` |
| 修复前（种子 42） | 执行通过；各层前向差 ≤ 1.5e-8；loss 差 1.43e-6；Linear 1 的权重和偏置梯度为 0（源程序为 0.342 和 0.109），其余 6 个参数梯度差 ≤ 6.2e-7；梯度向量 L2 差 0.359；梯度范数差 0.046（**低于 0.05 阈值，这项检查是通过的**）；参数更新相对差 0.771，Linear 1 只剩 weight decay 带来的更新 | `audit/tool-evidence.json`；`key_events/` |
| 修复后（种子 42） | 梯度向量 L2 差 1.01e-6，参数更新相对差 6.42e-6，loss 差不变；三个种子全部通过 | `key_events/ladim_call24_response.json` |
| 诊断测试（第 17 次调用） | 在 MindSpore 求导下比较输入梯度绝对值之和：原生 `tanh` 4.894，经支撑库分派的 Tanh **0**，分派的 ReLU 5.0、sigmoid 2.14、乘法 24 | `key_events/`；`audit/calls.csv` |
| LaDiM 过程 | 共 24 次调用、1,488,495 token（不含初始翻译）。第 1 次提交只做了调查、没有修改，未通过；第 8 次调用给出诊断，唯一成立的假设是 Tanh；第 22 次调用打补丁；第 23 次调用公开验收通过（第 2 次提交）；第 24 次调用输出最终报告。耗时 509 s | `audit/summary.json`；`audit/calls.csv` |
| SWE-agent | 40 次调用用满，1,606,058 token，生产代码未改，耗时 492 s。第 27 次调用发现 Linear+Tanh 梯度为零，第 35、38 次调用指出缺少映射，第 40 次调用还在检查 `F.tanh` | `raw/` 下 swe 目录 |
| MatchFixAgent | 40 次调用用满，2,340,608 token，未改代码，耗时 345 s。第 17 次调用就怀疑 Tanh 反向传播，第 37、38 次调用写出了与 LaDiM 相同的注册代码，但第 40 次调用仍在读源码 | `raw/` 下 matchfix 目录 |
| Direct repair | 没有修好这个程序（本案例的 token 未单独统计，不写进图注） | `autonomous_recovery_final.json` |
| 图中数字 | 1.488 / 1.606 / 2.341、第 17、22、23 次调用的标注，均与 `calls.csv` 一致；画图脚本里有断言检查 | `figure/make_tanh_repair_case.py` |

### 7.4 LaTeX：图

放在 4.3 第一段和表 2 之后。图注第一句直接给出结论。

```latex
\begin{figure}[t]
\centering
\includegraphics[width=\linewidth]{figures/tanh_repair_case.pdf}
\caption{Layered Diagnosis localizes and repairs a silent gradient fault that execution, forward, and loss checks all miss, in a translated autoencoder-style classifier. (a) Execution and forward values match the source, but the first linear layer receives zero gradients while the second receives correct ones, isolating Tanh as the break. A targeted test confirms that the supporting library lacks a MindSpore mapping for Tanh; the highlighted repair registers MindSpore's \texttt{tanh} for \texttt{torch.tanh} and \texttt{torch.nn.functional.tanh} (decorators omitted). (b) Cumulative investigation and repair tokens, excluding initial translation. LaDiM tests its diagnosis at call 17, patches at call 22, and is accepted at call 23, finishing with 1.488 million tokens. SWE-agent and MatchFixAgent (crosses) exhaust the 40-call limit at 1.606 and 2.341 million tokens without a repair.}
\label{fig:tanh-case}
\end{figure}
```

### 7.5 LaTeX：替换第二段（experiments.tex 第 70 行）

删除原段落 `\textbf{Training Signals and Detection Latency.} ...`，换成下面这段。所有数字都已核实（见 7.3）。

```latex
\textbf{Case Study: From a Silent Gradient Fault to an Accepted Repair.} \cref{fig:tanh-case} shows how Layered Diagnosis turns training measurements into a targeted repair on one of the five failing translations in \cref{tab:repair-results}a, an autoencoder-style classifier whose encoder applies Tanh between two linear layers. The translation is silently wrong: it executes, its forward values match the source, its loss differs by only $1.4\times10^{-6}$, and even the gradient-norm check passes. Only the gradient-vector and parameter-update comparisons expose the fault: the first linear layer receives zero gradients and changes only through weight decay. From this pattern, Layered Diagnosis pinpoints the cause. Because forward values agree and the second layer's gradients are correct, the Verifier isolates Tanh as the only operator on the broken path by call 8, and a targeted test at call 17 confirms it: Tanh dispatched through the supporting library passes zero gradient, whereas MindSpore's native \texttt{tanh} and the other dispatched activations propagate gradients. The root cause is a missing high-level Tanh mapping that silently routes the operator to PyTorch, outside MindSpore differentiation. The Repair Agent registers MindSpore's \texttt{tanh}, and the program is accepted at call 23 and confirmed on all three seeds, using 1.488 million tokens in total. SWE-agent and MatchFixAgent also suspect Tanh, yet neither turns that suspicion into a tested patch: both exhaust the 40-call limit, after 1.606 and 2.341 million tokens, and leave the program unrepaired. LaDiM thus completes the repair with fewer calls and tokens than either baseline spends without one. The case reflects a general property of training faults: gradient and update faults take effect after the loss is computed, so loss comparison cannot reveal them at the faulty step. Across four models and three seeds, gradient and update checks detect injected gradient-scaling and update-suppression faults at step~1 in all 12 runs per fault, whereas a loss check at the 0.02 threshold detects at most 4 of 12 within 50 steps (\cref{sec:detection-measurements}).
```

这段的三个落点：

- **准**：常规检查全部通过的情况下，仅凭分层测量就锁定到单个算子，并用测试证实。
- **快和省**：第 8 次调用形成诊断，第 23 次调用通过；总成本低于两个 baseline 失败时的消耗。
- **普遍性**：最后两句把单个案例接到检测实验上。四个模型、三个种子上结论一致：梯度和更新错误发生在 loss 计算之后，所以在出错的那一步，loss 比较看不出来；按 0.02 阈值，50 步内最多只能检出 4/12。
- 这里写明 “0.02 threshold”，是因为附录表里阈值降到 $10^{-5}$ 时 loss 也能在第 8 步前全部检出。写明阈值后，“4 of 12” 这个对比依然成立，而且没有破绽。

### 7.6 LaTeX：附录段（`sec:natural-protocol`，接在 LSTM 段之后）

正文压缩了 LSTM 案例、新增了 Tanh 案例，附录也按 LSTM 段的写法补一段 Tanh 的细节，供审稿人核对：

```latex
In the autoencoder example of \cref{fig:tanh-case}, the supporting library registers the low-level Tanh operator but not \texttt{torch.tanh} or \texttt{torch.nn.functional.tanh}. Unregistered calls fall back to PyTorch on copied tensors, which preserves forward values but disconnects the MindSpore differentiation graph. Before repair, on the public evaluation seed, layer outputs differ by at most $1.5\times10^{-8}$ and the absolute loss difference is $1.43\times10^{-6}$. The gradients of the first linear layer's weight and bias are zero, against norms of 0.342 and 0.109 in the source, while the other six parameter gradients differ by at most $6.2\times10^{-7}$. The gradient vector L2 difference is 0.359 and the relative parameter update difference is 0.771, whereas the absolute gradient-norm difference, 0.046, stays below its threshold. LaDiM's first submission contains no edits and fails. Its diagnostic test compares summed absolute input gradients under MindSpore differentiation: 4.894 for native \texttt{tanh} and zero for dispatched Tanh, while dispatched ReLU, sigmoid, and multiplication all pass nonzero gradients. The patch adds a four-line registration to the library, and the second submission is accepted on all three seeds, with gradient vector L2 difference $1.01\times10^{-6}$ and relative parameter update difference $6.42\times10^{-6}$ on the public seed. SWE-agent and MatchFixAgent both attribute the zero gradients to Tanh, and MatchFixAgent even drafts the same registration, yet neither applies an edit to the library within 40 calls, so both leave the program unrepaired. The contrast isolates the contribution of the repair stage: a correct diagnosis becomes an accepted repair only when it is carried into an applied edit and a test after that edit, which is exactly the completion condition LaDiM's Repair Agent enforces (\cref{sec:repair-agent}).
```

附录不计入 9 页，可以放心加。最后一句把案例和 3.3 节的设计直接对应起来（`sec:repair-agent` 是 methods.tex 中 3.3 节已有的 label）。

**第一段同步修改**：第一段结尾现在有 LSTM 案例（从 “In the LSTM case, …” 到段末，共两句）。正文里同时放两个案例太重复，建议把这两句删到只剩半句，例如：

```latex
... but recover none of the failed programs. \cref{sec:natural-protocol} details a repaired LSTM whose recurrent operators and tensor indexing in the supporting library required two further submissions.
```

LSTM 的完整过程在附录 `sec:natural-protocol` 里已经有了。附录 LSTM 段第一句 “In the LSTM example in \cref{sec:fault-characterization}” 可以保留。

### 7.7 图本身的修改建议

图里的数字都不用改，只建议改几处标注：

| 位置 | 现状 | 建议 |
|---|---|---|
| (a) Tanh 下方 | “Error” | 改为 “Gradient blocked”。“Error” 容易被理解成执行报错，和上方 Execution ✓ 矛盾；而且这个 Tanh 前向值是对的，只是梯度断了 |
| (a) 代码框 | 只有两行 `+` | 在代码框上方加一行小字 `torch4ms/ops/mtorch.py`（论文附录已经出现过 `torch4ms`，不算泄露内部信息），说明改的是支撑库，不是翻译出的程序 |
| (a) baseline 结论 | “SWE-agent and MatchFixAgent: unrepaired ✗” | 保留。这句只说没修好，没说没找到，和实验记录一致 |
| (b) 横轴 | 0–40 | 可选：在 40 处加一条竖直虚线，标 “Call limit”，让读者看出 baseline 是因为用满调用次数而停下的 |
| (b) 标注 | “17 Test / 22 Patch / 23 Accepted” | 保留。LaDiM 的第 1 次提交（前 8 次调用，没有修改代码）没有通过，图上可以在第 8 次调用处加一个小的空心标记，也可以不标；但图注和正文不能写成 “一次提交就通过” |
| 整体 | — | 已经是矢量 PDF（Times New Roman + Consolas）。按 `\linewidth` 插入后，确认最小的字不小于约 7pt |

### 7.8 版面代价

- **新增**：图是 5.5 × 2.04 英寸，按 `\linewidth` 插入正好是原尺寸，约 13 行；加上图注（约 6 行）和浮动体间距，共约 21 行。
- **正文段**：7.5 的段落约 13–14 行，原第二段约 6 行，净增约 7 行。
- **腾出**：LSTM 两句压成半句，约省 2 行。
- **净增**：约 26 行，接近半页，很可能把正文推到第 10 页。

如果超页，可以按顺序试这几种办法：

1. 把正文段换成下面的**精简版**（约 150 词，比 7.5 少约 5 行），数字全部照旧：

```latex
\textbf{Case Study: From a Silent Gradient Fault to an Accepted Repair.} \cref{fig:tanh-case} traces a failing translation from \cref{tab:repair-results}a, an autoencoder-style classifier whose encoder applies Tanh between two linear layers. Execution and forward values match the source and the loss differs by only $1.4\times10^{-6}$, yet the first linear layer receives zero gradients. Because the second layer's gradients are correct, the Verifier isolates Tanh, and a targeted test confirms that the supporting library lacks a MindSpore mapping for it, so Tanh silently runs in PyTorch outside MindSpore differentiation. LaDiM registers MindSpore's \texttt{tanh} and is accepted at call 23, using 1.488 million tokens in total. SWE-agent and MatchFixAgent also suspect Tanh but never turn the suspicion into a tested patch, exhausting the 40-call limit after 1.606 and 2.341 million tokens. LaDiM thus repairs the program with fewer calls and tokens than either baseline spends without a repair. Such faults are invisible to the loss at the step where they occur: gradient and update checks detect injected faults at step~1 in all 12 runs per fault, whereas a loss check at the 0.02 threshold detects at most 4 of 12 within 50 steps (\cref{sec:detection-measurements}).
```

2. 图注只保留 (a)(b) 各一到两句，细节放附录（7.6 的附录段已经覆盖），约省 3 行；
3. 把图宽改为 `0.9\linewidth`，约省 1–2 行，但字会变小，要确认仍不小于 7pt；
4. 把新图和表 2 放在同一页的页顶，减少浮动体留下的空白。

改完后务必确认正文不超过 9 页。
**超页时的删减顺序**（每一项都不影响核心 claim）：

1. 第 7 节正文段换成 7.8 的精简版。
2. §3.2 和 §3.4 新加的句子只保留 §3.3 那一句，因为它是 Tanh 案例的方法对应。
3. Repair history 段删掉 “50/50 against 49/50” 那半句。
4. Generalization 段删掉最后的附录引用句。

---

## 参考来源

- ICLR 2027 Author Guidelines：https://iclr.cc/Conferences/2027/AuthorGuidelines
- ICLR 2026 Author Guide：https://iclr.cc/Conferences/2026/AuthorGuide
- ICLR 官方模板说明（iclr2026_conference.tex）：https://github.com/ICLR/Master-Template
- ICLR 2027 Reviewer Guidelines：https://iclr.cc/Conferences/2027/ReviewerGuidelines
