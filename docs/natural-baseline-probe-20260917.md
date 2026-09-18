# I-08 / I-09 自然迁移案例的基线追踪

本次四个条件都在首个 checkpoint 自行生成并运行了训练行为测试，发现了前向 loss 接近、部分梯度或参数更新错误。SWE-agent 和 MatchFixAgent 均能发现这两个自然案例中的反向问题；本次记录不支持把它们画成只检查执行、完全漏检的基线。四个条件在本次预算内均未修复通过。

| 自然案例 | 方法 | 首轮实际检测 | 最终结果 |
|---|---|---|---|
| I-08 | SWE-agent 1.1.0 | 对齐初值比较更新，再比较梯度；用简化网络定位到 Tanh 切断前层梯度 | 4 个 checkpoint 用尽，未改生产代码 |
| I-09 | SWE-agent 1.1.0 | 自建测试发现前六个参数不更新，仅 head 更新；进一步测得前层梯度为零 | 4 个 checkpoint 用尽，未改生产代码 |
| I-08 | MatchFixAgent + DeepSeek 工具执行适配 | 实际梯度对比测得 encoder.0 的源梯度非零、目标梯度为零 | 返回并应用了显式传递 backward 上下文的补丁，指标未改善 |
| I-09 | MatchFixAgent + DeepSeek 工具执行适配 | 实际更新对比测得源端八参数均更新、目标端仅 head 两参数更新 | 返回并应用了显式参数与梯度写回补丁，指标未改善 |

## 实际测试证据

I-08 的 MatchFix 测试采用相同初始参数和输入。实际 shell 输出为：

```text
encoder.0.weight native_norm=3.422239e-01 cand_norm=0.000000e+00 close=False
encoder.0.bias   native_norm=1.094964e-01 cand_norm=0.000000e+00 close=False
```

同一测试的 encoder.2、decoder、head 梯度逐元素接近。源端 loss 为 1.5309827327728271，目标为 1.5309813022613525。见 [测试源码](../data/audits/natural-baselines-20260917/I-08/r_matchfix/first_detection_test.py) 与 [真实命令和输出](../data/audits/natural-baselines-20260917/I-08/r_matchfix/first_detection_evidence.json)。

I-09 的 MatchFix 自建测试运行后输出：

```text
cand param changed: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0007000007, 0.0006999969]
src param changed:  [0.0007000044, 0.0006999997, 0.0006999997, 0.0007000007,
                     0.0006999969, 0.0007000000, 0.0007000007, 0.0006999969]
loss diff: 1.5497207641601562e-06
```

这里的 loss 来自它自建的同步测试，输入初始化细节不同于隐藏验收，因此不与归档的 4.77e-7 混用。见 [测试源码](../data/audits/natural-baselines-20260917/I-09/r_matchfix/first_detection_test.py) 与 [真实命令和输出](../data/audits/natural-baselines-20260917/I-09/r_matchfix/first_detection_evidence.json)。

SWE 首轮也执行了对应比较。I-08 首轮推理明确写出 “Tanh breaks gradient flow to preceding layers”，随后检查 torch.tanh 返回普通 torch.Tensor 的行为。I-09 首轮实际打印各参数更新量和梯度，再用简化模型定位断点。其测试源码、命令输出和全部首轮推理摘录保存在对应 [I-08](../data/audits/natural-baselines-20260917/I-08/r_swe/first_detection_evidence.json) / [I-09](../data/audits/natural-baselines-20260917/I-09/r_swe/first_detection_evidence.json) 目录。

## 修复与验收

四条件均保持真实 torch4ms/MindSpore 求导，没有退回纯 PyTorch；源程序、普通测试及任务配置的 hash 均未改变。新的目标后端检查记录了受评估模型的 MindSpore 反向执行。参数数值验收仍然失败：

| 案例 | 初始及最终 loss 差 | 初始及最终梯度范数差 | 初始及最终更新相对差 |
|---|---:|---:|---:|
| I-08 | 1.4305e-6 | 0.045961 | 0.771127 |
| I-09 | 4.7684e-7 | 0.418632 | 0.925266 |

MatchFix 的两个合法结构化修复代码都已正式应用后重验。I-08 给 backward 增加 `inputs` 与 `forward_fn`；I-09 另外尝试把包装参数上的梯度写回模型。两个补丁都没有补充 Tanh / GroupNorm 的适配映射，修改的上下文/写回机制没有消除实际错误。I-09 最后 verdict JSON 存在格式错误，但 test/repair JSON 合法，其补丁已独立应用并验证失败；格式错误不承担这里的功能失败结论。

SWE 的退出状态都是 `exit_cost` 或 `submitted (exit_cost)`，这是调用预算终止及自动保存，不是模型声明已经修好。续跑只基于它自身的预算终止状态及已有轨迹，未以隐藏验收失败催促。后续 checkpoint 只收到上一段轨迹末尾 24,000 字符，长文件输出挤掉了更早的 Tanh 定位，出现重复检查。因此后续修复记录属于有上下文截断限制的探索运行，不能用来做修复能力排名；首轮自主发现的结论有完整真实测试支撑。

## 协议与归档

冻结输入来自原始 `8c5c635b0c5c718fab052b885966be8980eea6ad`、`runs_real_core_v3` 的 I-08/I-09。没有重新翻译、注入故障或重跑 LaDiM。新远程分支为 `codex/natural-baselines-20260917`，原主仓库的未提交工作保持不动。

模型为 deepseek-v4-flash，温度 0.1。基线能读完整 source/candidate/私有适配层；普通测试仅输出执行情况和 loss，没有提供梯度异常、缺失算子或分层诊断。隐藏同步验收及报告放在 agent 工作区外，轨迹未读取它们。shell 工具沿用本地执行能力，未增加 OS 级沙箱；agent 使用了各自的 `/tmp` 测试脚本，实际脚本路径没有跨条件同名冲突。

MatchFix 保留上游六类语义分析、角色提示、格式解析及 verdict，用 DeepSeek shell 工具循环恢复历史 wrapper 缺失的真实读写/测试能力。它应标记为“MatchFixAgent + DeepSeek 工具执行适配”，区别于历史单次 chat wrapper 和原版 Codex/Claude Code 后端。本次结果不并入原始 50 实例统计。首次启动缺少 Graphviz PATH 的基础设施记录单独保留，不算方法失败；其中已产生的部分 API 调用不计入下面正常运行的 token 合计。

| 案例 | 方法 | 正常运行总 token |
|---|---|---:|
| I-08 | SWE-agent | 1,139,623 |
| I-09 | SWE-agent | 1,538,339 |
| I-08 | MatchFix 工具适配 | 349,560 |
| I-09 | MatchFix 工具适配 | 554,247 |

机器可读结果、初始和最终候选、补丁、真实测试及后端验收位于 [summary.json](../data/audits/natural-baselines-20260917/summary.json)。完整轨迹在 `tmp/natural-baselines-20260917/results/`，压缩归档及其 SHA-256、远程全量路径在 summary 中。完整执行细节见 [PROTOCOL.md](../data/audits/natural-baselines-20260917/PROTOCOL.md)。
