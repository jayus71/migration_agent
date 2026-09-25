# LaDiM 论文修改方案（执行版）

2026-09-25。本文件是唯一的执行依据，按顺序逐项修改即可。

- **行号**：文中行号指当前的 `conference_101719.tex`、`sections/methods.tex`、`sections/experiments.tex` 和 `sections/supplementary_experiments.tex`。
- **修改范围**：只改下面列出的内容，其余正文不动。
- **需要编译确认的部分**：字号、环绕和页数的效果，需要改完后编译确认。

| 项目 | 改哪里 | 要点 |
|---|---|---|
| 0 架构图 | figures/、methods.tex 第 3、6、7 行 | 换成最新 (a)(b) 两部分方法图的矢量 PDF，宽度 90%；先改图内 4 处问题；方法节首段改一句；按 (a)(b) 重写图注 |
| 1 伪代码 | methods.tex 三个 algorithm | 用 `\small`，比较全栏与半栏 |
| 2 表格字号、表前空行 | 所有 table | 用 `\small`；去掉人为留白 |
| 3 自动引用 | 全部 `Appendix~\ref` 等 | 改为 `\cref` |
| 4 Fig 前缀 | 导言区 | 输出 “Fig. 1” |
| 5 §3.4 | methods.tex 第 104–110 行 | 整节重写，先讲问题，再讲每个组件怎么做 |
| 6 Fig 3(b) | figures/repair_comparison.pdf、experiments.tex 第 32 行 | 左右并排，横轴只写一次 Task，刻度 1–29；单位改为 millions |
| 7 Fig 4 | experiments.tex 第 54–60 行，附录 A.6，ref.bib | 移到附录；正文段落缩短；附录说明阴影含义，补充 loss 对照的已有实践和阈值敏感性 |
| 8 Table 3 | experiments.tex 第 65–70 行 | 转置为窄表，环绕在正文旁；单位改为 millions |
| 9 Table 4 与全文 token 单位 | experiments.tex 第 85、90、97 行，各表数据，附录正文 | 标题改为一行；token 用量统一为 millions |
| 10 页数 | — | 正文不超过 9 页；按顺序压缩 |

---

## 0. 架构图（方法图）

**新图的结构**：新图分上下两部分：

- (a) Layered Diagnosis for Multi-Agent Code Migration：
  - 左侧是 Migration Setting。
  - 中间是四个模块：Translator Agent、Orchestrator（Execute / Coordinate Agents）、Verifier Agent（Layered Diagnosis 阶段表）、Repair Agent（Patch and Validate）。另有 Evidence Handoff，列出 Code observations、Test results、Locations、Hypotheses 四类证据。
  - 右侧是 Verified Output。
- (b) Repository Coordination：Repository Context management 包含三个组件：Repository Structural Analysis、Dependency Graph Planning、Evidence Retrieval & Context Reconstruction。
- 底部图例：LLM、$A_T,A_V,A_R$=<prompt…>、Work unit、Stages not reached。

### 0.1 导出前先改图内的四处问题

1. **迁移方向与实验不一致（必须改）。**
   - 问题：图中源端是 PyTorch (Python)；目标一栏列出了 Java；右侧输出是 `Main.java / Model.java / Data.java`。读者会理解为 PyTorch→Java。但论文实验的方向相反：18 个 Java/DJL 程序迁移**到** Python/PyTorch（experiments.tex 第 6 行），并没有迁移到 Java 的实验。
   - 建议改法：右侧输出改为 `train.py / model.py / data.py`（对应迁移到 MindSpore 的结果）；左下 “Java” 格子删掉，只保留 MindSpore、JAX 和 “…”。
   - 如果来不及改图：在图注末尾加一句 “Java/DJL programs are migrated in the opposite direction, to Python/PyTorch.”，但这只是补救办法。
2. **组件名与正文一致。** 图中写的是 “Dependency Graph Planning”，正文和附录 G.3 标题都是 “Repair Dependency Graph Planning”。把图中改为 **Repair Dependency Graph Planning**。
3. **大小写和空格。**
   - “Repository Context management” 改为 “Repository Context Management”。
   - 图例 “Work  unit” 中间有两个空格，改为一个。
4. **导出格式。**
   - 从源文件（PPT 或 SVG）导出**矢量 PDF**，不要用截图 PNG。
   - 截图里 “PyTorch” 下方有红色波浪线，那是 PowerPoint 拼写检查的痕迹。导出 PDF 后确认它没有出现。
   - 导出后裁掉四周白边（PPT 选“仅导出所选内容”，或用 `pdfcrop`）。

### 0.2 替换文件和宽度

把导出的 PDF 命名为 `hierarchical_feedback_architecture.pdf`，覆盖 `figures/` 下的同名文件。methods.tex 第 6 行改为：

```latex
\includegraphics[width=0.9\textwidth]{figures/hierarchical_feedback_architecture.pdf}
```

- **尺寸**：新图宽高比约 1.64:1。按 90% 宽度（约 125.7 mm），图高约 76 mm。
- **字号检查**：编译后确认最小的文字（如 “Candidate”、“Code observations”）不小于约 5 pt，打印出来能看清。
- **放大备选**：Fig 4 移到附录后（见第 7 项）正文会空出不少位置。如果小字太小，可以改为 `width=\textwidth`，图高约 85 mm。

### 0.3 方法节第一段（第 3 行）

前五句不变，只把最后一句 `Figure~\ref{fig:architecture} shows this process.` 替换为：

> \cref{fig:architecture}a shows this process. For repository migration, LaDiM additionally maintains repository context across files and conversations (\cref{fig:architecture}b; \cref{sec:repository-method}).

### 0.4 图注（第 7 行）

整句替换。新图注按 (a)(b) 两部分解释图中每个模块，并说明图例：

> Overview of LaDiM. (a) The Translator Agent produces a candidate, and the Orchestrator executes it, returns measurements, and coordinates the agents. The Verifier Agent applies Layered Diagnosis, comparing source and target in execution, forward values, gradients, and parameter updates. It focuses on the first stage that diverges (gradients in this example), and later stages are marked as not reached. Its code observations, test results, locations, and hypotheses are handed to the Repair Agent, which patches the candidate and submits it for validation. (b) For repositories, repository context management analyzes the repository structure, plans repairs over a dependency graph of work units, and reconstructs the context from an evidence store. $A_T$, $A_V$, and $A_R$ are the role instructions of the three agents. The code edit and signal traces are illustrative.

**注意**：如果按 0.1 第 1 点保留了 Java 而没有改图，在图注最后加上那句补救说明。

---

## 1. 伪代码字号：调小，并比较全栏和半栏

**字号**：在三个 `algorithmic` 环境开始前加 `\small`，即 9pt 字号。`\caption` 放在 `\small` 之前，这样标题字号不变。

- Algorithm 1：methods.tex 第 38 行 `\begin{algorithmic}[1]` 之前插入一行 `\small`。
- Algorithm 2：第 80 行之前插入 `\small`。
- Algorithm 3：第 114 行之前插入 `\small`。

可以同时在导言区（`\usepackage[noend]{algpseudocode}` 之后）缩小缩进：

```latex
\algrenewcommand\algorithmicindent{1em}
```

**全栏还是半栏**：Algorithm 3 行宽较长，保持全栏。Algorithm 1 和 2 试排以下三种方案，比较正文结束的位置：

| 方案 | Algorithm 1、2 的排法 |
|---|---|
| A | 半栏环绕，保持 `wrapfigure{l}{0.55\textwidth}` |
| B | 半栏环绕，改为 `wrapfigure{l}{0.50\textwidth}` |
| C | 全栏：去掉 `wrapfigure` 和 `minipage`，改为 `\begin{algorithm}[t] … \end{algorithm}` |

**选择规则**：选正文结束位置最早的方案。如果差别不到两行，选半栏（A 或 B），因为左右并排的排版更紧凑。选 B 时要检查两处是否折行：Algorithm 2 第 2 行 `\While{SubmissionsLeft ∧ BudgetLeft}`，以及 Algorithm 1 第 6 行的注释。如果折行，改回 A。

**配套修改**：环绕的算法块不能跨页，所以第 72 行的 `\Needspace{18\baselineskip}` 要保留。算法变小后，把数值改为缩小后的实际行数，约 `15\baselineskip`。第 25 行和第 64 行的 `\Needspace` 先删掉；编译后如果 3.2 节或 3.3 节的标题落在页底，再加回去。

---

## 2. 表格字号和表前空行

**字号**：每个 `table` 环境中，在 `\centering` 的下一行加 `\small`。caption 在它之前，所以不受影响。

- 正文：Table 1（experiments.tex 第 19 行）、Table 2（第 49 行）、Table 4（第 81 行），以及第 8 项中的新 Table 3。
- 附录：所有 table 同样处理。
- Table 4 目前的 `\setlength{\tabcolsep}{1.75pt}` 很挤，字号变小后可以改为 `3pt`。

**空行从哪里来**：模板本身没有规定这些空白，来源有三个：

| 来源 | 位置 | 处理 |
|---|---|---|
| 固定高度的子表标题：`\parbox[t][2\baselineskip]` 强制占两行，(a) 只有一行字，所以多出一行空白 | experiments.tex 第 85、90 行 | 见第 9 项 |
| `\Needspace`：剩余空间不够时直接换页，在页底留下空白 | methods.tex 第 25、64、72 行 | 见第 1 项 |
| 表格用 `[!htb]` 放在页中间：上下各有一段浮动体间距 `\intextsep`（模板默认的正常间距），读起来像多出的空行 | Table 2（第 46 行） | 改为 `[t]` 放在页顶，只有下方一段间距 |

---

## 3. 引用自动识别正文和附录

cleveref 已经加载，第 4 项配置好后，把以下写死的引用全部替换：

| 原写法 | 替换为 |
|---|---|
| `Appendix~\ref{x}`、`Section~\ref{x}` | `\cref{x}`（正文显示 “Section 4.3”，附录显示 “Appendix A.1”） |
| `Table~\ref{x}`、`Figure~\ref{x}`、`Algorithm~\ref{x}` | `\cref{x}` |
| `Tables~\ref{a} and~\ref{b}` | `\cref{a,b}` |
| `Algorithms~\ref{a} and~\ref{b}` | `\cref{a,b}` |
| `Table~\ref{tab:signal-ablation}a` | `\cref{tab:signal-ablation}a` |

出现位置：

- methods.tex：第 3、62、100、110、120、121 行。
- experiments.tex：第 8、12、24、28、36、40、45、54、64、74、76、101、103 行。
- supplementary_experiments.tex：第 68、76、89、94、104、118、120、124、136、163、187 行。

文献引用 `\citep`、`\citet` 不动。

---

## 4. Fig 前缀

conference_101719.tex 第 16 行改为下面三行：

```latex
\usepackage[capitalise,noabbrev]{cleveref}
\crefname{figure}{Fig.}{Figs.}
\Crefname{figure}{Fig.}{Figs.}
```

- 图的引用输出 “Fig. 1” 和 “Figs. 3 and 4”。
- 表、节、附录和算法的引用分别输出 “Table 1”、“Section 3”、“Appendix A”、“Algorithm 1”。
- 引言里现在显示的小写 “fig. 1” 会自动变成 “Fig. 1”。
- 图注开头的 “Figure 1:” 由模板决定，不需要改。

---

## 5. §3.4 重写

**删除**：第 104 行第一句 “A change to a shared implementation can affect several callers in a repository.”

**替换**：用下面五段替换第 104–110 行，Algorithm 3（第 111 行起）不动。内容全部取自附录 F、G.2 和 G.3 已有的描述，没有新增说法。

```latex
Repository migration raises two problems that single-program migration does not: a repair may span several files that depend on each other, and evidence gathered on one file must remain available while the agent works on others. Repository context management addresses both through three components, described below.

\textbf{Repository Structural Analysis.} This tool returns an inventory of the target repository: its files, the imports among them, the functions and classes each file defines, and the cells of each notebook. It also lists target files that are not yet assigned to any work unit, showing which parts of the repository remain unplanned. The agent invokes the tool on demand; it is not run at initialization or when the context is rebuilt.

\textbf{Repair Dependency Graph Planning.} Based on this inventory, the agent partitions the target files into \emph{work units}. Each unit specifies the files it may edit, a repair goal, and the tests that check it, and declares the units it depends on; together, the units form a directed acyclic graph $C.G$. The agent may start a unit only when the checks of its prerequisite units remain valid, and may edit only the files assigned to that unit, so prerequisite units such as shared implementations are repaired before the units that depend on them. For each unit, LaDiM stores the results of syntax checks and selected tests in $C.Q$, together with the code version on which they ran. When a file or the plan changes, these results are invalidated for the affected units and all of their dependents, which must then be checked again. Unit checks only guide the agent; acceptance is decided by the Orchestrator, which verifies the complete repository, including its entry points and training computations.

\textbf{Evidence archive and context reconstruction.} Tool observations, code read by the agent, measurements, hypotheses, and conversations are stored in an archive $C.E$ outside the editable workspace, each tagged with the code version it describes. When evidence is handed to the Repair Agent, when the agent switches to another work unit, or when the conversation exceeds 75\% of the context capacity, \textsc{PrepareContext} replaces the conversation with a compact one. The new conversation contains the current plan and progress, the structured findings and hypotheses, the latest measurements and tool results, and previously read code that is relevant to the active unit and unchanged since it was read. Notebook tools let the agent read and edit individual code cells, with a syntax check after each edit.

\cref{alg:repository} connects these components to \cref{alg:diagnose,alg:repair}. \textsc{UpdateDependencyGraph} applies Repair Dependency Graph Planning, and \textsc{Execute} handles unit selection, file and notebook operations, tests, and evidence retrieval. Each operation updates the shared state $S$ and context $C$, and returns an observation $o$ together with the set $U$ of units affected by changes to files or the plan. All work units share the repository files, the repair history, and the total budget.
```

---

## 6. Fig 3(b) 横轴

**图的修改**：替换 `figures/repair_comparison.pdf`：

- 两个子图左右并排。
- (b) 的横轴只在左端写一次 “Task”，下方横排刻度 1–29，每根柱对应一个数字。删掉 “Migration inputs”，也删掉 “Passes before repair / Needs repair” 两个分组文字。
- 保留 20 与 21 之间的虚线分隔，分组含义由图注说明。
- 纵轴单位从千改为百万，刻度改为 0、0.25、0.5、0.75、1.0、1.25。单位写在子图标题 “(b) Tokens saved (millions)” 里，纵轴不再单独加标签。
- (a) 不变，横轴仍为 Total tokens (millions)。
- 保留全部 29 根柱（包括两根负值）、组内排序和图例 Fewer tokens / More tokens。

**目标尺寸**：图宽约 134 mm（约 0.96\linewidth）、高约 45 mm，刻度字号不小于 6 pt。29 个刻度数字横排，不能重叠，也不能被裁掉。

**图注**（experiments.tex 第 32 行）替换为下面的写法。同时改正原图注的拼写错误 “signicantly”：

> Token costs on MindSpore migration. (a) Total tokens, comprising initial translation and subsequent calls, grouped by whether programs pass evaluation before repair. (b) Tokens saved by LaDiM relative to MatchFixAgent on each of the 29 distinct task inputs. Tasks 1–20 pass evaluation before repair and tasks 21–29 require repair; each group is sorted from low to high. Both methods accept 50/50 tasks, while LaDiM uses significantly fewer tokens.

---

## 7. Fig 4：移到附录

**决定**：Fig 4 整体移到附录 A.6（Detection Measurements）。

- **理由**：这张图对主结论的支撑有限，阴影和阈值归一化又需要不少文字解释。
- **正文怎么处理**：只保留一句话结论，并指向附录。
- **附录怎么处理**：附录负责回答两个问题——阴影是什么意思，以及 loss 阈值有没有依据。

**两个问题的答案（写在附录里）：**

- **阴影的含义**：每个训练步上，12 次运行（4 个模型 × 3 个种子）的最小值到最大值的范围；实线是这 12 次运行的均值。
- **有没有 baseline 用过 loss 阈值**：没有现成方法用“loss 差值超过阈值”来自动判错。MatchFixAgent 和 SWE-agent 看的是测试是否通过、程序有没有报错。最接近的已有实践有两个：
  - MindSpore TroubleShooter 的 `loss_compare`：比较两份训练日志的 loss 曲线，输出误差统计，但没有自动判错的阈值。
  - MindSpore Transformers 精度调优指南：先比较第 1 步的 loss，再比较梯度的 local norm 和更新后的权重。

  所以附录的写法是：引用这两个来源，说明“比较 loss”是迁移中的常规检查；论点放在与阈值无关的机制上——两种故障都发生在 loss 计算之后，所以第 1 步的 loss 与无故障运行完全相同；再用阈值敏感性表说明，第 31/18 步只是阈值取 0.02 时的结果。

**(1) ref.bib 新增两条**（年份按文档版本核对后填写）：

```bibtex
@misc{mindspore_troubleshooter_loss_compare,
  author       = {{MindSpore}},
  title        = {{TroubleShooter} \texttt{loss\_compare}: Comparing Loss Curves of Two Training Logs},
  howpublished = {\url{https://github.com/mindspore-ai/toolkits/blob/e0486eee96a1893b5e1b59f02669804a2d796030/troubleshooter/docs/api/widget/loss_compare.md}},
  year         = {2024},
  note         = {Accessed: 2026-09-25}
}
@misc{mindspore_precision_tuning,
  author       = {{MindSpore}},
  title        = {Precision Tuning Guide},
  howpublished = {\url{https://www.mindspore.cn/mindformers/docs/en/r1.7.0/advanced_development/precision_optimization.html}},
  year         = {2025},
  note         = {MindSpore Transformers r1.7.0 documentation. Accessed: 2026-09-25}
}
```

**(2) 正文**：

- 删除 experiments.tex 第 55–60 行，即整个 `\begin{figure}…\label{fig:gradient-drift}…\end{figure}`，剪切备用。
- 第 54 行整段替换为：

> \textbf{Training Signals and Detection Latency.} Gradient and update faults take effect after the loss of the current step has been computed, so the loss cannot reveal them at the step where they occur. In a detection study that injects gradient scaling and partial update suppression into four models with three seeds each, gradient and update checks detect the corresponding faults at step~1 in all 12 runs per fault. A loss check with a threshold of 0.02 detects 3 and 4 of the 12 runs, respectively, within 50 steps. \cref{sec:detection-measurements} gives the protocol, the detection trajectories, and the sensitivity to the loss threshold.

**(3) 附录 A.6**：supplementary_experiments.tex。

**第一步**：在第 66 行段落（“The detection study uses four models…”）之后，粘贴剪下的 figure 环境。把 `[!htb]` 改为 `[t]`，caption 替换为：

> Detection of (a) gradient scaling and (b) partial update suppression over 50 training steps. Solid lines show the mean over 12 runs (four models $\times$ three seeds), and shaded bands show the minimum and maximum across these runs at each step. Each difference is divided by its detection threshold, so values above the dashed line count as detected. Gradient and update checks detect both faults at step~1 in every run; with the loss threshold of 0.02, the mean loss difference first crosses at steps~31 and~18, respectively.

**第二步**：第 68 行原段落保留（其中 `Figure~\ref{fig:gradient-drift}` 按第 3 项改成 `\cref{fig:gradient-drift}`）。在它之后插入下面的段落和表格：

```latex
Loss comparison is an established check in framework migration. MindSpore TroubleShooter's \texttt{loss\_compare} tool plots the loss curves of two training logs and reports their error statistics~\citep{mindspore_troubleshooter_loss_compare}, and the MindSpore Transformers precision guide compares the step-1 loss before gradient norms and updated weights~\citep{mindspore_precision_tuning}. Neither prescribes an automatic threshold, so the loss-only check in \cref{fig:gradient-drift} applies our threshold of 0.02 to the recorded loss differences. Because both faults take effect after the loss is computed, every faulty run has exactly the same loss difference at step~1 as its fault-free counterpart. Lowering the threshold detects the faults earlier (\cref{tab:loss-threshold-sensitivity}): at $10^{-5}$, the loss check detects all 24 faulty runs by step~8 without false alarms, since the largest loss difference among fault-free runs is $3.815\times10^{-6}$. All thresholds are applied post hoc to the same saved trajectories.

\begin{table}[!htb]
\caption{Loss-only detection at different thresholds, computed post hoc on the saved trajectories (12 runs per fault, 50 steps). First detection gives the range of first-crossing steps over detected runs; mean crossing is the first step at which the mean loss difference crosses the threshold; false alarms count fault-free runs that cross the threshold.}
\label{tab:loss-threshold-sensitivity}
\centering
\small
\setlength{\tabcolsep}{3.5pt}
\begin{tabular}{@{}lcccc@{\hspace{10pt}}cccc@{}}
\toprule
 & \multicolumn{4}{c}{(a) Gradient scaling} & \multicolumn{4}{c}{(b) Partial update suppression} \\
\cmidrule(lr){2-5}\cmidrule(l){6-9}
Threshold & Detected & \hdr{First}{detection} & \hdr{Mean}{crossing} & \hdr{False}{alarms} & Detected & \hdr{First}{detection} & \hdr{Mean}{crossing} & \hdr{False}{alarms} \\
\midrule
0.02      & 3/12  & 10--11 & 31 & 0/12 & 4/12  & 6--20 & 18 & 0/12 \\
0.005     & 12/12 & 3--37  & 9  & 0/12 & 8/12  & 3--42 & 6  & 0/12 \\
0.001     & 12/12 & 2--8   & 3  & 0/12 & 9/12  & 2--14 & 2  & 0/12 \\
$10^{-5}$ & 12/12 & 2      & 2  & 0/12 & 12/12 & 2--8  & 2  & 0/12 \\
\bottomrule
\end{tabular}
\end{table}
```

**图号变化**：Fig 4 移走后，正文只剩 Fig 1–3，原来的 Fig 4 变成附录中的图，编号自动顺延。正文不再引用它，所以不需要其他修改。移走后正文约空出四分之一页。

---

## 8. Table 3：单栏窄表，环绕，单位改为百万

1. 删除 experiments.tex 第 65–70 行原来的 table 环境。不再使用 `figures/TABLE_jax_repairs.tex`。
2. 在第 62 行 `\textbf{Generalization Across Frameworks.}` 之前（紧挨着这段的开头）插入：

```latex
\begin{wraptable}{r}{0.45\textwidth}
\centering
\small
\caption{Repair and native conversion on six faulty JAX candidates. LLM repair allows up to four submissions, with costs covering investigation and repair. Native conversion runs once without an LLM. Tokens are in millions.}
\label{tab:jax}
\setlength{\tabcolsep}{3pt}
\begin{tabular}{@{}lccc@{}}
\toprule
Method & Accepted & Calls & Tokens \\
\midrule
\multicolumn{4}{@{}l}{\textit{LLM repair}} \\
LaDiM         & 6/6 & 76 & 0.674 \\
Direct repair & 6/6 & 57 & 0.353 \\
\midrule
\multicolumn{4}{@{}l}{\textit{Single native conversion}} \\
Ivy                & 0/6 & 0 & 0 \\
\texttt{torch2jax} & 0/6 & 0 & 0 \\
\bottomrule
\end{tabular}
\end{wraptable}
```

**注意**：`wraptable` 必须放在段落开头，而且这一段不能刚好跨页。编译后如果表格压到了下一节，或者环绕不正常，把宽度改为 `0.48\textwidth` 再试。

---

## 9. Table 4 标题换行，全文 token 单位统一

### 9.1 Table 4

- 第 85 行改为 `{\raggedright\textit{(a) Training signals}\par}\smallskip`。
- 第 90 行改为 `{\raggedright\textit{(b) Repair components}\par}\smallskip`。
- 第 97 行开头的 “Tokens are reported as counts.” 改为 “Tokens are in millions.”，其余句子不变。
- 三个子表的数值改为下表（修改 `figures/TABLE_training_signals_compact.tex`、`TABLE_program_components_compact.tex` 和 `TABLE_repository_components.tex`；如果这些文件由脚本生成，同时修改脚本）：

| 子表 | 行 | 原值 | 新值 |
|---|---|---|---|
| (a) | Execution and basic checks / + Forward values / + Gradients / + Parameter updates | 2,088,915 / 2,603,211 / 3,302,873 / 3,418,960 | 2.089 / 2.603 / 3.303 / 3.419 |
| (b) | LaDiM / Continuous conversation / Without repair history | 15,547,813 / 14,516,463 / 10,851,537 | 15.548 / 14.516 / 10.852 |
| (c) | Repository context management（without / with） | 6,047,074 / 1,936,579 | 6.047 / 1.937 |
| (c) | Repository Structural Analysis（without / with） | 2,651,248 / 2,126,900 | 2.651 / 2.127 |

### 9.2 全文统一规则

- token **用量**（成本）一律写成百万，保留三位小数。
- **预算和单次上限**是配置值，不是用量，保留整数写法，例如 120,000、16,384、131,072、480,000、32,768、64,000。
- 在附录 A.1 第 19 行段末加一句：

  > Token usage is reported in millions and rounded to three decimal places; budgets and per-call limits are given as exact token counts.

- 已经使用百万的表格不用改：Table 1、2、6、7、8。

### 9.3 附录表格改为百万

| 表 | 文件 | 修改 |
|---|---|---|
| Table 9 repository costs（第 126 行 caption） | TABLE_repository_costs.tex | caption 末句 “Token values are counts.” 改为 “Tokens are in millions.”。Input / Output / Tokens 三列的数值见下方 |
| Table 11 cumulative（第 165 行） | TABLE_cumulative_components.tex | caption 末尾加 “Tokens are in millions.” |
| Table 12 independent（第 178 行） | TABLE_repository_independent.tex | caption 末尾加 “Tokens are in millions.” |
| Table 13 native JAX（第 197 行） | TABLE_native_jax.tex | caption 中 “31,427 and 139,724 shared initial translation tokens” 改为 “0.031 and 0.140 million shared initial translation tokens”；“Token values are counts.” 改为 “Tokens are in millions.” |

**Table 9 数值**（Input / Output / Tokens）：

| 仓库 | 方法 | Input | Output | Tokens |
|---|---|---|---|---|
| Time series | LaDiM | 2.345 | 0.105 | 2.614 |
| Time series | SWE-agent | 7.985 | 0.051 | 8.200 |
| Time series | MatchFixAgent | 13.306 | 0.128 | 13.598 |
| Recommendation | LaDiM | 8.148 | 0.295 | 8.811 |
| Recommendation | SWE-agent | 7.890 | 0.058 | 8.317 |
| Recommendation | MatchFixAgent | 8.215 | 0.095 | 8.679 |

**Table 11 数值**（Time series / Recommendation 的 Tokens 列）：

| 行 | Time series | Recommendation |
|---|---|---|
| Repair Agent | 6.128 | 8.336 |
| + Verifier investigation | 3.896 | 8.913 |
| + Independent evidence handoff | 6.047 | 9.556 |
| + Repository context management | 1.937 | 10.191 |

**Table 12 数值**（Time series / Recommendation 的 Tokens 列）：

| 行 | Time series | Recommendation |
|---|---|---|
| LaDiM | 2.127 | 9.962 |
| Without Repository Structural Analysis | 2.651 | 7.172 |
| Without Repair Dependency Graph Planning | 1.804 | 9.214 |

**Table 13 数值**（Tokens / Two tasks / All sources）：

| 方法 | Tokens | Two tasks | All sources |
|---|---|---|---|
| LaDiM | 1.840 | 1.871 | 1.980 |
| Direct repair | 0.761 | 0.792 | 0.901 |
| MatchFixAgent | 0.259 | 0.290 | 0.399 |
| SWE-agent | 1.014 | 1.045 | 1.153 |

### 9.4 附录正文中的 token 数字

supplementary_experiments.tex 中的替换如下。每处只改数字，并把 “tokens” 改为 “million tokens”，句子其余部分不变。

| 行 | 原文数字 | 改为 |
|---|---|---|
| 15 | 2,286,034 tokens / 574,304 / 1,711,730 | 2.286 million tokens / 0.574 million / 1.712 million |
| 17 | 429,109 tokens / 1,409,686 / 3,320,339 / 5,135,863 / 6,532,453 | 0.429 million tokens / 1.410 million / 3.320 million / 5.136 million / 6.532 million |
| 58 | 674,009 tokens / 353,311 tokens | 0.674 million tokens / 0.353 million tokens |
| 108 | 39,982,844, 42,579,064, and 12,459,013 | 39.983, 42.579, and 12.459 million |
| 110 | 6,642,603 and 14,505,833 tokens | 6.643 and 14.506 million tokens |
| 118 | 13,206,863 tokens | 13.207 million tokens |
| 124 | 163,661 tokens / 368,368 tokens | 0.164 million tokens / 0.368 million tokens |
| 171 | 1,936,579（两处）/ 6,047,074 / 5,730,588 / 1,699,639 | 1.937 million / 6.047 million / 5.731 million / 1.700 million |
| 184 | 9,961,503 / 7,172,218 | 9.962 million / 7.172 million |
| 189 | 1,803,551 | 1.804 million |
| 207 | 29,455 input and 110,269 output tokens, totaling 139,724 | 0.029 million input and 0.110 million output tokens, totaling 0.140 million |

**不改的数字**：

- 预算和单次上限：第 34、58、110、157、191、203 行的 120,000、16,384、131,072、480,000、32,768、64,000。
- 第 155 行的 “120,000 characters”，这是字符数，不是 token。
- 百分比沿用原来按整数算出的值，例如 68.4%、68.0%、38.9%、15.2%。

---

## 10. 页数

**限制**：ICLR 2027 规定投稿时正文不超过 9 页，超出直接 desk reject。正文指到 Conclusion 为止；参考文献、附录和 AI use statement 不计入。现在 Conclusion 结束在第 10 页上半部分，超出约半页。

**压缩顺序**：第 7 项已经把 Fig 4 移到附录，这一步约空出四分之一页，大概率就能回到 9 页以内。其余步骤按下面的顺序做，每做完一步编译一次，一旦 Conclusion 回到第 9 页就停止：

1. 第 1 项和第 2 项：算法和表格改为 `\small`，调整 `\Needspace`，Table 2 改为 `[t]`，去掉 Table 4 的固定高度标题。
2. 第 8 项：Table 3 改为环绕。
3. 第 9 项：Table 4 数值改为三位小数后，列宽变窄，(a)(b) 也变矮。
4. 如果还超页，删掉下面这些与表格或前文重复的句子，每句约 1–2 行：
   - experiments.tex 第 28 行最后一句 “It therefore achieves complete migration with at most two submissions per program while substantially reducing the context processed by the LLM.”
   - 第 36 行最后一句 “LaDiM thus extends training behavior repair across languages, accepting more programs with fewer tokens than both agent baselines.”
   - 第 40 行 “The repository results show that LaDiM combines … inference, and retrieval.” 这一句。
   - 第 64 行 “The same diagnosis and repair procedure thus works beyond MindSpore with JAX differentiation and parameter updates.”
   - 第 74 行整段（它只是列出下面三段的内容）。
   - 第 101 行 “The LaDiM row enables both components, and the other two rows change one component at a time.”
   - 第 103 行 “Repository Structural Analysis identifies relevant implementations. Repository context management keeps plans, measurements, and inspected code available throughout the investigation.”（§3.4 已经讲过）
5. 最后一步，如果还超页：架构图从 0.9 缩到 0.85\textwidth。

**如果页数有余量**：先把架构图放大到 `\textwidth`（见第 0 项），让小字更清楚。

---

## 附：发现的其他问题（不在上述修改范围内，是否修改由你决定）

- 摘要语法错误：“LaDiM includes Translator, Verifier, and Repair agents work under a shared Orchestrator” 应改为 “LaDiM consists of Translator, Verifier, and Repair agents that work under a shared Orchestrator”；“which revises  using evidences” 应改为 “which revises the candidate using the evidence”。
- 引言第 52 行 “On the repository-level translation tasks, LaDiM achieves the best translation accuracy while saving more than 80% tokens used” 与实验结果不符：80.8% 只来自时间序列仓库；在推荐仓库上，LaDiM 用了 8.811M token，比两个对照（8.317M 和 8.679M）都多。
- Fig 1 图注 “migrations tasks” 应改为 “migration tasks”。
