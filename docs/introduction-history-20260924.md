# 引言旧版本节选

按用户要求展示历史原文，暂不替换当前引言。以下保留各提交中的原始措辞和引用命令；历史论断不视为当前稿已确认结论。

## 2026-09-10：单独一段介绍已有翻译与修复方法

来源：提交 `b1dd9fd` 的 `conference_101719.tex`，Introduction 第一段和第三段。第三段是本次找到的、对已有方法介绍较充分的一版。

> Large language models (LLMs) support code translation across programming languages, reducing the manual effort needed to reuse existing implementations~\cite{he-etal-2025-execoder,macedo2024intertrans}. For deep learning, migration makes training programs available in another framework and its software and hardware ecosystem. Moving a program from PyTorch to MindSpore or JAX involves tensor computations, automatic differentiation, and optimizer behavior. The objective is to preserve the learning process implemented by the source program when it executes in the target runtime.

> Existing translation and repair systems provide several forms of evidence for making code edits. Unit tests check translated behavior~\cite{roziere2021unittests}, and interactive repair agents inspect source code and execution results~\cite{yang2024sweagent}. RepoTransAgent combines repository context, test failures, and reflection during refinement~\cite{guan2025repotransagent}. MatchFixAgent supplies reports from multiple semantic analyses to an agent that generates tests and repairs translations~\cite{ibrahimzada2025matchfixagent}. These systems organize feedback around tests, repository context, or general semantic properties. For training-code migration, the remaining question is how to interpret the evidence using the dependencies between training computations, so that a repair agent can distinguish the stage requiring correction from discrepancies in later stages.

## 2026-09-21：固定基线中的紧凑版本

来源：[固定基线](../data/manuscript_baselines/pre-6pro-20260921/conference_101719.tex)，Introduction 第一段。

> Migrating deep learning code allows existing models and training programs to run in new software and hardware environments. Differences in operator semantics, numerical precision, and random number handling can change the computations performed after migration. Automatic differentiation and optimizer interfaces introduce further differences in how a model learns~\citep{paszke2019pytorch,mindspore2020whitepaper}. Large language models (LLMs) reduce the manual effort involved in code translation~\citep{he-etal-2025-execoder,macedo2024intertrans}, while automated tests and interactive repair help assess and correct translated behavior~\citep{roziere2021unittests,yang2024sweagent,ibrahimzada2025matchfixagent}. Training programs require these capabilities to preserve the computations that determine each parameter update.

## 2026-08-29：按三类反馈组织的更早版本

来源：提交 `40982c5` 的 `conference_101719.tex`，Introduction 第三段。该版本最后一句对已有方法作了较强的概括，保留作历史比较，恢复时需重新核对来源。

> Existing systems supply repair feedback in three main ways. Translation pipelines validate against a single outcome such as compilation, unit tests, or repository-level pass rates~\cite{he-etal-2025-execoder,macedo2024intertrans,guan2025repotransagent}. Repair agents explore the program until a test or execution trace exposes the fault~\cite{shinn2023reflexion,chen2023selfdebugging,wang2024codeact,xia2023aprplm,yang2024sweagent}. Conversion and differential-testing tools compare a converted output or a single behavioral property against a reference~\cite{mindspore2023mindconverter,yang2011csmith,pei2017deepxplore}. Despite their variety, all three share an implicit assumption that one verdict on the whole program is a sufficient unit of repair feedback.
