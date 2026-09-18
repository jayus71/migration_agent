# 自然迁移任务的自主诊断评分协议

本文件属于评估方私有材料，包含任务映射、既有证据和待审定假设。不得复制到 agent 工作区、任务说明、检索目录、工具输出或修复提示中。它用于在首次修改前评估自主分类和定位，并在修复运行完成后复核证据。

评估对象是 Experiment I 冻结的 10 份自然翻译初态，原始基线提交为 `8c5c635b0c5c718fab052b885966be8980eea6ad`。现有归档中 I-01、I-04、I-05、I-06、I-10 初态通过，I-02、I-03、I-07 执行失败，I-08、I-09 执行和前向值接近而梯度/更新异常。新的真实后端、梯度向量与完整状态同步检查可能改变初态验收，正式分组以新协议的 preflight 为准。历史归档提供待复核的证据，不替代当前运行。

## 冻结时点与审阅程序

首次生产代码修改前冻结 agent 的诊断输出及此前工具调用。后续发现单独记录为第几次补丁后的诊断修正，禁止用最终成功补丁回填首轮归因。Direct 条件若直接产生补丁而未提交诊断，记录 `not_reported`；补丁位置可单独报告，不折算成修改前的自主定位。初态即接受且未调用模型的任务记录 `not_invoked`，用于系统误报和误修改控制，不计为模型自主分类正确。

审阅输入包括匿名后的诊断文本、公开源码哈希、工具请求/结果、引用的证据位置和各次补丁时点。第一遍审阅不显示方法名或最终修复是否通过；第二遍对照本文件的私有证据和真实运行记录。每个结论应有一条可定位的原文证据和一个审阅理由。分歧保留原判断与裁决记录，避免无依据地统一标签。

分类不要求复述原 25 类编号。自然故障可使用目录外类别，并允许 `unknown` 或多个假设。评分按语义判断故障机制及位置，不按术语或字符串匹配。主张越具体，所需证据越具体；只观察到未更新不能自动判为优化器错误。

## 分开计量的项目

| 项目 | 满足标准 | 不满足标准的典型情况 |
| --- | --- | --- |
| 异常识别 | 指出当前可复现的运行或数值契约失败，并引用真实测量；执行失败时将后续未测阶段标为不可用 | 把训练未执行后的零更新当作已定位的更新故障，或只复述没有实际执行的测试 |
| 阶段归类 | 分类与实际可观测阶段一致，可同时记录梯度和更新异常；观察不足时保留未知 | 看到更新差就确定为 optimizer 根因；把缺测当通过 |
| 机制归因 | 提出可检验的机制，并把代码路径与至少一项独立运行观测连接起来 | 只列“dtype、shape、detach、optimizer”候选清单；引用旧报告的标签；从参数异常直接猜精确代码 |
| 文件定位 | 排名第一的位置命中已审定责任模块，或指出等效实现方案的明确边界并给出证据 | 只列整个仓库、所有 ops/autograd 目录或第一个观察到异常的无关调用者 |
| 符号定位 | 指出责任函数/注册键/调用边界，且引用公开代码或自己执行的局部 reproducer | 只列参数名或受影响层，未定位计算/派发/求导的实际边界 |
| 证据有效性 | 所引文件、行或工具结果存在，说明与结论相符；实验独立于隐藏答案 | 引用不存在的工具输出、未来补丁结果、不可见 evaluator 或私有标签 |

异常识别、阶段归类、文件定位、符号定位各记 `correct / partial / incorrect / not_reported / not_invoked / not_scorable`。机制归因再记录证据等级：`observed_failure`（运行失败直接确认）、`supported_mechanism`（代码路径与运行观测相互支持）、`counterfactually_validated`（隔离机制的干预或最小复现已确认）。这些等级不拼成单一总分。

主要定位指标使用 agent 明确排序的 top-1；另报告预先固定的 top-3。没有排序时只把最先陈述的明确假设作为 top-1，最多取前三个已说明的位置。不能把长清单中碰巧出现的正确文件计为 top-1。若真实责任符号尚未独立审定，该项记 `not_scorable` 并给出实际分母，不用临时“答案”给方法扣分。

## 10 个任务的私有审阅表

原始源码与首次翻译位于 `experiment-results-local-20260906/09_experiment_I_real_translation/runs_real_core_v3/tasks/<ID>/translation/`；历史首轮运行测量位于同任务的 `r_hier/reports/<ID>__r_hier_iter1_paired_report.json`。下表列出已核对的观测和机制状态。所有 provisional 项在正式评分前仍需审阅当前证据。

| 原始任务 | 历史初态观测 | 可审阅的类别与位置 | 机制状态 |
| --- | --- | --- | --- |
| I-01 | pocket_resnet 初态接受，无代码修改 | 正常控制；当前 preflight 通过则无需修复 | 仅在已测输入和协议内成立 |
| I-02 | `OperatorNotFound`，`lstm` 无 lowering 且无法原生回退；目标侧 losses/grad_norms 为空 | 执行/算子支持缺口；`BiLSTMClassifier.encoder` 调用 `nn.LSTM`，责任边界为 LSTM 派发/目标实现；`torch4ms/tensor.py::_get_op_or_decomp` 和 ops 注册是合理调查范围 | 首个执行阻断由异常直接确认；完整 LSTM 修复位置和全部后续问题 provisional |
| I-03 | `OperatorNotFound`，`gru` 无 lowering 且无法原生回退；目标侧 losses/grad_norms 为空 | 执行/算子支持缺口；`GRUAttention.gru`，GRU 派发/目标实现；调查注册映射或保持原语义的目标计算分解均可 | 首个执行阻断确认；精确实现方案及是否还有 attention 后续问题 provisional |
| I-04 | temporal_convnet 初态接受，无代码修改 | 正常控制 | 以当前 preflight 复核 |
| I-05 | deep_sets 初态接受，无代码修改 | 正常控制 | 以当前 preflight 复核 |
| I-06 | highway_network 初态接受，无代码修改 | 正常控制 | 以当前 preflight 复核 |
| I-07 | 目标 `RecursionError`；运行日志重复 `dispatch of __getitem__`；初始 forward 先执行 `x[:, :6]` 与 `x[:, 6:]` | 执行/索引派发递归；`BilinearFusion.forward` 切片调用，以及 `torch4ms/ops/mtorch.py::getitem`、`torch4ms/tensor.py` 的派发/包装边界 | 阻断与相关边界有证据；造成重入的精确条件和最小修复仍 provisional。旧 Verifier 的 environment_harness 标签不作真值 |
| I-08 | 首层 encoder 梯度/更新异常，后续 encoder/decoder/head 较接近；loss 差约 1.43e-6 | 梯度依赖中断，并导致参数更新差；`encoder.0 → nn.Tanh/torch.tanh → encoder.2` 边界，高层 Tanh 注册缺口与回退转换路径 | `supported_mechanism`：代码检查和基线自建运行相互支持；完整最小补丁的反事实验证尚未完成 |
| I-09 | value/gate/norm 六个参数不更新，仅 head 更新；loss 差约 4.77e-7 | 梯度依赖中断，并导致参数更新差；`GroupNorm/F.group_norm` 边界，高层注册缺口和回退转换路径 | `supported_mechanism`：代码路径与独立逐参数测试相符；完整最小补丁的反事实验证尚未完成 |
| I-10 | inception_micro 初态接受，无代码修改 | 正常控制 | 以当前 preflight 复核 |

I-02/I-03 的历史报告在执行失败后仍给出了接近 1 的更新相对差。评分只使用目标执行失败及异常作为该阶段证据，后续更新量按不可用处理。归类为更新根因不因这些残留值而获分。

I-08/I-09 的定位证据见[归档代码路径复核](natural-translation-cause-review-20260916.md)及[SWE/MatchFix 自主测试追踪](natural-baseline-probe-20260917.md)。两例首次翻译没有在上述位置人为插入 `detach()`。Tanh/GroupNorm 高层映射缺失后的原生回退经过 `asnumpy()`/`torch.from_numpy()`；数值传递与求导依赖中断可以同时发生。agent 若定位到这一边界，并用局部梯度测试支持，即使未写出精确注册键，也可获得机制和边界定位的相应分数。

I-08 的源端 AdamW 可能在梯度错误时仍产生权重衰减引起的微小更新。仅凭“更新不完全为零”宣布梯度正常，应判为错误；仅凭最终 loss 接近宣布训练正确也不满足该任务契约。I-09 的 head 仍可反向和更新，说明应检查整组参数；仅观测到一次 MindSpore 反向不能证明所有参数梯度正确。

旧 Direct 在 I-07/I-09 的“接受”结果已由[后端真实性审计](backend-authenticity-audit-20260917.md)判为完整退回 PyTorch。此类最终代码不作正确修复参考，也不用于给初态机制设定答案。

## 位置匹配与开放修复方案

I-02/I-03 允许两类有证据的定位：指出缺失的 LSTM/GRU 目标算子实现或注册边界，或者在 candidate 的具体 recurrent 调用处提出保持同一数学定义的目标框架分解。二者均需说明责任边界与异常的联系，不能只说修改 candidate。成功修复不强制编辑某个预定文件；验收仍核对语义与真实后端。

I-07 的符号真值目前只审定到索引派发边界。agent 若声称某个精确条件造成递归，应提供最小索引测试或调用栈。没有此证据时可得执行类别与边界定位分数，精确机制保持 provisional。不能把诊断器过去给出的错误 environment 标签用作人工答案。

I-08/I-09 的文件可覆盖 `ops/mtorch.py` 的高层映射、`tensor.py` 的原生回退、`ops/mappings.py` 的值转换，以及 candidate 中可等效替换的对应算子调用。准确定位需要把至少一个责任边界与受影响参数分布联系起来。只指出 `encoder.0.weight` 或 `value.weight` 是受影响参数，记为参数级症状定位，尚未达到根因符号定位。

## 正式结果记录

每个方法、每个初态失败任务保存一条私有记录：`task_id`、`anonymous_id`、`method`、`input_hashes`、`diagnosis_artifact`、`before_first_edit`、`predicted_categories`、`ranked_locations`、`evidence_references`、各项目评分、机制证据等级、`reference_status`、审阅理由和审阅时间。正常控制保存初态/确认验收、是否调用诊断、是否修改生产文件、修改后的验收，不向模型补充任务真值。

分类与定位统计以新 preflight 后的可评分任务为分母，同时报告数量。例如五个初态失败、四个责任符号已审定时，应分别写阶段归类 `x/5`、符号定位 `y/4`，并列出未审定任务。少样本逐例结果优先于小数百分比。失败检测、类别、责任位置、修复接受和成本保持为独立结果。

正式运行后逐条审阅时，仅在新工具证据或独立反事实检查支持下提升 provisional 等级。若出现目录外故障、新隐藏错误或健康控制被新协议拒绝，记录新证据与规则版本，并统一重评所有方法的同一任务，保留原评分。评估文件、人工修改记录和最终评分均与 agent 输入包隔离。
