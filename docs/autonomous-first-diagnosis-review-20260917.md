# 首次自主诊断证据复核

本记录属于评估方私有材料，不得放入 agent 工作区或提示。依据[冻结评分协议](autonomous-diagnosis-assessment-20260917.md)，本轮复核正式 `formal_v1` 中五个初始失败任务的二十份首次诊断。材料读取截止 2026-09-17 07:51:13 UTC。所有首次诊断均已结束，生产编辑列表为空；复核只使用 `initial_diagnosis` 和该阶段之前的工具证据。

本轮审阅已看到条件名和结果状态，没有实行协议所要求的方法匿名第一遍，因此以下作为有证据的初步评审，不作为完成盲评的定位准确率。原始首次输出与哈希已保存，可交给另一位审阅者按同一规则匿名复评。

## 首批逐例判断

两例的当前 controller observation 分别直接报告 `lstm`、`gru` 的 `OperatorNotFound`，reference 成功、target 失败，损失、梯度与更新比较均 unavailable。私有参照审定到 recurrent 调用与目标实现/注册边界；完整修复位置和精确 overload 保持 provisional。下表的符号定位评分只覆盖这个已审定边界。

| 任务 | 条件 | 异常识别 | 阶段归类 | 文件 top-1 | 符号边界 top-1 | 文件/边界 top-3 | 机制证据 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| I-02 | Autonomous layered | correct | correct | correct | correct | correct | supported_mechanism |
| I-02 | SWE-style shared tools | correct | correct | correct | correct | correct | supported_mechanism |
| I-02 | Direct shared tools | correct | correct | correct | correct | correct | supported_mechanism |
| I-02 | MatchFix shared tools | correct | correct | partial | partial | partial | observed_failure |
| I-03 | Autonomous layered | correct | correct | correct | correct | correct | supported_mechanism |
| I-03 | SWE-style shared tools | correct | correct | correct | partial | correct | supported_mechanism |
| I-03 | Direct shared tools | correct | correct | correct | correct | correct | supported_mechanism |
| I-03 | MatchFix shared tools | correct | correct | partial | partial | partial | observed_failure |

此表没有把精确 overload、应增加的实现函数或完整修复方案作为已知真值。没有模型在这八份首次诊断中完成隔离机制的反事实实验，故均不记 `counterfactually_validated`。模型所说工具“不可用”实际出现在阶段预算耗尽后的收束提示，阶段内 `run_test` 可用；六个通用工具条件的首次诊断均没有实际调用它。

I-02 Autonomous 的首位是 `torch4ms/tensor.py:923–924` 的 `XLAFunctionMode.__torch_function__` 回退抛错与 `1369–1370` 的查找失败，明确关联原始 LSTM 异常。`event_00010/00011_tool.json` 的 lstm/LSTM 搜索和 `event_00019/00020_tool.json` 的两个源码窗口支持该边界。首次诊断冻结在 `event_00025_stage_end.json`，时间 07:37:38.808198 UTC。其第三个位置把 `torch4ms/ops/op_map.py` 与其他文件并列；真实文件是 `torch4ms/aten/op_map.py`，这一引用错误使证据有效性记为 partial，首位的实际证据仍成立。

I-02 SWE-style 的首位是 `candidate.py::BiLSTMClassifier.forward` 的 `self.encoder(x)`，并连接 `train_one_step` 如何进入 torch4ms；其第二位是实际异常发生的 `tensor.py` 派发边界。`event_00005/00007_tool.json` 的 source/candidate、`event_00010_tool.json` 的 lstm 搜索、`event_00017_tool.json` 的派发源码支持判断；首阶段结束于 `event_00024_stage_end.json`，07:37:55.220820 UTC。它额外将 loss wrapper 对 Linear 的特例与 LSTM 实现缺口连接起来，现有证据只足以支持缺少 LSTM lowering；该额外推断不升级为已验证根因。

I-02 Direct 的首位是 `candidate.py:13,17` 的 `nn.LSTM` 构造与调用；其不确定性明确允许在 candidate 保持数学语义地展开 recurrence，或在库中补齐 lowering。`event_00007/00008_tool.json`、`event_00010/00011_tool.json` 和 `event_00013_tool.json` 分别提供源/候选、异常/注册搜索与派发源码。首次阶段结束于 `event_00024_stage_end.json`，07:38:00.165573 UTC。文件与已知边界成立，精确算子 overload 未直接运行确认。

I-03 Autonomous 首位是 `candidate.py:12,17` 的 `nn.GRU` 构造与调用，并在第二位引用 `tensor.py` 的实际回退抛错。`event_00007/00008_tool.json` 公开程序、`event_00010_tool.json` 的 gru 搜索、`event_00014_tool.json` 的源码窗口支持判断。冻结事件为 `event_00025_stage_end.json`，07:38:54.387403 UTC。没有首轮 scratch test，所以保持代码与运行观测共同支持的机制等级。

I-03 SWE-style 首位文件和行号指向 `tensor.py:920–925`，但将该处称为 `__torch_dispatch__`，实际为 `XLAFunctionMode.__torch_function__` 的回退。它又将“fallback 失败”写成“fallback 不被允许”，而首次诊断只执行了字符串搜索，未读取这段控制流。文件 top-1 正确，符号边界和证据有效性记为 partial；第三位 `candidate.py:12,17` 的 GRU 调用由 `event_00009_tool.json` 直接支持，故 top-3 边界正确。冻结事件为 `event_00024_stage_end.json`，07:39:45.361291 UTC。

I-03 Direct 首位是 `tensor.py:899–925::__torch_function__`，说明先查找 lowering、再尝试 native fallback、两者均无法完成后抛出异常。`event_00013/00014_tool.json` 读取了实际控制流与查找函数，`event_00007_tool.json` 和 `event_00010_tool.json` 给出 candidate 及 gru 搜索。冻结于 `event_00026_stage_end.json`，07:40:55.539737 UTC。机制与边界有证据，精确 overload 和最终修复位置仍未审定。

MatchFix 两例保存的 structured diagnosis 顶层为 undetermined，但其中保留了原始 `upstream_analyses`。I-02 的 data_flow 角色明确写出“target run fails with OperatorNotFound”并归因 bidirectional nn.LSTM 缺少 lowering；I-03 的 data_flow 与 io 角色也指出 candidate 中 `self.gru(x)` 与实际 gru 异常。按语义复核，这些输出具有正确的异常和阶段判断。它们先把 native training 与 torch4ms wrapper 的差别列为 divergence，没有给出有证据、排序明确的责任模块调查，且初始化语义角色没有实际源码检索工具调用；因此文件/符号边界记 partial、机制证据记 observed_failure。I-02 四个角色、I-03 两个角色出现 tagged-JSON 格式错误，作为单独的协议失败保留，不抹去成功角色已有的诊断证据。原始材料位于 `evidence/agent/matchfix_initialize/worker_result.json`、前五个 `matchfix_role_*.json` 及 `result.json.initial_diagnosis`。

## 首次诊断指纹

下列哈希针对 `initial_diagnosis.diagnosis`，按 JSON `sort_keys=True, ensure_ascii=False, separators=(',', ':')` 序列化后计算 SHA-256。原始 task 映射只存在于评估方清单；task_002 对应 I-02，task_003 对应 I-03。

| 任务/条件 | 诊断 SHA-256 |
| --- | --- |
| task_002/autonomous_layered | `fdb144942ba443bab9a695d6730180c48278f4edb707461f4d4d14cb85a50060` |
| task_002/swe_style_shared_tools | `c38d80f6fdd5a1c1058a813785bf69bd52c2defd67ed7d3d66f0f85a650482a8` |
| task_002/direct_shared_tools | `713682326c4ada49f748c21e23462d39c404eefb3270386f39cb62415d9a8ddb` |
| task_002/matchfix_shared_tools | `821291f11852e47a340ffbf50ba79e67bb826964898ea59146f4c5e93056772b` |
| task_003/autonomous_layered | `0ddf3ebde5034ef7eb04d7d0d9df90d8e236406ce40e657cfa07eaa4e75f458a` |
| task_003/swe_style_shared_tools | `2e908038cb72a1a3200da3658ce1cfafcc061e350ae9df3064f7c16c882fa35c` |
| task_003/direct_shared_tools | `ff95373899cfca9d034d5a492dc198a8337386831579f4e22aa904984e3ae3aa` |
| task_003/matchfix_shared_tools | `eb24dae76a22d0862186b87348952cce506d8f263c1d650795dc7aa6283056a6` |

## 索引与梯度故障复核

I-07 的四个方法均识别 RecursionError，但首次诊断都没有指出 `__getitem__` 索引边界。本次四个正式条件及 preflight 的 `evidence/measurement_0001/process.json` 中，每份日志都包含 2,492 次 `__getitem__`，与旧归档的执行阻断一致；公开 paired observation 只提供异常摘要，未暴露这些原始算子日志。模型可以自建 scratch test 调查，但这一组首次诊断中，仅 Direct 再次调用了 `public`，得到同一摘要。对外应将输入信息损失和自主调查不足分别分析。

I-08 Autonomous 找到 `encoder.0 → nn.Tanh → encoder.2` 的边界，仍将具体原因猜成 tanh_backward/TanhGrad 返回零；它没有发现高层 Tanh 注册缺口及 native fallback 的 NumPy 转换。I-09 Autonomous 将非 head 参数无梯度归于通用 autograd/extractor，SWE-style 归于 mean reduction；二者均没有定位 GroupNorm 高层派发与回退边界。以下机制判断以冻结协议中的 supported 参照为依据，精确补丁仍未当作真值。

| 任务 | 条件 | 异常识别 | 阶段归类 | 文件 top-1 | 符号边界 top-1 | 文件/边界 top-3 | 机制判断 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| I-07 | Autonomous layered | correct | correct | incorrect | incorrect | incorrect | incorrect；仅确认执行失败 |
| I-07 | SWE-style shared tools | correct | correct | incorrect | incorrect | incorrect | incorrect；仅确认执行失败 |
| I-07 | Direct shared tools | correct | partial | incorrect | incorrect | incorrect | incorrect；把故障定位到 backward |
| I-07 | MatchFix shared tools | correct | correct | incorrect | incorrect | incorrect | incorrect；未验证 env 嵌套假设 |
| I-08 | Autonomous layered | correct | correct | correct | correct | correct | partial；正确切点、错误具体机制 |
| I-08 | SWE-style shared tools | not_reported | not_reported | not_reported | not_reported | not_reported | 未交付首次结论 |
| I-08 | Direct shared tools | not_reported | not_reported | not_reported | not_reported | not_reported | 未交付首次结论 |
| I-08 | MatchFix shared tools | not_reported | not_reported | not_reported | not_reported | not_reported | 五个模型角色均无语义结论 |
| I-09 | Autonomous layered | correct | correct | incorrect | incorrect | incorrect | partial；识别梯度中断、未定位责任算子 |
| I-09 | SWE-style shared tools | correct | correct | incorrect | incorrect | incorrect | incorrect；把责任算子定为 mean |
| I-09 | Direct shared tools | not_reported | not_reported | not_reported | not_reported | not_reported | 未交付首次结论 |
| I-09 | MatchFix shared tools | correct | correct | partial | partial | partial | 仅报告参数级症状与通用训练入口 |

I-07 的 candidate 文件名匹配不算根因文件命中：模型全部指向 `train_one_step`、`loss.backward` 或 autograd wrapper，没有把该文件中的 `x[:, :6]`/`x[:, 6:]` 与索引派发连接起来。Direct 的 top-3 虽包含 `tensor.py`，所指符号是 backward，仍不算索引责任边界命中。Autonomous 的 `event_00023_stage_end.json`、SWE-style 的 `event_00025_stage_end.json`、Direct 的 `event_00023_stage_end.json` 和 MatchFix 的初始化 spec 输出保存了这些首轮判断。MatchFix spec 角色把嵌套环境明确称为导致递归的机制，却没有读取 wrapper 实现或运行最小复现；它还将“单次环境进入”写进自行产生的 formal_spec。这是模型提出的未经验证假设，未成为外部验收要求。

I-08 Autonomous 的 `event_00008_tool.json` 给出 candidate 中 Tanh 的确切位置，`event_00010_tool.json` 给出 tanh 搜索；逐参数实际梯度指出上游 encoder.0 全零而下游近似一致。这个边界位置符合协议，故 top-1 与 top-3 均记 correct。其将 `decompositions.py` 的 tanh_backward 名单称为“自定义 backward 实现”，而未阅读其正文；首次阶段结束于 `event_00022_stage_end.json`，没有局部执行。机制只支持“在 Tanh 附近丢失依赖”，不支持“TanhGrad 返回零”的具体说法。

I-08 SWE-style 与 Direct、I-09 Direct 的首次阶段为 `response_truncated`。检查各自 `call_0008_response.json`，`finish_reason` 为 `length`、最终 `content` 为空，`initial_diagnosis.diagnosis` 为空对象；因此记录 not_reported，保留对应预算与 API 状态。I-08 MatchFix 的五个模型角色只输出未被执行的 DSML 风格工具请求和探索意向，不能据此补写分类或定位。

I-09 Autonomous 的 `event_00023_stage_end.json` 保存了“只有最后 Linear 正常”的判断，但只读 autograd、extractor、optimizer 等模块，没有检索或检查 GroupNorm 注册/回退。SWE-style 的同名阶段事件将梯度边界唯一归到 `x.mean(dim=(2,3))`，并明确承认没有读取所指的 mten/mappings；GroupNorm 自身的依赖中断也会导致完全相同的逐参数分布，因此“只有 mean 能解释”不成立。其 top-3 内出现 mappings 文件名，但所述责任操作与参照机制不符，不作为碰巧命中文件。MatchFix spec 角色准确复述 value/gate/norm 的零梯度与无更新，引用实际非零 reference 数值；它未给出责任算子或文件调查，故保留症状定位的 partial。

| 任务/条件 | 诊断 SHA-256 |
| --- | --- |
| task_007/autonomous_layered | `03941cab9505786aec012eeeb3e31e4a814f56fc67fda869f6a38e187e07e2f9` |
| task_007/swe_style_shared_tools | `97f5f20e06ee3851b59d1551d600192dabf5d63f320c8709efc4f658ecf1ed47` |
| task_007/direct_shared_tools | `f970f78482de02eef8d86ebd58d2c731ee26ad76f150cb07fe4f1c5e5caf76a3` |
| task_007/matchfix_shared_tools | `cc6f954bf402cc756186fe27c0ca3fa2b2266b7e3b2ca1ae8ac3e7281a7e4d7e` |
| task_008/autonomous_layered | `208bdc21dd96112707fe93eda186553d956dd865ef9fd2141107bf7a25f81b95` |
| task_008/swe_style_shared_tools | `44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a` |
| task_008/direct_shared_tools | `44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a` |
| task_008/matchfix_shared_tools | `37808a7029063af1c3f7ab5c174a0ff8ca4453d0674c9458401518dc095cb383` |
| task_009/autonomous_layered | `95be015b35d7671c925c0eb892f1f57ac9361272605af58ff3ebabb15c1b23cb` |
| task_009/swe_style_shared_tools | `3afc2cf75b46a5042e6276d510a23e48f358e5c31299039297d134cb3d2a0744` |
| task_009/direct_shared_tools | `44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a` |
| task_009/matchfix_shared_tools | `68229c89a4e364391d998987c30b19a180979a03874e9395b42d085b8f160d74` |
