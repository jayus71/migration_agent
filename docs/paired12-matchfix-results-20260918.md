# Paired12: 精简 v4 与 MatchFixAgent

24 条条件已全部完成。两方法使用相同的 12 个公开原生 PyTorch 工作负载、目标候选、完整故障适配库和公共契约，接受判定沿用各例的原单元检查。主方法是已合入实现仓库 main 的精简 v4，提交 `694f6920ac89de66492d556e00dacb42fcd47154`。模型请求统一为 `deepseek-v4-flash`，返回的模型标识为 `deepseek-flash`。

| 方法 | 接受 | 第 1/2/4 次累计接受 | 调用 | 总 token | 每接受 token |
| --- | ---: | --- | ---: | ---: | ---: |
| 精简 v4 | 12/12 | 7/12/12 | 225 | 6,642,603 | 553,550.25 |
| MatchFixAgent 完整上游编排，共享 DeepSeek 工具后端 | 11/12 | 11/11/11 | 449 | 14,505,833 | 1,318,712.09 |

两方法共同接受 11 例，精简 v4 另外接受 `task_011`。MatchFix 在这例用完 40 次请求后仍有 TypeError；该失败保留在 12 例分母和全部成本中。精简 v4 的总 token 为 MatchFix 的 45.8%，每接受修复的 token 为其 42.0%，后者比值约为 2.38。MatchFix 在第一次外部提交时接受更多实例；精简 v4 在第二次提交时完成全部实例。一次外部提交可以包含多个上游角色和工具调用，不能据此外推内部步骤更少。

这组结果支持小幅接受数收益和较低 token 成本。12 个工作负载来自同一种公开接口形态，不能替换 Fixed50 的完整 50 例结果，也不用于估计所有故障类型上的优势。

## 程序对与预算

原 Fixed50 的 50 份公开输入均无独立 `source.py`。准备器扫描所有公开候选，选出其中全部函数都由单一 `torch4ms.default_env()` 包裹的 12 个工作负载，机械去除适配环境与 import，保留函数签名、PyTorch 调用和参数。这建立了新的原生工作负载协议 `public-native-workload-paired12-20260918`。12/12 源程序通过原生前向和梯度预检；源程序属于新生成的公共参考，不是恢复出的历史原文件。

两方法每例共享同样的总预算：40 次请求、120,000 输出 token、1,800 秒、最多四次外部提交、每次最多 16,384 输出 token。精简 v4 每阶段最多八次调用；MatchFix 保留上游调用结构，只有共享总预算。原 MatchFix `66a52a5` 的六种语义分析、TestGenRepair、Verdict、提示和解析器均保留；实际每例执行到哪一阶段由上游控制流及共同预算决定。

MatchFix 接收完整公开 `source.py` 与 `candidate.py`。`ground_truth_target_function` 为空，未提供健康目标实现、私有故障类别或预选修复位置。原 Claude/Codex CLI 由共享 DeepSeek 工具后端替代，这一适配身份随结果一并报告。

## 核验与产物

主任务离线审计逐条核对全部 674 个独立 provider 响应、请求模型、输入/输出/总 token 与控制器账本，未知 usage 为 0。24 条条件的初始生产代码及不可变 source/task 均与准备输入一致；冻结实现逐文件散列与清单一致。审计没有调用模型或修改候选。

- 远端原始结果：`/media/main/whj/projects/torch4ms/paired12-matchfix-20260918-v1`。
- 本地结果与账本：`output/paired12-matchfix-20260918-v1/paper_results.json`、`paper_results.csv`、`usage_ledger.json`。
- 离线审计程序：`scripts/audit_paired12_results_20260918.py`。
- 原始证据包：`output/paired12-matchfix-20260918-evidence.tar.gz`，SHA-256 为 `ebbb3adaf47fe29b164ff3f5cd94918e12e7641d1f776b3c95e7a3b84c630657`。远端与本地哈希一致；包中排除凭据配置和 Python 缓存。

来源筛选与机械转换的详细记录仍保留在独立 worktree `/home/jayus71/code/migration_agent-matchfix-source-pairs-20260918`，报告为 `docs/matchfix-source-pairs-20260918.md`。原始 pilot 属于本次 24 条矩阵，未重复计算。
