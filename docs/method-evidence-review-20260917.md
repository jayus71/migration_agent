# 信号设计与修复流程的证据复核

本次只检查已有实验、逐轮补丁和历史源码，没有运行新的 LLM 实验，也没有修改论文或原始评分。结论分开对应信号检测、给定诊断后的修复、自动诊断以及多 agent 组织。

## 可以直接支持的信号设计

Experiment C 在真实训练计算中分别注入梯度缩放和部分参数更新屏蔽。

- 梯度乘以 1.5：同步初态比较时 loss 最大差为 3.815e-6，梯度范数差最小为 0.09916，高于 0.05 阈值。梯度存在仍可能计算错误。
- 测量正确梯度后屏蔽部分参数更新：loss 最大差为 3.815e-6，梯度范数差最大为 1.192e-7，参数更新相对差最小为 0.042761，高于 0.03 阈值。前向和梯度检查通过仍可能更新错误。
- 自由运行条件下，两类直接信号各在 12/12 条轨迹的第一步越界。平均 loss 差在第 31、18 步越界；这两个数是平均曲线的交点，不是每条轨迹的检测时间。

这些结果支持分别检查前向、梯度和参数更新。它们比较的是验证信号，不是 SWE-agent / MatchFixAgent 的自主测试能力。

来源：[Experiment C 协议](../data/experiments/03_experiment_C_gradient_and_parameter_faults/README.md)、[逐步结果](../data/experiments/03_experiment_C_gradient_and_parameter_faults/results_per_step/section65_per_step_divergence_steps50.csv)。I-08/I-09 提供无注入情况下的对应现象；新增基线运行已经确认 SWE 和 MatchFix 也能主动发现它们，见[自然案例追踪](natural-baseline-probe-20260917.md)。

12 任务信号消融中，执行、执行加前向、完整信号分别接受 4/12、8/12、12/12。故障不在可见信号范围内时不触发修复，因此它支持信号覆盖和修复触发策略，不能单独证明修复推理更强。

## 两个真实修复成功记录及其诊断来源

原始 Fixed50 的 NU-07-B 中，Direct 和 SWE 的首个可运行补丁使用 `tile`，将两个 KV heads 排成 `[0,1,0,1]`；所需顺序是 `[0,0,1,1]`。LaDiM 第二轮改用 `repeat_elements`，输出最大误差从 1.028591 降为 9.9465e-7，通过该探针的 1e-4 阈值；Direct 和 SWE 在四轮内没有通过。三者首个补丁都修改同一个 `torch4ms/ops/mtorch.py`。补丁与测量见 [GQA 证据](../data/paper_figures/repair_case_evidence.json)。

NU-03-B 中，错误实现把布尔 attention mask 当数值直接相加。LaDiM 第二轮改为 `where(mask, scores, -inf)`，同时保留数值 mask 的加法语义，输出最大误差由 1.062416 降到 3.5763e-7。SWE 四轮没有提交生产代码修改。这个案例可以展示给定诊断后的修复以及补丁应用失败后的重试。

进一步审查发现，这两个案例的精确根因由实验脚本预设。该事实在原 Fixed50 提交 `3454be4e1e58f4889e362bd33289d49f98ebbcf6` 和 Experiment J 提交 `2d6bd3dfd4f3aefdcc1dc6d4d91277f181b141a8` 中均存在，并非后来新增。

`autofix/faults/core_qwen.py::_report(case, fault_probe)` 按 case 分支写入：

- NU-03：布尔 keep-mask 被当作数值 mask 相加，应屏蔽 False 位置。
- NU-07：KV heads 在 score matmul 后才复制，且 tile 顺序不符合 repeat_interleave。

同一函数将这些文本放入 `root_cause_ranked`，并预设 `failure_type`、修复文件、符号和路由。`FixerAgent._prompt_diagnosis_payload()` 序列化诊断时保留这些字段。由此，这些胜例证明了在给定根因指导下可以生成并验收正确补丁，不能当作从运行信号自主发现根因的证据。

核对位置：[根因构造](../ascend-torch4ms/autofix/faults/core_qwen.py#L156)、[修复提示构造](../ascend-torch4ms/autofix/agents/fixer.py)、[原 NU-03-B 修复记录](../ascend-torch4ms/experiments/baselines/full_hier_fixed50/r_hier/raw/NU-03-B.json)。

## 消融数据能支持到哪一步

Experiment J 的完整方法三次接受 44/50、47/50、48/50，flat 条件一次为 34/50。记录支持这套完整配置的接受结果更高；但至少上述核心算子案例同时比较了预设根因指导是否可见。

`autofix/baselines/repair.py` 中，hierarchical 条件保留 `report.root_cause_ranked`、`fix_hints` 和完整 metadata；flat 条件清空根因与提示。GR-05-B 的 flat 记录还只允许修改 `forward_extractor.py`，完整方法允许同时修改梯度写回文件。因而这些数据没有单独分离信号组织、自动定位能力、根因指导、补丁格式和可编辑范围的效果。

来源：[反馈保留与删除规则](../ascend-torch4ms/autofix/baselines/repair.py#L91)、[Experiment J 汇总](../data/experiments/10_experiment_J_feedback_ablation/README.md)、[逐轮原始记录](../experiment-results-local-20260906/10_experiment_J_feedback_ablation/formal_run_2d6bd3d/r_hier/results/section65_fault_pool_repair_raw.json)。

反序条件保持相同诊断和路由，三次接受 49/50、46/50、48/50；不能用它证明某一文字呈现顺序更优。当前没有仅改变 agent 拆分方式、同时固定信息、工具权限和预算的独立消融。

## 与外部 baseline 的案例选择

GQA 和布尔 mask 案例的正确补丁及接受差异可以展示，但应明确给定诊断的实验设置，不作为自主定位优越性的案例。GR-05-B 中 SWE 已修成功却被单文件范围拒绝，GR-07-A 的 MatchFix 输入存在同名构造函数错配，均不适合当作方法能力胜例。MatchFix 缺标签属于输出协议问题，也不能归为缺少梯度信号。

当前最扎实的结论是训练信号具有互补性，以及反馈能够驱动后续修复。证明 LaDiM 自动诊断或多 agent 组织优于这些外部 baseline，还需要用实际观测生成诊断、统一修复权限与接口，并保证每种方法获得的额外信息来自其自身可执行流程。不能把预先给定的正确根因当成系统自动发现的贡献。
