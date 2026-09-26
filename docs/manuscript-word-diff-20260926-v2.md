# 2026-09-26 审稿意见 v2 逐字修改报告

## 对照范围

本报告将修改前检查点 `9ce1e718` 与最终论文源文件逐项对照。标记使用 `[-删除-]` 和 `{+新增+}`；为便于审阅，每项同时给出完整的修改前、修改后片段。没有变化的长段落只保留必要上下文。

本轮论文修改包括 `conference_101719.tex`、`sections/experiments.tex`、`sections/supplementary_experiments.tex`、表格源和图形生成器。并行任务 `aa53b43` 生成的匿名补充包及其说明文件不计入本轮论文逐字改动；本报告只记录其作为复现材料存在的事实。

## 1. 主文文字

### 1.1 摘要：计算顺序措辞

位置：摘要，意见 10 的第一项。

修改前：

```text
To address this, LaDiM preserves the underlying training computation order, e.g., forward, gradient computation, update, and uses the dependencies among these stages to detect and localize silent computational errors.
```

修改后：

```text
To address this, LaDiM follows the underlying training computation order, e.g., forward, gradient computation, update, and uses the dependencies among these stages to detect and localize silent computational errors.
```

逐字变化：`preserves` → `follows`。

### 1.2 引言：方法指代和计算顺序

位置：引言第二段和第三段，意见 10 的第一、第二项。

修改前：

```text
... We use semantic drift to describe the changes in such training behavior introduced by migration. These methods primarily target language level translation and test based functional correctness, leaving framework specific computational drift less directly addressed...
```

修改后：

```text
... We use semantic drift to describe the changes in such training behavior introduced by migration. Existing translation methods primarily target language level translation and test based functional correctness, leaving framework specific computational drift less directly addressed...
```

逐字变化：`These methods` → `Existing translation methods`。

修改前：

```text
We propose LaDiM (Layered Diagnosis for Multi-Agent Code Migration), a multi-agent framework that preserves the training computation order of deep learning programs.
```

修改后：

```text
We propose LaDiM (Layered Diagnosis for Multi-Agent Code Migration), a multi-agent framework that follows the training computation order of deep learning programs.
```

逐字变化：`preserves` → `follows`。

### 1.3 引言：acceptance 和仓库结论

位置：引言结果段，意见 1 和意见 10 的第三项。

图 1 的标签 `Acc.` 保留，没有修改。用户确认只将引言中的 `accuracy` 改为 `acceptance`。

修改前：

```text
LaDiM completes all 50 migrations from PyTorch to MindSpore with 57.4\% fewer total tokens than MatchFixAgent, and 75.2\% fewer than SWE-agent while obtaining higher accuracy. On the repository-level translation tasks, LaDiM achieves the best translation accuracy while saving more than 80\% tokens used.
```

修改后：

```text
LaDiM completes all 50 migrations from PyTorch to MindSpore with 57.4\% fewer total tokens than MatchFixAgent, and 75.2\% fewer than SWE-agent while obtaining higher acceptance. On repository-level migration, LaDiM saves more than 68\% of tokens on the time series repository at full acceptance and achieves the highest behavioral coverage on the recommendation repository.
```

逐字变化：

```text
... while obtaining [-higher accuracy-]{+higher acceptance+}. [-On the repository-level translation tasks, LaDiM achieves the best translation accuracy while saving more than 80\% tokens used.-]{+On repository-level migration, LaDiM saves more than 68\% of tokens on the time series repository at full acceptance and achieves the highest behavioral coverage on the recommendation repository.+}
```

替换依据是意见中对两个仓库分母和结果的区分：68% 节省对应时间序列仓库，推荐仓库改为报告 behavioral coverage。图 1 的 `Acc.` 属于图中 acceptance 的缩写，按用户要求保留。

### 1.4 术语统一和结论

位置：贡献第 2 条、结论、附录相关段落和表格。

修改前：

```text
Repository Structural Analysis and Repair Dependency Graph Planning
```

修改后：

```text
Repository Structural Analysis and Dependency Graph Planning
```

修改前：

```text
while repository context management coordinates work across shared implementations and entry points.
```

修改后：

```text
while repository coordination manages work across shared implementations and entry points.
```

逐字变化：`Repair ` 删除；`context management coordinates` → `coordination manages`。

### 1.5 复现声明

位置：AI use statement 后、参考文献前。用户最后确认采用原建议措辞。

新增原文：

```text
The supplementary material contains the implementation of LaDiM, the evaluation scripts, and the configurations used to run all baselines, anonymized for review. Section 4.1 and Appendix A specify the task collections, numerical tolerances, random seeds, and call, token, and time budgets. Appendix I lists the LLM backend and decoding settings shared by all methods. All reported costs include failed calls and the shared initial translation, as described in Appendix A.1.
```

本声明不展开说明补充包排除的数据集或桥接库。相关包的 SHA-256、内容范围和核验边界只保存在 `docs/review-evidence/manuscript-20260926-v2/evidence.json`，供内部证据记录使用。

## 2. 实验正文和附录

### 2.1 50 个任务与 29 个不同输入

位置：`sections/experiments.tex` 的 Tasks 段，意见 5。

新增句：

```text
These 50 task identifiers correspond to 29 distinct combinations of source program and evaluation settings (Appendix A.1).
```

位置：`sections/supplementary_experiments.tex` 的附录 A.1。

新增原文：

```text
Over the 29 distinct inputs, LaDiM and MatchFixAgent each accept 29/29, and SWE-agent accepts 25/29. The four remaining SWE-agent inputs comprise three failed outcomes and one interrupted run with unavailable final acceptance; all remain in the denominator.
```

这保留 50 个任务标识的主表分母，同时明确 token 去重统计所对应的 29 个输入。SWE-agent 的 25/29 来自冻结审计；中断项保留在分母中，没有改成 0 或通过。

### 2.2 Table 3b 和 Table 2a 的 token 差异

用户要求不改正文和 Table 3 caption，解释移入附录。Table 3 caption 仍保留原句：

```text
(b) Repair history and evidence handoff on ten translations, where parentheses count repairs among five failing programs.
```

附录新增句：

```text
The edit-format assistance in \cref{tab:signal-ablation}b therefore accounts for the different LaDiM token totals in the two tables.
```

因此没有采用意见中建议的 caption 追加文本，Table 3 的 caption 不增加长度。

### 2.3 Tanh 案例：从检测改为定位

位置：`sections/experiments.tex` 的 Case Study 段，意见 2。

修改前末句：

```text
Such faults are invisible to the loss at the step where they occur, and most remain undetected by the loss even 50 steps later, whereas gradient and update statistics expose them immediately. Detailed detection measurements are reported in \cref{sec:detection-measurements}.
```

修改后：

```text
Neither the loss nor the gradient-norm difference (0.046, below its 0.05 threshold) flags this fault; the per-parameter gradient comparison exposes it, and agreement in the neighboring layers localizes it to Tanh. A loss comparison can show that training has drifted, but not where. \cref{sec:detection-measurements} reports further detection measurements.
```

逐字变化：

```text
[-Such faults are invisible to the loss at the step where they occur, and most remain undetected by the loss even 50 steps later, whereas gradient and update statistics expose them immediately. Detailed detection measurements are-]{+Neither the loss nor the gradient-norm difference (0.046, below its 0.05 threshold) flags this fault; the per-parameter gradient comparison exposes it, and agreement in the neighboring layers localizes it to Tanh. A loss comparison can show that training has drifted, but not where. \cref{sec/detection-measurements} reports further detection measurements.+}
```

### 2.4 匿名化和名称

修改前：

```text
MindSpore measurements use the \texttt{torch4ms} forward and backward bridge...
Target forward computation and differentiation execute in MindSpore through \texttt{torch4ms}.
```

修改后：

```text
MindSpore measurements use our PyTorch-to-MindSpore bridge library (anonymized for review) for forward and backward computation...
Target forward computation and differentiation execute in MindSpore through this bridge library.
```

图 4(a) 同步修改：

```text
torch4ms/ops/mtorch.py  →  supporting library
```

附录标题同步修改：

```text
Natural Translation Repair Protocol  →  Initial Translation Repair Protocol
```

### 2.5 组件和规划名称

修改前后：

```text
Continuous investigation and repair conversation → Continuous conversation
Repair Dependency Graph Planning                  → Dependency Graph Planning
Without Repair Dependency Graph Planning          → Without Dependency Graph Planning
```

其中规划名称在贡献、附录小节标题、正文解释、消融表和表格生成器中同步替换；数字、预算、分母和消融条件未改。

## 3. 新增 LLM 设置附录

位置：附录 I，`sections/supplementary_experiments.tex`。

新增内容包括请求模型 `deepseek-v4-flash`、返回模型 `deepseek-flash`、HTTP chat-completion API、阶段性 reasoning 设置、上下文容量、输出上限、上下文重建阈值、API 错误处理和访问时间。

本轮根据冻结配置修正两项：

```text
Temperature: ... 0.1 in reused Java initial translations and native InterTrans configuration.
Top-p: Not set explicitly in the inspected generation and agent requests.
```

改为：

```text
Temperature: ... 0.1 in reused Java initial translations, native InterTrans, and test-guided repair.
Top-p: 0.95 for native InterTrans; omitted in the inspected shared-generation and agent requests.
```

InterTrans 的 `top-p=0.95` 来自归档的 `intertrans_adapter.py` 和补充包配置；test-guided repair 的 `temperature=0.1` 来自冻结 cross-language manifest。其他方法的实际差异仍按记录分别保留，没有写成所有方法共享同一套解码设置。

## 4. 排版和工具改动

### 4.1 导言区

新增：

```latex
\usepackage[hyphens]{url}
\usepackage{xurl}
```

作用：允许脚注、参考文献和长链接在合适位置断行，消除原有 URL overfull。

新增算法行号超链接编号：

```latex
\makeatletter
\providecommand*{\theHALG@line}{}
\renewcommand*{\theHALG@line}{\thealgorithm.\arabic{ALG@line}}
\makeatother
```

作用：每个算法行使用算法编号和行号组合，避免重复 hyperlink destination。

### 4.2 Figure 1 宽度

修改前：

```latex
\includegraphics[width=0.4\textwidth]{figures/migration_motivation.pdf}
```

修改后：

```latex
\includegraphics[width=\linewidth]{figures/migration_motivation.pdf}
```

外层 `wrapfigure` 的 `0.39\textwidth` 未改，图像现在填满自己的环绕容器。图中 `Acc.` 标签和数值均未改。

### 4.3 第八页空白的原因和处理

原因：官方样式中的 `\flushbottom` 会在页面内容不足时拉伸浮动体之间的可伸缩间距。第八页恰好连续放置 Table 2、Figure 4 和 Case Study；表格结束、图注结束及段落防孤行约束共同留下可拉伸空间，于是截图中出现多段空白。该现象来自 TeX 的分页和浮动体排版，不是正文中插入了多余空行。

局部处理：

```latex
Figure 3 后：\vspace{-12pt}
Table 2 后：\vspace{-12pt}
Figure 4 后：\vspace{-12pt}
Case Study 前：\Needspace{4\baselineskip} 和 \looseness=-1
Table 3 子表间：缩小 \medskip 为 \smallskip
Table 3 末尾：\vspace{-8pt}
```

结果：案例段落完整留在第八页，结论完整留在第九页；没有修改官方 style 文件、版心、正文全局字号或行距。

### 4.4 差异稿构建器

`scripts/build_manuscript_latexdiff.py` 新增清理 `\looseness=<integer>` 的步骤。原因是 latexdiff 标记插入到赋值和整数之间时，TeX 会把变更标记当作 `\looseness` 的值并报 Missing number。该清理只作用于差异 PDF 的可读性副本，不改干净论文源文件。

## 5. 证据、清单和输出

- `docs/manuscript-feedback-register.md` 新增 S90/S91，并记录本轮逐项回归检查、用户对复现声明的最终取舍、第八页排版反馈和未解决的历史核查项。
- `docs/review-evidence/manuscript-20260926-v2/evidence.json` 保存冻结审计的 29 输入验收、模型请求/返回名、阶段性解码设置、归档哈希和匿名补充包核验信息。
- 固定基线对照仍使用 `data/manuscript_baselines/pre-6pro-20260921/`；本轮修改前检查点是 `9ce1e71`。HTML 对照和 LaTeX 差异 PDF 均已刷新。
- 并行提交 `aa53b43` 的 `supplementary/ladim-supplementary.zip` 未作为本轮论文逐字改动计入报告；本轮只读取其 README、配置和归档内容，未重复运行其打包测试。

## 6. 验证结果

- `latexmk -pdf -interaction=nonstopmode -halt-on-error conference_101719.tex` 成功。
- 最终 PDF 共 25 页，正文在第 9 页结束，AI use statement、复现声明和参考文献从第 10 页开始。
- 最终主文和差异稿日志均无 `Overfull`、重复 destination、未定义引用或 LaTeX/package warning。
- 28 项论文、图形、统一结果和差异测试通过。
- Figure 4 的数据、24/40/40 调用轨迹、1,488,495/1,606,058/2,340,608 token 数和表格数值未改变；本轮没有重跑实验。
- 用户 PPT、未跟踪的架构 SVG、`.vscode/` 和 `other/` 未纳入本轮提交。
