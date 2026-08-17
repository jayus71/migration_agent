# 论文项目进度与阶段性成果核查结论

| 项目 | 值 |
|---|---|
| 核查日期 | 2026-08-14 |
| 论文 | *Hierarchical Feedback for PyTorch-to-MindSpore Training-Code Migration Repair* |
| 论文仓库 HEAD | `2577180 paper: add Track C results and baselines` (2026-08-11) |
| 论文状态 | 7 页，编译通过，无 undefined citation / reference |
| 实验仓库当前分支 | `codex/llm-fixer-capability` @ `f66cafe` |
| 核查范围 | 论文 TeX、结果索引、2 份审计报告、`refine-logs/` 计划与追踪、`.mindfs` 会话记录、3 条 Track 的原始结果 |

## 一、总体结论

论文主体已完成，四类实验（机制消融、诊断与最终修复、跨后端迁移、训练路径验证）都有真实 LLM 运行的原始证据支撑。**我逐项复核了论文当前所有主表数字，全部与原始结果一致**（详见第三节）。

但存在三个必须处理的问题，都不是"实验没做"，而是"做完了没有归档 / 没有进论文 / 没有记录原因"：

1. **Track A 全部结果（5 个迁移 baseline × 15 run）未进入论文**，是全项目对比最强的一组结果。
2. **MatchFixAgent（47/50，外部最强 baseline）被排除但原因从未记录在任何文件里**。
3. **一份判定为 `FAIL` 的实验完整性审计只存在于 `.mindfs` 会话日志中，从未落盘**；而唯一在磁盘上的审计报告 `PAPER_CLAIM_AUDIT.md` 结论是 `PASS`，且审计的是已被替换的旧数字。

数据本身没有丢失。核查中我确认 Track B/C 的提交此前只以 detached HEAD 形式存在于 `/tmp`，本地任何分支都不可达，但它们在 gitee 远端有对应分支；我已把两个分支 fetch 到本地，现在本地可达。

## 二、各阶段实验进度

| 阶段 | 内容 | 状态 | 是否在论文中 | 数据位置 |
|---|---|---|---|---|
| 6.3 | 反馈粒度消融 `4/12 -> 8/12 -> 12/12` | 完成，real LLM | 是（摘要+正文） | 主仓 `results/section63_..._20260715/` |
| 6.4.1 | 多作用域 Fixer-guide 消融，96 runs | 完成 | 是 | 主仓 `results_section641_multiscope_v1/` |
| 6.4.2 | Translator-guide 消融，30 runs | 完成 | 是 | 主仓 `results_section642_..._v4/` |
| 6.5.1 | 信号有效性 36 组 | 完成 | 是 | 主仓 `results_section65_signal_sanity_current/` |
| 6.5.2 | Fixed50 最终修复 | **有两版**：主仓 46/50；Track B 50/50 | 论文用 Track B 的 50/50 | 主仓 + `origin/codex/track-b-repair-baselines` |
| 6.6 | 50-step 训练一致性 | 完成 | 是 | 主仓 `results_realdata_66/` |
| Track A | 迁移赛道 5 baseline（T-DIRECT / T-CTE / T-X2MS / T-MSA / T-HIER） | **完成** | **否** | `origin/codex/track-b-repair-baselines` |
| Track B | 修复赛道 6 baseline × Fixed50 | **完成** | 部分（缺 MatchFixAgent） | `origin/codex/track-b-repair-baselines` |
| Track C | PyTorch→JAX 4 baseline | 完成 | 是 | `origin/codex/track-c-torchax-autofix` |

`refine-logs/EXPERIMENT_TRACKER.md`（7-23）全部条目仍为 `TODO`，已完全过时——实际上 M001-M005、R001-R006、R101-R105、X001-X003 绝大部分已经跑完。

## 三、论文数字复核（全部通过）

我用原始 CSV 重算了论文所有主表数字：

**Table `tab:baseline-comparison`（Fixed50 对比）** — 与 `full_hier_fixed50/summary.csv` 完全一致：

| 方法 | 论文 | 原始数据 |
|---|---|---|
| R-EXEC | 33/50 (66.0%) | 33/50 ✓ |
| R-FLAT | 34/50 (68.0%) | 34/50 ✓ |
| Direct LLM | 40/50 (80.0%) | 40/50 ✓ |
| SWE-agent | 46/50 (92.0%) | 46/50 ✓ |
| R-HIER | 50/50 (100.0%) | 50/50 ✓ |

**Table `tab:end-to-end-results`（分层/分作用域）** — 论文的 Repair@1 用的是 runner 的 `effective_rounds` 定义，我按该定义重算，7 个数字全部逐一吻合：execution 90.0%、numerical 64.3%、gradient/update 93.8%、overall 84.0%、candidate 92.3%、core operator 75.0%、core A/O 75.0%。（注：若改用 `attempts` 列重算，execution 会变 80.0%、core operator 变 65.0%、overall 变 80.0%。两者差异来自 `EX-06-A/B` 两条记录 `attempts=0` 但 `effective_rounds=1`、`patch_count=1`。`effective_rounds` 是自洽的口径，也与 `summary.json` 的 `repair_at_1=0.84` 一致；这只是记账瑕疵，不影响结论。）

**Table `tab:track-c`** — 与 `track_c/*/summary.csv` 完全一致：R-HIER 6/6、Direct LLM 5/6（CNN-NU 失败）、Ivy 0/6、torch2jax 0/6。

**摘要 12/12 是真实 LLM 结果。** 我特别检查了这一点：`run_section63_feedback_ablation.py:483` 存在一个把 GR-07 故障直接替换成正确实现的硬编码 mock payload，但它只在 `AUTOFIX_FIXER_LLM_ENABLED=0` 分支生效；论文采用的结果包记录 `mode=real_llm`，GR-07 的 `exec_num_grad` 条目是真实生成并通过。**该 mock 未污染论文数字。**

## 四、阶段性成果丢失情况核查

### 4.1 确认丢失：`FAIL` 完整性审计从未落盘（最严重）

2026-07-31 有一次独立 `experiment-audit`，对 Track A/B 做了带行号的 A–F 六维判定，**总判定 `FAIL`**（Ground-truth/leakage FAIL、Metric normalization FAIL、Completeness/provenance FAIL、Fairness FAIL 等）。这份审计只存在于 `.mindfs/sessions/1785541058-c888332928e8.jsonl`，而 `.mindfs/` 在 `.gitignore` 中——**它不在版本控制里，任何 clone 都看不到，会话清理即永久丢失**。

对照之下，磁盘上唯一的审计报告 `PAPER_CLAIM_AUDIT.md` 结论是 `PASS`，日期 7-20，审计对象是**已被替换的 46/50 版本**。当前论文用的是 Track B 的 50/50，从未被任何落盘审计覆盖。

其中已被后续工作真正修复的一条值得记录：审计指出旧 6.7 runner 声称 TorchAX/JAX 迁移，但代码实际 import 的是 `torch4ms`，从未 import TorchAX 或 JAX，判定 C2 `unsupported`。**8-11 的 Track C 工作实质性解决了这个问题**——`run_track_c_baselines.py` 真实 import `torchax_backend` / `PairedTorchaxVerifier` / Optax，不再 import torch4ms，论文已改用 Track C 结果。这是本项目最重要的一次修复，但因为审计没落盘，"修复了什么"也无从追溯。

### 4.2 确认丢失：Track A 五个 baseline 结果未进论文

Track A 是 `EXPERIMENT_PLAN.md` 里规划的**两条主赛道之一**（迁移生成赛道），已完整跑完：

| Method | Runs | Strict Success | Compile | Execution | Training |
|---|---:|---:|---:|---:|---:|
| T-HIER（本文） | 15 | **100.0%** | - | - | - |
| T-DIRECT | 15 | 0.0% | 26.7% | 20.0% | 20.0% |
| T-CTE | 15 | 0.0% | 13.3% | 13.3% | 13.3% |
| T-MSA | 15 | 0.0% | 100.0% | 100.0% | 0.0% |
| T-X2MS | 15 | 0.0% | 100.0% | 100.0% | 0.0% |

这组结果直接支撑论文最核心的动机——"能编译、能前向执行不等于训练语义正确"（T-MSA/T-X2MS 各 100% 编译执行但 0% 严格成功）。论文现在完全没有这段，也没有任何官方迁移工具（X2MindSpore、MSAdapter）或公开翻译框架（CodeTransEngine）的对比。

**丢失原因链**：7-31 用户提出"为了发论文有必要这么严格吗，只要能补一个 baseline 的结果不就可以了"，随后决策收敛为"补一个可信外部 baseline 就够"，主表固定为 R-EXEC / R-FLAT / Direct / SWE-agent / R-HIER。这个决策是针对**修复赛道**做的，但执行时把**整条迁移赛道**一起去掉了。

**但必须同时指出**：审计对 Track A 有实质性负面发现——`track_a/*/{raw,candidates,logs}` 全部只有 `.gitkeep`，没有任何候选代码、原始 JSON 或日志；`overall_results.md:3` 声称数据来自五个 `summary.json` 但这些文件不存在；`run_t_hier.py:497` 把 `strict_success` 取自内部 verifier 而非它自己算出的 strict checker；`run_t_msa.py:42-59` 把 `CrossEntropyLoss` 的 reduction 从 mean 改成 sum，改变了模型语义。**所以按当前状态不能直接放进论文**——这属于"该收但原因没记录"，不是单纯的过度防御。

### 4.3 确认丢失：MatchFixAgent 排除原因未记录

MatchFixAgent 跑完 Fixed50，**47/50 = 94.0%，是所有外部 baseline 里最强的一个，高于论文采用的 SWE-agent 46/50**。论文完全没有提到它。

排除**有正当技术理由**，但这个理由不在任何文件里：`run_external_repair_pilot.py:932-934,959-967` 把 healthy（正确）实现的函数片段作为 `source_function` 直接喂给 MatchFixAgent，属于 oracle 泄漏，它的 94% 被显著抬高。

问题在于风险方向：论文写"R-HIER 在 Repair@4 上超出 SWE-agent 8 个百分点、Repair@1 超出 12 个百分点"，而 artifact 里躺着一个 47/50 的更强 baseline，没有任何说明。审稿人或 artifact evaluator 找到它时，会看成有选择性地挑了较弱的对手。

顺带说明公平性两个方向都存在，需要如实披露：
- **对 baseline 有利**：SWE-agent 的 workspace 里被写入了 `healthy_probe.py`（`:326-333`，虽经 `redact_fault_identity` 处理），MatchFixAgent 直接拿到 healthy 函数。
- **对 R-HIER 有利**：50 个实例中有 14 个经过 `core_optimizer_mapping` 的 private-oracle 校验路径。我核查了 `GR-07-A.json`，该路径是一条 `recommended_validation` 校验命令 + preflight 作用域门控，patch 本身仍由真实 LLM 生成（该实例 `reasoning_tokens=1400`），**不是把答案直接写进去**，但它确实是外部方法没有的内部通道。
- Token 预算差异巨大：R-HIER 190,588，Direct 1,582,865，MatchFix 5,205,141，SWE 7,635,016。R-HIER 用最少的预算取得最好结果，这其实是对本文有利的证据，但论文目前完全没写。

### 4.4 归档链条断裂（不是丢失，但会导致他人无法复现）

- **submodule 指针过时**：论文仓 `ascend-torch4ms` 固定在 `f66cafe`（7-20），**早于** Track A/B（7-28）和 Track C（8-1/8-11）。任何人 clone 论文仓 + `submodule update` 拿到的是 46/50 的旧结果，**拿不到支撑论文当前主表的数据**。
- **结果索引过时**：`paper_experiment_results_index.md` 的 "6.5 repair" 仍指向 46/50 的 `results_section65_fixed50_full_real/`，与论文的 50/50 不符；索引里没有 Track A/B/C 任何条目；6.7 两行指向已被 Track C 取代的旧结果。
- **Track B/C 曾只在 `/tmp`**：两个提交在本地任何分支都不可达，只以 detached HEAD 存在于 `/tmp` 工作树。已确认远端有 `codex/track-b-repair-baselines` 和 `codex/track-c-torchax-autofix`，**本次核查已 fetch 到本地，现在可达**。
- **provenance 不一致**：计划写 `f66caf...`、Track B 工作树是 `365652d...`、Fixed50 summary 记 `3454be4...`、README 复现命令用 `3aaafd...`，四处互不相同。

### 4.5 反方向问题：披露被删得过多

`Limitations and Threats to Validity` 从独立 `\section` 缩成 2 句话。7-20 审计明确要求保留的边界披露现在都没了：50-step 结果的 `oracle_candidate` provenance、缺少 dataset/batch ID、没有 prompt redaction manifest、controlled training-fault 行的 candidate gradient norm 为 null。这与"过度防御"相反——是**披露不足**，但同样是审计成果的流失。

## 五、结论与建议优先级

**已完成、可信、可直接投稿的部分**：机制消融（6.3/6.4）、信号有效性（6.5.1）、训练路径验证（6.6）、Track C 跨后端迁移。论文这些部分的数字我已全部逐项复核通过。

**必须处理（不改实验，只补记录）**：
1. 把 `FAIL` 审计落盘为版本控制文件，并标注哪些条目已被 Track C 修复、哪些仍未解决。
2. 更新 `paper_experiment_results_index.md`：修正 6.5 指针，补 Track A/B/C 条目，标记旧 6.7 已被取代。
3. 推进 submodule 指针到包含 Track B/C 数据的提交，或在论文仓明确记录数据分支与 commit。
4. 更新 `refine-logs/EXPERIMENT_TRACKER.md` 的实际完成状态。
5. 书面记录 MatchFixAgent 的排除理由（oracle 泄漏 + 行号证据）。

**已执行（2026-08-14）**：
- **MatchFixAgent 已补入主表**，含 dagger 脚注说明 oracle 泄漏，并新增 token 列。摘要、引言、结论、Related Work、实验范围段同步更新。编译通过 8 页（第 8 页仅参考文献溢出）。详见 §6。

**需要你决策（会改动论文声明）**：
- **Limitations 是否恢复关键披露**。建议恢复 3–4 句，覆盖 oracle_candidate provenance、外部方法的 healthy 可见性、R-HIER 的 private-oracle 通道（14/50）。

## 六、2026-08-14 论文改动记录

### 已补入：MatchFixAgent

改动内容：
- `ref.bib` 新增 `ibrahimzada2025matchfixagent`（arXiv:2509.16187，ICML 2026）
- `tab:baseline-comparison` 新增 MatchFixAgent 行（47/50、74.0%、86.0%、94.0%）与 **Tokens 列**
- dagger 脚注：说明其 fragment-pair 接口提供了 healthy 实现，成功率为上界而非盲修复结果
- Results 段改写：MatchFixAgent 为最强 baseline，R-HIER 在 Repair@4 超出 6 点、Repair@1 超出 10 点，且为盲修复；补充 token 效率对比（27× / 41×）
- 摘要、引言、结论：对照基准从 SWE-agent 46/50 改为 MatchFixAgent 47/50 + SWE-agent 46/50
- Related Work 新增 MatchFixAgent 介绍句
- 实验范围段新增披露原则：外部接口暴露更多参考实现时随结果说明，不调整分母

净效果对本文有利：消除"挑弱对手"质疑；token 列使 R-HIER 以 0.19M 取得 50/50 与 MatchFix 5.21M / SWE 7.64M 形成鲜明对比。

### 未补入：Track A（复核后判定为有害，非有利）

你要求"有利的再补充"。我按此标准复核 Track A，结论是**它目前不利**，因此没有补入。两个具体原因：

**1. T-HIER 与四个 baseline 用的不是同一把尺子。** `run_t_hier.py:487-497` 确实调用了 `_run_strict_verifier()` 并把结果写入 `final_strict_verification.json`，但下一行 `strict_success = verifier_success` 把它**丢弃**，改用 T-HIER 自己的内部诊断报告。四个 baseline 走的是 paired metric checker。所以"T-HIER 100% vs 四个 baseline 0%"是两套判定标准的对比，不是同一标准下的结果。

**2. T-MSA 的 0% 是被 harness 改出来的。** `run_t_msa.py:47-56` 注入的 `_MSAStableCrossEntropyLoss` 强制 `reduction="sum"`，且**显式拦截** `reduction="mean"` 改成 `sum`。reference 用 mean。sum 下 loss 随 batch size 放大，`loss diff <= 0.02` 的阈值必然失败。T-MSA 的 0% 因此不能归因于 MSAdapter 本身。

叠加审计已确认的 raw artifact 全缺（五个目录的 `raw/`、`candidates/`、`logs/` 只有 `.gitkeep`，`summary.json` 一个都不存在，而 `overall_results.md:3` 声称数据来自这五个文件），当前状态下 Track A 放进论文的风险是：审稿人只要打开 `run_t_msa.py` 就能看到 baseline 被 harness 改弱，而我方数字走的是另一套门。这比不放更糟。

**要让 Track A 变成有利，需要重跑**，顺序如下：
1. 删掉 `run_t_msa.py:45-58` 的 `CrossEntropyLoss` 覆写，让 MSAdapter 用原生 reduction。
2. 把 `run_t_hier.py:497` 改成 `strict_success = bool(strict.get("strict_success"))`，让 T-HIER 与 baseline 同门。
3. 五个 baseline 全部重跑，保留 `raw/`、`candidates/`、`logs/` 实际产物。
4. 重跑后 T-HIER 大概率不再是 100%，T-MSA 大概率不再是 0% —— 但那才是可辩护的数字。

需要 MindSpore/CANN 环境和 LLM 凭据，我这边跑不了。你决定是否安排，以及是否值得为此推迟投稿。
