# 修复依赖图规划消融证据

Repair Dependency Graph Planning（修复依赖图规划）的两个新增消融运行已结束。完整方法复用前次 Repository Structural Analysis（仓库结构分析）消融的两项 full 结果。冻结实验路径与配置标识保持原样；具体边界和结果分析见[实验报告](../../../docs/work-unit-planning-ablation-20260922.md)。

时间序列两条件均完整接受 69/69；关闭规划在首次提交接受，端到端 token 为 1,803,551，比完整方法少 15.2%。推荐关闭规划最终为 130/145、未完整接受，端到端 token 为 9,213,723，比完整方法少 7.5%；其四次提交通过项为 128、103、133、130，最后一次耗尽 480,000 输出 token。完整方法最终为 131/145，同样未完整接受。报告采用最后一次结果，保留所有中间结果与缺测。

- `protocol.json`、`freeze.json`：新增运行的冻结定义、预算、输入与代码哈希。
- `offline.json`、`reuse_consistency.json`：56 项启动前离线检查、五项复用检查及 CPU 放置差异。
- `reference_origins.json`：两项完整方法来源、原结果与协议哈希，以及原始映射消融归档的哈希。
- `summary.json`、`summary.csv`：四项结果，明确标记复用记录；JSON 账本分开记录新增与历史费用。
- `progress_and_usage.json`：每次外部提交的通过与未测项目、累计调用及 token、实际工具事件计数与修改路径。
- `audit.json`：146 项最终审计全部通过，包括逐调用请求哈希与费用、冻结输入和代码、消融状态，以及复用证据和初译生成状态的原字节比较。
- `verification.json`、`runtime_versions.json`：本次重验的 20 项机制测试和一项费用分账测试，以及与复用来源一致的实测软件版本。
- `launch.json`、`scheduler.json`、`collection.json`：原始调度、两个正常退出的进程及完整归档哈希。

新增费用为 90 次调用、10,485,245 token，输出 534,855 token，未知 usage 为零。复用结果的 110 次调用和 11,556,374 个修复 token 单独计入历史账本；新增完整方法调用及新增初译调用均为零。200 组原始请求、metadata 和响应全部与控制器账本对应。

完整归档为本地 `output/work-unit-planning-ablation-20260922/evidence.tar.gz`，SHA-256 为 `baf213e9db54fe924f0c25513a108bd8dd503f968e6f2f5ec7e12b6499622afc`，大小 146,061,249 字节。解包位置为同目录的 `runtime_snapshot/`。远端副本为 `/media/main/whj/projects/torch4ms/ascend-torch4ms-unit-planning-ablation-20260922/evidence.tar.gz`。

在仓库根目录复查完整归档与原始复用来源：

```sh
python3 scripts/audit_work_unit_planning_ablation.py output/work-unit-planning-ablation-20260922/runtime_snapshot --reference-snapshot output/repository-map-ablation-20260922/runtime_snapshot --output output/work-unit-planning-ablation-20260922/audit.json
python3 scripts/analyze_repository_map_ablation.py output/work-unit-planning-ablation-20260922/runtime_snapshot/experiments/work_unit_planning_ablation_20260922/results --conditions full no_work_unit_planning --output output/work-unit-planning-ablation-20260922/trajectories.json
```

这些命令只读取已完成的结果，不调用模型或重新执行评估。检查分母 69 与 145 描述两个仓库内部的候选完成程度；每个条件的完整仓库接受分母为二。
