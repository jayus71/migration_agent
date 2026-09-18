# 诊断评估 v3：确定性引用片段

新入口 `scripts/score_autonomous_diagnosis_spans.py` 保留冻结 driver，沿用 v2 的 DeepSeek enabled/high、32,768 输出 token 和 600 秒请求超时。修改限于评估器的引用传输，修复机制、因果位置、证据支持和评分状态仍由 DeepSeek 判断。38/12 范围、两条评分通道、两阶段私有参考隔离、全部原始证据和无自动重试规则保持原样。

v2 跨方法 pilot 暴露了两类问题：部分原句来自保存为文本的诊断 JSON，原校验只读取带转义的整段文本；另有真实改写和必填字段遗漏。v3 对完整且合法的 JSON 对象或数组严格执行 `json.loads`，提取字符串叶子，不对普通文本做反转义、模糊匹配或语义匹配。

每条正文或辅助推理陈述中的全部字符串叶子，按原顺序切成可引用片段。优先按行切分，超过 1,200 字符的行再确定性切分；保存父证据 ID、通道、叶子路径、起止偏移和原文。切分只依赖公开陈述，不读取方法名、私有参考或最终修复结果。全部原始证据继续保留，片段表作为附加索引。

第一阶段模型在 claim 中返回 `quote_span_id`，程序据此恢复 `quote` 和 `statement_evidence_id`。其他 claim、机制和位置字段由模型填写。原始 provider 响应按收到的内容保存，恢复原句后的评分保存在 `assessment.json`，两者可以通过请求中的片段表对应。未知或跨通道片段、正文引文改写、额外/缺失字段以及缺少 `no_explicit_diagnosis` 都会拒绝。第二阶段提示和评分规则完全沿用冻结版本。

每个 v3 输出保存独立 wrapper manifest，记录新脚本哈希、基础 driver 哈希、源配置哈希、引用策略和预算覆盖项。evaluation manifest 的版本含新脚本哈希；修改实现后不能静默复用旧输出。旧 v1/v2 记录和调用成本保留，v3 使用全新的评估目录。单个输出目录仍只允许一个进程写入。

运行参数与旧入口相同：

```bash
python scripts/score_autonomous_diagnosis_spans.py \
  --evidence-export /path/to/export \
  --rubric data/audits/fixed50-private-diagnosis-rubric-20260917.json \
  --run-config /path/to/repair/manifest.json \
  --output /path/to/evaluator_v3/case_output \
  --case-id opaque_case_id --dry-run
```

执行时使用 `--execute`。评估输出不能放在修复运行或证据输入目录中。

## 离线验证

`python scripts/test_score_autonomous_diagnosis_spans.py` 的 7 项测试通过，涵盖严格 JSON 解码、精确连续切片、全量证据保留、原句恢复、跨通道/改写拒绝、必填布尔值、原始响应与规范化结果分别保存、预算和模型不变、恢复不重试，以及契约依赖任务规则。聚合器增加 v3 校验入口，重新生成片段表并核对规范化引文；其 13 项测试通过。

六个实际 v2 pilot 第一阶段请求离线构造 v3 片段后，大小为 361,842–614,654 字符，均低于原有 1,000,000 字符限制；片段数为 237–679。表中原始陈述的重复呈现会增加评估输入成本，后续两阶段实际请求仍执行同样的大小检查。本次未调用真实 API，也没有将旧失败响应重新记为成功。

另对原有八条件导出包运行完整 dry-run，六项生成请求，两项为 `input_too_large`，对应请求为 1,063,146 和 1,155,345 字符。输出保存在 `tmp/diagnosis-scoring-dry-run-20260917/assessment_spans_v3`。这两个输入的原证据较长，附加片段表超过了本地字符上限；脚本按协议保留未评分状态，没有丢弃原证据或扩大限制。当前六条件跨方法 pilot 的输入通过大小检查，全量执行前还需统计总体大小覆盖。
