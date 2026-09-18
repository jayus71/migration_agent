# 去除预设答案与自主诊断评估审计

本次评估应从不含故障标签的任务快照出发，使用真实运行观测，让 agent 自行提出类别、位置和修复，再由独立验收器决定接受。原 Fixed50 的专用报告、按故障选择的编辑范围和可见注入源码共同提供了答案；只删两段提示不能消除这些输入。分类目录可以保留为所有任务共享的可选输出词表，允许 `unknown`、多个假设以及目录外类别。

审计读取了项目 `AGENTS.md`、[已有分类审计](fault-taxonomy-and-diagnosis-audit-20260917.md)、[方法证据复核](method-evidence-review-20260917.md)，并检查本地 `ascend-torch4ms/autofix/{faults,agents,baselines,verifiers}` 与实验入口。服务器主仓库只读检查的 HEAD 为 `29149ba178310e81d5b8aa2124cdfdef828096fe`，工作区有未提交修改；服务器当前目录缺少本地已有的 `autofix/faults/candidate_artifacts.py` 和 `autofix/baselines/repair.py`。以下逐行实现结论以本地文件为准，不能用服务器 HEAD 代替这份本地快照。本次审计没有调用模型或执行修复实验。

## 逐类答案来源

表中类别与位置由受控实验预先知道，不能出现在新评估的任务输入。A/B 两个实例沿用相同报告构造家族；实例命名、模型变体与历史结果目录也需隔离。

| 类别 | 报告家族 | 预设信息及额外可见线索 |
| --- | --- | --- |
| EX-01 | controlled_cases | 执行层、candidate 范围、准确文件、0/1 信号；源码含 wrapper/downstream 契约与故障探针 |
| EX-02 | controlled_cases | 执行层、candidate 范围、准确文件；dtype-sensitive 命名、FP32/BF16 专用探针 |
| EX-03 | controlled_cases | 执行层、candidate 范围、准确文件；高维排列专用源码和探针 |
| EX-04 | controlled_cases | 执行层、candidate 范围、准确文件；索引 dtype 专用探针 |
| EX-05 | controlled_cases | 执行层、candidate 范围、准确文件；输入容器契约探针 |
| EX-06 | core_tensor_boundary | `tensor_boundary_type_mismatch`、`torch4ms/tensor.py`、预设算子和返回转换根因；模块中含 HEALTHY_BLOCK/MUTATED_BLOCK |
| EX-07 | core_qwen | `unsupported_bf16_embedding_kernel_dtype`、embedding 符号、算子文件、BF16 kernel 根因、历史提交标识 |
| EX-08 | core_attention | `operator_rank_semantics_mismatch`、SDPA 符号、文件、转换/转置/包装的精确建议；head_dim/rank 常量 |
| EX-09 | controlled_cases | 执行层、candidate 范围、准确文件；重载注册表和 `OVERLOAD_FIXED/OLD` 可被源码搜索找到 |
| EX-10 | controlled_cases | 执行层、candidate 范围、准确文件；tuple/Tensor 协议及修复常量 |
| NU-01 | controlled_cases | 前向层、candidate 范围、准确文件；完整生成文件同时含正确 ReferenceResidual 与 candidate |
| NU-02 | candidate_softmax | 概率归一化不稳定的根因和稳定化建议、准确候选文件、StableSoftmaxNet.forward；核查量实际为 row-sum difference |
| NU-03 | core_qwen | `attention_bool_mask_semantics_mismatch`、SDPA 符号、准确文件、False 应被屏蔽的根因 |
| NU-04 | controlled_cases | 前向层、candidate 范围、准确文件；mask-fill 的参考计算、专用 probe、修复常量 |
| NU-05 | core_attention | `attention_scale_mismatch`、准确文件/符号、缺 `1/sqrt(head_dim)` 的根因、`expected_default_scale=0.5` |
| NU-06 | controlled_cases | 前向层、candidate 范围、准确文件；RoPE 参考函数和 OLD/FIXED 常量 |
| NU-07 | core_qwen | `gqa_head_repeat_mismatch`、准确文件/符号、tile 与 repeat_interleave 次序根因、历史提交标识 |
| GR-01 | candidate_training | 明示隐藏激活 detach 和移除建议；候选文件、first-layer-gradient 专用 oracle requirement |
| GR-02 | controlled_cases | 梯度/更新层、candidate 范围、准确文件、顺序检查建议；训练步骤与独立正确 manual path 共存 |
| GR-03 | controlled_cases | 梯度/更新层、candidate 范围、准确文件、step 检查建议；缺失 step 的精确 OLD/FIXED 常量 |
| GR-04 | candidate_training | 明示错误冻结和恢复 requires_grad；准确文件、目标层训练要求 |
| GR-05 | core_gradient_mapping | `trainable_parameter_mapping_mismatch`、提取/写回两个准确文件、两条精确根因；预设参数名单、首个异常参数、bridge preflight success |
| GR-06 | controlled_cases | 梯度/更新层、candidate 范围、准确文件；对 fc2.weight 的显式 trainable/gradient/update 要求 |
| GR-07 | core_optimizer_mapping | `optimizer_trainable_parameter_mapping_mismatch`、Optimizer.__init__、准确优化器文件、trainable-only 顺序根因；验证时预设 bridge preflight success |
| GR-08 | controlled_cases | 梯度/更新层、candidate 范围、准确文件；目标层梯度存在且更新非零的专用检查 |

主要入口为 [`controlled_cases._report`](../ascend-torch4ms/autofix/faults/controlled_cases.py#L879)、[`candidate_training.report_for_candidate`](../ascend-torch4ms/autofix/faults/candidate_training.py#L339)、[`core_qwen._report`](../ascend-torch4ms/autofix/faults/core_qwen.py#L156)、[`core_attention._report`](../ascend-torch4ms/autofix/faults/core_attention.py#L144)、[`core_gradient_mapping._report`](../ascend-torch4ms/autofix/faults/core_gradient_mapping.py#L133)。14 个目录类别经过 controlled 家族，11 个经过其余专用家族；controlled 模块还包含兼容实现，模块中存在的案例数量不能直接当作当前注册表的路由数量。

## 输入泄漏的完整路径

`failure_type`、`failure_stage`、`repair_scope`、`scope_confidence`、`recommended_target_files`、`source_symbols`、`read_only_source_symbols`、`touched_files` 和 `exec_signal.location/op_name` 均可能来自故障定义。`root_cause_ranked` 与 `fix_hints` 为空时，Fixer 仍序列化报告、按路由提供源代码、决定补丁格式并施加编辑范围。`r_hier` 保留完整 metadata；`r_flat` 删除定位但固定到选出的一个候选文件，两者权限也变化。因此原对照不能单独归因为诊断或组织方式。

部分观测是预设值。controlled 报告按 `spec.layer` 写入 0/1 差异并使其他层通过；core_attention/core_qwen 写 `loss_diff=1.0`，GR-05 写梯度和更新差均为 1.0，GR-01/GR-04 写前向差 0.0、梯度/更新差 1.0。原始 probe 可能真实运行，但这些报告量不能作为测量重用。GR-05 的异常参数、GR-05/GR-07 的 bridge preflight 状态也在报告或验证准备阶段预设。

`blind=True` 主要替换案例字符串。`FAULT_CASE_001` 等是按已知目录排序生成的稳定映射；具有目录源码的 agent 仍可恢复对应关系。`injection.run_probe` 又把 `fault_id`、adapter 名和 candidate 路径加回返回值。错误栈、命令行 `--probe-only NU-07`、`run_gr05_frozen_layer_backward_oracle` 等测试名、模型变体路径、旧结果 JSON 以及重试中的 validation/proposal 都可能再次带回同一信息。应在每个对 agent 可见的输出边界构造允许字段，避免继续递归删除少数已知词。

可见仓库包含更直接的答案库：`autofix/faults/*` 中的 `HEALTHY/OLD/FIXED`、`_mock_payload`、`healthy_snapshots` 与健康状态生成函数，实验结果中的成功补丁，以及 Git 的健康版本。[`injection._prepare_controlled`](../ascend-torch4ms/autofix/faults/injection.py#L59) 当前把带 reference 和 probe 的完整源码写入候选；[`isolate_candidate_source`](../ascend-torch4ms/autofix/faults/candidate_artifacts.py#L162) 虽能移除这些节点，当前 adapter 没调用它。只读权限不能阻止答案读取。新 agent 工作区应从故障状态构造独立可见包，排除注入器、隐藏测试、历史修复、报告和健康 Git 历史；需要 Git 时，以故障快照建立初始提交。还需处理绝对路径、符号链接、父目录读取和安装包路径，不能只约束当前工作目录。

真正的原始 PyTorch 程序属于迁移任务的公开输入，可作为只读语义参考。专门为某个故障生成的已修 target、可直接逆向的注入 diff、隐藏 evaluator 及健康 target 快照属于评估方私有信息。二者在任务准备时分开，来源和哈希由评估方记录。

## 通用 Verifier 能力与验收缺口

现有 `VerifierAgent` 会执行命令、读取 JSON、比较损失/逐层标量/梯度范数/参数更新，并结合异常和 candidate 源码产生启发式定位。它没有根据注册表自动选择 25 类标签；通用路径也没有调用 LLM 自主调查。源码规则把 detach、训练入口、backward/zero_grad/step、训练上下文等模式视为候选问题；默认数值失败指向 candidate，更新失败指向 autograd/optimizer。这样的输出应记录为规则假设，不能直接作为已证实位置，也不应限制 agent 随后检查其他生产文件。

| 核查项 | 本地实现及影响 | 新验收要求 |
| --- | --- | --- |
| 缺失量 | `_build_grad_signal` 已要求梯度和更新两个字段同时存在，这是可保留的检查；`observed` 默认 True，执行失败返回的空信号仍可显示为已观测 | 每个量单独记录 observed/unavailable/invalid；未执行阶段为 null，原因明确 |
| 只运行前向 | paired harness 默认 eval_forward，两个分支追加梯度 0.0，参数不变可得到更新差 0 | 训练验收要求实际 backward/step 证据；inference-only 的梯度/更新为 unavailable，验收明确按任务契约选择阶段 |
| 目标框架 | `train_entry` 分支先于 `use_torch4ms`，环境标志不会强制入口真正进入 MindSpore；`use_torch4ms_env=False` 仍把结果标成 torch4ms | 可信 runner 记录实际 backend 路径与执行证据，禁用静默回退；报告中的字符串不作为真实性证明 |
| 执行失败 | 运行侧失败后仍返回当前模型状态；main 继续计算已保存的 loss/grad 和更新差 | 总运行失败时不能凭残留量接受；诊断用 partial 量必须单独标记 |
| 初态同步 | `_clone_state` 只保存 named_parameters，未含 buffers；`_try_load_state` 使用 strict=False 并吞异常 | 同步参数、buffers、所需 RNG/optimizer 状态，验证键、形状和数值，失败阻断可比性判定 |
| 逐层比较 | hook 将张量缩成均值；同均值的排列/符号错误会消失；重复调用同层覆盖旧值 | 至少输出张量差的 max-absolute/relative-L2、shape、dtype、调用序号；保留执行顺序 |
| 梯度比较 | 比较整体 gradient norm 差；方向或参数置换可能保持相同 norm | 记录逐参数梯度存在性、名称映射、向量差；norm 可作为辅助值 |
| 参数比较 | 只遍历 reference 名称且跳过缺失键，candidate 额外参数不检查 | 键集合/shape/trainability 的缺失与额外项单独失败，使用实际 before/after 差 |
| 指标类型 | `_coerce_float` 不排除 NaN/Inf、负数；负的 absolute difference 可通过 `<= threshold` | 严格 finite、非负、非 bool；null 与无效值不得变成 0 |
| 层缺失 | `max_abs_diff` 排除缺失项，剩余层或 loss 通过时可覆盖缺层 | 必需层覆盖缺口进入独立 coverage 失败；不要只取已匹配层最大值 |
| 报告来源 | generic_script 接受指定 JSON，未验证新鲜度/源码哈希；success 字段取决于报告内容 | 固定 evaluator 输出通道，绑定运行 ID、源码与补丁哈希，拒绝旧报告/候选伪造输出 |

测量入口为 [`paired_code_report.py`](../ascend-torch4ms/autofix/verifiers/paired_code_report.py#L301) 和 [`VerifierAgent._diagnose_generic_payload`](../ascend-torch4ms/autofix/agents/verifier.py#L884)。这些是静态代码推导，本审计未运行反例。

受控 pool 的部分候选只导入并运行 PyTorch。把生成文件放入 `torch4ms/ops` 或把任务标为 core 不会使其成为 MindSpore 执行。新的首批对比宜使用 Experiment I 的 10 个自然翻译初态和统一真实后端测量，保留最初已经正常的任务作为误报/过度修改控制。受控 pool 可以后续单列为通用 Python 修复或在补齐真实后端适配后再评估；两种结果分开统计。

## 最小公开输入契约

任务输入提供不含标签的随机 ID、公开迁移源程序、故障状态的生产源码、入口/API 与真实输入契约、固定依赖环境、所有方法相同的生产文件编辑权限和预算。随机 ID 仅用于配对，agent 看到的路径稳定为 source.py、candidate.py 和原生产树；不包含 EX/NU/GR、A/B、fault family、注入历史或实际修改文件表。

公开测量由新对象从原始 paired JSON 的允许字段构造，不能把 `DiagnosisReport.metadata` 或外部 report 透传。对象包含 reference/target 执行状态和净化后的实际异常、损失/输出差、梯度差、参数更新差、逐层/逐参数测量，以及观测状态。测量名只表达被测对象；`failure_type`、建议路径、分类置信度、修复建议和框架路由均不在对象中。路径净化保留异常栈中的真实生产文件位置，移除评估路径和 ID；自然观测到的位置是可用证据。

agent 的诊断作为单独产物，字段可为 `hypotheses[{category, locations, evidence_ids, confidence}]`、`next_actions`。分类词表对所有任务相同，输出允许未知、多个位置和目录外类别。agent 能搜索、读源码、执行公开 probe、创建局部 reproducer、提交同一格式的 patch，再通过相同验收/重试循环继续；分类不能决定隐藏测试、权限或验收阈值。

验收器保持独立：来源不可变、测量完整且 finite、真实目标后端成功执行、固定阈值内的必要指标均通过。候选打印 `passed=true`、agent 说修好了、合法 JSON 或某个专用 probe 通过都不替代该判定。正常控制任务应先验收，接受后不触发修改。每次运行记录输入包/源码/补丁/测量/提示哈希、模型与工具调用预算、失败类别和重试历史。初态分类/定位在首次补丁前评分，避免用修复结果回填诊断。

## 有意义的验证与比较

1. 用两个不同秘密 fault manifest 指向相同公开源码和测量；公开任务、工具输出、提示和路由应逐字节一致。改变隐藏类别、target_files、root_cause、fix_hints、metadata 都不能改变公开输入。
2. 扫描所有首次与重试提示、路径、命令、traceback、tool 输出及公开文件；秘密哨兵、故障编号、健康补丁和隐藏路径不可出现。验证父目录/符号链接/Git/安装模块不能绕开可见包。
3. 验收反例覆盖：执行失败但附加全零指标，缺某个指标，NaN/Inf/负值/bool，缺 reference/target 状态，旧报告，candidate 伪造 JSON，后端回退，source 被改。结果均不得接受。
4. 用可区分观测测试测量能力：同均值不同张量、同 norm 不同梯度方向、漏参数/额外参数、同 loss 和梯度但更新被阻断、冻结参数/非零 buffers 不一致、step 末清梯度。这些验证真实测量风险，不为已有规则逐条抄写单元测试。
5. 对初始正常任务、实际执行故障、前向差异、梯度差异和更新差异均做小批端到端检查。通用未知故障应允许 `unknown` 并继续调查；精确类别/位置正确率只对有独立审定标签的样本计算。
6. 所有方法固定同一初始快照、公开信息、可编辑范围、模型、温度、token/时间/工具预算、验收阈值与四次补丁预算。工具交互轮数和补丁尝试数分别记录。比较首轮/两轮/四轮接受、正常任务误修改、总 token 和耗时，并保留每例配对结果。

首次 10 个自然任务的新结果只对应这份协议与样本。原 Fixed50 的 50/50、84% 和约 29 倍成本结果保留为历史记录；新协议的结果与旧表不可直接拼接。对 SWE-agent/MatchFixAgent 应区分实际 upstream 运行和本地仿照框架的 adapter；公开信息和验收一致后，再解释差异来自交互能力、诊断观测或实现。

## 文件快照与交接

| 本地文件 | SHA-256 |
| --- | --- |
| autofix/agents/verifier.py | 344b4d4b611a17209bc660cb3596c2155d1e713940e437d650704a310e9fb451 |
| autofix/faults/injection.py | c0f87b51fe36bb00bfe8485bc67c08563ccfa782952371a4b446bb4a37f1d8a8 |
| autofix/faults/candidate_artifacts.py | 447d135b2669ba1a8c89792b55cd8fabb095295c9b654711b6ff9e6d637ef803 |
| autofix/baselines/repair.py | e06e3babd23d025a667500e7de169b9dc6de052997a04e72ac563e35f5c79933 |

服务器 verifier/injection 的当前文件哈希分别为 `e68f8ae7168300be9babcd7d90cd21b7586fad36486e429b5550272a88ce4cfa`、`174948cad161cbe2339b74f8a355a7f525fd09fb49d9336a92c72bc967ade4e0`。新实现与实验应固定新 worktree 的完整快照，不覆盖服务器主仓库现有改动。

## 本次落实的接口与检查

新分支 `codex/autonomous-verifier-20260917` 的 `autofix/autonomous/observations.py` 已实现 `build_observation` 和 `evaluate_acceptance`。公开对象从 paired JSON 允许字段构造，不读取分类、定位、根因、提示或任意 metadata；执行不完整时测量为 null/unavailable。验收单独要求可信调用方提供后端证据和 source 不变证据，二者默认均为 False。局部测量若已提供，缺失覆盖或超阈值也不能由聚合值掩盖。模型生成的类别和位置独立于该对象。

`tests/test_autonomous_observations.py` 的 14 项测试在本地通过，包括秘密字段变更不影响公开对象、失败后残留零值、缺状态、无效值、inference 伪装 training、独立真实性证据、局部差异、路径净化和任意 stdout JSON 不透传。`evaluation.backend_attested` 已按真实 `TargetBackendObserver.report()` 的 `required/backend/steps/events` 字段实现，要求每个完成训练步有属于被测模型与返回 loss 的 MindSpore 梯度观测；原先猜测的 `passed` 字段并不存在。主代理在 paired runner 中另行加入梯度向量差与完整状态同步。

服务器新 worktree `/media/main/whj/projects/torch4ms/ascend-torch4ms-autonomous-verifier-20260917` 中，用 `mstorch` 的 Python 执行 `tests/test_autonomous_sandbox.py`，4 项测试通过，耗时 2.483 秒。测试实际运行 MindSpore CPU 前向及梯度；尝试读取本次测试创建的私有父目录、模拟宿主秘密和符号链接；尝试修改 source/task；检查运行缓存、环境变量清除和网络 connect 限制。所有秘密样本均由测试临时创建，没有读取用户凭证。这些检查验证隔离与测量接口，不代表修复成功率。
