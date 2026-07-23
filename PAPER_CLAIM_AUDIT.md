# 论文声明与实验结果对齐审计

| 项目 | 值 |
|---|---|
| 日期 | 2026-07-20 |
| 论文 | *Hierarchical Feedback for PyTorch-to-MindSpore Training-Code Migration Repair* |
| 结果分支 | `codex/llm-fixer-capability` |
| 结果提交 | `f66cafebb8bda4881e92d40f1aa9432b94e36d2c` |
| 最终论文 SHA256 | `981dc07935900cff87a9e64006a5558a634a360790eab11dcfb33716c6c1d1bd` |
| 审计输入 | 1 个 TeX 文件 + 23 个原始 JSON/CSV/manifest 文件 + 1 个结果选择索引 |
| 独立审计路由 | `codex-subagent-runtime-id-unexposed`；运行时未暴露可验证的模型 ID 或 reasoning 等级 |

## 总体结论: PASS

最终零上下文审计逐条核验了 456 个实验相关声明。所有数字、分母、配置、聚合、增量、标题、表注、来源和范围声明都能与指定证据对应；仅有 32 个标准四舍五入项，不存在实质性不一致。23 个 raw 文件是数值证据，结果索引仅用于判定 paper-facing 选择及 `latest` provenance。

| 状态 | 数量 |
|---|---:|
| `exact_match` | 424 |
| `rounding_ok` | 32 |
| `ambiguous_mapping` | 0 |
| `missing_evidence` | 0 |
| `config_mismatch` | 0 |
| `aggregation_mismatch` | 0 |
| `number_mismatch` | 0 |
| `scope_overclaim` | 0 |
| `unsupported_claim` | 0 |
| **合计** | **456** |

计数规则：每个可独立检查的实验声明计一次；分数本身计一次，单独印出的百分比另计；摘要、正文和表格中的重复出现分别计数。引用、公式、交叉引用和排版尺寸不计入。

## 章节到结果映射

| 论文位置 | 原始证据 | 论文采用的结果 | 审计 |
|---|---|---|---|
| 摘要、6.3 反馈粒度消融 | `section63_summary.json`、episode CSV、两个 feedback/fault CSV | 36 episodes；严格成功 `4/12 -> 8/12 -> 12/12`；执行/数值/梯度故障分解与中位轮次均一致 | PASS |
| 6.4.1 多作用域 Fixer-guide 消融 | `section641_multiscope_raw.json`、tasks CSV、scope CSV、private manifest | 24 个 base tasks、96 个 condition runs；binary 为 `0/24, 0/24`，layered 为 `18/24, 14/24`；各 scope 的 Repair@1/@4 与 OOS 均一致 | PASS |
| 6.4.2 Translator-guide 消融 | `section642_translator_guide_ablation_raw.json`、tasks CSV | 5 tasks x 3 repeats x 2 conditions；guide off 为 compile/execute `2/15`、train/success `0/15`；guide on 全部 `15/15` | PASS |
| 6.5.1 信号有效性 | `section65_signal_effectiveness_raw.json`、table CSV | 4 models x 3 faults x 3 seeds = 36；每个 model/fault 行均 `3/3` 命中预期信号 | PASS |
| 6.5.2 fixed-50 Fixer | `section65_fault_pool_repair_raw.json` 及 5 个结果 CSV | 25 类、50 实例、`46/50=92.0%`；25/25 类有成功实例；层级、scope、Repair@k 和 4 个失败原因一致 | PASS |
| 6.6 oracle-candidate 50-step path consistency | raw JSON、600-row step CSV | 4 labels x 3 seeds x 50 steps；全部阈值检查通过；CNN/NLP/Transformer/TinyLM 的均值和最大值逐项一致 | PASS |
| 6.7 TorchAX signal | `torchax_verifier_summary.json` | 6/6 首失败层定位正确 | PASS |
| 6.7 TorchAX repair | `section67_fixer_torchax_raw.json`、tasks CSV | clean `2/2`；repair `6/6`；全部一轮完成，Repair@1/@3 均为 100% | PASS |

23 个声明输入文件全部映射到至少一个论文声明，没有 orphan evidence。

## 主要修正

| 原稿问题 | 最终处理 |
|---|---|
| 摘要中的旧版 `0/5, 1/5, 4/5` 无当前 raw 证据 | 改为当前 6.3 的 `4/12, 8/12, 12/12` |
| 旧 6.4 使用 `1/4, 3/4, 2/4, 4/4`，与最新 multi-scope 运行冲突 | 用 24-base-task、96-run 的 6.4.1 结果重写，并新增 6.4.2 Translator-guide 表 |
| 原稿声称 Fixer guide 与 layered feedback 有互补增益 | 改为当前证据支持的结论：layered feedback 有效，但 Fixer guide 没有严格成功率收益 |
| real-data 表的 MLP 行来自被替代结果 | 按 selected raw 的 `nlp` 行改为 NLP，并替换四个聚合值 |
| 50-step 结果被写成自动迁移输出一致性证据 | 明确为 `oracle_candidate` 的短期 path consistency，不外推到 Translator/Fixer 输出 |
| 数据集、blind prompt、verifier 版本和缺失梯度的来源边界过强 | 改为结果包实际可证明的范围，并在正文和限制中显式披露缺失字段 |
| raw-only 审计曾把四处 `latest` 误判为无证据 | 按权威结果索引恢复 `latest`；索引负责选择 provenance，raw 继续负责全部数值 |
| oracle、lineage 和 prompt-manifest caveat 在摘要、设计、表注、结果和结论中重复 | 删除重复表述，仅在实验定义和 Limitations 保留必要边界 |

## 合规四舍五入

32 个非精确项全部为标准显示精度：`1/3 -> 33.3%`、`2/3 -> 66.7%`、`7/12 -> 58.3%`、`13/14 -> 92.9%`、`25/26 -> 96.2%`、`22/26 -> 84.6%`，以及 6.6 表中的科学计数法截断。没有数值膨胀、best-seed cherry-pick、相对增益/百分点混用或宏平均/池化平均混用。

## 结果包与复现风险

以下事项不构成论文到指定 raw 的不一致，因此不影响本次 `PASS`；它们仍应在提交或复现实验前处理：

1. selected raw 将第二个 50-step 模型标为 `nlp`，但当前分支的 `models.py` 只注册 `mlp`，`realdata.py` 也只处理 `mlp`。这使该结果包无法由当前 runner 按 `nlp` 标签直接重放。
2. 50-step raw 明确记录 `candidate_provenance="oracle_candidate"`，不能作为自动 Translator/Fixer 输出质量的证据；论文已按此收窄。
3. 50-step bundle 验证了 CIFAR-10 与 AG News 文件，但 run/step 行没有 dataset/batch ID；fixed-50 bundle 也没有保存可见字段或 prompt redaction manifest；论文已披露这些缺口。
4. controlled training-fault 行的 candidate gradient norm 为 null，但 checker 可结合 update difference 将 G+U 判为命中；论文已明确 G 在这些行表示 missing-gradient evidence。
5. 当前 TeX 能编译为 9 页 PDF，但 BibTeX 仍缺少 `mindspore2020framework` 条目。这是原稿已有的引用告警，不属于实验结果对齐问题。

## 审计轨迹

审计经历了“初始 FAIL -> 修正后 WARN -> PASS -> raw-only 措辞误判 -> 索引感知最终 PASS”。不同轮次采用的声明粒度不同，因此声明总数不能作为轮次间质量指标；应以每轮的具体 mismatch 类别为准。

- 初始审计发现旧版 6.4、无证据的摘要数字、错误 real-data 行和 oracle provenance 外推。
- 中间复审确认数值错误已归零，并继续收紧 verifier、blind prompt、数据 lineage 与缺失梯度措辞。
- 分支复核后的 raw-only 线程确认全部数值正确，但因排除了结果索引而误判四处 `latest`。
- 最终线程将结果索引限定为选择/provenance 证据，将 23 个 raw 文件限定为数值证据；恢复 `latest`、压缩重复 caveat 后，结论仍为 `PASS`。

完整 prompt/response 轨迹位于 `.aris/traces/paper-claim-audit/2026-07-20_run01/`。机器可读哈希、计数与结果文件清单见 `PAPER_CLAIM_AUDIT.json`。
