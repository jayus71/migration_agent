# 自动仓库映射的单因素配对消融

四项运行已完成：两个固定仓库，各比较完整方法与仅关闭自动结构映射。所有条件保留工作单元规划、聚焦、检查点、独立调查与交接、证据及上下文管理。具体定义与后续规划消融设计见 [实验报告](../../../docs/repository-map-ablation-20260922.md)。

- `protocol.json`、`freeze.json`：启动前冻结的对照定义、预算、代码和输入哈希。
- `offline.json`：42 项启动前检查，零模型调用。
- `summary.json`、`summary.csv`：四项完整结果、调用和费用账本。
- `progress_and_usage.json`：各次外部提交的固定分母进展、实际工具调用和改动路径。
- `audit.json`：129 项最终检查全部通过，包括源与任务、初译、运行代码、原始请求哈希、所有调用费用、预算以及 no-map 的系统提示与返回内容。
- `historical_tool_usage.json`：先前累计消融完整条件的唯一工具事件统计，与本轮结果分开。
- `runtime_versions.json`、`launch.json`：实际软件版本和持久进程启动位置。
- `collection.json`：完整证据归档 SHA-256 与大小。

本轮新增 232 次调用、20,847,811 token，输出 795,902 token，未知 usage 为零；未重新生成初译。原始请求、响应、工具事件、候选与验收材料位于本地 `output/repository-map-ablation-20260922/runtime_snapshot/`，完整压缩包为同目录上一级的 `evidence.tar.gz`。远端副本为 `/media/main/whj/projects/torch4ms/ascend-torch4ms-map-ablation-20260922/evidence.tar.gz`。

归档 SHA-256 为 `1bee1bd9551d5b6b88fa1cc3ada483f9a93792de00fb2dabc56ccca17699e3e1`，大小 126,888,468 字节。归档中的实验记录相对路径为 `experiments/repository_map_ablation_20260922/results/`。

复查命令（在仓库根目录）：

```sh
python3 scripts/audit_repository_map_ablation.py output/repository-map-ablation-20260922/runtime_snapshot --output output/repository-map-ablation-20260922/audit.json
python3 scripts/analyze_repository_map_ablation.py output/repository-map-ablation-20260922/runtime_snapshot/experiments/repository_map_ablation_20260922/results --output output/repository-map-ablation-20260922/trajectories.json
```

每个条件各接受一个仓库（1/2）。时间序列均通过 69/69；推荐均为 131/145，未通过完整验收。完整映射在时间序列费用较低，在推荐费用较高。一次配对测量不足以估计重复间变动；冻结协议记录了再做两轮完整配对的建议，目前未调度追加运行。
