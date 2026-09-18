# 首次生产编辑前的诊断证据导出

[`export_autonomous_diagnosis_evidence.py`](../scripts/export_autonomous_diagnosis_evidence.py) 将 Fixed50 `formal_v3` 的已有日志整理成待审阅包。它只读实验文件，不运行模型、候选程序或验收器，也不读取私有 rubric。评分依据仍为已冻结的 [Fixed50 协议](autonomous-fixed50-protocol-20260917.md)；导出器不判断机制正确性，不从最终补丁推断先前诊断。

支持共享工具条件 `autonomous_layered`、`autonomous_layered_native`、`autonomous_category_ablation`、`direct_shared_tools`，以及实际原生 `swe_native_isolated`。原始轨迹、初态、运行代码和已冻结协议均保持原样。运行中的条件暂不导出，跳过原因写入私有映射；完整结果到齐后，在新目录重新导出全量。

## 输出与使用

```bash
python scripts/export_autonomous_diagnosis_evidence.py \
  --run /path/to/autonomous_fixed50_20260917/formal_v3 \
  --output /path/to/review_exports/fixed50_pre_edit_v1
```

输出目录必须不存在，并位于原始运行目录之外。按 `--condition task_001/autonomous_layered` 可选取单个条件，重复该参数可选子集。默认 `--max-chars 0` 完整保留导出文本；设置正数时，对每个字符串应用显示长度上限，同时保存原字符数、保留的半开字符区间和未截断匿名文本的 SHA-256。原日志始终保留完整内容。

| 路径 | 用途 |
| --- | --- |
| `blind/index.json` | 匿名案例索引、边界状态和记录数量 |
| `blind/cases/<opaque-id>.json` | 初态观察、编辑前陈述与工具证据、边界、来源 ID、截断和缺口 |
| `blind/inputs/<opaque-id>/` | 原始公开故障代码和任务说明；同一任务的各条件共用一份副本 |
| `private/mapping.json` | 匿名案例与实际条件、来源文件路径／哈希、导出代码和协议哈希、跳过原因及匿名化密钥 |

独立审阅者只接收 `blind/`。`private/` 由评估负责人保管，用于回查原始证据和后续配对统计。默认随机生成匿名化密钥；需要复现相同匿名 ID 时，可使用私有映射中的十六进制密钥通过 `--key` 传入。新包的案例按匿名 ID 排序。

导出完成时同时写出 `blind/index.json` 和 `private/mapping.json`。执行出错后可能留下未完成的目录；保留错误记录，并使用新目录重试，不把缺少这两个文件的输出当成完整包。

## 编辑边界如何恢复

共享工具条件按 `event_*` 顺序寻找首个成功的生产编辑交易，要求 `candidate.py` 或 `torch4ms/**/*.py` 的 `before_sha256` 与 `after_sha256` 确实不同。scratch 修改、失败编辑和无字节变化的编辑不触发冻结。导出停止在该编辑结果之前；触发该交易的模型回复已经在执行前产生，因此保留其中的自然语言陈述与已记录推理。该回复内的编辑参数、拟议 diff、实际编辑结果及之后所有观察均不进入审阅证据。

脚本核对首次编辑的旧文件哈希与初态，并检查 `after_diagnosis` 的生产快照。发现此前已有未解释的变化时记 `missing_artifact`，最多保留独立核对过的诊断阶段。共享工具日志没有每个任意工具执行后的全树哈希，瞬时写入后复原等行为不能由现有日志完全排除；包中逐例保存这一记录粒度限制。

原生 SWE 优先使用已有 `swe_event_*_first_edit.json`。它由每个 native step 前后的生产树哈希变化触发，保存 `history_before`、触发步和该步原始模型回复。导出器保留 `history_before` 与触发模型回复的自然语言部分；不读取触发步的测试输出作为编辑前证据，也不复制该步的 shell 命令或后续历史。这个边界精确到一次 native step；一条 shell 命令内部多个动作的先后时刻未单独记录。

没有首次编辑记录时，脚本要求初态与最终生产快照一致，才导出完整未编辑过程并标为 `no_recorded_production_edit`。该状态表述已有日志及端点检查，不宣称排除了所有不可见瞬时变化。SWE 的未编辑过程来自已提交 checkpoint history；生产树发生变化而缺少相应边界时，脚本保留缺口，不根据最后补丁猜测修改时点。

## 模型陈述与证据限制

`assistant_statement` 是模型实际回复正文，`explicit_report` 是冻结点前记录的报告。`recorded_reasoning` 与 `recorded_reasoning_auxiliary` 来自 provider 保存的 `reasoning_content`，保留渠道区别，不自动当作已提交的结构化诊断。原生历史不一定保存该字段，因此辅助记录通过工具调用 ID 匹配到已冻结的 action；未编辑完整 episode 也允许用非空正文精确匹配。辅助记录附有对应的历史下标，其在导出列表末尾的位置不代表发生在触发编辑之后。匹配不上的推理不补写进历史。

评审只评价已明确表达的机制及所引证据。补丁动作、代码提案中的偶然文件名和修复后的成功结果都不能替代先前的诊断。类别字段仍可选，导出器不因缺失类别生成错误。

工具分页和可见内容边界记录在 `source_limits`：包括读取行区间、总行数、`next_line`、搜索／列表的 `next_offset`、输出中已有的截断标记，以及恰好达到已知 stdout 长度上限的情况。provider 的 `finish_reason=length` 单独记录；请求元数据保留原始／准备后字符数、是否压缩和请求哈希。导出器不会用未展示的源码行补充模型当时的观测，也不会把上下文压缩后丢失的内容伪称为后续请求仍然可见。

## 匿名化的范围

显示包移除系统提示和方法特有的流程要求，将实验绝对工作区、条件路径、原匿名任务号和显式方法名称替换为稳定占位符。公开初态代码按原字节复制并保存哈希；原始模型回复和工具输出也保持原文件，通过私有来源映射回查。显示层只改变标识信息及用户明确设置的长度上限，不改写诊断含义。

工具名称、角色间交接方式、输出结构和用词仍可能让审阅者推测框架。这里完成的是带方法名称遮蔽的待审阅材料准备；独立盲审和裁决尚未执行，不能据导出成功宣称评审已完全盲于方法。

## 验证范围

脚本自带针对导出风险的七项检查：

```bash
python scripts/export_autonomous_diagnosis_evidence.py --self-test
```

检查覆盖触发模型陈述保留、修改后输出／最终结果／patch 参数排除，无变化编辑不会提前截断，未记录的生产变化导致保守停止，原生边界字段分离，未编辑原生轨迹的推理匹配与空 tool_calls，分页／截断记录，以及拒绝在源运行目录内写输出。

实际解析验证使用 `formal_v3` 的八个已完成条件：task_001 的五个方法条件，以及 task_003 的主方法、Direct 和 SWE。导出共 476 条证据，六个条件恢复首次生产编辑边界，两个条件为未记录生产编辑且首尾快照一致。记录 55 个源码读取窗口和 32 个分页边界；默认完整导出没有引入文本截断。逐项回查来源哈希、来源 JSON 字段和边界，未发现引入编辑后结果或触发步输出；没有对这些案例做诊断正确率评分。

该验证包保存在服务器 `/tmp/autonomous-diagnosis-evidence-sample-20260917-v4`，`private/validation.json` 记录逐条件覆盖、缺口和检查结果。它是解析验证样本，正式全量评审应在结果到齐后按最终脚本生成新包。导出期间发现并修复了原生历史 `tool_calls: null` 的兼容问题；原始运行日志未改动。
