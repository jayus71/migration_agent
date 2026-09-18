# JAX 主文实验自主流程复跑

正式 `formal_v5` 的 12 个 LLM 条件全部结束。当前自主流程与 Direct 控制均修复六个初始失败候选，全部在第一个提交 checkpoint 通过三种子验收。该六例中两方法接受结果一致，Direct 的 token 用量和耗时更低。

| 方法 | 接受 | 首轮接受 | API 调用 | 总 token | 每接受 token | 每接受秒数 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 自主 Verifier / Fixer，v4 evidence | 6/6 | 6/6 | 76 | 674,009 | 112,334.8 | 302.7 |
| Direct shared-tools 控制 | 6/6 | 6/6 | 57 | 353,311 | 58,885.2 | 137.2 |
| Ivy 原生转换 | 0/6 | 0/6 | 0 | 0 | n/a | n/a |
| torch2jax 原生转换 | 0/6 | 0/6 | 0 | 0 | n/a | n/a |

自主流程分别使用 624,463 输入 token 和 49,546 输出 token；Direct 为 309,997 和 43,314。两方法总耗时分别为 1,816.379 和 823.218 秒。模型请求名固定为 `deepseek-v4-flash`，133 次原始响应均返回 `deepseek-flash`。原始响应复算与各条件账本完全一致，未知 usage 为零。成本包含调查、修复及所有格式无效的结束报告。

最终审计核对了 12 个终态补丁、全部冻结文件和 36 个最终种子检查。12 份终态代码的 AST 均与原健康目标实现一致；36 次检查均观测到 `JittableModule+jax_value_and_grad+optax.sgd` 及真实 `jax.Array`，初始参数与参考完全一致。最终最大损失差为 `1.1920928955078125e-7`，梯度范数差为 `1.5104204775795438e-8`，参数更新相对 L2 差为 `1.1934221092617947e-6`。五次修复阶段的结束报告为 `invalid_final`，另七次为 `completed`；五次均已应用有效补丁并通过外部验收，原始状态没有改写。

全部 118 个目标测量另行完成初态审计：88 个包含可比较的向量，30 个缺失向量记为 unavailable。修复方法的 50 个接受测量（含中间公开测试和最终复验）全部精确匹配参考初态。60 个接受测量中另外四个转换器健康 gate 缺少 `initial_vector`，其初态一致性保持 unavailable；其余六个是 TorchAX 健康控制。

最终结果位于 `formal_v5/final_analysis/`：`summary.json`、逐响应成本核对 `comparison.json`、`initial_states.json`、`final_patch_audit/` 内的 12 份补丁与审计、交叉核对结果 `final_checks.json`。本地副本位于 `output/maintext-jax-autonomous-20260918/final_analysis/`。

## 协议与来源

原始六例来自实现仓库 `3352f719636d0fd9eda6dcff2dc4578863ab542e`：MLP、CNN 各包含执行、前向、梯度故障。旧 `c_hier` 由控制器给出 `predicted_layer`、候选文件位置和专门的初始化／设备约定；`c_direct` 只接收二元失败信息。前者最多三轮、后者一轮。该记录支持当时条件下的修复结果，未测量当前自主 Verifier 从未知故障收集证据的过程。

新运行直接复制 `progress_v4` 的代码快照和 DeepSeek 配置，保留原六个候选字节、三种子 `6701/6702/6703`、单步 SGD 和 `0.02/0.05/0.03` 阈值。公共 workspace 只包含原始 PyTorch 参考模型、候选、任务合同及 scratch tests。任务名匿名化。故障注入器、类别、历史结果、健康目标实现和参考运行数值保持私有。候选执行器删除 `_reference_model` 的定义，原参考在外部进程计算；候选及自建测试通过 Landlock/seccomp 执行，不能读取完整历史执行器或凭证。程序初始化和设备专门修复提示未加入公共合同。

修复方法为当前 `autonomous_layered` 的 evidence / progress_loop 和现有 `direct_shared_tools` 控制，二者均最多四个提交 checkpoint、40 次调用、120,000 输出 token、1,800 秒，每调用最多 16,384 输出 token；thinking 配置继承 v4。两者均有最多八次调用的只读调查阶段。Direct 随后保留每个修复 checkpoint 两次调用和一次多文件编辑的流程；自主流程每个修复阶段最多八次调用，并进行独立角色交接。实际成本统计包含调查阶段。Direct 的名称指当前直接修复控制，不冒称旧 `c_direct` 或上游独立 agent。系统提示仅将目标运行时名称 `torch4ms/MindSpore` 替换为 `TorchAX/JAX`，其余方法算法、解析和历史保持冻结版本。

Ivy 和 torch2jax 保留 `3352f71` 原生转换调用及健康 clean gate；没有 LLM 修复或算法改动。运行失败后缺失的数值记为 null／n/a。健康 gate 的基础设施错误单列，不记为六次实际修复失败。转换器仍为单次转换，它们的工作性质和 LLM 修复不同。

原协议把已注入故障的候选交给转换器。转换器保持输入语义时也会保留输入故障，因此这组对照测量转换后已有故障是否消失；它没有测量从健康源程序迁移的正确率。保留这组原生结果时必须保留该任务定义。

启动前计划 12 个 LLM 条件、两个 API worker；硬预算上界为 480 次调用、1,440,000 输出 token，实际消耗按每次调用原始 usage 统计。转换器和离线检查不使用 API。

实现为 `scripts/run_maintext_jax_autonomous.py`，五个针对缺失量、非有限数、参数名对齐、参考隔离和任务网格的单元测试通过。第一轮真实离线检查：六个故障均触发、两种模型在三种子上的六个健康检查全部通过。`formal_v1` 的 Ivy 检查发现 virtualenv Python 指向另一 Conda 环境，初版 sandbox 未授权该实际解释器路径；这是新接入缺陷。`formal_v2` 仅为实际解释器运行库增加只读权限并将此类错误单列，原失败记录完整保留。未发生 API 调用。

`formal_v2` 进一步发现 Ivy 在导入编译器时写入当前目录的 `ivy_logs.txt`；不可写导致 Ivy 吞掉导入错误，表面表现为缺少 `ivy.transpile`。`scripts/probe_maintext_jax_ivy.py` 在同一沙箱直接导入编译器，记录了真实 PermissionError。`formal_v3` 将 backend 的 cwd、HOME、XDG_CACHE_HOME 放入每例独立 `.runtime` 临时目录，仍发现 Ivy 通过父目录搜索找到宿主的 `.ivy`。`formal_v4` 使用 Ivy 自身支持的 `IVY_ROOT` 将缓存放在同一独立临时目录。直接导入编译器检查通过。以上修复保持候选及 source 只读约束和网络隔离，没有更改 Ivy 的函数或生成内容。v1/v2/v3 的记录属于接入调试证据，不能作为 converter 性能结论。

远端输出根目录：`/media/main/whj/projects/torch4ms/experiments/maintext_jax_autonomous_20260918/`。每版包含 `manifest.json`、`frozen_hashes.json`、冻结 runner、v4 code snapshot、全部执行记录和初始／终态候选。独立调度器 `scripts/dispatch_maintext_jax_autonomous.py` 在首次请求前保存自身 hash、runner hash、条件网格和并发配置，不允许覆盖旧条件。

`formal_v4` 实际到达 Ivy 代码生成阶段后，发现其原生格式化步骤需要 `ruff`。可执行文件已安装在实际 Conda 环境，但初版 PATH 只包含虚拟环境目录。`formal_v5` 将实际解释器的 bin 目录加入 PATH；不安装新版本或跳过格式化步骤。运行时快照分别保存于 `environment_torchax.json` 和 `environment_ivy.json`。

启动脚本只 source 指定凭证文件、不输出环境变量。当前正式目录为 `formal_v5`，已有条件不得覆盖或重新运行。

`scripts/smoke_maintext_jax_agent.py` 在独立 `offline_agent_smoke` 目录使用假传输验证两种方法的完整条件生命周期。两者均正常完成、保持未修复判定，实际 API 调用为零。假传输轨迹不纳入实验效果或模型成本。主任务提供的初始参数审计脚本已检查 v5 的前 14 个测量：六次接受的 TorchAX 健康测量均与参考初态完全一致；两个接受的 Ivy 健康测量没有 `initial_vector` 字段，初态比较记为 unavailable。

## 离线结果与正式启动

v5 的六个初始故障全部触发，六个 TorchAX 三种子健康检查全部通过。Ivy、torch2jax 均完成六个故障候选，接受均为 0/6，且各自的 MLP/CNN 健康 gate 全部通过。Ivy 候选总耗时 561.935 秒，健康 gate 191.663 秒；torch2jax 分别为 39.234 秒和 15.930 秒。两种转换器实际 API 用量均为零；每接受成本因接受数为零记为 n/a。

2026-09-17 18:30 UTC 左右，主任务通过 `dispatch_parent_review.py` 以两个 worker 启动 v5 正式修复，PID `2829944`。本代理未重复启动。v5 manifest SHA-256 为 `c02524ceefa24abacf65fb281a27e46ef2cbc855c335b90e8fdbff79367193c6`，runner SHA-256 为 `2665bf64c30f5943b44f2e44d9d0a45b80ae8bd5476d7a201d374b6d73e27ead`。

离线过程和正式启动时快照保留在 `output/maintext-jax-autonomous-20260918/preflight-and-startup-snapshot.tar.gz`，本地／远端 SHA-256 均为 `2e5ae6d4fdad12a128eb2ef250504f7d29ea7c6bac31a0b7882c44f947cc5212`。它包含全部接入失败版本、v5 转换器完整原始记录及两个刚启动的 LLM 条件，是启动快照，不是完整 LLM 结果包。

## 最终归档

全部正式 worker 与 dispatcher 结束后，完整证据写入 `output/maintext-jax-autonomous-20260918/maintext_jax_complete_20260918.tar.gz`，大小为 5,883,421 字节，SHA-256 为 `cabff024da637e58471ecc8d530adc3124bda671ef84cd9e2568e15912edb65e`。远端生成后校验和本地下载后流式校验均通过，逐一核对 2,903 个条目的路径、字节数及 SHA-256。清单为同目录的 `final_file_manifest.json`，本地验证记录为 `local_archive_verification.json`。归档保留全部离线失败版本、假传输测试、原生转换器记录、12 条正式修复的全部请求／回复／用量／工具观测／代码快照，以及最终分析和审计脚本。

本次只运行上述六例 JAX 协议及必要接入检查，没有改动论文正文、历史实验或其他正在执行的任务。JAX 相关 11 项现有及新增测试通过，`git diff --check` 通过。
