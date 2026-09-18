# 训练信号消融独立最终审查

2026-09-18 04:07 UTC 完成只读审查。远端目录为 `/media/main/whj/projects/torch4ms/maintext-ablations-20260918/training_signal16_v2`，64 条条件已完成并写出 `dispatch_result.json`。本次未调用模型 API、重跑候选或修改冻结代码，只读取原始请求、响应、补丁、验收与预算记录并独立计算。未发现最终接受假象、目标框架回退或调用/token 账本不一致。

## 最终结果与统计口径

| 可见反馈 | 三 seed 全检查接受 | 控制器可见检查通过 | 未触发修复 | API 调用 | Prompt tokens | Completion tokens | 未知 usage 调用 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| execution | 4/16 | 16/16 | 12 | 145 | 2,004,180 | 84,735 | 0 |
| execution_forward | 8/16 | 16/16 | 8 | 168 | 2,496,189 | 107,022 | 0 |
| execution_forward_gradient | 12/16 | 16/16 | 4 | 184 | 3,179,699 | 123,174 | 0 |
| all_observations | 16/16 | 16/16 | 0 | 193 | 3,291,755 | 127,205 | 0 |

64 条初始程序在完整检查下都失败。四组各自修复了其可见信号覆盖的 4、8、12、16 个故障，其余 24 个条件在可见检查通过后未进入修复。以上 4/8/12/16 是四个真实模型、四种受控程序修改的新实验；不可与旧三 fixture、每 fixture 四次重复的 signal12 结果混用。

反馈设置同时决定是否触发修复、向代理提供哪些默认测试观测、何时停止。因而该实验测量的是可见验证信号对完整检测—修复流程的作用，不能把接受率差解释成“在相同已触发修复任务上，提示信息增加带来的修复能力提升”。`controller_accepted` 全部为 true，实际完整成功只有 40 条；报告必须使用最终全检查的 `accepted`。

`execution` 也保留 schema、实际 backend、source immutability、training-reported 等基础契约检查（runner 第 103 行附近），并非只看进程退出码。四组都允许自建 scratch tests，所以设置限制的是默认公开测试反馈，不是代理可以主动测量的全部信息。

## 处理隔离与预检

四个模型为 PaperCnn、TinyImageMLP、TinyTransformerClassifier、TinyCausalLM，从原模型定义提取实际类；没有用一个 toy fixture 改名冒充四个模型。输入形状和任务分别固定在 runner 的 `MODELS`，每次训练一步，batch size 4。源模型与候选同步初始化，SGD 学习率 0.01。公开 source.py 提供正确计算，是合法任务输入；该研究为受控修改，并非自然 LLM 翻译故障。

四种修改分别是 SGD 无效关键字 `learning_rate`、可微 loss 中加 0.25、反向后梯度乘 1.5、SGD 学习率乘 1.5。四个健康模型各三 seed 的 12 次预检均通过；16 个故障各三 seed 的 48 个预检签名全部满足声明的阶梯：执行故障四组均失败，前向故障仅 execution 通过，梯度故障前两组通过，更新故障前三组通过。此次梯度和更新故障执行正常，修复了旧 GR-07 在初始执行阶段即异常的问题。

四个 variant 的 runner、manifest 与各 765 个冻结文件均逐项哈希一致。各任务在四个 variant 中的初始 candidate 字节一致。复制的 torch4ms 库含 43 个文件，与声明的诊断提交 `81181da81efa6c6c7dbbd9b0eae0f370ca7a4b2b` 及 control 使用的库均相同，`library_provenance_audit.json` 未记录不同文件。四组使用相同 source、模型、故障、预算与代理实现；处理差异集中在 `mask()`。

## 控制器与最终验收

runner 的 `Masked.paired()`（第 229–235 行）将完整结果保留在宿主 `full_evaluation` 中，以重新构造的可见 `acceptance.accepted` 控制流程。基础 evaluator 的 `tool()` 动态调用该覆写方法，公开测试同样经过 masking；`confirm()` 的另外两个 seed 也经过同一可见检查。控制器接收 observation，而非 full_evaluation。

runner 第 245–253 行在流程完成后，额外对最终工作区用 4101、5101、6101 三个 seed 执行全部信号检查，并重新写入最终 accepted。独立核对全部 64 条的 seed 序列、三个结果的逻辑合取和最终 accepted，均一致。最终输出没有把 hidden full failure 提前用于可见控制器，也没有把 masked stop 当作修复成功。

存在一个实时读取边界：基础 `run_condition()` 会先写 `status=completed`，随后 wrapper 才执行三 seed 全检查并补上 `full_final_confirmation`。审查中短暂看到一条 completed 但尚未有该字段的中间结果。最终化与统计应等待 worker/dispatch 结束并要求三 seed 字段完整。当前 64 条最终结果已越过该边界。

## 接受补丁与实际后端

逐一审查 40 条接受条件的最终候选 diff，并检查所有生产 Python 文件及 source/task 哈希：接受补丁只修改 candidate.py；没有新增或改变库/验收代码，source.py 与 task.json 在全部 64 条中保持不变。补丁恢复了真实计算：改回合法 SGD 参数名、去除 loss 偏移、去除梯度缩放、恢复正确学习率。少量补丁保留等价 criterion 包装或增加说明注释，不改变任务语义。

40 条接受结果的 120 次最终 seed 检查均有原始 `paired_report.json`。逐一检查其 `results.torch4ms.backend_execution`：`required=true`、backend 为 `torch4ms/MindSpore`，对应训练步 `observed=true`，事件含正数 MindSpore gradient tensors。共确认 120 个最终目标反向步骤；与公开 backend_attested 标记一致。候选仍调用 torch4ms 环境、真实目标反向桥与优化器，未出现完整 PyTorch 回退或伪造验收输出。

这些结果证明三个固定 seed 的单步训练契约，不提供多步训练稳定性或未测输入的泛化数据。seed 同时用于健康/故障预检和最终评估，不是额外留出的测试集。

## 请求隔离与调用账本

逐一读取 690 个实际 request 与 response。所有请求模型均为 `deepseek-v4-flash`，所有响应记录模型均为 `deepseek-flash`。按实际响应重新累加 prompt/completion tokens，逐条件核对 budget.calls、两个 token 合计与 unknown_usage_calls，全数一致；690 个调用均有完整整数 usage，未知调用为 0。失败尝试及诊断请求均计入账本，表中成本未仅选择成功调用。

递归解析请求内控制器 observation、工具结果与交接 JSON，共核对 1,134 个含 provided_observations 的公开观测。execution 无数值 measurements；execution_forward 仅有 loss 和层前向；execution_forward_gradient 增加梯度范数与梯度向量；前三组均无参数更新列表。未发现隐藏检查的 acceptance/reasons 随结果残留。690 个请求均未出现 full_evaluation、private_preparation、expected_signature、private_construction 等私有字段。源码中可直接看到故障代码属于公开调试证据，source.py 中正确实现属于已声明参考，不构成私有答案泄露。

## 最终化脚本的解释边界

`finalize_training_signals.py` 要求完整三 seed、检查最终评分、模型 ID、请求计数和未知 usage；这与本次独立计算一致。本次还额外读取了接受候选的实际 diff 与原始后端事件，并比较 source/task 及生产库文件，超出了只检查公开 backend 布尔值的范围。

`wall_time_sec` 来自基础 `experiment.run_condition()`，在 wrapper 的额外最终三 seed 验证前已停止计时；因此若后续报告时间成本，应明确其为代理控制流程耗时，不包括这次额外最终评分。API token/call 账本不受该时间边界影响。

本轮支持使用 4/16、8/16、12/16、16/16 作为新受控训练信号流程实验的完整验收结果，配合可见检查触发/停止机制解释。没有发现需要撤销当前最终结果的实施或评分缺陷。
