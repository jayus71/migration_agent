# 25 类缺陷目录、通用诊断与 Fixed50 提示来源

Fixed50 确实按已知缺陷编号进入专用报告构造函数，再把报告交给 Fixer。代码里有 25 类缺陷目录，也有依据运行结果和候选源码进行诊断的通用 Verifier；目前两者没有组成完整的“观测 → 25 类之一 → 类别提示”流程。

本次检查本地代码、原 Fixed50 提交 `3454be4e1e58f4889e362bd33289d49f98ebbcf6`、Experiment J 提交 `2d6bd3dfd4f3aefdcc1dc6d4d91277f181b141a8`，并只读检查服务器主仓库当前文件（HEAD `29149ba178310e81d5b8aa2124cdfdef828096fe`；当前文件不假定全部已提交）。另外核对已有组件补测的实际提示词。没有调用 LLM、重跑修复实验或修改论文。

机器可读记录见 [audit.json](../data/audits/fault-taxonomy-20260917/audit.json)，包含逐类目录、报告函数位置和哈希，以及已有补测 50 条首轮提示的保留字段。

## 25 类目录确实存在

定义位于 [`autofix/faults/registry.py`](../ascend-torch4ms/autofix/faults/registry.py)，原 Fixed50 和 Experiment J 都是 10 类执行、7 类数值、8 类梯度／更新问题。`FaultSpec` 记录编号、层级、修改范围、运行器、验证探针和说明；这些字段服务于受控故障的选择、构造、运行和评分。

| 编号 | 目录中的缺陷含义 |
| --- | --- |
| EX-01 | 候选算子返回原始张量，下游预期包装对象 |
| EX-02 | 矩阵乘法的 FP32/BF16 输入类型不匹配 |
| EX-03 | 高维转置使用不完整的维度排列 |
| EX-04 | 索引使用浮点类型 |
| EX-05 | 下游预期字典却收到列表 |
| EX-06 | 框架派发边界的张量转换错误 |
| EX-07 | BF16 embedding 进入不支持该类型的内核 |
| EX-08 | SDPA 转换、转置维度和输出包装错误 |
| EX-09 | 算子派发到错误的重载 |
| EX-10 | 算子的 tuple/Tensor 返回协议错误 |
| NU-01 | 前向遗漏残差分支 |
| NU-02 | exp/sum softmax 数值不稳定 |
| NU-03 | 布尔 attention mask 的保留／屏蔽语义错误 |
| NU-04 | mask 填充值不足以屏蔽概率贡献 |
| NU-05 | attention 遗漏默认缩放 |
| NU-06 | RoPE 旋转的符号或配对错误 |
| NU-07 | GQA 的 KV head 复制语义错误 |
| GR-01 | 隐藏激活 detach 导致前层缺少梯度 |
| GR-02 | backward 后、step 前清空梯度 |
| GR-03 | 训练步遗漏 optimizer.step |
| GR-04 | 错误冻结最后一层 |
| GR-05 | 梯度提取／写回的可训练参数映射错误 |
| GR-06 | 目标可训练层被错误冻结 |
| GR-07 | 优化器梯度／更新顺序包含冻结参数 |
| GR-08 | 优化器遗漏一组可训练参数 |

这是已有的受控故障覆盖设计。目录本身没有提供把任意运行观测映射到这 25 类的分类函数，也没有独立验证其对现实故障总体的覆盖率。

## 通用 Verifier 已实现的能力

[`VerifierAgent`](../ascend-torch4ms/autofix/agents/verifier.py) 的通用报告路径计算执行、前向、梯度和参数更新是否通过，并结合异常信息、逐层差异、逐参数更新和候选源码生成诊断。

- `_classify_execution_ownership` 识别缺算子、算子运行错误、张量边界、不支持的 BF16、返回协议和重载问题。
- `_build_candidate_code_diagnostics` 检查缺训练入口、backward 缺 module、缺 step、清梯度顺序、训练上下文、普通优化器和计算路径上的 detach。
- `_build_failure_localization_metadata` 选择失败阶段和修改范围，并保留首次分歧、更新异常参数等信息；证据不足以具体区分时产生 `numeric_mismatch`、`gradient_mismatch` 或 `param_update_mismatch`。
- Fixer 的 `_layered_failure_context` 按执行、数值、梯度／更新三个层次添加检查建议；`_route_repair` 依据报告中的修改范围选择候选代码、算子实现、反向／优化器桥接或环境路径。

这些规则与 25 类目录有部分语义重叠，但没有形成一一对应的 25 类分类器。检查的通用 Verifier/Fixer 路径没有调用该故障注册表来选择 25 类提示。mask 语义、attention 缩放、GQA head 顺序等也没有对应的专门自动判别分支。

例如，若程序能够执行、只有前向数值不一致，而且异常信息和源码扫描没有提供其他线索，通用定位默认输出 `numeric_mismatch`，把修改范围设为候选程序。它不会仅凭这一信号自动给出 GQA 的复制顺序根因，也不会自动锁定 `torch4ms/ops/mtorch.py`。

## Fixed50 的实际调用链

[`run_section65_real_fault_repair.py`](../ascend-torch4ms/experiments/paper_section_65_66/run_section65_real_fault_repair.py) 的 `fixed50_instances` 为每类分配 A/B 两个实例；`_run_one_fault` 把已知 `fault_id` 传给 `select_faults` 和 `run_faults`。[`faults/runner.py`](../ascend-torch4ms/autofix/faults/runner.py) 再按注册表中的运行器进入具体实现。

```text
实例已知的 fault_id
  → 专用运行器与真实故障探针
  → 专用函数构造 DiagnosisReport
  → Fixer 生成补丁
  → 探针验证补丁
```

通用 orchestrator 的路径则是 `verifier.verify(...) → fixer.propose(report)`。Fixed50 的八个故障实现家族均直接构造报告，没有经由这个通用 Verifier 来决定缺陷类别。逐家族核对如下；数量按类别计，50 个实例是每类两个。

| 报告构造模块 | 类别数 | 给定信息 |
| --- | ---: | --- |
| `controlled_cases.py` | 14 | 由已知 `spec.layer/scope` 设置失败层级、范围、文件和一般性根因／检查建议 |
| `candidate_training.py` | 2 | GR-01 明确给出 detach 及移除建议；GR-04 明确给出错误冻结及恢复训练建议 |
| `core_qwen.py` | 3 | BF16 embedding、布尔 mask、GQA 的专属根因与定位 |
| `core_attention.py` | 2 | SDPA 转换／转置／包装问题，或缺少默认缩放 |
| `core_tensor_boundary.py` | 1 | 派发边界返回非 Torch 张量 |
| `candidate_softmax.py` | 1 | 概率归一化不稳定与稳定化建议 |
| `core_gradient_mapping.py` | 1 | 可训练参数提取与梯度写回错位；同时指定两个文件 |
| `core_optimizer_mapping.py` | 1 | 优化器未按可训练参数建立对应顺序 |

因此，11 类提供故障专属的预设诊断／提示，14 类提供按已知层级和范围生成的一般性诊断。二者信息量不同。全部 25 类的归类路径由实验已知信息决定，不代表全部 25 类都给出了同等精确的修复答案。

报告构造还包括部分预设信号值。例如 `controlled_cases._report` 根据 `spec.layer` 写入 0/1 差异值；`core_qwen._report` 也直接设置数值信号。原始探针输出是真实运行记录，但 `DiagnosisReport` 中每个字段不能都解释成从探针测得。`blind=True` 在相应路径中主要隐藏案例标识，不会自动重新执行通用诊断或清除所有预设定位。

## 去掉具体提示之后：已有结果及其含义

已有的 `component-ablation-20260917/formal_v2` 使用请求模型 `deepseek-v4-flash`、温度 0、最多四次尝试，以原有故障探针验收。它与历史主实验是不同批次。归档 SHA-256 为 `8d96fee85dd4d9c73058ca1d4a544ad19d85316386e331937dd976d55d439f1c`。

| 同批条件 | 首次接受 | 两次以内接受 | 四次以内接受 | 总 token |
| --- | ---: | ---: | ---: | ---: |
| full | 49/50 | 50/50 | 50/50 | 491,526 |
| without_guidance | 46/50 | 50/50 | 50/50 | 577,848 |

这次删除根因文字、修复提示、分阶段推理建议和报告中的建议验证字段后，首次接受率下降 6 个百分点，总 token 增加约 17.6%，最终接受数相同。[已有汇总](../output/component-ablation-20260917/formal_v2/summary.csv)

过滤的具体实现位于补测源码 `autofix/component_ablation.py`：将报告顶层 `root_cause_ranked`、`fix_hints` 清空，并按字段名递归删除 metadata 中的 `fix_hints`、`reasoning_constraints`、`recommended_validation`、`recommendation`、`repair_guidance` 和 `root_cause_ranked`。Fixer 同时关闭分层证据部分的 `reasoning_constraints`，并把桥接探针及前次验证上下文的指导段落换成数据摘要。这是按指定字段和生成位置过滤，没有删除所有带有指导含义的文本。

实际提示仍保留系统角色、最小修改要求、路由决定、修改范围、当前源码、输出格式与提交规则、部分字段形式的预设诊断，以及修复历史。例如 `_scope_prompt_sections` 的补丁格式示例仍包含 `verify_commands`，所以不能将这个条件解释为“所有验证建议都消失”。NU-07-B 仍有“按核心算子问题修复”的说明；GR-05-A 仍要求修改反向／优化器桥接文件。这里没有通过一个 25 类提示检索器重新补回已删除的具体根因文字，但预设类别、位置和上述通用操作指导继续进入模型输入。

本次从完整归档逐一读取了 `without_guidance` 的 50 个首轮提示，核对结果为：

- 50/50 的 `root_cause_ranked` 和 `fix_hints` 都为空，提示哈希也全部匹配。
- 50/50 仍有 `recommended_target_files`。
- 48/50 仍有 `failure_type`；NU-02 两例原报告就没有这个字段。
- NU-07-B 保留 `gqa_head_repeat_mismatch`、算子文件和 `_sdpa_reference` 等函数名。
- GR-05-A 保留 `trainable_parameter_mapping_mismatch`、提取与写回两个文件，以及预设的异常参数和桥接状态字段。

所以，这组结果对应“去掉根因说明、保留预设定位”的条件。它没有测量“清除案例答案，再从真实观测重新归类”的效果。Experiment J 的 flat 条件同时改变了路由、上下文和编辑范围，也不能作为后一种条件的单独测量。

完全移除案例提供的类别、位置和预设诊断，需要接回通用 Verifier，并让后续定位只依赖实际观测和代码检查。现有代码仍能发现信号越界和若干可识别的源码模式，但 mask／GQA 等数值问题可能先被归入较宽的前向错误，算子问题也可能被路由到候选代码。这个条件的成功率和成本没有对应的完整实验结果。

## 与通用 agent 框架的流程差异

通用 `run_orchestration` 会调用 Translator 的 bootstrap/apply、每轮调用 `verifier.verify` 产生当前诊断，再调用 Fixer 并在后续轮次验证；根据验证分数是否改善决定回滚，并有无进展停止条件。Fixed50 从已准备的故障状态出发，直接调用专用报告构造函数和同一个 Fixer，用对应的故障探针验收；历史实现通常把未通过验收的补丁回滚，并将结果附给下一次尝试。

因此，Fixed50 复用了真实的补丁生成和应用组件，但诊断来源、运行探针和循环控制采用实验专用实现。它没有按通用框架的整条流程评估“从未知故障自主诊断并修复”。

按用户提出的设计，25 类可以保留为通用诊断知识：系统依据异常、源码和针对性探针选择类别，再取该类的检查提示；证据不足时保留多个假设并继续采集证据。当前需要补齐的是观测到类别及修复位置的连接，并在评估中检验这一步，而非删除所有通用领域知识。
