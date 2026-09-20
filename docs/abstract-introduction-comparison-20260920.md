# 摘要与引言：本轮修改前后对照

修改前取自本轮改稿开始前的已提交论文（`27ebd64c4ba0`），修改后保留首次结果更新后的快照，供追溯本轮扩写；随后按用户要求精简的正文见当前论文。生成此对照时未改动论文。正文保留原文，显示时仅去除 LaTeX 格式命令并展开图号；引文以原键名列出。

| 部分 | 修改前英文词数 | 修改后英文词数 | 增加 |
| --- | ---: | ---: | ---: |
| 摘要 | 189 | 216 | 27 |
| 引言正文与贡献列表 | 420 | 437 | 17 |

词数按英文单词与数字计，连字符词、斜杠词合计为一个词；引言不计图注、引文和 LaTeX 命令。

本轮摘要主要改动结果段，并将 `updated diagnoses` 改为 `updated measurements`。新结果段同时加入主比较、token 节省、故障修复与健康保持、跨语言结果、信号消融概括，信息集中在摘要末尾。引言前两段、第二项贡献和图 1 图注未改；修改集中于第三段及第一、第三项贡献。


## 摘要

### 修改前

Migrating deep learning training code across frameworks requires preserving training behavior. Large language models can produce executable translations whose forward values agree with the source, yet whose gradients or parameter updates are incorrect. Checking these stages exposes such faults, but error propagation can produce multiple discrepancies and obscure which computation needs repair. We propose LaDiM, a multi-agent repair system that uses dependencies between training stages to organize verification evidence into layered diagnoses. Its verifier investigates execution status, forward values, gradients, and parameter updates, then records hypotheses and code locations supported by observed measurements. The translator supplies an initial target program, and the repair agent uses this diagnosis to edit the permitted code. An orchestrator coordinates translation, verification, and repair, using updated diagnoses after each edit to guide subsequent attempts within a fixed budget. On 50 MindSpore fault instances, LaDiM accepts 45 within four submissions, compared with 29 for SWE-agent and 35 for a shared-tools Direct control. It also repairs four of five faulty natural translations while retaining all five healthy translations. Experiments on MindSpore and JAX demonstrate the effectiveness of the same diagnosis and repair procedure across target frameworks.

### 修改后

Migrating deep learning training code across frameworks requires preserving training behavior. Large language models can produce executable translations whose forward values agree with the source, yet whose gradients or parameter updates are incorrect. Checking these stages exposes such faults, but error propagation can produce multiple discrepancies and obscure which computation needs repair. We propose LaDiM, a multi-agent repair system that uses dependencies between training stages to organize verification evidence into layered diagnoses. Its verifier investigates execution status, forward values, gradients, and parameter updates, then records hypotheses and code locations supported by observed measurements. The translator supplies an initial target program, and the repair agent uses this diagnosis to edit the permitted code. An orchestrator coordinates translation, verification, and repair, returning updated measurements after each edit to guide subsequent attempts within a fixed budget. On a collection of 50 PyTorch-to-MindSpore migration tasks, LaDiM achieves 50/50 acceptance, matching MatchFixAgent while using 57.4% fewer end-to-end tokens. It repairs every failing initial translation and preserves every initially accepted program. On 18 Java/DJL-to-Python/PyTorch tasks, LaDiM accepts nine translations, compared with eight for SWE-agent and MatchFixAgent. Controlled experiments show how gradient and parameter update checks expose faults that remain hidden under incomplete verification. Experiments on MindSpore and JAX demonstrate the effectiveness of the same diagnosis and repair procedure across target frameworks.

## 引言第 1 段：背景与问题

本轮未改动。

Migrating deep learning training code makes existing programs available in another framework and its software and hardware ecosystem. Large language models (LLMs) reduce the manual effort involved in code translation [he-etal-2025-execoder, macedo2024intertrans], but an executable translation may still change how a model learns. A PyTorch program moved to MindSpore or JAX can produce different forward values, compute incorrect gradients despite matching losses, or update the wrong parameters despite plausible gradients. Differences in operator conventions, differentiation interfaces, and optimizer semantics cause these failures [paszke2019pytorch, mindspore2020whitepaper, google2025torchax]. Preserving training behavior requires checking each computation and identifying where a discrepancy originates.

## 引言第 2 段：相关方法与训练信号

本轮未改动。

The evidence available to translation and repair systems does not directly identify this origin. Unit tests check translated behavior [roziere2021unittests]; interactive agents inspect code and execution results [yang2024sweagent]; RepoTransAgent combines repository context, test failures, and reflection [guan2025repotransagent]; and MatchFixAgent supplies reports from multiple semantic analyses to guide test generation and repair [ibrahimzada2025matchfixagent]. These approaches leave the repair process to infer how discrepancies depend on one another during training. A forward error can change both gradients and parameter updates, while an incorrect update affects later forward computations as training continues. Figure 1 shows the resulting delay: the gradient or parameter update check detects every injected fault at step 1, whereas the mean loss difference crosses its threshold only at steps 31 and 18 in panels (a) and (b). The faulty computation is observable well before its accumulated effect on loss. Execution must succeed before numerical comparisons are available; once forward values agree, later discrepancies motivate investigation of differentiation or optimizer behavior. These relationships make training measurements useful evidence for an agent that must identify an unknown fault.

## 引言第 3 段：方法和结果

### 修改前

We introduce LaDiM (Layered Diagnosis for Multi-Agent Code Migration), which separates evidence gathering from repair. A translator supplies the initial target program. An independent verifier reads public code, runs tests, and records supported hypotheses and locations. A repair agent receives this investigation and revises the implementation, retaining its observations across attempts. The orchestrator controls acceptance through external tests. Experiments on MindSpore and JAX examine repair effectiveness, training signals, and repair history. The selected slim v4 configuration accepts 45 of 50 injected MindSpore faults and repairs four of five faulty natural translations. This paper makes three contributions.

### 修改后

We introduce LaDiM (Layered Diagnosis for Multi-Agent Code Migration), which separates evidence gathering from repair. A translator supplies the initial target program. An independent verifier reads public code, runs tests, and records supported hypotheses and locations. A repair agent receives this investigation and revises the implementation. The orchestrator evaluates each submitted program and returns observations for further attempts. On a unified MindSpore migration collection, LaDiM and MatchFixAgent both achieve 50/50 acceptance, while LaDiM uses 57.4% fewer tokens. Training-signal studies explain how the verification procedure exposes faults, and experiments across languages and target frameworks examine the procedure's applicability. This paper makes three contributions.

## 贡献 1

### 修改前

We formulate training-code repair using execution, forward values, gradients, and parameter updates as evidence for investigating unknown faults.

### 修改后

We formulate autonomous training-code repair using execution, forward values, gradients, and parameter updates as evidence for investigating unknown faults and verifying candidate changes.

## 贡献 2

本轮未改动。

We develop LaDiM, a multi-agent repair framework with an independent investigation, explicit evidence handoff, and a shared acceptance and retry loop.

## 贡献 3

### 修改前

We evaluate repair effectiveness and cross-framework applicability on MindSpore and JAX, and analyze retry behavior, repair history, and training-signal coverage.

### 修改后

We evaluate migration effectiveness and token use under a common acceptance protocol, and examine training-signal coverage, repair behavior, and applicability across languages and target frameworks.

## 引言中的图 1 图注

本轮未改动。

Loss and gradient differences (a) and loss and update differences (b), normalized by each signal's threshold. Gradient and update checks detect faults at step 1 in all 12 runs per panel. The mean loss difference crosses the detection threshold (dashed) at steps 31 and 18, respectively. Curves show means and shading shows ranges.
