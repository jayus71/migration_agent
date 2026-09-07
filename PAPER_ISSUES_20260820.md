# 论文与仓库侧待处理事项

| 项目 | 值 |
|---|---|
| 日期 | 2026-08-20 |
| 对应论文 | `conference_101719.tex` |
| 对应仓库 | `ascend-torch4ms`，分支 `codex/llm-fixer-capability`（HEAD `f3c84bb`） |
| 范围 | 不需要跑实验的事项：论文措辞、结构重排、仓库结果目录整理、文档更正 |

跑实验的事项在 `EXPERIMENT_REQUEST_20260820.md`，两份互不依赖，可并行。

1–7 是逐条的问题，按是否影响论文正确性排序（1 会影响，2 是措辞与数据的一致性，3–7 是仓库整理和文档更正）。最后一节是论文结构的重排建议。

---

## 1. `nlp` 这个模型名在两份数据里指的不是同一个模型

`d1f66fe` 这个 commit 把 `nlp` **换成了另一个模型**，不只是改名：

```
-MODEL_NAMES = ("cnn", "nlp", "transformer", "tiny_causal_lm", "qwen_tiny")
+MODEL_NAMES = ("cnn", "mlp", "transformer", "tiny_causal_lm")

-class TinyTextClassifier(nn.Module):     # nn.Embedding + Linear(embed_dim, 24)
+class TinyImageMLP(nn.Module):           # Linear(in_dim, hidden) + Linear(hidden, num_classes)
```

数据绑定也跟着换（`realdata.py:72-73`）：旧的 `nlp` 跑 **AG News 文本分类**，新的 `mlp` 跑 **CIFAR-10（5 类、4×4 图像）**。而 `_display_model()`（`run_section66_realdata_training_consistency.py:76-79`）又把 `mlp` 在 CSV 里显示回 `nlp`。

**后果**：旧 6.6 那份 CSV 里的 `nlp` 行是文本分类器，新数据里的 `nlp` 行是图像 MLP。同一个标签、不同的模型、不同的数据集。实测两份的 `torch_loss` 从第 1 步就差 0.22 且不随步累积（三个种子的 signed delta 均值都是 +0.22、std≈0.025），与这个解释一致。其余三个模型逐位相同。

**要做的事**：

1. 论文 `:152` 和 Table V 都写作 **MLP**，对应新的图像 MLP，**当前措辞是对的**。已核实 `:152` 引的三个数字（3.815e-6 / <4e-8 / <3.9e-6）在新数据上仍然成立。无需改动。
2. `results_realdata_66/` 那份旧 CSV 已过时，它的 `nlp` 行对应一个不存在的模型。若仍有地方引用，改指向新数据。
3. `DATA_REQUEST_per_step_divergence.md` 第 4 节写「`nlp` 和 `mlp` 指同一个模型」，这句是错的，后续规格不要沿用。

## 2. 6.6 节候选代码的来源需要在正文说一句

已交付数据的 raw JSON 里 `candidate_provenance` 是 `oracle_candidate`。这个字段有三个合法取值（`run_section66_realdata_training_consistency.py:883-884`）：

| 取值 | 含义 |
|---|---|
| `oracle_candidate` | 候选代码是人工写好的已知正确的 torch4ms 实现 |
| `translator_output` | 候选代码是 LLM 翻译器直接产出的 |
| `fixer_final_artifact` | 候选代码是修复流水线的最终产物 |

两点事实：候选侧跑的是真 torch4ms（`import torch4ms`、`torch4ms.default_env()`、`Torch4msOptimizer`、`loss.backward(module=model)`），不是 PyTorch 假装；但候选代码是人工正确实现加人工注入故障，不是翻译器的产出。

**后果**：这批数据支持的结论是「三层检查在故障存在时按预期分层响应」。它不涉及翻译器在真实迁移中产出的缺陷分布——那是 6.5 节 Table I 的事。

**要做的事**：Analysis 一节加一句说明候选构造方式，例如「候选为已知正确实现加受控故障注入，用以隔离检测信号本身的行为」。这是描述实验设计，不是让步。不要把它写成「我们在真实迁移候选上验证了分层检测」，那句与数据不符。

## 3. Figure 3 已从论文中删除，幅值分离目前没有图

`figures/signal_magnitude.pdf` 已生成，但 tex 里没有 `\includegraphics` 引用它。git 历史是先加后删：

```
635ecd5  2026-08-17  Add signal-magnitude figure to the analysis section
9da362f  ...         Fix figure 2 label placement and drop figure 3 from the manuscript
```

`DATA_REQUEST_per_step_divergence.md` 第 1 节的前提是「图 3 已展示幅值分离，缺的是时间维度」，这个前提现在不成立。

**要做的事**：新图不必受图 3 构图约束，见 `EXPERIMENT_REQUEST_20260820.md` 第三部分。`signal_magnitude.pdf` 若不再用，从 `figures/` 移走或标注。

## 4. 仓库里有两份 fixed50 结果（46/50 和 50/50）

| 路径 | 结果 | 时间 |
|---|---|---|
| `results_section65_fixed50_full_real/` | 46/50 (0.92) | 2026-06-28 |
| `baselines/full_hier_fixed50/r_hier/` | 50/50 (1.00) | 2026-07-26 |

两份同配置（`real_llm=true`、`blind=true`、`instance_suite=fixed50`），论文用后者。

**已核实差异来自代码改进，不是同代码跑两次挑好的**：两次之间有 50 个 commit 动了 `autofix/`，其中 `f66cafe "fix(autofix): enforce strict gradient verification"`（2026-07-20）落在中间，gradient_update 恰好从 14/16 涨到 16/16。

**要做的事**：`paper_experiment_results_index.md` 目前仍指向 46/50 那份旧结果（见 `PROJECT_STATUS_CONCLUSION.md:104`）。更新指向到 `full_hier_fixed50/r_hier/`，旧目录标注 superseded。这是仓库整理，让索引指向论文实际用的数据。

## 5. 仓库里那份审计文档本身有错，需要更正

`EXPERIMENT_INTEGRITY_AUDIT_20260731.md` 是之前某个 Claude 会话的自查输出（原本只在 `.mindfs/` 会话日志里，2026-08-14 补录成文件），不是外部审计。逐条进代码核验后：

| 审计原判 | 核验结果 |
|---|---|
| 六方法未共用同一 strict verifier | **基本不成立**。是两套入口（内部 `run_section65_real_fault_repair.py`、外部 `run_external_repair_pilot.py`），但判定过没过的 `run_probe` 是同一个，横向比较公平 |
| 外部方法分阶段状态是合成的 | **成立**（见实验文档 Bug 5），但内部方法同样如此，不是区别对待 |
| R-HIER 有 private-oracle 绕过 | **不成立**。审计引的 `:537` 在 `run_section63_feedback_ablation.py`，属 6.3/6.4 节，不在 Table I 的路径上；且 `core_gradient_mapping.py:320-324` 显示 mock 只在 `real_llm=False` 时注入，Track B 是 `--real-llm` 跑的 |
| Track A 不可复现 | **成立**。五个 `summary.json` 全不存在，15 个目录只有 `.gitkeep` |

**要做的事**：那份文档已进版本控制，其中两条不成立。在文件里加一段更正，写明哪两条经代码核验不成立及依据行号。「private-oracle 绕过」这条尤其需要更正——它描述的是一个不存在的问题。

## 6. 已核实候选源码里没有泄漏参考实现

`controlled_cases.py` 里参考函数和候选函数是同一个文件里逐字节相同的实现（`_candidate_attention`/`_reference_attention` 等，`:328-363`），故障靠单字符替换注入（如 `ROPE_OLD` 把 `+` 改成 `-`，`:644-647`），修好的版本与参考函数逐字节相同。所以有必要确认 LLM 拿到的源码里看不到参考实现。

已实测：调用 `candidate_artifacts.isolated_faulty_source()` 生成 30 个（故障 × 模型）组合的候选源码，检查 `class Reference` / `expected =` / `def run_probe(` / `_reference_` / `FIXED = ` 等标记，全部 0 命中。参考实现只存在于 `isolated_verifier_source()` 那一份，与候选是分开的两个 artifact。

**要做的事**：这是实验设计正确性的核验结果，记在仓库里（例如 `paper_experiment_results_index.md` 或 6.5 节的实验说明）即可，不需要写进论文。论文里主动讨论「我们的故障会不会太简单」没有必要——没人提出这个质疑，写进去反而是自己给自己挖坑。

## 7. 6.4 节的消融有五个互相矛盾的结果目录

`results_section64_fault_feedback_ablation_v{3,4,5,6_isolated,7_execution_binary}/` 五个目录结果互相矛盾（v5 的 test1 是 16/18，v7 的 test1 是 0/18）。论文 `tab:feedback-ablation` 用的都不是这五个，而是 `results/section63_feedback_ablation_nu04_clean_alias_rerun_20260715/section63_summary_by_feedback.csv`（12 任务 3 条件，`4/12 → 8/12 → 12/12` 精确匹配）。

**要做的事**：确认论文用的那份是最终版，五个 `v*` 目录标注 superseded 或移出仓库。留着五份矛盾的中间结果，以后自己回来看也分不清哪份算数。


---

# 论文结构：建议重排成 4 个 RQ

「实验少」这个感觉，至少一半来自结构而不是数据量。三条具体证据：

1. **正文顺序和表编号打架**。Table V（signal effectiveness）在 RQ2 的正文里讨论，编号却排在 Table IV（JAX）之后。读者第一眼就觉得乱。
2. **RQ2 塞了三样不同的东西**：反馈消融（Table II）、文档消融（Table III）、信号有效性（Table V）。三者回答的不是同一个问题。
3. **Table III panel (b) 讲的是翻译器，不是 LADDER**。「翻译器 prompt 里放框架文档，0/15 → 15/15」是个干净的结果，但它不属于方法的贡献部分，放在消融里分散注意力。

建议重排：

| RQ | 问什么 | 装什么 |
|---|---|---|
| **RQ1 有效性** | 固定预算下修得更好吗 | 主表 + cost-quality 图 + **token 构成图**（prompt vs completion，见实验文档图 4） |
| **RQ2 信号设计为何有效** | 反馈的哪一部分在起作用 | Table II（哪些信号）+ 反馈粒度（新）+ 一个反序条件 + Table III panel (a) |
| **RQ3 信号的诊断质量** | 信号说得准不准 | 灵敏度 + 特异性 2×2 + **定位准确性**（新）+ 阈值敏感性 + 验证开销 = 1 步 |
| **RQ4 泛化性** | 换模型/换框架/换规模还成立吗 | 跨 LLM + JAX（现 Table IV）+ 真实规模 spot-check + 真实翻译产物 |

几点说明：

- **RQ3 是新的一节，但内容大部分已经在手**。特异性、开销、阈值敏感性三项只需要对已交付的 4800 行数据做离线重分析（数字已算好，见实验文档附录）。唯一需要跑的是定位准确性——而那是唯一 baseline 结构上产不出来的证据。
- **RQ3 不要写得太长**。灵敏度和特异性都是满分（36/36 检出，1200 行零误报），三个满分适合占半页，不适合占一整节的篇幅。这一节的重心应该是定位准确性。
- **Table III panel (b) 移出消融**，放到 setup 里介绍翻译器的地方，或者正文一句话带过。
- **JAX（n=6）不要再当独立 RQ 卖**。n=6 是可行性演示，作为 RQ4 下的一小段更合适，正文里就这么定性说。
- **表编号跟着正文顺序重排**，Table V 挪到 RQ3 位置。

## MatchFixAgent 的脚注要提到正文

现在 Table I 的脚注写着「MatchFixAgent receives the healthy implementation of the changed function; LADDER does not」。这条信息值得写进正文：**它拿到了正确实现，仍然只有 47/50，而且 gradient/update 层只修好 13/16**（比不给正确实现的直接 LLM 修复的 14/16 还低一个）。

这说明拿到正确代码不等于知道什么时候算修好了——缺的是判断梯度是否等价的验证信号。这是对方法的正面论证，藏在脚注里浪费了。

另外正文应当写明：六个方法用的是同一个 backbone（`deepseek-v4-flash`）、同一个温度（0.1）、同一个尝试预算（4 次）。已逐个核实过三个外部方法的 `metadata`。不写这一点，27 倍的 token 差距看起来像是把 baseline 配坏了。

## Table III panel (a) 两个数字需要在正文交代

**文档反而让 candidate scope 变差（12/12 → 8/12）**。合理的机制解释是上下文稀释：冗长的通用文档挤占了具体的差分证据，fixer 开始去「修」并非故障的 API 用法。**如果这个解释站得住，它对论文的论点是有利的**——定向的执行证据比通用文档更有用。

但 4 个实例撑不起一个主张（4 个不一致对，双侧 p=0.125）。两条路：

- 降级为散文观察，给出机制说明，再补那 4 个回退案例的定性分析（fixer 具体改了什么）
- 如果「fixer 里放文档」要作为一个贡献点留着，就在 50 实例池上 ×3 seeds 重做

**不要留着一个反直觉的数字不解释。** 现在正文只说 documentation「eliminates core-operator out-of-scope edits」，没提 candidate scope 掉了 4 个。

**核心 autograd/optimizer 全条件 0/4**：这是方法的边界，直接写成一句「LADDER 修不了什么」，给出机制——修复需要改候选可编辑范围之外的适配器内部自动微分/优化器代码，局部 diff 推不出框架级语义。但 n=4 不足以说「从不」，措辞收成「在我们的实例集中无一成功」。
