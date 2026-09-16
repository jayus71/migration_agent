# 修复案例、前向一致但训练错误的证据与图 1 解读

本记录补充 `baseline-first-attempt-audit-20260916.md`。仅检查已有代码和归档结果，没有执行候选修复或重跑实验。

## 两个 baseline 都未获接受、LaDiM 获接受的实例

原始 Fixed50 中，SWE-agent 最终未接受的集合是 NU-03-B、NU-07-A、NU-07-B、GR-05-B；MatchFixAgent 是 GR-05-A、GR-05-B、GR-07-A。交集只有 GR-05-B。

GR-05-B 使用 Transformer 变体，冻结前层参数。梯度提取端与写回端应使用相同的可训练参数列表；如果提取端跳过冻结参数，写回端却按全部参数的位置索引，梯度就会对应到错误参数。原始故障探针的 `first_trainable_grad_present=false`。

| 方法 | 已有轨迹的具体行为 | 结果 |
| --- | --- | --- |
| MatchFixAgent | 替换 `get_trainable_params()`，参数名称恢复正确；梯度写回未修复 | 四轮内失败，`first_trainable_grad_present=false` |
| LaDiM | 首轮仅修改 extractor，仍失败；第二轮同时修改 extractor 和 `_sync_grad_to_param_grad()`，让两端都过滤冻结参数 | 第二轮通过，`first_trainable_grad_present=true` |
| SWE-agent | 首轮同时修改 `forward_extractor.py` 和 `autograd/__init__.py` | 功能探针通过，但第二个文件被单文件允许范围拒绝 |

因此，这个实例可以说明跨文件参数映射的修复机制，以及现有接入权限不一致。它不能用来声称两个 baseline 都缺乏修复能力。在当前 50 个实例里，没有找到同时排除该接入因素、又满足“两者都修不好而 LaDiM 修好”的案例。该组实验的成功口径是注入故障的修复验收。

原始证据目录：`ascend-torch4ms/experiments/baselines/full_hier_fixed50/{r_hier,r_swe,r_matchfix}/raw/`，分别读取 `GR-05-B*.json`。

## MatchFixAgent 的首轮补丁是否有效

11 个缺标签而被拒绝的首轮 `test_repair.result` 都能通过标准 JSON 解析，并包含修复代码。进一步用 Python AST 比较首轮未应用代码与该实例后续已获接受的函数实现，以下 7 个实例的语法树完全相同：EX-02-B、EX-07-A、EX-10-A、EX-10-B、GR-02-A、GR-03-A、NU-04-B。

这是比“含有修复字段”更直接的证据：这 7 个实例在首轮已经生成与后来成功版本相同的函数实现，却在标签解析环节被丢弃。AST 比较不包含执行，也没有据此改写 Repair@1。

其余 4 个实例与后续通过版本不同或没有通过版本。最终仍失败的 GR-05-A/B 存在修复范围不足，GR-07-A 存在不同类的同名构造函数错配，因此整个 MatchFixAgent 失败集合不能统一归为标签问题。

## LaDiM 为什么较少遇到输出协议问题

LaDiM 的 fixer 调用显式使用 `response_format={"type": "json_object"}`，由 API 请求 JSON 对象。返回后 `_extract_json()` 兼容 Markdown JSON 代码块，也能提取从第一个 `{` 到最后一个 `}` 的内容，再交给 `json.loads()`。它没有 MatchFixAgent 的特定 XML 外层标签依赖。

LaDiM 返回结构化编辑，由宿主程序应用补丁并调用 verifier；SWE-agent 每次交互还需要正确产生可解析的 shell 操作。LaDiM 的报告提供阶段、目标文件和相关诊断，减少仓库浏览回合。以上机制减少了协议和搜索开销；它仍会给出不完整补丁，GR-05-B 的首轮就是已记录的例子。

代码：`ascend-torch4ms/autofix/agents/fixer.py:291`、`:2555`；MatchFixAgent 请求包装：`ascend-torch4ms/autofix/external_tools/run_matchfix_agent.py:20`。

同时读取了原始 Fixed50 provenance 指定的提交 `3454be4e1e58f4889e362bd33289d49f98ebbcf6`：该版本 fixer 第 298 行已设置 JSON response format，第 2541 行已包含上述容错提取逻辑，确认这两项机制在原实验版本中存在。

## 摘要所述现象：有真实 LLM 翻译实例

Experiment I 的冻结任务清单明确 `no_fault_injection=true`。I-08 和 I-09 的 `translation/translator_patch_v0.json` 保存了 `deepseek-v4-flash`、温度 0.1、API token usage 与翻译文件哈希。对首次修复前的候选进行同步初始化的一步训练比较，结果如下：

| 自然翻译实例 | 执行 | loss 绝对差 | 梯度范数绝对差 | 参数更新相对 L2 差 |
| --- | --- | ---: | ---: | ---: |
| I-08，autoencoder head | 两侧均成功 | 1.4305e-6 | 0.04596 | 0.77113 |
| I-09，带 value/gate/norm/head 的模型 | 两侧均成功 | 4.7684e-7 | 0.41863 | 0.92527 |
| 检测阈值 | — | 0.02 | 0.05 | 0.03 |

I-09 的 PyTorch loss 为 1.5050275326，候选为 1.5050270557。参考模型的 value、gate、norm 参数都有更新，候选的这六个参数张量更新范数全部为 0；head.weight 和 head.bias 的更新则与参考完全相同。I-08 的第一层 encoder 权重参考更新范数约 0.012248，候选仅约 0.000018869，其他几层的更新正常。

这支持“LLM 生成的迁移程序可正常执行、已测前向值接近，而训练更新错误”的现象。层输出记录是标量均值，不是完整张量逐元素等价证明。自然故障的最终根因尚未在人工归因记录中确认，可能涉及生成代码与适配层的交互；不能把它直接归因为 LLM 写错某一行。LaDiM 在 I-08/I-09 都以 STOP_NO_PROGRESS 结束，这两例提供现象与检测证据，不提供 LaDiM 修复成功证据；Direct 在 I-09 最终获接受。

来源：

- `data/experiments/09_experiment_I_real_translation/runs_real_core_v3/pool_audit.json`。
- `experiment-results-local-20260906/09_experiment_I_real_translation/runs_real_core_v3/tasks/I-08/r_hier/reports/I-08__r_hier_iter1_paired_report.json`。
- `experiment-results-local-20260906/09_experiment_I_real_translation/runs_real_core_v3/tasks/I-09/r_hier/reports/I-09__r_hier_iter1_paired_report.json`。
- 同一任务下的 `translation/translator_patch_v0.json`、`r_hier/manual_attribution.json` 与 `condition_result.json`。

## 图 1 的具体含义

图 1 来自 Experiment C 的受控故障注入。每个面板有四个模型 × 三个随机种子，共 12 条 50 步训练轨迹。图中选择 free-running：初始状态对齐后，两边保留各自上一步训练产生的状态，允许错误累积；不是每一步都重新同步参数的那组条件。

- 面板 (a)：在候选 backward 后，把梯度乘以 1.5。当前步前向计算未变，但梯度和随后的参数更新改变。
- 面板 (b)：记录正确梯度后，屏蔽部分参数更新。当前步前向值与所测梯度仍正常，但 optimizer 更新结果改变。

横轴是训练步数，不是修复轮次。纵轴是“差值除以对应检测阈值”，并使用对数坐标。loss、梯度、更新阈值分别为 0.02、0.05、0.03，因此所有信号都以纵轴 1 为越界线。蓝线上升表示源与目标的 loss 差扩大，不表示训练 loss 本身上升。实线表示 12 条轨迹的均值，阴影表示最小值到最大值，不是置信区间。

| 统计 | (a) 梯度错误 | (b) 更新错误 |
| --- | ---: | ---: |
| 第一步平均 loss 差 | 8.2453e-7 | 8.2453e-7 |
| 直接诊断信号 | 梯度差均值 0.25849，阈值 0.05 | 更新相对差均值 0.73112，阈值 0.03 |
| 直接诊断首次越界 | 12/12 都在第 1 步 | 12/12 都在第 1 步 |
| 平均 loss 差首次越界 | 第 31 步，0.02005 | 第 18 步，0.02103 |
| 单条轨迹 50 步内 loss 越界 | 3/12，首次在第 10–11 步 | 4/12，首次在第 6–20 步 |

图的主要证据是：直接检查梯度或参数更新可在第一步发现错误，仅检查 loss 会延迟发现，且部分轨迹在 50 步内一直不触发 loss 阈值。31 和 18 是平均曲线交点，不能解释为每次运行的检测时间。图 1 没有测量修复成功率或比较三个修复系统，也不是 LLM 自然翻译失败案例的统计；自然发生的对应现象由上面的 Experiment I 记录补充。

来源：`figures/make_gradient_drift.py`、`figures/paper_data.py`、`data/experiments/03_experiment_C_gradient_and_parameter_faults/README.md`、该实验 `results_per_step/section65_per_step_divergence_steps50.csv`。
