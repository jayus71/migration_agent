# 分支结果来源与论文对齐报告

## 基线

| 项目 | 值 |
|---|---|
| 仓库 | `https://gitee.com/feixiao13/ascend-torch4ms.git` |
| 论文结果基线分支 | `codex/llm-fixer-capability` |
| 基线提交 | `f66cafebb8bda4881e92d40f1aa9432b94e36d2c` |
| 结果索引 | `paper_experiment_results_index.md` |
| 索引声明证据 | 23 个 JSON/CSV/manifest 文件 |
| 拉取范围 | 15 个远端分支，完整历史（非 shallow） |

论文数字只使用当前基线分支和结果索引声明的文件。其他分支仅用于解释结果来源、runner 演化和被替代实验，不用于替换当前论文数字。

## 跨分支证据矩阵

以当前 23 个声明证据文件的 Git blob 为基准：

| 远端分支 | 与当前相同 | 不同版本 | 不存在 | 结论 |
|---|---:|---:|---:|---|
| `codex/llm-fixer-capability` | 23 | 0 | 0 | 唯一完整 paper-facing 结果集 |
| `codex/scoped-guide-routing` | 2 | 0 | 21 | 仅共享 6.6 raw/step；其 guide-routing 实验不在当前索引 |
| `codex/section67-candidate-fixer` | 2 | 0 | 21 | 仅共享 6.6 raw/step；当前 6.7 结果快照后来单独汇入基线分支 |
| `experiment6566` | 2 | 0 | 21 | 6.6 raw/step 的生成来源分支 |
| `llm-fixer-xyz` | 2 | 0 | 21 | 仅继承相同 6.6 raw/step |
| `phase10-core-apply-gated` | 2 | 0 | 21 | 当前分支祖先；把 6.6 raw/step 带入当前 lineage |
| 其余 9 个远端分支 | 0 | 0 | 23 | 不包含当前索引声明的结果文件 |

不存在“其他分支有同路径但不同数值”的情况。非当前分支中的旧实验使用不同目录和文件名，因此不能作为当前论文表格的替代数据。

## 6.6 `nlp` 来源

6.6 是唯一需要跨分支历史才能完整解释的结果组。

| 时间 | 提交/分支 | 事实 |
|---|---|---|
| 2026-06-11 | `d1f66fe`，phase10 lineage | runner 将 `nlp` text classifier 替换为 image `mlp`；`models.py` 变为 `TinyImageMLP`，`realdata.py` 将 `mlp` 映射到 CIFAR-10 |
| 2026-06-13 14:01:04 UTC | 6.6 raw `started_at` | 结果记录的模型为 `cnn,nlp,transformer,tiny_causal_lm` |
| 2026-06-13 14:02:09 UTC | `6deff10`，`experiment6566` lineage | raw/step 在运行开始约一分钟后提交；该提交的 runner 将 `nlp` 实现为 `TinyTextClassifier`，并映射到 AG News |
| 2026-06-14 | `ab195e7`，phase10 lineage | 以单父提交方式复制相同 raw/step blob；没有恢复历史 `nlp` runner |
| 2026-07-20 | `f66caf...`，当前基线 | 仍保留相同 raw/step blob，但当前 runner 只注册 image `mlp` |

Git object identity：

- raw JSON blob：`8729f8344d2372d963ccc48d23263a4850aa541c`
- 600-row step CSV blob：`5cfe0234c52d5eae51c372f05c5e28249612595a`
- 历史 `nlp` models blob：`825388f5d5252b0628c2a5b797938dcda10945fa`
- 当前 `mlp` models blob：`76b549f17550d776cf8b8020eeff229a9f710443`
- 历史 `nlp` realdata blob：`d19644e44acfd2832acd84e39704490b0748d7d9`
- 当前 `mlp` realdata blob：`cc201c01ef699b9fc3cd7fe356f0a56f91492db2`

因此，6.6 表格第二行的正确含义是归档的 `nlp` 文本分类器结果，而不是当前 runner 的 image MLP。当前分支无法在不恢复历史配置的情况下直接以 `nlp` 标签重放该 bundle。

## 对论文的影响

跨分支核验不要求修改任何论文数字或模型标签。最终采用“索引负责结果选择、raw 负责实验数值”的证据层级：

1. 表格保留 `NLP`，没有错误改写为当前 runner 的 MLP。
2. 正文称其为四个“model labels”，没有把 raw 的 `nlp` 强行等同于当前 image MLP。
3. 正文明确使用 `oracle_candidate`，不把 50-step 结果外推到 Translator/Fixer 输出。
4. 正文明确 raw/step 行没有逐 run 的 dataset/batch ID。历史 runner 能说明配置映射，但不能补出缺失的逐 trajectory lineage。
5. 其他分支的旧 Section 6.4、guide-routing、旧 Section 6.5 和中间 TorchAX 实验均未混入论文。
6. 结果索引明确声明只保留最新 paper-facing 结果，因此四处 `latest` 已恢复；不再用 raw-only 规则否定索引 provenance。

论文以 `paper_experiment_results_index.md` 确定 paper-facing 结果，以当前分支 23 个声明文件提供数值证据。跨分支历史只用于解释 `nlp` 的来源，不替换论文数据。

## 当前结果引入点

- 6.3、6.5 signal、fixed-50、TorchAX signal/repair 的 paper-facing 文件由 `346e002` 于 2026-07-20 汇入。
- 6.4.1 raw/private manifest 由 `6aca843` 于 2026-07-18记录；配套 CSV 由 `346e002` 汇入。
- 6.4.2 final Translator-guide raw/tasks 由 `62a9104` 于 2026-07-17记录。
- 6.6 raw/step 首次由 `6deff10` 于 2026-06-13记录，随后以相同 blob 进入当前 lineage。

这说明当前分支是唯一同时包含索引所列全部最终结果的分支，其他分支是历史或专项实验来源。
