# 新分支实验与后续补跑范围

已检查远端 `codex/experiments-emn-integration`，提交为 `c21dadcf6e5e82665fa163b90c9dccb1ea15c4ef`。用户确认统一使用 v4 独立证据交接，论文由用户修改。本次只审查已有实现和结果，没有启动新的付费实验。此前组件恢复已完成 143/143，合并为 276/276 有效条件；新增训练信号 64/64、原比较 610/610 和 JAX 12/12 均已完成。

## 先统一方法和数据名称

主方法固定为 `progress_v4/autonomous_layered`，配置来源见 [冻结说明](frozen-method-v4-20260918.md)。新分支仍调用旧 `autofix.orchestrator`、规则 Verifier 和 Fixer 路由，不能只改结果标签就视作 v4。框架变更只影响实际调用了该框架的条件；已经生成的 baseline 候选不会因此改变。

Natural10 的输入来自旧 Experiment I 的十份首次迁移代码，本次未重新翻译或注入故障。初始五份有故障、五份正确。其三个易混淆字段已在 [结果汇总](maintext-results-20260918.md) 中改为：

| 字段 | 含义 | v4 |
| --- | --- | ---: |
| 自然迁移总通过／10 | 修好原有故障，加上保留正确行为的健康程序 | 9/10 |
| 原有故障修好／5 | 只统计初始失败的五例 | 4/5 |
| 十例完整运行总 token | 十例所有诊断、修复及失败尝试的输入和输出 token | 15,547,813 |

token 包含每次重新携带的上下文，不等于输出长度或人民币费用。基础设施中断的旧运行成本另列，未知 usage 不记为零。

MatchFix 的源程序提供原框架语义，目标程序就是需要检查和修复的迁移候选。当前自然迁移提供真实 source/candidate 对；原 Fixed50 缺少这样的原始源程序，当前 MatchFix 标为不适用。旧 wrapper 把健康目标当源程序的记录存在答案泄漏，不能复用。M 中另一种按 fault ID 选择参考片段和目标符号的方式仍会提前给出位置，也不适合自主定位主张。

## E：端到端 PyTorch 到 MindSpore

E 是五个模型、三个种子、五个迁移方法，完整声明矩阵 75 条。外部方法包括 MSAdapter、X2MindSpore、CodeTransEngine，另有 Direct 和旧 T-HIER。它没有人工注入故障。

| 部分 | 现有证据 | 后续所需工作 |
| --- | --- | --- |
| Direct | 冻结结果 7/15；15 份原始生成与实际 usage | 优先保留候选和费用；评分变更只离线重验 |
| CodeTransEngine | translation-only 配置，8/15；token 为估算值 | 保留这个准确配置名；不把它写成完整 InterTrans 搜索 |
| MSAdapter | 原版历史训练报错；patched 版训练 15/15、strict 0/15 | 干净上游作为 baseline；修正我方初态对齐和验收后离线重验 |
| X2MindSpore | 正式归档只有输入准备，0 个可测结果 | 记录未测；只有工具环境实际可用后才能补这一行 |
| T-HIER | 旧框架 15/15，全部首次翻译通过，Fixer 调用为零 | 先核对翻译器、候选和验证契约；保留相同首次候选，补齐 v4 流程证据。该组原本未触发修复，不单独证明新修复 agent 有效 |

MSAdapter 的补丁改了上游 Tensor 除法和 SGD；按用户要求，正式 baseline 应保持原生方法。原 patched 目录作为历史保留，不能就地覆盖。其 strict 0/15 另有我方评分问题：先后两次建模造成 RNG 初态不同，最新评分路径也没有确认跨框架参数逐值一致。修复这类测量缺陷不涉及修改 baseline 算法，也不需要调用 LLM。

E 的 Direct/CTE 为每个任务生成三个独立候选，MSAdapter 为一个候选测三个种子。报告需保留这个运行单位差异。旧总表中 Direct/CTE 的 0/15 已经过时。

## M：诊断插入外部修复 agent

声明设计为 Fixed50 × SWE-agent/MatchFix × ordinary/measurements/layered 三种反馈，共 300 条。当前 layered 使用 `ProbePairVerifier` 的字段规则和给定候选位置；MatchFix 还通过旧接入按 fault ID 选择源码片段。已有高分描述的是这套旧输入和规则反馈，不能代表 v4 自主调查。

需要把 v4 的实际调查记录接给外部 agent，并保留外部 agent 的原生工具、解析、历史和重试。诊断调用与后续修复调用一起计入总预算。可复用已有普通 baseline 的前提是源码、可编辑范围、工具、预算、输入和测量完全相同；不能只因方法名称相同就复用。

在当前数据上，SWE 的 Fixed50 普通运行是一个已有比较起点。MatchFix 应优先使用有真实源／目标对的自然迁移任务，或先建立合法、完整且不按故障选择的源码输入。未解决输入问题前启动完整 300 条没有意义。删去 measurements 条件、缩为一个宿主都会改变原研究问题，应明确记录为新的缩减协议，而不是声称完成旧 300 条矩阵。

## N：两个方向、两条实验

N 的注入轨是 Python/PyTorch 到 Java/DJL，当前协议为 12 个故障 × 两个宿主 × 三种反馈，共 72 条。旧 144 条使用另一个 24 例池；SWE 三组均为 24/24，MatchFix 三组均为 23/24，不能拿来填当前 72 条的结果。若要验证 v4 诊断插件在 Java 目标端的作用，需要更新接入并重新定义对应配对实验。该轨与 M 的问题有重叠，可在 N18 主比较之后安排。

N18 是 18 个真实 Java/DJL 源码迁移到 Python/PyTorch，包含完整 AutoFix、Direct、Direct 加普通测试修复、SWE-agent、MatchFixAgent、InterTrans 六种方法。验收覆盖数据预处理后连续两步训练的输出、损失、梯度、参数更新及已观测优化器状态。

最新准备批次 `n18_prepared_20260917` 的 Direct 已完成，1/18 通过。旧 full 阶段有用户暂停记录，只保存 15 条，其中 12 条可验收、4 条通过、3 条生成错误；不是完整 18 例结果。其余阶段没有形成当前完整六方法比较。更早的六方法批次含较多 provider/基础设施缺失，不能将未测值算成失败补齐比较。

18 份 Direct 候选具备复用价值；当前公共训练接口 hash 与冻结接口一致，还需核对源码、候选、提示、验证器和参考轨迹后固定输入。把 v4 应用到这些候选，测量的是条件于共同初译的修复能力。端到端主张还需记录相应初译阶段及其费用。源轨迹和健康／故障校准通过版本和环境核对后可以复用，不应重新生成所有材料。

## 更多 baseline 的优先级

现有远端已经有 MSAdapter、CodeTransEngine、Ivy、torch2jax 和 InterTrans。2026-09-17 审查过前四者，新分支补充了 N18 的 InterTrans。未发现另一个独立 MindAdapter/MindConverter 接入或结果。

优先完成 N18 的完整 InterTrans 比较，可以增加一个不同于 SWE、MatchFix 的外部方法。E 的 MSAdapter 和 CodeTransEngine 分别提供兼容层与翻译器对照；它们应进入端到端迁移表。Ivy、torch2jax 当前六例已经完成，输入为有故障的候选，保留该任务定义。Fixed50 修复表若仍需新增独立 agent，需要另外选择并接入完整方法；内部反馈消融不作为新增 baseline 计数。

## 执行顺序与证据

先完成零 API 的候选来源、参数初态和原生 baseline 配置核对，再进行少量 v4 接入检查。之后按论文实际要保留的 E、M、N18 结论固定正式矩阵及费用上界；不因一句提示修改再次展开多版本全量网格。本次没有启动这些追加运行，也没有恢复另一个任务里被用户暂停的 N18 队列。

- [baseline 库存与 E 审查](baseline-inventory-emn-20260918.md)
- [M/N 代码、历史结果与复用条件](emn-mn-rerun-audit-20260918.md)
- [组件消融与 v6/v7 真实成本](component-final-version-cost-review-20260918.md)
- [v4 主方法冻结](frozen-method-v4-20260918.md)

此前消融恢复归档已经逐一验证 135,522 个文件，SHA-256 为 `4418d13309523a45187687e7d583010259f23a6c0b86626be4618f8e35b75da0`。完整表和 CSV 已更新，论文正文与图表未修改。
