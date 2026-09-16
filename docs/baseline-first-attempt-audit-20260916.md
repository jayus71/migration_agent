# Fixed50 首轮失败与 token 用量分析

本次核对原始 Fixed50 的 LaDiM、SWE-agent、MatchFixAgent 共 150 个实例记录、逐轮补丁、工具轨迹和调用用量。结论是：首轮差距包含大量输出协议、调用预算和修复范围因素；LaDiM 的低 token 用量同时包含实际调用较少与汇总漏计两部分。原始实验表、论文和实验程序均未修改，没有调用模型或重跑修复实验。

源目录为 `ascend-torch4ms/experiments/baselines/full_hier_fixed50/`。其中 `summary.csv` 与论文快照 `data/paper_figures/fixed50_original_summary.csv` 字节一致。本次按原表接受规则分析，保留 50/50、84% 等接受结果；“通过功能检查”和“最终获接受”分别记录。

| 方法 | 首轮获接受 | 四轮内获接受 | 首轮未接受 |
| --- | ---: | ---: | ---: |
| LaDiM | 42/50，84% | 50/50 | 8 |
| SWE-agent | 36/50，72% | 46/50 | 14 |
| MatchFixAgent | 37/50，74% | 47/50 | 13 |

SWE-agent 和 MatchFixAgent 的首轮成功率分别低 12、10 个百分点。配对到同一个实例，LaDiM 对 SWE-agent 是 8 个独有首轮成功、2 个独有首轮失败，净多 6 个；对 MatchFixAgent 是 12 个独有首轮成功、7 个独有首轮失败，净多 5 个。两个 baseline 共同首轮未接受的具体实例只有 GR-05-B。

| 故障阶段 | LaDiM 首轮获接受 | SWE-agent 首轮获接受 | MatchFixAgent 首轮获接受 |
| --- | ---: | ---: | ---: |
| 执行 | 18/20 | 15/20 | 14/20 |
| 前向数值 | 9/14 | 6/14 | 12/14 |
| 梯度与参数更新 | 15/16 | 15/16 | 11/16 |

这些分布说明首轮优势随故障类别变化。MatchFixAgent 的前向数值首轮结果高于 LaDiM；SWE-agent 的梯度与参数更新首轮结果与 LaDiM 相同。只看总体差距会掩盖这些差异。

## MatchFixAgent：11/13 首轮失败来自标签解析

以下 11 个实例首轮的 `test_repair.parsed_final_response` 都报告格式错误，`generation.edits` 为空：EX-02-B、EX-06-A、EX-06-B、EX-07-A、EX-10-A、EX-10-B、GR-02-A、GR-03-A、GR-07-A、NU-02-A、NU-04-B。

逐一对 `test_repair.result` 使用标准 JSON 解析器后，11 个输出全部可解析，全部包含非空 `correct_target_method_implementation`。它们共同缺少 `<final_response_format>...</final_response_format>` 外层标签，因此 MatchFixAgent 的解析结果没有交出修复代码，包装器也没有应用补丁。例如 EX-02-B 已生成将矩阵乘法输入转为 float32、再把结果转回输入 dtype 的代码；GR-03-A 已生成补回 `optimizer.step()` 的代码。

其中 10 个实例在后续轮次获接受，GR-07-A 最终失败。这里确认的是首轮输出被协议拒绝；没有重新执行这些未应用的候选，因此不把它们改记为首轮成功。

剩余两个首轮失败是 GR-05-A/B。补丁成功应用到 `get_trainable_params()`，验证中的可训练参数名称已恢复正确，但 `first_trainable_grad_present` 仍为 false。故障涉及参数筛选和梯度写回的对应关系；包装器只替换选中的一个函数，梯度写回一侧仍未修复。两例四轮内均未获接受。

GR-07-A 还有一个独立的输入构造问题。`tool_runs/GR-07-A*/checkpoint_1/input.json` 中的参考函数是 `OptimizerState.__init__(params, step=0)`，目标却是 `Optimizer.__init__(params, gradient_transform)`。`_changed_function_pair()` 仅按函数名和缩进匹配健康实现，忽略所属类，把同名构造函数错配。第二至四轮仍受该错配影响，出现补入 `step/extra_state`、丢失 `trainable_params` 等与目标修复偏离的修改。这是本次接入程序的具体问题。

## SWE-agent：10/14 首轮未接受时没有补丁

| 首轮直接原因 | 实例数 | 实例 |
| --- | ---: | --- |
| 格式错误退出，无补丁 | 4 | EX-03-B、EX-08-A、EX-09-B、NU-07-A |
| 调用次数用尽，无补丁 | 6 | EX-08-B、NU-02-B、NU-03-A、NU-03-B、NU-05-A、NU-06-B |
| 有补丁，功能检查失败 | 3 | EX-07-B、NU-05-B、NU-07-B |
| 功能检查通过，修改范围被拒绝 | 1 | GR-05-B |

格式错误退出的轨迹为 `exit_format`。EX-03-B 和 NU-07-A 连续输出 `<bash>...</bash>`，而配置要求 Markdown 命令块，工具没有执行这些操作。NU-07-A 的第一段推理已经指出 grouped-query attention 需要复制 key/value heads，随后仍在命令格式环节结束。EX-03-B 首轮只有 2,803 个记录 token，是三次无效格式回复后提前退出。

另外六例为 `exit_cost`。配置的 `per_instance_call_limit` 是 12，相关轨迹记录 13 次 API 调用；美元预算均为 0，此处退出对应调用次数限制。轨迹显示大量读取、搜索和诊断仍未产出编辑。NU-05-A 首轮读取大文件后转向卷积实现，最终未编辑 attention 缩放代码；该轮已有 355,969 个记录 token。NU-03-B 首轮读取整个算子文件后持续搜索与故障相关的实现，消耗 306,931 个记录 token，补丁仍为空。

三例实际补丁失败分别是：

- EX-07-B 修正 OneHot 的 bfloat16 不兼容后，又将结果转回 bfloat16，后续 CPU MatMul 仍不支持该类型。
- NU-05-B 用 `math.rsqrt` 恢复 attention 缩放，但 Python 的 `math` 模块没有该函数，引入 AttributeError。
- NU-07-B 把 key/value 复制移到矩阵乘法之前，恢复了形状兼容，却使用 `tile` 产生错误的 head 排列，最大数值差仍约为 1.029。

GR-05-B 的首轮修改同时修正 `forward_extractor.py` 的参数筛选和 `autograd/__init__.py` 的梯度写回，功能探针全部通过。包装器只允许修改 `candidate_rel` 指定的一个文件，第二个文件使 `out_of_scope_edit_count=1`，因此最终 `strict_success=false`。原始 episode 的 `repair_at_1=true` 表示功能通过轮次；统一 `instances.csv` 在严格接受条件下把这一项计为 false，形成论文的 36/50。该实例应归为修改范围拒绝，不能当作 SWE-agent 未修复梯度问题的例证。LaDiM 在该故障上允许面向两个文件的修复。

## 共同模式及对差距的解释

两个 baseline 的共同模式是修复流程容易在输出到可执行补丁的衔接处丢失有效信息：MatchFixAgent 缺少标签，SWE-agent 命令格式不匹配、搜索耗尽调用次数，或者修改范围阻止完整修复。这些因素直接影响首轮接受率。

训练语义方面也有具体困难，包括 bfloat16 的连续算子兼容、attention 的缩放与 head 排列，以及参数列表和梯度写回的跨文件一致性。LaDiM 的阶段信息、目标文件和针对性指导能减少这类搜索；但当前全部 10–12 个百分点不能直接归因于分层诊断。输出解析和修复权限的接入差异必须同时纳入解释。

## LaDiM token 汇总漏掉 14 个实例

`summarize_track_b_fixed50.py::_internal_token_usage()` 只读取 `candidates/<instance>/attempt_*.json`，并只从 `generation.metadata.llm_call.usage` 取 token。一部分核心故障使用 `attempts.json`，原始逐轮记录中的调用则在 `raw.attempts[*].llm_call`；EX-06-A/B 使用 `raw.generation.metadata.llm_call`。这些布局没有进入原汇总。

因此 14 个实际调用 LLM 的实例在原 `instances.csv` 中被记为 0 token。它们是 EX-06-A/B、EX-07-A/B、EX-08-A/B、NU-03-A/B、NU-05-A/B、NU-07-A/B、GR-05-A/B，共漏计 398,651 token。例如 GR-05-B 的两次调用分别为 17,878 和 22,522，合计 40,400，而汇总为 0。

此次复算每个实例优先读取逐轮 `attempts`，仅在没有逐轮记录时读取 `generation`，避免将顶层保存的最后一次生成重复相加。其余 36 个实例的复算值与原汇总逐个一致。

| LaDiM 用量 | 原汇总 | 原始调用记录复算 |
| --- | ---: | ---: |
| 输入 token | 147,251 | 486,359 |
| 输出 token | 43,337 | 102,880 |
| 总 token | 190,588 | 589,239 |
| 每个获接受修复的 token | 3,811.8 | 11,784.8 |

原表约 29 倍的数值来自 `(5,205,141 / 47) / (190,588 / 50) ≈ 29.1`。补齐本次找到的原始用量后，同一接受分母下为 `(5,205,141 / 47) / (589,239 / 50) ≈ 9.40`；相对 SWE-agent 的记录用量约为 14.08 倍。这里只另记审计结果，不覆盖原始表中的任何数字。

## 补齐漏计后，LaDiM 为什么仍较省

LaDiM 在这 50 个实例上保存了 59 次 LLM 调用；SWE-agent 的轨迹共记录 877 次 API 调用，MatchFixAgent 共记录 491 次。一个“修复尝试”在三个系统中包含的内部调用数不同，四次补丁预算并非相同的 LLM 调用预算。

SWE-agent 的原始记录总量为 7,635,016，其中 98.4% 是输入 token。轨迹反复传入仓库文件、测试输出和交互历史，而配置中的 `history_processors` 为空。长上下文在多次交互中重复计入成本，解释了为什么输出 token 较少而总量很大。

MatchFixAgent 的 5,205,141 token 中，数据流分析占 3,854,995，即约 74.1%；直接测试与修复阶段占 443,266，即约 8.5%。EX-06-A/B 两例共用 3,682,148 token，占总量约 70.7%。EX-06-A 首轮数据流分析单次输入就有 659,574 token，而该轮测试与修复输入为 12,267。可确认成本主要集中于数据流分析；本次没有展开外部工具的数据流 prompt 构造，未进一步归因到某种图序列化算法。

只看首次尝试，LaDiM 复算为 409,754 token，SWE-agent 记录为 4,372,873，MatchFixAgent 为 2,694,765；平均每个实例约 8.2K、87.5K、53.9K。因此较少的后续重试只解释成本差异的一部分，单轮内部工作流的调用与上下文规模也有明显影响。

SWE-agent 用量来自其 `model_stats.tokens_sent/tokens_received`，MatchFixAgent 和 LaDiM 来自保存的 API usage；这里保留这些原始计数来源，未把 token 比值解释为美元成本。完整修复次数和调用数均是已有轨迹统计。

## 后续处理顺序

先修正内部方法 token 汇总对记录布局的兼容；再修正 MatchFixAgent 合法 JSON 的标签兼容与按所属类匹配函数；统一 GR-05 所需的修改文件范围；最后核对 SWE-agent 命令协议和单轮调用预算。完成这些实现问题后，才适合通过用户授权的同组实验复测，量化分层诊断对剩余首轮差距的贡献。

## 复核入口

- 分析脚本：`tmp/baseline_audit_20260916/analyze.py`。
- 逐实例分类、调用用量、漏计实例和源文件 SHA-256：`tmp/baseline_audit_20260916/audit.json`。
- 运行方式：`python3 tmp/baseline_audit_20260916/analyze.py`，只读取本地归档，写出审计 JSON。
- 汇总漏计：`ascend-torch4ms/experiments/paper_section_65_66/summarize_track_b_fixed50.py:164`。
- SWE-agent 调用上限：`ascend-torch4ms/autofix/examples/run_external_repair_pilot.py:614`；范围判定：同文件第 728、783 行。
- MatchFixAgent 函数配对：同文件第 847 行；修复提取与应用：第 995 行。
- GR-05-B 的 LaDiM 原始调用：`ascend-torch4ms/experiments/baselines/full_hier_fixed50/r_hier/raw/GR-05-B.json:327`。

脚本已运行完成：核对三个方法各 50 份原始记录；两个外部 baseline 的复算 token 与原汇总完全一致；MatchFixAgent 分组件用量之和与总用量一致；11 份无标签修复输出均通过标准 JSON 语法检查。未执行候选代码、修复实验或论文排版检查。
