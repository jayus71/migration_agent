# 自主修复正式实验的输入审计

审计对象为服务器 `ascend-torch4ms-autonomous-verifier-20260917/experiments/autonomous_verifier_20260917/formal_v1`。截至 2026-09-17 07:42:27 UTC（15:42:27 新加坡时间），全部十个冻结任务输入包与当时已写出的 180 份实际模型请求中，未发现历史故障标签、预设责任位置、健康目标实现或修复答案。原生 PyTorch 的 `source.py` 是公开迁移规格。审计发现 scratch test 输出保留宿主绝对路径；这些路径包含匿名条件与依赖环境位置，本批未检出原始任务编号或答案路径。

首轮为运行中的定点审计。2026-09-17 07:53:50 UTC 的终态扫描覆盖全部 40 个已完成条件的 442 份实际请求，包括 442 条 system、1,750 条 user、3,216 条 tool 消息；本文件定义的两组历史标签、答案和私有路径模式仍为零命中。以下 180 份请求表保留首轮定点证据，终态计数另见文末。审计只读服务器文件，在论文仓库记录结果；没有调整正式实验的代码、输入、预算或提示。

## 冻结材料与可见输入

正式运行选择原 Experiment I 的全部十份自然迁移初态，不注入新故障。`manifest.json` 中的原始任务映射、归档来源和哈希由评估方保存。公开工作区每个任务含 46 个文件：`source.py`、`candidate.py`、`task.json` 和 43 个 `torch4ms` 库文件。逐包检查得到：

| 检查 | 结果 |
| --- | --- |
| 十份 source 与私有清单 SHA-256 | 全部一致 |
| 十份初始 candidate 与私有清单 SHA-256 | 全部一致 |
| 十个库树逐文件比较 | 完全相同 |
| 库文件与原提交 `8c5c635b0c5c718fab052b885966be8980eea6ad` 比较 | 43/43 文件一致 |
| `task.json` 字段 | 每包均仅有 `input_shape`、`lr`、`num_classes`、`seed`、`steps` |
| 输入包符号链接 | 0 |
| 输入包中的历史标签、答案常量、私有路径模式 | 460 个文件均未命中 |

库归档 SHA-256 为 `063c3d51ef850da64a8f061034d416cc0829ef5fc150fba31bbac5120e9fba2b`。实现快照创建于 epoch `1789630565.9806542`；仓库 HEAD 为 `2d6bd3dfd4f3aefdcc1dc6d4d91277f181b141a8`，完整实现以 `implementation.json` 的 19 个文件哈希及 `code_snapshot/` 为准。本次检查时，运行目录中的代码和保存的代码快照均与这些哈希逐一一致。环境记录为 Python 3.9.25、PyTorch 2.8.0、MindSpore 2.7.2、NumPy 2.0.2。

`WorkspaceTools` 公开 `source.py`、`candidate.py`、`task.json`、`torch4ms/**/*.py` 与模型自己创建的 `scratch_tests/**/*.py`。读取、搜索、列表和编辑共用允许范围检查；隐藏路径、父目录、绝对路径、符号链接和硬链接被拒绝。首次诊断阶段只允许编辑 scratch tests。运行隔离的四项集成测试已另行验证父目录/模拟秘密读取被拒绝、规格只读、环境变量清除、网络 connect 限制与真实 MindSpore CPU 梯度；本次审计没有重复运行这些测试。

## 实际请求审计

读取实际 API body `conditions/<task>/<method>/evidence/agent/call_*_request.json`，检查所有 system、user 和 tool 消息。assistant 的自行推断不作为外部标签来源；转交给另一角色的既有模型输出仍被扫描并按来源区分。实际请求文件不含 API headers 或凭证。

定点快照共 180 份请求、180 条 system、784 条 user、1,415 条 tool 消息；所有 JSON 可解析。历史标签与答案检索包括 `root_cause_ranked`、`fix_hints`、`recommended_target_files`、`failure_type`、`scope_confidence`、`fault_id`、EX/NU/GR 编号、`_mock_payload`、`MUTATED_BLOCK`、`HEALTHY_BLOCK`、`FAULT_CASE_`。另外检查 I-01 至 I-10 形式的原编号、旧运行目录、`healthy_snapshots`、最终修复文件名、`private_inputs`、`manifest.json`、评分协议路径和 Git 历史访问字符串。输入包与非 assistant 请求消息中，这两组均为零命中。检查结果与提示、输入构造代码和首轮实际请求的代理逐项阅读一致。

| 匿名任务 | Autonomous layered | SWE-style shared tools | MatchFix shared tools | Direct shared tools |
| --- | ---: | ---: | ---: | ---: |
| task_001 | 8 | 8 | 5 | 8 |
| task_002 | 14 | 13 | 22 | 14 |
| task_003 | 13 | 17 | 24 | 13 |
| task_004 | 8 | 8 | 5 | 尚未生成 |

Autonomous 的 system prompt 要求根据公开规格、代码和实际执行证据自行推断机制与位置，使用自由文本分类，允许 healthy 或 undetermined，并保存假设、证据和可反驳测试。首次 user 消息提供实际 controller observation，其中包含同一验收阈值、执行状态、实际测量和覆盖检查；没有给定故障类别或建议修改文件。SWE-style 提示采用读代码、复现、修改与重测的一般流程，并明确当前条件是共享工具的风格对照。Direct 的首次诊断使用同一通用提示，后续修复流程区别由控制器实现。

MatchFix 条件使用 upstream `66a52a5626f5e8b480abbcd4b0e7a287fb3d85a7` 的角色与 tagged-JSON parser。审计代理核对 task_002 的初始化输入及五次模型请求：`source_function` 和 `target_function` 实际包含完整公开模块，`ground_truth_target_function` 为空字符串；没有预选责任函数。`source_path`/`target_path` 分别固定为 `source.py`/`candidate.py`。上游静态 CFG/DFG 与语义角色提示从这两个公开模块构造。语义角色自行生成的后续假设属于模型输出，并未使用私有评分表。

task_001 首次请求 SHA-256 为：Autonomous/Direct `6821ef2c51aa19ab468133ed1addaae008ff157f158ce03f456b68588422e89a`；SWE-style `b37d6da783ea32478a531c96835a9e6473d144ee934e82b15e2c68a4b627d8b7`；MatchFix `30a7d0d1fac720f4a933f24cb0c841de2140c80eef1b30d2173547c0bac5dde7`。

## 历史命名文件与路径输出

原提交的 `torch4ms` 树中，按 `autofix|repair|fault|case_|proposal|repro|backup|patch|original|healthy` 检索文件名，只有 `torch4ms/_autofix_probe_core.py` 命中。完整文件共八行，说明其用于 Phase10 的快照、验证和回滚管线测试，且不被运行时导入；唯一赋值为 `PROBE_VALUE = "baseline"`。它不含故障定义、修复实现或健康目标答案。实际日志显示多个模型读取过该文件，故审计明确记录其内容与影响。冻结运行保留原库树。

scratch test 的 `run_test` 输出直接保留截断后的 stdout，未经过 paired observation 使用的路径别名处理。例如 task_003/SWE-style 的 `call_0014_request.json` 中，scratch `probe_gru.py` 的 traceback 含服务器正式实验匿名条件路径和 conda site-packages 路径；task_003/MatchFix 的 `call_0018_request.json` 有依赖警告路径。32 条不同的模式命中均属于这类宿主路径。它们没有携带旧标签或正确目标代码，但削弱了对实验目录布局的隐藏。后续协议版本应把 scratch stdout/stderr 中的工作区与依赖根统一换成稳定别名，并保留真实相对文件、行号和异常信息。当前正式运行未据此修改。

## 首批诊断观察的使用范围

I-02/I-03 的已完成首次诊断均保存于各条件 `result.json.initial_diagnosis`，六个通用工具条件的首次 `stage_end` 事件可以核对读源码和搜索记录；生产 `edited_files` 均为空。它们自行识别 LSTM/GRU 的执行阻断，并将后续未测损失、梯度和更新保留为 unavailable。精确 overload 与最终修复方式仍未独立确认，评分遵守[冻结诊断协议](autonomous-diagnosis-assessment-20260917.md)。

MatchFix 两个任务的 data_flow 输出也识别了相同执行阻断；I-02 的四个其他语义角色、I-03 的两个角色出现上游返回格式错误，初始阶段标为 `upstream_role_error`。这些错误与其实际表达出的机制判断分别记录。后续诊断评审只读取已冻结的首次输出和此前工具证据，不用最终补丁改写首轮结论。

## 终态请求扫描

| 匿名任务 | Autonomous layered | SWE-style shared tools | MatchFix shared tools | Direct shared tools |
| --- | ---: | ---: | ---: | ---: |
| task_001 | 8 | 8 | 5 | 8 |
| task_002 | 14 | 13 | 22 | 14 |
| task_003 | 13 | 17 | 24 | 14 |
| task_004 | 8 | 8 | 5 | 8 |
| task_005 | 8 | 8 | 5 | 8 |
| task_006 | 8 | 8 | 5 | 8 |
| task_007 | 14 | 18 | 16 | 13 |
| task_008 | 11 | 11 | 18 | 12 |
| task_009 | 12 | 14 | 14 | 13 |
| task_010 | 8 | 8 | 5 | 8 |

终态检查共 442 份 JSON 请求，40/40 条件为 completed；扫描未命中预设分类、旧任务编号、修复答案常量或私有评分/清单路径。宿主路径输出问题仍按前述记录保留。五个初始失败任务的二十份首次诊断证据另见[首次诊断复核](autonomous-first-diagnosis-review-20260917.md)。
