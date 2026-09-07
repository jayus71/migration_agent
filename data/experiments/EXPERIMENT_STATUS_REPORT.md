# Experiment A–K 状态汇报

更新日期：2026-09-06。

## 总体判断

可以说“主要实验矩阵已经运行并形成了大量结果”，但不能说“所有实验都完整通过或都支持论文主张”。更准确的表述是：实验执行暴露了多项真实问题，部分结果支持局部主张，D、E、H、I、J 对整体正向叙述形成了明确限制。

| 实验 | 当前状态 | 关键结果 | 论文口径 |
|---|---|---|---|
| A | 完成 | 6 方法 × 50 实例 = 300；严格通过 188/300；66 个旧/新判定发生变化 | 可用于修正后的严格阈值重算 |
| B | 完成 | 6 方法 × 60 = 360；R-HIER 54/60，Direct 54/60，MatchFix 58/60 | 支持 R-HIER 明显优于执行-only/flat，但不是全基线最优 |
| C | 完成 | 72 条件、3,600 step rows；所有自检通过 | 支持梯度错误与参数更新错误可被分层信号区分 |
| D | 部分完成，正式真实规模被 gate 阻断 | 受控 24/24、9,600 rows 全部训练有效并过阈值；真实规模 10-step 最大 minibatch paired residual 0.0897305 > 0.02 | 受控四模型支持正向主张；Experiment D 整体不支持正向主张 |
| E | 部分完成 | 修复严格复验初始化后，T-HIER 全新重跑 15/15 编译、执行、训练且严格通过；T-MSA 15/15 训练有效但严格 0/15；T-X2MS 无 15 条可测结果 | 支持 T-HIER 自身正向结果；仍不支持完整 Track-A 五方法比较，不能把不可测方法记为 0% |
| F | 已并入 D/I | 不维护独立结果表 | 真实数据/真实任务证据分别由 D 和 I 承担 |
| G | 完成 | 6 方法 × 20 = 120；R-HIER 15/20，Direct 15/20，MatchFix 16/20 | 支持分层反馈优于弱反馈，但不是最高成功率 |
| H | 运行矩阵完成，存在配置混杂 | 27 条件 × 50 = 1,350；DeepSeek 上 R-HIER 143/150，Qwen 上 111/150，GLM mixed 上 126/150 | R-HIER 稳定优于 R-EXEC；相对 Direct 的优势不跨 backbone 稳定 |
| I | 完成 | 10 真实任务 × 2 方法；R-HIER 5/10，Direct 7/10；自然失败任务中修复成功分别为 0/5、2/5 | 不支持 R-HIER 在真实翻译任务上的强正向主张 |
| J | 完成（含两轮确认重复） | 当前本地六条件视图为 300/300：R-HIER 48/50、R-Reverse 48/50；三轮合计分别为 139/150、143/150，轮次差值为 reverse 相对 hier +5/-1/0 | 完整层级反馈有效；reverse 优势未稳定复现，最佳呈现顺序未确定 |
| K | 完成 | 定位 48/50（96%），严格修复 46/50（92%） | 支持分层故障定位准确性主张 |

## Experiment D 口径

D 使用优化方案修订后的 gate：reference 侧在 deterministic fixed probe 上的 loss displacement 必须大于 0.05，同时比较 `loss_torch4ms - loss_torch` 的 paired residual peak-to-peak 是否小于 0.005。这样衡量的是“reference 确实在学习”以及“两条轨迹彼此贴合”，避免了原要求中“reference 明显变化”与“candidate 自身绝对变化小于 0.005”的逻辑冲突。

受控四模型的最大偏差为：loss `4.0531e-6`、gradient norm `5.4836e-6`、parameter update relative L2 `1.1810e-4`，均低于原阈值 0.02/0.05/0.03。

真实规模采用 CIFAR-10、PyNative、ResNet18/MobileNetV2。1-step 两个条件通过；10-step 两个条件都能执行且训练有效，但最大 minibatch paired residual 为 0.0897305，超过 0.02 gate，所以 2 models × 3 seeds 的正式 6 条件保持 fail-closed，没有启动。

用户要求的 seed 101、50-step 探索诊断也已保留。两模型都训练有效，但都越界：ResNet18 的 minibatch/probe 首次越界在 step 6/14；MobileNetV2 在 step 4/39。MobileNetV2 的 Torch4MS dispatched fixed-probe loss 最终达到 10.7042，而同一候选状态退出 dispatch 后的 native validation 为 2.3177，当前证据更指向 dispatch eval/BatchNorm 路径问题，而不是简单的参数爆炸。这一诊断不计入正式 6 条件。

## 解释“完成”的四层含义

1. `execution_success`：程序成功退出。
2. `training_valid`：反向传播无异常/warning，梯度非空，参数确实更新，参数映射和初始化审计有效。
3. `gate_pass`：训练有效后，数值漂移仍在预注册阈值内。
4. `paper_positive_claim_supported`：完整实验矩阵和比较关系足以支撑论文中的正向结论。

前一层成立不代表后一层成立。D 的真实规模 10-step 和 50-step 就是“执行成功、训练有效，但 gate 失败”；E 的 T-MSA 是“训练有效，但严格指标 0/15”；I 是“矩阵完成，但真实修复效果不支持原先的强主张”。

## Experiment E T-HIER 修订

旧归一化表中的 T-HIER `0/15` 已被确认是严格复验器假失败：候选侧先构建一次 disposable execution model，再构建训练模型，却没有在第二次构建前恢复 seed；reference 侧则重置 seed 后直接构建训练模型，导致最终比较使用不同随机初始化。修复没有改变阈值，只恢复了候选/reference 训练初态对齐。

在 commit `b32d9f4a27ed90646943b671d43f8616b4ad73fe` 上重新进行 5 models × 3 seeds 的真实 LLM 运行后，15/15 均严格通过，最大 loss/gradient/parameter-update 差分别为 `3.3379e-6`、`4.7684e-7`、`0.00285634`，低于 0.02/0.05/0.03。所有候选在初始翻译后通过，Fixer 调用为 0。旧 `final/T-HIER` 结果保留用于审计，但不再作为有效严格成功率。
