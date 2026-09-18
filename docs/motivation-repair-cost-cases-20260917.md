# Motivation 案例的修复结果与 token 对照

本记录读取原始 Fixed50 逐轮报告、SWE 轨迹、MatchFix 分组件用量和 Experiment A 配对复核，没有运行新实验或修改论文。所有 token 均为完整修复尝试的记录用量，不是首次检测到故障所需的 token。

## 错误冻结参数：GR-04-B

| 方法 | 修复尝试 | LLM 调用数 | 输入 token | 输出 token | 总 token | 原始验收 / 后续配对复核 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| LaDiM | 1 | 1 | 4,346 | 1,551 | 5,897 | 通过 / 通过 |
| SWE-agent | 1 | 10 | 25,676 | 1,263 | 26,939 | 通过 / 通过 |
| MatchFixAgent | 1 | 7 | 7,370 | 3,841 | 11,211 | 通过 / 通过 |
| Direct LLM | 1 | 1 | 1,741 | 2,259 | 4,000 | 通过 / 通过 |

SWE 的总量为 LaDiM 的 4.568 倍，MatchFix 为 1.901 倍；Direct LLM 用量更低。因此这个实例支持现有接入下相对两个 agent baseline 的修复成本优势，不能说明这些 baseline 没有发现或修复问题。

SWE 输入已经包含 `fc2` 不可训练、梯度为空、更新为零的测试输出。轨迹第 5 个条目明确指出 `build_model()` 错误冻结 `fc2`，随后删除冻结代码；后续条目还查找 Python 环境并两次提交。记录的 26,939 token 覆盖这些完整交互。

MatchFix 的 data-flow 分析已经指出目标多出的 `requires_grad_(False)` 改变了训练行为；该分析调用记录 1,184 token。完整流程还执行其他语义分析、测试/修复生成和 verdict，分别合计 5,103、3,814、2,294 token。历史接入的测试执行文本来自聊天输出；此处修复成功依据宿主应用补丁后的实际验证及后续配对复核。

LaDiM 的相应 `candidate_training.py::report_for_candidate` 在 `low_hint=false` 时直接提供“目标可训练层被错误冻结”和恢复 `requires_grad=True` 的根因提示。该实例中 `low_hint=false`。其成本差包含给定根因指导以及宿主应用补丁、执行验证的流程，不能单独解释为自主诊断更高效。

本例为受控注入：修复前后当前步 loss 同为 1.211819052696228；输出层权重梯度由 None 恢复为 0.6227812170982361，更新范数由 0 恢复为 0.12455625087022781。冻结参数不会切断穿过该层、通向前层的全部反向传播；图应标记参数梯度分支。

## 更明显的完整修复结果差异

| 实例 | LaDiM | SWE-agent | MatchFixAgent | Direct LLM |
| --- | --- | --- | --- | --- |
| NU-03-B：布尔 attention mask | 成功，27,814 token | 四轮失败，1,072,210 token | 成功，112,638 token | 四轮失败，179,299 token |
| NU-07-B：GQA head 排列 | 成功，41,772 token | 四轮失败，693,742 token | 成功，85,381 token | 四轮失败，188,710 token |

以上采用原始故障验收口径，LaDiM 用量来自逐轮原始调用，已补齐旧汇总的零值漏计。布尔 mask 的 LaDiM 修复用量为 MatchFix 的约四分之一；GQA 为约二分之一。二者都已经出现前向输出错误，适用于“执行成功但语义错误”的图，不支持“前向已通过而反向失败”的图。

这两个核心算子案例同样使用脚本预先构造的具体根因，详见 `method-evidence-review-20260917.md`。成功补丁和记录成本可以展示，自主根因发现能力未由这些案例隔离验证。

## 来源

- 原始报告：`ascend-torch4ms/experiments/baselines/full_hier_fixed50/{r_hier,r_swe,r_matchfix,r_direct}/raw/` 下对应实例 JSON。
- 原始成本复算：`tmp/baseline_audit_20260916/audit.json`，`methods.*.per_instance`；GR-04-B 又独立核对了逐轮 API usage / SWE model_stats。
- SWE 调用数：对应报告 `attempts[0].generation.metadata.trajectory.info.model_stats.api_calls`；非 episode 中的 checkpoint 数。
- MatchFix 组件：对应报告 `attempts[0].generation.metadata.matchfix_result.results`。
- LaDiM 冻结案例提示：`ascend-torch4ms/autofix/faults/candidate_training.py:369`。
- 修复后配对复核：`data/experiments/01_experiment_A_paired_threshold_revalidation/formal_final/paired_summary.csv` 中四种方法的 GR-04-B，均通过。
- LaDiM / MatchFix 使用保存的 API usage；SWE 使用框架 `tokens_sent/tokens_received` 计数。本文对照记录 token，不将其直接转换为美元成本。
