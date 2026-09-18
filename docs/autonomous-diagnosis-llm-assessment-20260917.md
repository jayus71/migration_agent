# 首次生产编辑前的 LLM 辅助诊断评估

[`score_autonomous_diagnosis.py`](../scripts/score_autonomous_diagnosis.py) 读取已完成的[诊断证据导出包](autonomous-diagnosis-evidence-export-20260917.md)，在独立评估目录准备两阶段请求。默认执行 dry-run；只有显式传入 `--execute` 才会调用配置中的 DeepSeek。评估结果统一标注为 **LLM-assisted exploratory assessment; not independent human blind review**。评分输出不回传修复 agent，不修改修复轨迹、任务输入、冻结协议或私有 rubric。

## 两阶段输入与两条评分通道

第一阶段只接收公开初态源码、首次生产编辑前的模型陈述与工具证据，以及已有的边界和可见性限制。评分器要求模型提取已有诊断、引用原句，并根据公开证据说明支持程度。第二阶段在相同公开材料上增加第一阶段通过校验的结果、该任务对应的 `private_reference`、`scorability` 和已冻结的评分规则。私有参考用于核对已有主张，不用于补写 agent 没有报告的机制或位置。

每个阶段分别保留以下通道：

| 通道 | 来源与用途 |
| --- | --- |
| `primary_report` | 实际回复正文或明确提交的报告。自然语言陈述可直接评分，无须 agent 输出 JSON。 |
| `auxiliary_recorded_reasoning` | provider 已记录的辅助推理。单独评价，不填补正文中缺失的主张。 |

两个通道分别引用自己的陈述 ID 和主张 ID。正文通道的支持证据也不能引用辅助推理。第一阶段保留原句、证据支持程度、已报告机制、最多三个因果位置、原有不确定性和证据缺口。第二阶段分别评价失败证据、证据有效性、可检验机制、首位因果符号、前三位因果符号和不确定性处理。

机制和位置按各自的陈述覆盖评分：没有报告某项时记 `not_reported`。缺失类别没有惩罚。偶然命中文件名不产生机制或因果符号分数；由 agent 明确支持的等价因果边界可获认可。冻结协议中的 12 个依赖未公开契约的任务，在机制与因果位置轴上记 `not_scorable`，另存私有参考一致性；主要机制和位置分母保持 38。缺失记录、执行失败、未报告、错误和不可评分状态分别保存。

评分器不提供方法身份、最终修复结果、后续补丁、健康版本或注入 diff。输入继承导出包的方法名遮蔽，但工具形式与行文仍可能暴露框架特征，因此这里不声称完成了独立人工盲审。

## 公开源码与可见证据

评分输入完整保留导出包中的所有编辑前证据记录，包括文本、证据 ID、分页边界、可见行范围、provider 截断标记及导出限制。评分器不会静默截短历史。

附加源码包含现有的 `candidate.py`、`task.json`、`source.py`，以及公开陈述、辅助推理、真实读取请求、原生命令或运行观察中出现完整相对路径的文件。文件内容来自公开初态，按导出哈希核对；选择过程不读取私有参考。全部文件哈希仍进入清单，未附内容的文件逐一列出。

这些完整文件均标为 `additional_public_context`，供评估模型核对实现。agent 当时读到了哪些行，只能由实际工具证据确定。请求超过运行配置的本地字符上限时，保存 `input_too_large`，不自动改选源码或压缩历史。字符检查不保证满足服务商的 token 上限；实际服务商拒绝或截断会进入失败记录。

## 使用与输出

```bash
python scripts/score_autonomous_diagnosis.py \
  --evidence-export /path/to/pre_edit_export \
  --rubric data/audits/fixed50-private-diagnosis-rubric-20260917.json \
  --run-config /path/to/formal_v3/manifest.json \
  --output /path/to/diagnosis_assessment \
  --dry-run
```

可重复传入 `--case-id <opaque-id>` 选取匿名案例。省略 `--dry-run` 和 `--execute` 时仍为 dry-run。显式执行时使用相同命令，将最后一个参数替换为 `--execute`，并由运行环境提供 `AUTOFIX_LLM_API_KEY` 与可选的 `AUTOFIX_LLM_BASE_URL`；脚本不读取凭证文件或记录请求鉴权头。

当前运行配置为 `deepseek-v4-flash`、thinking enabled、high effort、每次输出上限 16,384 token、本地请求上限 1,000,000 字符。配置来自修复运行 manifest，评分请求只携带这些模型参数，不携带运行的方法列表。温度参数与现有客户端保持一致，省略不传。私有 rubric 固定核对 SHA-256 `156a4a3df700d905f661204984649586463a3494542efba0774f948f84690f24`。

| 输出 | 内容 |
| --- | --- |
| `evaluation_manifest.json` | 脚本、配置、rubric 哈希，两阶段调用上限，通道与无自动重试规则。 |
| `bundles/<hash>.json` | 本次导出包路径、私有映射哈希、来源运行和案例数；不发送给评估模型。 |
| `cases/<id>/input_fingerprint.json` | 规范化公开输入与对应参考的哈希。 |
| `cases/<id>/phase1/request.json` | 第一阶段完整请求。 |
| `cases/<id>/phase2/request.template.json` | dry-run 的第二阶段模板，第一阶段结果为明确占位符。 |
| `cases/<id>/phase2/request.json` | 第一阶段成功后生成的实际第二阶段请求。 |
| `cases/<id>/phase*/response.json` | 已返回的 provider 响应，独立于通过校验后的结果保存。 |
| `cases/<id>/phase*/assessment.json` | 通过格式、原句引用、通道和评分约束校验的结果。 |
| `cases/<id>/phase*/state.json` | 状态、调用是否尝试、已知 usage、实际响应模型，以及失败记录。 |
| `cases/<id>/coverage.json` | 当前案例完成或缺失状态。 |
| `summary.json` | 阶段状态、调用数、已测 token、未知 usage 数与冻结分母；不把部分成功折算为分数。 |

第二阶段只有在第一阶段成功后才执行。实际第二阶段请求会包含真实第一阶段结果，并再次检查大小。模型输出可解析成 JSON，也仍需通过原句、证据 ID、通道、位置顺序、逐轴报告覆盖及 38/12 可评分范围校验。有效格式不能替代判断质量，结果保留 `needs_human_review=true`。

## 失败、恢复与增量导出

每个阶段至多发送一次请求。`schema_error`、`transport_error`、`provider_truncated` 和 `input_too_large` 都作为已有结果保留，重新运行不自动重试。provider 已返回的响应即使评分格式不合格也会保存；运输异常只保存异常类别，不输出可能含凭证的异常字符串。未返回 usage 的尝试保留未知用量，不按零成本处理。

发请求前先落盘 `started`。若进程中断，恢复时有响应文件便从已有响应继续校验；只有 `started` 而没有响应时，记 `outcome_unknown_no_automatic_retry`，避免重复发送可能已被服务端接受的请求。成功记录在复用前核对已保存评分文件的哈希。

同一输出根目录可接收后续增量证据包。重新导出时须沿用原导出器的匿名化密钥，使已完成条件保持相同匿名 ID。不同导出路径分别写入 `bundles/`；相同案例的规范化输入和参考哈希一致时复用原结果。案例内容、配置、脚本或冻结参考改变时明确报错，不覆盖旧结果。需要评估新版本时应使用新输出目录，并保留原目录以便核对。

usage 仅统计该评分器的评估调用，不能混入修复 token。汇总中的已测 token 是已返回值的合计；只有 `token_totals_complete=true` 才表示所有已尝试调用均返回了必要 token 字段。当前脚本不估算缺失 token 或货币成本。

## 离线验证与八条件 dry-run

```bash
python scripts/test_score_autonomous_diagnosis.py
```

九项离线行为测试全部通过，覆盖两阶段输入隔离、正文与辅助推理分离、自然语言和 `not_reported`、逐轴缺失定位、12 个契约依赖任务的排除、schema 失败与未知 usage、增量复用和内容变更拒绝、中断恢复，以及 provider 截断。测试使用模拟响应，真实模型调用为零。

实际打包验证使用八个已完成条件的导出包，共 476 条证据，包含 38 条正文陈述和 135 条辅助推理记录。最新输出是 [`assessment_v3`](../tmp/diagnosis-scoring-dry-run-20260917/assessment_v3/summary.json)，逐项审计见 [`assessment_v3_input_audit.json`](../tmp/diagnosis-scoring-dry-run-20260917/assessment_v3_input_audit.json)。下表按实际发送序列化方式统计字符，第二阶段为尚未加入真实第一阶段结果的模板。

| 匿名案例 | 第一阶段请求字符 | 第二阶段模板字符 | 证据记录 |
| --- | ---: | ---: | ---: |
| `0641ff2ccb52e52a2ba9` | 423,467 | 429,040 | 28 |
| `23dcc082f05e1a00d67b` | 282,636 | 288,209 | 96 |
| `330ad9738e150dbdca18` | 293,792 | 299,365 | 40 |
| `414b034b235a1e8ea0b7` | 342,347 | 347,920 | 39 |
| `4abebd4b22b1bb677d17` | 745,407 | 750,970 | 60 |
| `782768655e07ccc84829` | 382,503 | 388,066 | 114 |
| `a402e2f9da7695a707ce` | 756,632 | 762,195 | 68 |
| `d77a0badde46294a60a5` | 290,796 | 296,369 | 31 |

八个请求均为 `dry_run`，API 尝试数为零，没有 provider 响应或诊断分数。隔离审计逐项确认第一阶段没有私有 reference、scorability、原任务号或显式方法名；第二阶段只增加对应参考和冻结规则；全部导出证据原文与限制均保留；附加源码与初态哈希一致。导出器、冻结协议与 rubric 哈希未变化。

本次评分脚本 SHA-256：`d8acb0b0b7c8a037d762bc63cf978f4231c0dfc04e11bf1cd5e4bece14817f26`。
