# Experiment J 本地结果索引

本目录的正式入口是 [`formal_run_2d6bd3d/`](formal_run_2d6bd3d/)。当前视图包含六个条件、每个条件 50 个 canonical 实例：

- `r_exec`：只检查并反馈执行结果；
- `r_binary`：检查 E/N/G 后仅向 Fixer 提供一个总 pass/fail 位；
- `r_stage`：仅提供第一个失败阶段标签；
- `r_flat`：提供无序的完整 E/N/G/U 指标，不做 first-failure 路由；
- `r_hier`：execution → numerical → gradient/update 的完整层级反馈；
- `r_reverse`：信息量与路由相同，但按 gradient/update → numerical → execution 呈现。

## 当前正式视图

`r_exec/r_binary/r_stage/r_flat` 来自首个六条件正式运行；`r_hier/r_reverse` 使用第三轮独立确认结果。顶层 `manifest.json` 的 `assembled_condition_sources` 记录了这一映射。

| 条件 | Strict | Repair@1 | Repair@2 | Repair@4 | Tokens |
|---|---:|---:|---:|---:|---:|
| `r_exec` | 33/50 | 64% | 64% | 66% | 235,952 |
| `r_binary` | 34/50 | 64% | 68% | 68% | 747,802 |
| `r_stage` | 34/50 | 64% | 66% | 68% | 628,216 |
| `r_flat` | 34/50 | 64% | 68% | 68% | 430,400 |
| `r_hier` | 48/50 | 72% | 88% | 96% | 327,312 |
| `r_reverse` | 48/50 | 70% | 82% | 96% | 304,188 |

## 三轮顺序复核

| 轮次 | R-HIER | R-REVERSE | Reverse 相对差值 |
|---|---:|---:|---:|
| 1 | 44/50 | 49/50 | +5 |
| 2 | 47/50 | 46/50 | -1 |
| 3 | 48/50 | 48/50 | 0 |
| 合计 | 139/150 | 143/150 | +4 |

reverse 的点估计优势没有跨轮稳定复现。论文可据此主张完整结构化反馈优于粗粒度反馈，但不能宣称正序或反序已被证明更优。

主要文件：

- [`summary.md`](formal_run_2d6bd3d/summary.md)：人类可读六条件汇总；
- [`summary.csv`](formal_run_2d6bd3d/summary.csv)：绘表用统一字段；
- [`summary.json`](formal_run_2d6bd3d/summary.json)：机器可读指标与 provenance；
- [`manifest.json`](formal_run_2d6bd3d/manifest.json)：300 条运行记录及条件来源；
- [`prompt_templates.md`](formal_run_2d6bd3d/prompt_templates.md)：六种反馈契约的可读对照。
