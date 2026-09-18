# 远端 baseline 库存与实验 E 复核

本次只读检查用户分支 `codex/experiments-emn-integration`，提交为 `c21dadcf6e5e82665fa163b90c9dccb1ea15c4ef`，并对照远端历史 worktree 的原始 `summary.json`。没有调用模型 API、执行候选、修复 baseline 或修改论文。审查 worktree 为 `/media/main/whj/projects/torch4ms/ascend-torch4ms-emn-audit-20260918`。

## 主要判断

远端已经补充了 MSAdapter、CodeTransEngine、Ivy、torch2jax 和 InterTrans 相关实现。它们覆盖端到端框架迁移、已有故障修复、跨语言翻译等不同任务，应分别进入对应比较表。独立方法的数量不能通过重复命名内部 Direct、反馈消融或同一转换引擎来增加。

MSAdapter 在代码中的名字是 `T-MSA`，导入包为 `msadapter`。本次在指定分支的实验、autofix、文档及第三方目录中没有找到独立名为 MindAdapter 或 MindConverter 的 runner 或结果。2026-09-17 的 [baseline 审查](baseline-implementation-audit-20260917.md) 已查过多数框架；新分支补充了 N18 的 InterTrans 接入，因此其中“未发现完整 InterTrans 结果”的旧判断需要由 N18 审查更新。

实验 E 的旧 `overall_results.md` 写着 T-DIRECT、T-CTE 均为 0/15，已被原始正式结果推翻：当前冻结记录分别为 7/15 和 8/15。MSAdapter 的 0/15 也有具体的验收缺陷，详见下文。不能把这个旧总表作为新论文的数据入口。

## 库存

| 方法 | 已有实现和证据 | 当前可用范围 | 建议 |
| --- | --- | --- | --- |
| SWE-agent 1.1.0 | 冻结上游、原生工具和 parser；自主实验 Fixed50 29/50、Natural10 5/10 | 未知故障修复 | 复用已完成正式结果 |
| MatchFixAgent `66a52a5` | 完整上游编排、六语义角色、TestGenRepair/Verdict；编码后端接 DeepSeek 和公共工具；Natural10 5/10 | 有真实源程序和当前目标候选的语义修复 | 复用 Natural10；Fixed50 当前为不适用 |
| T-MSA / MSAdapter | v0.6.0，完整兼容库；五个任务统一替换 import，三个种子；原版和 patched 记录均存在 | PyTorch 到 MindSpore 的端到端迁移 | 原版作正式身份；修正验收后只需离线重验，不需要 LLM |
| T-DIRECT | 单次 DeepSeek 生成原生 MindSpore；15 次独立生成和验收 | 实验 E 的直接生成控制 | 现有候选和 7/15 可优先复用；必要时只离线重验 |
| T-CTE / CodeTransEngine | 实际 gRPC 翻译请求；15 次生成和验收，8/15 | 配置为 translation-only 的 CodeTransEngine | 保留准确名称和配置；不能声称完整 InterTrans 搜索 |
| T-X2MS / X2MindSpore | 输入准备、调用和候选验收 runner；正式记录只有五个已准备输入，0 个可测结果 | 端到端迁移工具；20260820 总 README 明确主动省略 | 记为未测，不能引用旧概览中的 0/15 |
| Ivy | 实际 `ivy.transpile`，JAX/Flax/Optax 训练；本轮六例已重跑、健康 gate 通过 | 已有故障程序转换到 JAX 后的结果 | 复用当前 0/6，保留其输入已有故障的定义 |
| torch2jax | 实际 `torch2jax.t2j`，JAX 梯度与 Optax 更新；本轮六例已重跑、健康 gate 通过 | 同上 | 复用当前 0/6 |
| InterTrans | 远端冻结上游 `84d2d4337dc82d848772cf834440ba17497b7683`；新分支 N18 有准备、公共资产、执行镜像、smoke、正式调用入口 | Java/DJL 到 Python/PyTorch 的 N18 | 由独立 E/M/N 审查核对完整搜索和原始结果；优先复用，不把 T-CTE 改名 |
| MindConverter / 独立 MindAdapter | 本次指定范围内未找到实际接入或结果 | 尚无可用比较行 | 需要新接入；当前不能填补一个结果行 |

## MatchFix 为什么需要目标程序

源程序提供原框架中的预期语义，目标程序是已经迁移、但可能有缺陷的待修复代码。MatchFix 对这两个程序做控制流、数据流、输入输出、库调用等语义检查，再生成测试和目标补丁。目标程序是工作对象，不应是健康答案。

当前 Natural10 接入把公开的 `source.py` 与 `candidate.py` 交给它，`ground_truth_target_function` 为空，没有借助健康目标 diff 预选责任函数。模型可以通过公开执行和工具观察定位问题。后端适配必须标为“完整上游编排 / DeepSeek 共享工具后端”，不能声称是未经适配的原 Claude/Codex CLI。

历史 Fixed50 的 wrapper 用健康目标与故障目标做 diff，把健康目标函数放进 `source_function`，构成答案泄漏；旧 47/50 不可作为当前 baseline。新分支 `MATCHFIX_CONTRACT_AUDIT.md` 已明确记录此问题。该文档另有 Experiment G 修正后的 16/20，但 G 使用公开失败符号配对函数，与当前从完整未知故障自主定位的输入条件不同，不能直接并入 Fixed50。

## 实验 E 的真实设计和记录

E 从五个健康 PyTorch 源文件开始，覆盖 Image MLP、CNN、ResNet、Transformer classifier、Tiny causal LM，没有人工注入故障。种子为 642、643、644。MSAdapter 对每个源文件只生成一个候选，再测三个种子；Direct 和 CTE 为每个任务生成三个独立候选，各测对应种子，不能把全部 15 行描述为同一候选的三种子稳健性检查。

| 方法及冻结 runner | 严格接受 | 训练完成 | token | 证据及限制 |
| --- | ---: | ---: | ---: | --- |
| T-DIRECT `4508d0e` | 7/15 | 13/15 | 361,566 | 原始 LLM usage；请求 `deepseek-v4-flash`；单次生成，无诊断和修复 |
| T-CTE `4508d0e` | 8/15 | 12/15 | 33,702，估算 | 来自输入/输出文本长度估算，不能与 provider usage 作精确成本比 |
| T-MSA 原版历史 `f3935d8` | 0/15，历史值 | 0/15 | 0 | 15/15 编译和前向；训练中 `TypeError: Expected a NumPy array`；没有应用 CPU 训练补丁 |
| T-MSA patched `5261529` | 0/15，验收有问题 | 15/15 | 0 | 两处上游补丁；初态不同且未验证一致，严格数值结果待重验 |
| T-X2MS | n/a | n/a | 0 | 正式归档 0 个可测条件；缺转换工具，不是 15 个算法失败 |
| T-HIER `b32d9f4` | 15/15，旧框架 | 15/15 | 见原结果 | 使用旧统一 orchestrator 和通用 guide；当前自主框架主张不能直接继承该数值 |

原始包在本地 `data/experiments/05_experiment_E_track_a_rerun/final/`。远端 Direct/CTE 原始结果位于 `/media/main/whj/projects/torch4ms/ascend-torch4ms-exp-e-final-5f3351f/experiments/experiment_request_20260820/05_experiment_E_track_a_rerun/final_4508d0e962d1/`。MSAdapter 正式包位于 `/media/main/whj/projects/torch4ms/ascend-torch4ms-exp-e-msa-5261529/experiments/experiment_request_20260820/05_experiment_E_track_a_rerun/T-MSA/formal_patched_5261529_5x3/`。

### MSAdapter：已有结果的两个问题

第一，patched 运行修改了 MSAdapter 自身的 `_tensor.py` 和 `optim/sgd.py`：删除 CPU 除法经过 NumPy 的实现，另将 SGD 中 `Tensor(ops.ones_like(p))` 等包装改为直接使用已有 Tensor。补丁 SHA-256 为 `892949be6044c4a395d7e623f925aa2ecec27ff766d2fcd042681e95e248f7fb`，远端第三方 worktree 仍保留这两处 tracked diff。这确实是替上游修复实现，不能作为用户要求的原生 baseline 身份。旧结果保留作开发记录；将来正式运行应使用隔离的干净上游，不要直接改动保存旧证据的 patched worktree。

第二，`5261529` 的 `_verify_torch_like` 在第 432 行设 seed，第 434 行创建模型做前向，第 450 行再次创建训练模型，期间没有重置 RNG；参考路径第 521 行设 seed 后只创建一次模型。该问题后来由 `b32d9f4` 修正，MSAdapter 正式结果却仍引用旧 evaluator。即便使用分支最新 evaluator，MSAdapter 路径也只有 seed 重置，没有原生 MindSpore 路径的 `_sync_mindspore_initial_state`；跨框架同 seed 本身不能证明初始参数相同。

例如 Image MLP/642 的 patched 记录中，参考与目标更新范数分别为 0.1490623 和 0.1490423，相对更新向量差却为 1.4216119；该记录没有 `initialization_alignment` 或 `initial_parameter_audit`。这组数字与代码一起表明 0/15 还需要正确初态验收，不能把大更新向量差全归因给 baseline。该问题属于我们的评分实现，不需要修改 MSAdapter 算法或调用模型。

T-MSA 的输入是健康源程序，但本次未找到其独立的、证明初态一致的健康验收记录。E 旧 worktree 有 native MindSpore golden/mutant calibration 脚本，覆盖的后端路径不同，不能自动代替 MSAdapter 的健康检查。

### CodeTransEngine：方法完整性和成本

T-CTE 调用真实 CodeTransEngine 服务，使用原生 MindSpore 目标 prompt，但配置为 `expansionIntermediaryNodes: 1`、`verifyIntermediateTranslations: false`、`applyRegexInferenceOnly: true`、空执行容器，并应用无 test suite 时跳过 `panic` 的 translation-only 补丁。它测量单次翻译配置，没有实现 InterTrans 论文中的完整多路径和测试搜索。现有 8/15 可以作为这个准确配置的结果；若用户要求新增完整外部方法，优先审查新 N18 的完整 InterTrans 接入。

CTE 原始两条 CNN 失败被标成 `environment_or_upstream`，实际是候选生成参数问题，旧审查已指出应计候选失败。8/15 分母已经包含这两条，不应删去失败缩小分母。CTE token 全部标为 `estimated`，没有精确 provider 用量。

### X2MindSpore：旧概览和实际归档矛盾

仓库 Track A 旧概览声称 X2MS 已跑 15 次，并在旧 Windows/WSL 环境训练失败。20260820 正式包的 `T-X2MS/summary.json` 则明确 `observed_runs: 0`、`paper_main_table_eligible: false`，只准备了五个输入；新分支总 README 写明 intentionally omitted。当前结果整理应采用有明确来源和实际产物的正式状态 n/a，不能使用前者补全五方法比较表。

## 最小追加工作

1. 先固定我们的一个框架版本。实验 E 若要支持新框架的端到端主张，需要更新 T-HIER 接入并产生新结果；旧 15/15 留作旧版本结果。
2. 冻结 T-DIRECT/CTE 现有候选、原始调用和费用。新框架不会改变 baseline 输出；若评分协议保持一致可直接复用，评分代码变动时只做离线重验，不重复生成。
3. MSAdapter 在干净上游隔离环境恢复其原生设定，修正评分初态、检查健康门禁后重新验收五个已生成候选。保留原生训练失败，不替它修复除法或优化器。
4. 优先把已经接入的 InterTrans 放入其适用的 N18 比较，检查完整上游搜索与测试是否执行。E 的 CTE 和 N 的 InterTrans 使用同系引擎，名称和不同配置应准确公开。
5. 若仍需给未知故障修复主表新增外部 agent，再选择一个支持现有 DeepSeek 接口的完整开源方法；先用离线契约测试和少量 pilot 确认适用性，固定后运行一组正式比较。当前没有发现可以无需接入就加入该主表的第三个独立修复 agent。

本报告只整理证据和下一步范围。新增运行、上游回退及评分代码修改均未在本次审查执行。
