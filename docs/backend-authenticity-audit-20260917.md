# Experiment I 目标框架真实性复核

## 结论

Experiment I 的 Direct LLM 有两个被原验收器接受的结果实际退回普通 PyTorch：I-07 和 I-09。按“迁移后必须在目标框架完成训练”的标准，这两个结果均为失败。Direct LLM 的整体接受数从 7/10 修正为 5/10；LaDiM 保持 5/10。两者的五个通过任务都是初始翻译即通过，五个初始失败任务中的真实修复数均为 0/5。

| 方法 | 原接受数 | 排除源框架回退后 | 五个初始失败任务中的真实修复数 |
| --- | ---: | ---: | ---: |
| Direct LLM | 7/10 | 5/10 | 0/5 |
| LaDiM | 5/10 | 5/10 | 0/5 |

此次复核检查了所有 20 个终态候选的训练入口，并重新执行 10 个共享初始候选和 20 个终态候选的单步验证。没有调用翻译或修复 LLM，没有改变初始候选、归档适配层、原始汇总或论文。重新执行后，原接受的其余十份终态均观测到对应模型的 MindSpore 梯度计算，三个数值差异也均在原阈值内。

## 两个确证实例

I-07 Direct 的最终 `train_one_step` 使用普通 `torch.optim.RMSprop`、`nn.CrossEntropyLoss()(model(x), y)`、`loss.backward()` 和 `optimizer.step()`。没有 torch4ms 环境、目标求导桥或其他目标训练调用。初始版本使用 `Torch4msOptimizer`、`torch4ms.default_env()` 和 `extract_and_wrap_loss_fn`；修复删除了这些调用。

I-09 Direct 的最终训练入口同样直接运行普通 PyTorch，优化器是 `torch.optim.Adam`。代码还明确写了 `# torch4ms imports omitted to restore runnability`。GroupNorm 适配缺口没有得到修复，整个模型转回源框架后自然恢复了与源程序相同的训练结果。

| 候选 | 最终文件 SHA-256 | 原判定 | 本次判定 |
| --- | --- | --- | --- |
| I-07 / r_direct | `8eb1478986cff2236a8f1a797202f0a13a125ddacb503b624d4817304648ae11` | SUCCESS | 失败：完整训练退回 PyTorch |
| I-09 / r_direct | `e4f610cbe78fa9333bd450f127217a8cb71cc847f9d9ba2c18455c00526101df` | SUCCESS | 失败：完整训练退回 PyTorch |

这与 I-08 / I-09 初始翻译中的部分算子回退不同。初始翻译仍执行目标训练，目标反向也确实发生，但部分参数的梯度或更新错误。运行时复核在这两个初始候选和对应 LaDiM 终态中观测到了 MindSpore 反向；它们仍因原有数值检查失败而保持失败。

I-03 Direct 和 I-08 Direct 的终态也没有被新检查观测到所需目标反向证据，但它们原本就是失败结果。它们保留了适配环境和优化器调用，不能仅凭“未观测到”进一步归类为已经确认的完整源框架回退。

## 验收漏洞与修复

漏洞位于 `autofix/verifiers/paired_code_report.py::_run_side`。当 `mode == "train"` 且设置 `train_entry` 时，宿主直接调用候选训练函数；`use_torch4ms_env` 只在后续 `elif use_torch4ms` 分支生效。因此配置中的 `use_torch4ms_env=true` 并不证明候选训练使用了目标框架。原验收器比较执行、loss、梯度范数和参数更新，未核验这些结果来自哪个框架。纯 PyTorch 候选与 PyTorch 参考比较时恰好能通过这些数值检查。

独立修复增加 `TargetBackendObserver`。它在每一步被评估训练期间观测 torch4ms 求导桥返回的真实 MindSpore 梯度，将模型或参数对象绑定到被评估模型，并检查对应目标 loss 与该步返回 loss 数值一致。缺少证据时返回 `target_backend_not_observed`，保留每一步的观测记录；源参考不受这一要求限制。检查没有给候选补加适配环境，也没有修改候选训练代码。

检查支持当前 torch4ms 的 `_run_backward` / `_run_grad` 求导桥，不把普通 `torch` 导入、无关 MindSpore 算子或另一个模型的目标反向算作通过依据。合法 `Torch4msOptimizer` 底层通过 PyTorch 优化器写回参数仍可通过。若其他实现替换了这两条求导桥，需要为其增加对应观测支持；“证据未观测到”本身不是已确认源框架回退的证明。当前检查观察目标反向和返回 loss 数值匹配，没有宣称完整追踪优化器更新的因果链。

远程修改位于独立分支 `codex/backend-authenticity-20260917`，基于原 Experiment I 的 `8c5c635b0c5c718fab052b885966be8980eea6ad`。工作目录为 `/media/main/whj/projects/torch4ms/ascend-torch4ms-backend-authenticity-20260917`，未提交或推送。

## 验证与范围

在 `mstorch` 环境下使用实际 MindSpore 2.7.2 和 PyTorch 2.8.0 CPU 执行，新增 10 个集成测试全部通过。覆盖纯 PyTorch、只导入 torch4ms、无关 MindSpore 算子、无关模型的目标反向被拒；正常候选目标训练、宿主目标训练、清除梯度后的合法训练、源框架参考通过；第一步目标训练不能掩盖第二步源框架训练。现有 `paired_code` 测试结果为 1 通过、2 跳过，`git diff --check` 通过。

本次评分复核只涉及 Experiment I 的完整自然迁移。原 Fixed50 使用 `autofix.faults.injection.run_probe` 等受控故障探针，不走这条候选训练入口；其中普通 PyTorch 代码可能是控制或故障夹具，不能用本次规则批量将其重判为迁移回退。没有调整其 50 例汇总。

原始汇总 SHA-256 在复核前后保持一致，30 个被执行候选的 SHA-256 均与原汇总记录匹配。初始候选使用原始 worktree 的公共适配层，终态使用各方法自己的归档适配层副本。

## 交付文件

- [逐项审计与训练入口摘录](../data/audits/backend-authenticity-20260917/audit.json)
- [独立纠正评分表](../data/audits/backend-authenticity-20260917/corrected_scores.csv)
- [验收器、测试及复核脚本补丁](../data/audits/backend-authenticity-20260917/backend-authenticity-20260917.patch)
- [真实运行时集成测试日志](../data/audits/backend-authenticity-20260917/integration-tests.log)

远程逐项报告、生成的 harness 和日志位于该独立 worktree 的 `experiments/backend_authenticity_audit_20260917/`。脚本 `experiments/audit_experiment_i_backend.py` 重放现有候选并输出独立结果，不运行新的 LLM 尝试。
