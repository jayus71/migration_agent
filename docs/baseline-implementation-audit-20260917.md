# 现有 baseline 实现与证据审计（2026-09-17）

现有仓库已经实现六种修复条件、五种迁移条件，并保存了多组原始轨迹。当前证据支持重新建立公平的未知故障评估：历史实验同时存在直接提供健康目标实现、按故障标识指定函数、外部 agent 工具能力被移除、修改范围不一致及验收口径不同的问题。这些差异影响方法比较；旧成功率只能连同当时的输入、权限和验收条件解释。

历史结果审计只读检查了本地实验副本、原始 JSON/CSV、服务器冻结 worktree 和上游实现，没有调用 LLM、重跑旧实验或修改旧记录。随后完成的新接入与无 LLM 集成测试见文末。审计开始时服务器主仓库为 `29149ba`，分支 `codex/section63-structured-diagnosis-ablation`，有用户未提交工作。它并非所有实验共同的冻结版本；各组来源以 [SOURCE_INDEX.md](../data/experiments/SOURCE_INDEX.md) 为准。

| 修复条件 | 实际实现 | 模型可见材料及工具 | 主要约束 |
|---|---|---|---|
| `r_direct` | 单次 chat 生成 JSON 编辑，外层最多四轮 | 目标文件全文和普通 probe 输出；模型没有自主执行工具 | 旧 Fixed50 只许修改 `candidate_rel` 指定文件；外层按 fault-specific probe 判定重试 |
| `r_exec` | 内部 Fixer 的执行反馈消融 | 执行异常和 traceback | 是内部方法的反馈消融，保留共享 Fixer 实现，不能作为独立上游 agent |
| `r_flat` | 内部 Fixer 的平铺反馈消融 | 平铺诊断指标 | 输入仍由现有诊断/故障 harness 构造，需要纳入本次信息泄漏审计 |
| `r_hier` | 内部分层诊断、路由与 Fixer | 阶段、定位、路由及指导 | 历史高成功率不衡量从未知故障自主归类定位的全过程 |
| `r_swe` | 真正调用 SWE-agent v1.1.0 CLI | 仓库读取、编辑、shell 执行、普通测试；自定义系统提示 | 每 checkpoint 12 次模型调用，空历史处理器，旧单文件权限，non-root 本地部署补丁 |
| `r_matchfix` | 调用上游 MatchAgent 六分析角色和 parser，替换模型后端 | 旧 Fixed50 接收健康目标函数；测试/修复角色被替换为无工具 chat | 单函数补丁提取；上游 coding agent 的读写/测试能力未保留 |

上述入口在 [`run_external_repair_pilot.py`](../ascend-torch4ms/autofix/examples/run_external_repair_pilot.py)，Direct 提示从第 150 行开始，SWE 入口从第 564 行开始，MatchFix 入口从第 911 行开始。内部条件还应与本次独立的提示泄漏审计合读。

旧 Fixed50 的 MatchFix 输入直接泄漏健康目标实现。`_changed_function_pair()`（第 847 行）比较 healthy/faulty diff，用差异精确选定目标函数，再把健康目标函数写进 `source_function`。虽然 `ground_truth_target_function` 是空字符串，正确实现已通过另一个字段进入模型。函数配对只比较函数名和缩进，因此 GR-07-A 又把 `OptimizerState.__init__` 错配给 `Optimizer.__init__`。新协议应只提供原始 PyTorch 源程序、迁移候选和完整适配层，目标符号由 agent 自主选择。

后续 Fixed60 的 `f065b61` 已经改变这一点。服务器 `ascend-torch4ms-exp-bd-f065b61/autofix/examples/run_external_repair_pilot.py` 第 1032 行之后使用 qualified symbols；第 458 行调用 `get_matchfix_references(fault_id)`，提供 PyTorch source reference。Experiment G 的 `079a59a` 同样记录 `matchfix_clean_target_reference_provided=false`。它们修正了健康目标直接复制问题，但 Fixed60 的 reference 及目标符号仍按故障标识选择，所以仍未独立评估未知故障的自主定位。这个版本差异必须保留，不能把旧 Fixed50 的输入问题一概归给所有后续运行。

历史 MatchFix 的工具接入改变了上游算法的执行能力。服务器上游冻结为 `66a52a5626f5e8b480abbcd4b0e7a287fb3d85a7`，工作区无修改。其 `src/utils/model_utils.py:47` 的 `prompt_agent()` 调用真实 Claude Code/Codex CLI，`prompt_model()` 调用普通模型；`TestGenRepairAgent.analyze()` 调用前者执行测试和修复。项目 wrapper [`run_matchfix_agent.py`](../ascend-torch4ms/autofix/external_tools/run_matchfix_agent.py) 第 104–105 行把两者都替换成 `_prompt()`，而 `_chat()` 只有一次 `chat.completions.create()`，没有工具参数或 shell 子进程。因此角色文本里声称执行了测试，不构成实际测试证据。[上游仓库](https://github.com/Intelligent-CAT-Lab/MatchFixAgent) 将静态语义分析和可执行测试/修复组合为方法，且其主实验使用 Claude Code。

这条接入路径也有输出解析损失。本次遍历 Fixed50 的 50 份 MatchFix 首轮原始结果，确认 11 份 `test_repair.result` 是可解析 JSON，均有非空 `correct_target_method_implementation`，但缺失 `<final_response_format>` 外层标签，故 parser 拒绝、`generation.edits=[]`。例如 EX-02-B 有 101 字符的修复实现，首轮仍标记 `rolled_back`。11 例中后来有 10 例获接受；这些未应用的首轮候选本次没有重验，不能补记成首轮成功。应使用结构化响应/工具参数验证，并把解析失败与修复功能失败分别记录。

SWE-agent 上游冻结为 `0f3acafacabc0def8cc76b4e48acb4b6cf302cb9`，对应 v1.1.0。服务器保留六文件的 non-root 补丁，内容与本地 [`sweagent_v1.1.0_nonroot_local.patch`](../ascend-torch4ms/experiments/paper_section_65_66/external_patches/sweagent_v1.1.0_nonroot_local.patch) 一致方向：把 `/root` 的 shell 初始化、工具、状态和 patch 文件改到 `/home/whj` 或共享 `/tmp`。这些共享路径要求运行串行化或改成每实例独立目录，否则会相互覆盖状态。

旧 SWE 配置使用自定义命令块协议，模板中包含字面的 `\\n` 转义文本；每 checkpoint 配置 `per_instance_call_limit=12`，`history_processors=[]`。本次遍历首轮记录确认四例 `exit_format` 无补丁、六例 `exit_cost` 无补丁；另外三例实际补丁未通过 probe。GR-05-B 首轮同时修改 `torch4ms/autograd/forward_extractor.py` 和 `torch4ms/autograd/__init__.py`，probe 为 `verified_restored`，却因第二文件超出单文件 scope 被严格接受表拒绝；内部方法能在该问题上改两个文件。这是权限差异，不能解释为 SWE 未找到梯度修复。

SWE 的默认 v1.1.0 配置本身有函数调用工具和提交前复查流程，可借鉴其读取相关代码、编写复现、编辑、重测和检查 diff 的过程。[上游默认配置](https://github.com/SWE-agent/SWE-agent/blob/v1.1.0/config/default.yaml) 使用 cache-control 历史处理器；它主要标记缓存，不压缩上下文。上游另有 [LastNObservations 和 ClosedWindowHistoryProcessor](https://github.com/SWE-agent/SWE-agent/blob/v1.1.0/sweagent/agent/history_processors.py) 可移除重复观测。新框架应保存完整原始轨迹，同时维护包含已证实故障、证据 ID、定位和失败修复的持久状态，避免简单截断尾部导致发现丢失。

自然任务 I-08/I-09 的 2026-09-17 跟进已经恢复 MatchFix 真实 shell 工具循环，明确标为 “MatchFixAgent + DeepSeek tool execution adapter”。两方法都获得完整 source/candidate/私有适配层、普通执行测试，未获得梯度故障标签。四条件均在首 checkpoint 自行执行训练对照测试并发现反向异常；最终四条件均未通过独立隐藏验收。SWE 续跑只保留前 checkpoint 最后 24,000 字符，长文件输出挤掉了早期定位，影响了后续修复。这组记录支持自主检测能力，修复结果受续跑上下文限制，不能作为新框架的公平排名。实际命令、测试及初始/最终指标见 [自然案例报告](natural-baseline-probe-20260917.md) 和 [协议](../data/audits/natural-baselines-20260917/PROTOCOL.md)。

已有修复结果如下。每列使用对应运行自己的验收条件，列间不能合并成单一成功率。

| 方法 | 原 Fixed50：四轮内故障检查接受 | Experiment A：同一最终候选 paired 复验 | Fixed60：本组严格接受 | 多故障 G：本组严格接受 |
|---|---:|---:|---:|---:|
| R-EXEC | 33/50 | 27/50 | 42/60 | 1/20 |
| R-FLAT | 34/50 | 28/50 | 44/60 | 1/20 |
| R-HIER | 50/50 | 33/50 | 54/60 | 15/20 |
| Direct | 40/50 | 35/50 | 54/60 | 15/20 |
| SWE-agent | 46/50 | 32/50 | 43/60 | 3/20 |
| MatchFix 接入 | 47/50 | 33/50 | 58/60 | 16/20 |

本次从原始 CSV 重新分组计数 A、G，读取原 Fixed50 和 B 汇总核对。A 是已有最终候选的独立 paired-threshold 复验，没有再次调用模型；210/300 条件正常执行并测得指标，90/300 为执行失败，188/300 通过。G 的数值及梯度/更新阈值为 `1e-6`，并要求各注入故障独立触发，区别于自然迁移的 `0.02/0.05/0.03`。来源分别是 [Fixed50](../ascend-torch4ms/experiments/baselines/full_hier_fixed50/summary.csv)、[A](../data/experiments/01_experiment_A_paired_threshold_revalidation/formal_final/README.md)、[B](../data/experiments/02_experiment_B_fixed60/formal_summary_f065b61/README.md)、[G provenance](../data/experiments/07_experiment_G_multi_fault/results_six_methods_corrected/provenance.json)。

Experiment J 当前六条件有结果：execution 33/50、binary 34/50、stage 34/50、flat 34/50、hier 48/50、reverse 48/50。hier/reverse 三轮合计分别 139/150 和 143/150，呈现顺序优势未稳定复现。它们适合研究反馈因素；本次移除答案与标签之后应重新定义共同输入，不能直接沿用历史性能归因。Experiment I 经目标框架实际执行审计后，R-HIER 和 Direct 都为 5/10；五个初始失败任务的真正修复均为 0/5。五个成功任务初始已经通过，需作为健康控制单独报告。见 [J 汇总](../data/experiments/10_experiment_J_feedback_ablation/formal_run_2d6bd3d/summary.csv) 和 [I 后端审计](backend-authenticity-audit-20260917.md)。

迁移 baseline 也有真实实现和结果，但任务目标是从源程序生成迁移候选，与修复既有未知故障不同。

| 条件 | 已实现路径 | 当前有效 Experiment E 结果 |
|---|---|---|
| T-DIRECT | 直接 LLM 一次生成 native MindSpore 程序，无 guide/diagnosis/repair | 15 个条件，13/15 训练有效，7/15 paired 严格通过 |
| T-CTE | CodeTransEngine 服务，translation-only 接入补丁，单次翻译 | 15 个条件，12/15 训练有效，8/15 paired 严格通过 |
| T-MSA | MSAdapter v0.6.0 统一导入/启用，记录通用 CPU 兼容补丁 | 15/15 训练有效，0/15 paired 严格通过 |
| T-X2MS | 官方转换脚本及兼容装载路径已实现 | 当前正式环境阻断，0/15 可测，结果为 n/a |
| T-HIER | Translator + Verifier + Fixer | 15/15 paired 严格通过，全部初始翻译已通过，Fixer 调用为 0 |

源实现位于 `ascend-torch4ms/experiments/baselines/track_a/` 各目录的 `run_t_*.py`。服务器安装了 `external_baselines/InterTrans-84d2d43`、`third_party/CodeTransEngine-exp-e` 和多版 MSAdapter。CodeTransEngine 允许没有 fuzz/unit test 的 translation-only 请求，这是接口适配；不能将该实验称为完整测试驱动 InterTrans 搜索。当前证据优先级以 [Experiment E final](../data/experiments/05_experiment_E_track_a_rerun/final/overall_results.md) 为准，较旧 `ascend-torch4ms/experiments/baselines/track_a/overall_results.md` 的全零 baseline 表已经过时。本次没有发现需新增命名的独立修复 baseline 成功率。

原 Fixed50 的 token 比值也需要重新记账。已有逐调用审计发现 R-HIER 汇总漏掉 14 个实例，共 398,651 token；原表 190,588，原始调用复算 589,239。在原接受分母保持不变时，MatchFix/R-HIER 的每成功 token 比从约 29.1 变为约 9.40。这是已有调用用量修正，并非新实验。本次未修改旧表。三方法原始记录中调用总数为 R-HIER 59、SWE 877、MatchFix 491，“四次修复尝试”显然未统一内部模型工作量。详见 [首轮与用量审计](baseline-first-attempt-audit-20260916.md)。新比较应共用调用数、token、工具执行和修复轮预算，记录所有分析角色、诊断与重试成本。

新未知故障实验可以保留以下组件，并明确其输入边界：

1. 用公共源程序、候选和适配层建立完整可见工作区；注入器、健康目标实现、fault ID、历史结果、原答案和私钥放到不可访问区域。外层 task ID 使用中性编号，所有方法允许相同的多文件生产代码修改。
2. 共享列目录、读文件、搜索、编辑和运行测试工具，测试输出记录真实退出码、stdout/stderr、指标、产物及候选 hash。当前默认 Verifier 提交证据、原因假设、位置和反证测试，不要求先选类别；类别仅用于后验评估。是否强制分类作为独立消融，不能把故障真实标签输入模型。
3. 共享验收和重试循环：所有方法使用相同开发验收信息；独立隐藏评分固定在最终候选上，检查目标后端实际参与、不可变输入、执行、前向、梯度和更新。执行失败后的未测指标为 n/a。保留健康任务以评估误报和破坏率。
4. 保存结构化发现、证据 ID、已读文件摘要和尝试过的修复，跨 checkpoint 继续。预算包含所有角色；格式纠正与基础设施失败单独计数。结果分别报告自主检测、归类、定位、实际修复、最终接受和资源成本。

最初的五工具接口不能直接运行 SWE-agent v1.1.0：其 `SWEEnv`、`ToolHandler` 和 `DefaultAgent` 依赖 bash 部署、安装命令、工具状态文件及 git submit。复用流程思想的五工具控制已明确命名为 **SWE-inspired shared-tool control**。随后另建了隔离 bash runtime，保留上游原生工具协议和版本，其实现和验证见下一节。

MatchFix 的可行接入更直接：保留冻结上游六分析角色、PromptGenerator、TestGenRepairAgent 与 VerdictAgent，只把 `ModelUtils.prompt_agent` 的执行后端接到共享工具循环，并把 `prompt_model` 接到同一预算账本。它应标记 **MatchFixAgent + shared-tools adapter**。整个模块的源/目标输入可复用自然案例中已运行的 whole-module pairing；需去掉故障函数预选，并让模型自行搜索和定位。数据流/控制流分析可按模型发现的相关模块调用，完整方法和自适应精简版须分别命名、比较。上述是基于已读接口的接入可行性判断，新实现及性能要以随后实际测试为准。

## 已完成的新接入及验证

新代码位于独立 worktree `ascend-torch4ms-autonomous-verifier-20260917/autofix/autonomous/`。`swe_upstream.py::SWEAgentNative` 真正运行 SWE-agent 1.1.0 的 `DefaultAgent`，保留 `config/default.yaml`、原生函数调用 parser、bash、文件编辑器、提交前复查和默认 cache-control 历史处理器。源码从固定 commit 直接 `git archive` 导出，服务器已有的 non-root 修改不进入新运行。环境路径替换、预装编辑器依赖和专用 PTY 适配逐文件记录在每个条件的 `baseline_manifest.json`。

SWE 的整个原生进程在导入上游前进入 Landlock/seccomp 沙箱。其持续 shell、独立命令执行、命令语法检查子进程、文件读写和上传全部继承隔离；模型进程没有 API 密钥。控制器预先创建专用 PTY 并传入文件描述符，工作进程不能枚举或读写宿主的其他终端。公共测试通过只接受已登记测试名称的管道桥调用外部验收器。验收和快照期间，控制器用 pidfd 暂停整个原生后代进程树；退出时终止这些进程。生产代码允许多文件修改，源程序和公共任务契约保持只读。新 socket 规则同时阻止 IPv4/IPv6 的 TCP/UDP 创建，保留 asyncio 所需的本地 socketpair。

真实 DeepSeek 传输 pilot 发现，在公共测试被 `timeout` 或管道包裹时，按父进程优先恢复会让 bash 在子进程仍暂停时提前报告 `Stopped` 与退出码 147。修复后按实际父子树深度先恢复子进程，再恢复等待它们的父进程；真实原生集成测试要求 `timeout 60 run_public_test public 2>&1 | head -5` 返回 0 且不出现停止提示。没有关闭原生作业控制。工具契约仅说明命令的完整调用示例、测试的是当前可编辑工作区，以及验收源码由外部控制器持有。

原生 SWE 自主决定何时编辑，初始化只启动运行时。控制器在首次观察到生产代码改变时保存此前完整历史和触发动作；外部验收失败后向同一个 agent 追加反馈，继续其原有历史，最多四个提交 checkpoint。没有八次调用的阶段切片，也没有将 LaDiM 的证据压缩施加给 SWE。默认上游 cache-control 会移动缓存标记、把文本转换为内容块，测试按完整文本和工具内容核对历史连续性。

DeepSeek thinking 的传输适配保留原生 history：只在发往 API 的副本中无损拼接纯文本块、移除上游缓存元数据，并依据完整 assistant 内容、工具调用和实际响应顺序，回填上游 v1.1.0 未保存的 `reasoning_content`。无工具的 assistant 回复也从真实响应恢复该字段，不使用解析出的 thought 伪造推理。每次 RPC 同时保存原生消息与传输消息，首次生产编辑记录还包含触发动作的完整 provider response。返回内容与工具调用原样交给上游 parser，错误是否触发重试由上游处理；适配器不根据 `finish_reason=length` 改写工具调用或新增重试。该传输适配依据 [DeepSeek thinking 文档](https://api-docs.deepseek.com/guides/thinking_mode/) 和 [Chat API 消息类型](https://api-docs.deepseek.com/api/create-chat-completion/)。

`baselines.py::MatchFixFullOrchestration` 的明确名称是 **MatchFixAgent full upstream orchestration + shared-tools backend**。每轮直接调用未修改的 `MatchAgent.run()`，执行六个语义分析组件、TestGenRepair 和 Verdict。控制流与数据流组件在静态图相同的情况下会自行返回 `non-LLM response`；新接入保留这种上游行为。每次上游 coding-agent 调用内保留完整工具会话，外部重试重新调用上游完整编排、重新分析当前模块。上游本身没有跨轮 CLI resume；新模式因此不再复用初始六角色分析或人为拼接跨轮 role history，也不预留 verdict 调用、不在末次调用强行禁用工具。

MatchFix 的原始执行后端是 Claude Code 或 Codex CLI。新模式用共同 DeepSeek 账本和五工具执行后端替代它，因此保留了完整上游编排与 parser，同时存在明确的执行后端适配。上游传入的 1000 秒修复/300 秒判定 timeout 保存在 RPC 审计中，实际调用由共同总时限约束。服务器另有 Codex 0.11.0 包，默认 Node 为 18.19.1，而包声明 Node ≥22；当前没有发现可直接运行的 Claude CLI。真正原生 CLI 接入仍需兼容运行时、内部模型用量代理和限定网络出口，不能把现有五工具后端写成官方 CLI 复现。所有本轮正式 LLM 比较继续使用同一 DeepSeek 模型。

MatchFix 需要真实 source-target 对。原 Fixed50 的库单元任务没有对应原生源程序时，结果为不适用；不提供健康目标代码冒充 source，也不将这种适用范围记作修复失败。完整 MatchFix 编排用于具备真实 PyTorch 源程序的自然迁移任务。两个新 baseline 均只继承公共任务契约、候选代码和真实测试观测，不接受故障类别、预选函数或健康目标实现。

MatchFix 后端保存包括最终无工具回复在内的真实 `reasoning_content`。空回复、截断文本、缺失标签或正文 DSML 均原样交给上游 parser，不增加续答、修复标签或应用代码文本。具有真实工具调用的 coding-agent 后端维持执行工具和返回观测的常规会话循环。上游语义分析指令和响应 parser 保留；SWE/MatchFix 不使用本框架的 Verifier 类别 schema。

pilot 还发现，无工具的 MatchFix 语义分析角色收到了工具操作说明，导致 DeepSeek 在普通正文输出 DSML 工具意图。当前适配器按原上游 `backend=model` 与 `backend=agent` 分别提供契约：前者只追加中性公共任务/后端事实，后者额外获得实际五工具说明。原分析提示与响应格式由上游提供。没有给静态语义角色新增工具，也没有将正文 DSML 当作已执行工具调用。pilot_v3 和随后停止的 smoke_v4 冻结源码与原始记录保留，均为接入开发记录，不用于正式排名。

用户明确要求 baseline 保留原方法行为后，已撤回新增的健康鼓励、提前提交建议、自主调查/定位与反证等提示，以及 FullMatch 空回复/截断续答和 SWE 截断工具改写。自身框架的改进独立实现和评估。正式外部 baseline 的保留与撤回范围如下。

| 项目 | 当前处理 | 归因与可审阅证据 |
|---|---|---|
| SWE 原方法 | 保留 | 固定 `0f3acafacabc0def8cc76b4e48acb4b6cf302cb9`；`git archive` 直接导出默认模板、调度、parser、原生错误重试、编辑器、submit 和 history processors。安装目录六文件 non-root diff 不进入运行 |
| SWE 环境修改 | 保留 | 每实例路径、预装编辑器依赖、专用 PTY、权限隔离、无原仓库历史；`baseline_manifest.json.environment_edits` 保存每文件 before/after SHA256 与统一 diff |
| SWE DeepSeek wire | 保留 | 实际 reasoning 字段回填、纯文本块拼接与去缓存元数据；记录原生消息与 API 消息，不压缩/重排原生历史 |
| SWE 公共测试恢复顺序 | 保留 | 修复本适配器造成的 STOP/147，按子到父恢复；实际 timeout/管道测试验证退出码0，未改变上游调查或重试策略 |
| SWE 新增提示与截断补救 | 撤回 | 追加内容只包含共同公开契约、实际读写范围、解释器、测试命令及真实观测；不鼓励健康判定/提前提交，不指导调查或定位。provider返回原样进入原生parser |
| MatchFix 原方法 | 保留 | 固定 `66a52a5626f5e8b480abbcd4b0e7a287fb3d85a7`，`src/configs` 无 tracked diff；完整 `MatchAgent.run`、六语义组件、原提示/parser、TestGenRepair 与 Verdict；`max_retries=1` 与固定上游配置一致 |
| MatchFix 执行后端 | 必需适配，单独标明 | 原 Claude/Codex CLI 改为同一 DeepSeek 与五工具后端。`prompt_model` 单次返回文本；`prompt_agent` 执行常规工具会话。保持 **full upstream orchestration + shared-tools backend** 名称，不声称原 CLI 复现 |
| MatchFix 无工具角色的工具指令 | 撤回 | 删除不真实的能力说明；只对实际 coding-agent 后端描述可调用工具，语义分析提示仍来自上游 |
| MatchFix 新增输出修复/续答 | 撤回 | 空回复、length、缺标签和语义角色错误不触发适配器补救；原文本交上游parser，统一账本仅记录状态和成本 |
| 共同外部验收/最多四个提交 | 保留为实验协议 | 用户要求的共同验收与重试边界，明确属于外部控制器；不冒充上游原始实验配置 |

`SWE-inspired shared-tool control` 和较早的 `MatchFixSharedTools` 保留为历史开发条件，不是本轮两个正式外部 baseline。它们的自定义模板、阶段配额或分析复用不能归给上述固定上游执行。

服务器在 `mstorch` 环境完成以下验证，响应由脚本构造，没有调用真实模型：

| 检查 | 实际结果 | 覆盖内容 |
|---|---:|---|
| `tests/test_autonomous_swe.py`、`tests/test_autonomous_sandbox.py`、`tests/test_autonomous_baselines.py`，配置真实冻结 upstream 路径及解释器 | 30 passed，33.04 秒 | 原生 parser/editor/submit、公共测试及 timeout/管道退出码、跨 checkpoint 完整历史；真实 MindSpore CPU 前向/梯度；隔离边界；原版 `MatchAgent.run`、全部六组件重跑；单 coding 会话超过八次调用、无阶段配额；真实思考字段回传、缓存传输兼容；provider工具调用原样交原生parser；MatchFix空/截断回复不新增调用；无工具角色不收到工具能力说明 |
| `git diff --check` | 通过 | 本轮实现改动的空白错误检查 |

这些是实现与隔离验证，不是修复成功率实验。新实验的接受率、自主分类和定位表现以独立运行目录的结果为准。

## 其他 baseline 的实现、环境与证据

下表补充迁移转换器与 JAX 条件。它们覆盖不同任务：自动转换器负责将输入程序转换到目标框架，修复 agent 还要主动改变有缺陷的程序语义。实际评估应保留这一目标差异。

| 条件 | 已实现内容和完整性 | 当前环境及冻结来源 | 可核对结果和限制 |
|---|---|---|---|
| T-CTE / CodeTransEngine | `run_t_cte.py` 实际构造 gRPC `TranslationRequest` 并提交服务，单次生成 native MindSpore；服务采用 translation-only 补丁，无单元/模糊测试时跳过测试附加 | CodeTransEngine `e97e4ff0974774e67216b11da20b39d476b3a1e3`；正式 runner `4508d0e`；历史服务 `127.0.0.1:50053`。当前未观察到服务进程，`mstorch` 未安装 intertrans/grpcio，重新执行需要恢复记录中的客户端/服务环境 | [正式 summary](../data/experiments/05_experiment_E_track_a_rerun/final/T-CTE/formal_4508d0e_no_token_cap_5x3_20260906/summary.json)：8/15 strict，12/15 training。两个 CNN 的无效生成参数被原记录误标环境问题；最终汇总已计为候选失败。token 估算字段不能当 provider 精确用量 |
| InterTrans | 服务器有冻结完整上游源码 `external_baselines/InterTrans-84d2d43`；现有 T-CTE 只使用直接翻译接口，没有证明运行完整多路径、中间语言与测试搜索 | `84d2d4337dc82d848772cf834440ba17497b7683` | 未发现可单列的完整 InterTrans 修复/搜索结果；不得把 T-CTE 8/15 改名为完整 InterTrans |
| T-MSA / MSAdapter | 正式 runner `5261529` 对五个 PyTorch 源程序统一替换 import；每任务一个候选、三个种子，零 LLM、无修复循环；另有记录在案的通用 CPU 兼容补丁 | MSAdapter v0.6.0，commit `0a6d11d6d00243141e2bdd01f086782b37b49a21`；`mstorch` 当前安装 MindSpore 2.7.2、MSAdapter 0.6.0 | [正式 summary](../data/experiments/05_experiment_E_track_a_rerun/final/T-MSA/formal_patched_5261529_5x3/summary.json)：15/15 training、0/15 strict，指标实际可测。不是当前环境缺依赖导致的 0/15 |
| T-X2MS / X2MindSpore | 有输入准备、转换命令/WSL模板、候选发现与独立验收 wrapper；正式归档只完成五个输入准备，没有实际转换结果 | runner `d5f75ac`；当前服务器仍未发现 npu-smi 或检查过的 Ascend 安装目录 | [阻断记录](../data/experiments/05_experiment_E_track_a_rerun/final/T-X2MS/summary.json)：0 个可测条件、计划15；缺少驱动/CANN/MindStudio/转换程序的原始记录明确，接受率为 n/a |
| C-Ivy | `track_c_external.py::_ivy_one_step` 实际调用 `ivy.transpile`，同步原始模型参数，用 Flax NNX/JAX 梯度与 Optax 执行一步训练；不人工修复转换产物 | `/media/main/whj/venvs/trackc_ivy/bin/python`；当前 Ivy1.0.0.5、JAX0.4.35、Flax0.8.5、Optax0.2.4 | [固定 JAX 快照](../data/paper_figures/jax_original_instances.csv)：0/6。对应归档的 clean gate 可通过，故障候选部分执行/前向通过，梯度/更新未达最终条件。旧 `ebc6c67` 探索版本曾出现 `pt_weight` clean-gate 错误，不能覆盖正式快照 |
| C-torch2jax | 实际调用 `torch2jax.t2j(model)` 与参数转换，使用 `jax.value_and_grad`、`optax.sgd`；单次原始转换、无 LLM 或修复 | `/media/main/whj/miniconda3/envs/torchax311/bin/python`；当前 torch2jax0.1.0、JAX0.10.2、Optax0.2.8 | 同一固定 JAX 快照0/6。输入包含错误参数调用、输出缩放或 detach，转换器会保留输入语义；这些结果不能等同于自主修复 agent 的能力上限 |
| C-Direct / C-Hier | `run_track_c_baselines.py` 调用同一 `TorchaxCandidateFixer`；Direct为一次盲修复，Hier获得阶段反馈且最多三轮 | `data/paper_figures/README.md` 指定仓库快照 `3352f71`；内嵌结果有各自实际运行 commit | 固定快照5/6与6/6；成功均在首轮，但预算不同。Hier提示明确给定TorchAX初始化/设备移动责任及阶段信息，未评估从完整未知故障自主分类定位 |

MSAdapter 需要特别按版本读取实现。本地当前 `run_t_msa.py` 还包含把 `CrossEntropyLoss(reduction="mean")` 改成 `sum` 的包装；本次逐一核对了服务器 `git show 5261529:.../run_t_msa.py` 和正式 `raw/image_mlp/workspace/candidate.py`，正式候选只有 import 替换，不含这个包装。后加实现不能用于解释旧 0/15 的原因；新运行应避免无记录地继承会改变数学语义的兼容层。

JAX 的 24 行结果保留在 `jax_original_instances.csv`，原始记录可从实验仓库的 `3352f71:experiments/baselines/track_c/` 读取。该 snapshot 包含各方法运行 commit；其中顶层汇总的生成 commit 为 `6889058`，快照 commit 与运行 commit需要分开记录。服务器其他 worktree 有 Direct4/6、Ivy clean-gate失败等较早结果，不能替换论文固定的5/6和0/6。Ivy与torch2jax的两个执行故障没有后续测量，按当前报告规范应显示 n/a；旧 CSV 的逐阶段 failed 字段须结合 `observed` 和原始 JSON 解释。

本次检索到的独立外部修复框架仍是 SWE-agent、MatchFixAgent；`r_exec/r_flat/r_hier` 和 Experiment J 的 binary/stage/reverse 是内部反馈消融。T-DIRECT/T-HIER 是迁移工作流，C-Direct/C-Hier 是 JAX 修复条件。已有命名及用途应保留，避免把同一 Fixer 的不同反馈包装累加为更多独立 baseline。

可用于自身框架的通用机制包括：采用 SWE 的可执行复现、修改后重测和提交前实际 diff 复查；采用 MatchFix 对控制流、数据流、接口、库调用、异常和规格的互补审查；由 Verifier 根据工具证据决定哪些假设值得继续追查，再把证据交给 Fixer。共享总调用账本应覆盖这些分析成本。证据 memory 可记录假设、反证测试、真实观测、代码版本及失败修改，但只属于自身组件，并单独消融。上述机制均无需提供故障类别、指定修复符号、预先选好的 API 或健康目标代码。
