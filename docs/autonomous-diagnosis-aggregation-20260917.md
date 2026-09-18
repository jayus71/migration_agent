# 自主诊断评估的聚合口径

`scripts/aggregate_autonomous_diagnosis.py` 聚合独立评估目录中的两阶段 DeepSeek 评分。脚本只读评估记录、匿名映射和冻结 rubric，不调用模型，不读取修复是否成功，也不将评分反馈给修复 agent。输出沿用 `LLM-assisted exploratory assessment; not independent human blind review` 标记。

每个来源运行、评分配置和方法形成一个统计组。独立案例输出目录中的相同评分配置会合并；脚本对完整 `evaluation_manifest.json` 计算配置 ID。不同评分配置分开保留。同一配置下重复的条件明确报错，重复指定同一个根目录只读取一次。

每个组始终采用 50 个任务、38 个主要机制/位置任务和 12 个契约依赖任务三个固定范围。正文 `primary_report` 与辅助推理 `auxiliary_recorded_reasoning` 分别计数。机制和因果位置的可评分分母是 38；12 个契约依赖任务的这些评分轴为 `not_scorable`，其私有参考一致性单列。所有六个评分状态分别报告，`partial` 不折算为成功。

未执行、dry-run、缺失证据、schema 错误、运输错误、截断和进行中的案例保留为未评分，不放进 `incorrect`。JSON 同时报告固定范围的评分覆盖、每轴已评分条件中的正确比例，以及完整固定范围的正确比例。固定范围尚未评完时，后一项为 `null`；契约任务的机制/位置可评分分母为零，比例也为 `null`。因此中途结果不会通过删除未完成条件变成完整诊断准确率。

成功记录在进入统计前重新核对两个评分文件的哈希、公开输入和私有参考的指纹、两阶段实际请求之间的一致性、原句引用、通道归属和逐轴评分约束。校验失败记 `assessment_integrity_error`，已有评分调用成本仍保留。运行状态以读取时刻的落盘文件为准；要形成最终结果，应在相关评分进程结束后再生成一次报告。

2026-09-17 的离线审计发现，v3 的原文片段编号依赖导出包中字典的插入顺序，而 API 请求的序列化按键排序。旧聚合器从排序后的请求重建编号，误拒绝了 97 条内容不变的评分。修正后从原始冻结导出包重建完整公开 payload，再与实际请求精确核对。原请求、原文片段 ID、评分、两阶段约束均不改写，也不调用 API。原记录的 129 条两阶段成功均通过校验；其中一个 v2 pilot 与 v3 对应同一修复条件，因此不能把 129 直接作为不同修复条件的分母。修正后 14 项聚合测试通过，包含字典顺序回归与导出证据篡改拒绝。

调用成本只来自评估阶段记录，包括失败和未完成调用。分别累加已知 prompt、completion 和 total token，并报告每个字段未知的调用数。任意已尝试调用缺失某字段时，该字段的完整总量为 `null`，已知部分仍可查。脚本不根据已知字段推算缺失字段，不估算货币成本，也不混入修复调用成本。

## 使用

每个案例独立输出可通过共同父目录发现，无需列出数百个目录：

```bash
python scripts/aggregate_autonomous_diagnosis.py \
  --assessment-parent /path/to/evaluator/assessments \
  --evidence-export /path/to/evaluator/exports/formal_v3 \
  --evidence-export /path/to/evaluator/exports/progress_v4 \
  --evidence-export /path/to/evaluator/exports/repair_window_v5 \
  --rubric data/audits/fixed50-private-diagnosis-rubric-20260917.json \
  --output /path/to/evaluator/reports/diagnosis
```

`--assessment-root` 可重复指定单个评分输出目录。增量导出的旧包也要保留并传入，脚本用评分 bundle 中记录的映射哈希寻找对应导出包。输出为私有 `.json` 和 `.md`，包含任务与方法映射；输出位置须在证据包和修复运行目录之外。该报告不能发送给仍在执行的修复 agent。

## 验证

2026-09-17 执行 `python scripts/test_aggregate_autonomous_diagnosis.py`，12 项离线行为测试通过。测试覆盖固定分母、正文与辅助推理分离、契约依赖任务、独立案例输出合并、未评分与未知成本、部分评分单列、重复条件拒绝、评分版本分组、成功产物完整性、两阶段参考一致性，以及输出位置保护。测试使用模拟 provider 响应，没有真实 API 调用。

现有八条件 dry-run 也成功聚合为五个方法组，保留八条未评分记录，API 尝试为零。验证输出是 `output/autonomous-verifier-20260917/diagnosis-aggregation-dry-run-check.json` 和同名 Markdown；该输出只验证聚合行为，不包含实测诊断分数。
