# 仓库迁移优势、停止原因与下一轮比较审查

审查日期：2026-09-21。此次只读核查本地文档、JSON、控制器、目标产物及远端原始请求和响应；没有调用模型、执行训练、修复候选或重跑实验。唯一新增文件为本报告。

## 结论与可用主张

现有证据支持 LaDiM 能将调查和修复扩展到多文件仓库，并在两个案例中完成较广的代码及测试迁移。时间序列案例通过全部声明代码入口和核心三种子训练检查；双塔案例完成六条可执行路径和十个原测试。作为主实验的仓库泛化验证，这些是具体的能力证据。现有记录尚未建立共同完整协议下优于 SWE-agent、MatchFixAgent 的成功率或成本结论：时间序列的完整入口反馈不同，双塔三个方法完整成功均为零，且 LaDiM 的预算安排经过续接调整。

| 案例与方法 | 已有可核验结果 | 完整性边界 | 含生成的总 token |
| --- | --- | --- | ---: |
| 时间序列 LaDiM 仓库模式 | 主脚本、notebook、11 个教学片段执行通过；核心三种子各三步通过 | README 未迁移；notebook/片段没有逐入口数值等价测量；完整入口反馈从启动即提供 | 2,340,132 |
| 时间序列 SWE-agent | 主脚本、核心数值、notebook 通过 | 教学片段失败；完整入口反馈为运行后补查 | 1,815,031 |
| 时间序列 MatchFixAgent | 主脚本、核心数值通过 | notebook、片段失败；完整入口反馈为运行后补查 | 4,478,242 |
| 双塔 LaDiM | 六路径执行；10/10 原测试；21 个原断言保持；说明及映射完成 | CLI 失败；21 项数值检查失败；确认种子未进入 | 3,524,695 |
| 双塔 SWE-agent | 两个生产文件完成修改 | 其余框架导入阻断测试、CLI 和数值执行 | 3,272,548 |
| 双塔 MatchFixAgent | 11 个生产文件修改；CLI 一轮完成两次原生自动微分 | 测试未迁移；缺参数映射，数值检查未进入 | 3,300,847 |

表中的产物差异描述这些实际运行。时间序列 LaDiM 比 MatchFix 少用 token，但比 SWE 多用 token，且反馈条件不同。双塔 LaDiM 在测试和交付文件覆盖上更完整，MatchFix 的 CLI 完成了 LaDiM 尚未完成的一项。六条双塔路径共享组件，不能作为六个独立仓库样本计算成功率。执行失败导致的数值缺测继续记为 n/a。

## 生成起点与 MatchFix 的适用性

只读查阅固定上游 `MatchFixAgent-66a52a5/README.md`：其任务是翻译验证与修复，修复部分明确以 incorrect translations 为输入。双塔接入实际传入 `source/train/train.py` 和 `target/train/train.py` 的完整模块，目标起点是逐字相同的 PyTorch 源副本，工具可以访问全仓库。这个输入满足接口字段和路径要求，却没有提供已经生成的目标框架翻译。

远端 MatchFix 第 1 次响应直接指出两段源文本相同、数据流相同，随后依据公开原生 MindSpore 合同判为不等价。这排除了入口路由没有把任务送到模型的猜测，也表明该运行把目标框架生成工作纳入了翻译修复编排。LaDiM 同时拥有专门的生成阶段。因此双塔现有运行适合保留为从源副本开始的端到端开发案例；它没有独立测出各方法在原生翻译修复任务中的差异。

下一轮仓库泛化比较宜沿用主实验的共同初译设置：从公开源生成一次真实目标初译，冻结它的字节、输入、生成请求和费用，给所有方法同一初译、源仓库、参数初始状态、公开反馈和验收。初译可以包含真实生成失败或尚未完成的文件；应完整披露这些状态，不能利用健康目标补写、挑选最有利于某方法的初译或人工植入故障。若生成总体没有形成可用的目标翻译，应先按预注册生成规则完成准备，再冻结修复任务。MatchFix 原生算法、提示、解析器、重试及角色安排保持原样，已有共享工具后端适配如实报告。

共同初译在物理费用账本中计一次，在每个方法的端到端成本中计入同一份生成费用。原生修复比较使用相同修复额度；所有生成尝试及失败都计入端到端费用。

## 实际停止点

双塔 LaDiM 初始 9 次生成消耗 80,000 输出 token，只写入 4/17 个计划单元，5 次响应为空并以 length 结束，8 个单元尚未尝试。生成阶段推理为 75,590 token，占该阶段输出的 94.49%。`repository_bootstrap.py` 将单次生成硬限为 12,288，并在失败后继续依赖单元；后继读取到的 `current_dependency_files` 可能仍是未翻译源文件。低单次额度和未完成依赖确实影响了后续修复起点。

原运行第 20 次截断后，续接第 21 次改为 32,768 上限，仍全部用于推理且无工具输出；第 22 次才实际提交核心编辑。第 24 次局部检查仍受未迁移测试和训练器导入阻断。第 29—31 次修正注解及测试；第 30 次跨活动单元编辑被拒，第 31 次重新聚焦后执行，体现规划约束的一次额外调用成本。

关键完整反馈出现在第 32 次：同一响应请求 workflow、coverage、paired；CLI 暴露 Adam 的 `lr` 关键字错误，覆盖检查通过，数值运行才得到完整的可比较训练轨迹。第 33 次可用输出仅剩 24,286，响应全部为推理、content 为空、无 tool_calls，达到累计 240,000 后停止。模型收到具体数值反馈后没有再执行一次修复。增加输出预算因此有可检验的理由：它可以提供消化这次反馈并提交修改的机会，成功与否仍由同一验收判定。

SWE 第 38 次仍在调整历史编码器，第 39—40 次读取 MindSpore 注意力实现源码；MatchFix 第 38—40 次仍在编辑训练器。两者均以 40 次调用耗尽停止，全部响应无输出截断，输出分别仅 50,812 和 73,637。提高单次或累计输出、同时保持 40 次调用，会保留这两条轨迹的真实瓶颈。

LaDiM 累计约 975 秒，SWE 336 秒，MatchFix 348 秒，均未触及 1,800 秒。现有停止原因不支持单独增加时间上限。续接第 33 次请求消息序列化约 932,245 字符，配置上限为 1,000,000；继续追加稳定前缀可能很快转为上下文瓶颈。这是增加预算前应检查的实际边界。

## 自有机制可以改进的部分

**提前获得可执行反馈并预留修复额度。** 训练入口、参数映射与最小可运行模型应形成一个早期闭环，再扩展其余单元。当前代码只在提示中要求 reserve calls，生成阶段仍可占初始输出预算的三分之二，复杂数值反馈直到第 32 次才出现。下一版可在公开覆盖检查通过、核心入口可导入时触发既有 paired/workflow 观测，并给剩余数值调查、修改和复验留出明确额度。调度依据公开状态及剩余预算，不使用已知案例的修复答案。更改仅作用于我们的方法。

**让生成显式处理未完成依赖。** `generation_order` 收集静态 import，只选直接导入 torch 的文件；相对 import、动态依赖和非代码交付物需要单独覆盖。现有循环在依赖生成失败后继续把目标目录中的源副本当作当前依赖提供。可以保留完整失败记录，给依赖附上 generated/failed/unattempted 状态，并将缺失依赖交给受总预算约束的生成或修复调度。17 个单元的完成状态应随交接传入，避免重新调查哪些文件已翻译。

**缩短从发现错误到有效编辑的路径。** 第 30—31 次的活动单元错误可以用更明确的工具返回信息改善：返回当前单元、合法路径和需要聚焦的已规划单元，不给修复代码。计划目前三个单元的 depends_on 均为空，核心单元却声明全仓库 tests/paired，局部检查因此受训练器和测试未迁移影响。应让 agent 在可见 import 和测试实际依赖基础上选择局部检查，保留最终全仓库验收。依赖 DAG 的合法性检查只能证明无环，无法证明语义依赖完整。

**分阶段管理上下文。** 标准 `RepositoryAgent.complete` 在单元切换时压缩为当前计划、最近六次检查和独立调查结论；续接类直接调用父类 `AutonomousAgent.complete`，明确禁用了这个替换以保持用户要求的消息前缀。后者缓存命中率高，但输入长度仍增长。可在新协议里冻结“活动单元内稳定前缀，阶段边界保存结构化证据并重建上下文”的规则，分别记录总输入、缓存命中、未命中和遗漏证据率。把缓存节省与 token 总量分开报告；不把现有续接说成正常上下文压缩机制的验证。

**先定位数值差异的首次来源。** 已有失败是 14 项表示、6 项更新、1 项梯度；若干路径第一步更新先偏差，之后表示漂移。CLI 的 `lr` 错误已由代码和异常直接确认。训练轨迹的原因尚需从已保存参数、梯度和状态分解。优先核对每个参数的首次更新差异、接近零梯度的分量、Adam epsilon/bias correction、重复 embedding 索引的梯度累积和注意力实现；这些是机制假设，不是已确认根因。

特别要核对评估控制权：`repository_twotower_worker.py` 在数值测量中自己构造源 `torch.optim.Adam` 和目标 `mindspore.nn.Adam`，候选训练器接收外部 optimizer。因此 CLI 里的优化器关键字修改不会改变数值测量所用优化器。若差异源于评估器构造的跨框架更新语义，应作为协议/接入问题单独处理，冻结新协议并使全部方法一致；不通过修改阈值、补偿梯度或让某个候选绕过梯度验收取得通过。

Simple MoE 的 36 次调用、120,000 输出和零生产修改说明从源副本直接开始调查容易拖延；其中 104,663 为推理，8 次调用用于临时测试。它给生成先行与调查预算管理提供开发依据。任务、起点和机制共同变化，不能用它与双塔差异估计某一组件的效果。

## 最小共同预算与追加档

在共同真实初译、全部反馈从启动可见、原 DeepSeek 后端及 high 推理固定之后，建议先审查以下两档。数字是待冻结设计，不代表已获实验执行授权。

| 档位 | 每方法修复调用上限 | 累计修复输出（含推理） | 单次输出 | 活跃时间 | 外部提交 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 首档 | 40 | 240,000 | 32,768 | 1,800 秒 | 4 |
| 追加档 | 80 | 480,000 | 32,768 | 3,600 秒 | 4 |

首档保留已跑双塔 baseline 的主要资源上限，并移除 LaDiM 初始低额度造成的特殊历史；共同生成费用另行全额计入端到端结果。32,768 是已实测产生复杂编辑的上限。一次 32,768 全推理截断说明它仍可能限制某次请求，尚不足以证明统一翻倍单次额度优于分解任务、累计输出和连续反馈；先固定单次上限能更清楚识别累计资源的作用。

追加档同时放宽调用和累计输出，使三方法都能跨过已有实际停止点。时间相应放宽只是避免新的次生截断，不声称原来受时间限制。保留四次外部提交，模型在原生工具内的测试仍按原实现执行。每档记录实际首次触及的约束、截断、生产编辑、完整反馈出现位置以及接受时成本。

如果目的是严格估计预算响应，应独立从相同初译运行两档，避免把已知道预算的长轨迹截成短轨迹等同短预算运行。若为节省开发成本而续接，应在开始前声明同一续接制度，保存全部会话、余额和失败费用，并标为累计续接比较。旧双塔续接不能替代这个新协议。

按旧双塔观测粗估，三方法首档合计约 10.10M 总 token，其中 0.364449M 输出、0.498825M 未命中输入；若将全部方法工作量简单翻倍，累计约 20.20M 总 token。这只是线性量级参考：新共同初译会减少生成工作，追加历史会增大输入，缓存受前缀策略影响。新首档硬输出上界为三方法合计 0.72M，追加档累计为 1.44M，再加一次共同生成的实际输出。总输入未设上限，不能把线性估计当作消费封顶；执行前应依据配置的上下文上限、每档调用数和实际渠道单价核定支出。货币成本按缓存命中输入、未命中输入、输出分别乘实际单价，当前资料没有可核验单价。

## 无模型费用的准备与旧结果复用

1. 对全部仓库的冻结源、可执行入口、测试断言、缺失文档、参数映射合同与源端未实现行为建立清单；统一明确代码入口执行、训练数值等价和交付完整性的接受条件。
2. 从现有逐调用账本统计研究、读取、编辑、测试、无效工具调用和截断；把预算余额与第一次有用数值反馈对齐。对上述生成状态、聚焦提示、上下文交接和预算调度做离线回放及现有机制测试。
3. 用已有双塔源/目标数值记录定位首次分歧参数，检查 evaluator 构造的 optimizer 与目标训练器控制权。需要新的执行验证时另列实验需求，本次不运行。
4. 冻结共同生成方案、修复起点、方法版本、全部公开反馈、同一预算档和计费办法；通过无模型接入检查确认每个原生方法拿到其需要的输入。生成本身随后仍需模型费用。
5. 首档及追加档都报告完整仓库接受结果，并辅助报告入口执行、原测试、表示/梯度/更新及文档覆盖。保持仓库为比较单位；同一仓库内的路径和种子是覆盖证据。全部失败与缺测保留。

现有源提交、数据输入、源初始参数、源运行记录、合同阈值、未修改候选及其验收可以复用为准备资料和历史案例。复用测量须核对源码、数据、环境、测量器和协议哈希；协议更改后只复用仍符合新定义的原始观测。时间序列共同初译可在字节及合同一致时复用，但三方法的新完整反馈运行仍需重做。原 baseline 的后补入口观察可作为产物审查，不能作为它们已经得到同样反馈的证据。双塔三个旧候选可用于离线定位和开发续接，采用新共同初译后不能并入正式新协议排名。旧生成费用、失败和续接账本全部保留。

## 证据索引

本地已读：`AGENTS.md`、`README.md`、`docs/repository-agent-mechanism-20260920.md`、`docs/repository-timeseries-mindspore-20260920.md`、`docs/repository-twotower-20260920.md`、`docs/repository-twotower-baselines-20260920.md`；实现为 `scripts/repository_agent_mode.py`、`scripts/repository_bootstrap.py`、`scripts/continue_repository_twotower.py`、`scripts/run_repository_twotower.py`、`scripts/repository_twotower_worker.py` 及归档 `implementation/agent.py`。

时间序列数值与成本来源：`output/repository-timeseries-mindspore-20260920/final-evidence/experiments/repository_timeseries_20260920/summary.json` 及对应 `conditions/*/result.json`、`notebook_audit/*/result.json`。双塔来源：`output/repository-twotower-20260920/summary.json`、`condition/translation/result.json`、`continued/continuation_summary.json`、`continued/continuation/evidence/repository_state.json`、`continued/target/train/train.py`、`artifact_review.json`、`baselines/summary.json`、`baselines/provider_ledger.json` 及测量目录。

远端只读根目录：`/media/main/whj/projects/torch4ms/ascend-torch4ms-repository-pilot-20260920/experiments/repository_twotower_20260920`。关键轨迹为 `continuation/evidence/agent/call_0021_response.json`、`call_0022_response.json`、`call_0030_response.json` 至 `call_0033_response.json`、`call_0033_request.json`、`event_00053_tool.json` 至 `event_00055_tool.json`；baseline 为 `baseline_comparison/{swe,matchfix}/evidence/agent/call_0038_response.json` 至 `call_0040_response.json`、MatchFix 的 `call_0001_response.json` 及两个 `baseline_manifest.json`。MatchFix 原生任务说明取自 `/media/main/whj/projects/torch4ms/external_baselines/MatchFixAgent-66a52a5/README.md`。此次未修改远端文件。

## 后续有界核查：已确认评估器的 Adam 首步语义差异

追加 API 前应先解决数值评估的优化器控制权。对保存的 seed 101 初始参数、第一步梯度和更新后参数进行纯 NumPy 重建，确认两端外部 Adam 使用不同的 epsilon 位置；这解释了四条首步更新未通过路径中的主要系统性差异。此前列为假设的 Adam 语义问题，现已有实现源码与记录算术共同支持。候选自己的梯度仍存在小数值差异，后续训练步骤及完整验收尚未重新执行。

数据位于上述远端证据根目录的 `references/101.json`（源初始参数、梯度、状态）和 `continuation/evidence/measurement_0009/result.json`（最终候选相同 seed 的梯度、状态）；后者也归档在本地 `output/repository-twotower-20260920/continued/continuation/evidence/measurement_0009/result.json`。本次只载入这些 JSON 和 NumPy，没有导入 PyTorch/MindSpore，没有执行候选。

在首步零动量、lr=0.001、beta2=0.999、eps=1e-8 时，源更新公式为 `u_PT(g) = -0.001*g/(abs(g)+1e-8)`；目标原生 Adam 公式化简为 `u_MS(g) = -0.001*g/(abs(g)+1e-8/sqrt(0.001))`。目标的有效分母稳定项约为 3.1623e-7，等值 eps 参数在首步产生不同更新。

源码依据是源环境继承的 `/media/main/whj/miniconda3/envs/torchax311/lib/python3.11/site-packages/torch/optim/adam.py:518` 起：先对 `sqrt(v)` 除以 `sqrt(1-beta2**step)`，再加 eps；该源解释器的 `assessment_env/pyvenv.cfg` 明确 `include-system-site-packages = true`。目标 `/media/main/whj/miniconda3/envs/mstorch/lib/python3.9/site-packages/mindspore/nn/optim/adam.py:726` 调用 `P.Adam`；`mindspore/ops/operations/nn_ops.py:3399` 的底层算子公式是 `lr*sqrt(1-beta2**t)/(1-beta1**t) * m/(sqrt(v)+eps)`。高层 Adam 类说明中的公式与底层算子 epsilon 位置不一致，应依据实际算子路径和重建结果判断。

对每个路径，将参数按源名排序拼接。观测更新为 `u = recorded_state_after_step1 - initial_state`，原验收误差为 `norm(u_target-u_source)/norm(u_source)`。重建分别使用两端自己的已保存梯度；源公式重建源更新最大逐分量误差为 7.25e-8，目标公式重建目标更新最大误差为 1.01e-7。若错误地用源公式解释目标实际更新，最大逐分量误差达 6.98e-4，明显超过重建舍入误差。

| 路径 | 原首步更新相对差 | 将目标记录梯度代入源公式后的相对差 | 首步更新差平方中第二注意力层 in_proj_weight 的占比 |
| --- | ---: | ---: | ---: |
| 基础检索 | 0.017992 | 0.023684 | 非主要来源 |
| 用户历史 | 0.040574 | 0.018264 | 78.29% |
| 位置去偏 | 0.058662 | 0.021728 | 58.03% |
| 用户去偏 | 0.030379 | 0.018155 | 71.74% |
| 联合去偏 | 0.038732 | 0.006509 | 65.88% |
| 奖励包装 | 0.024423 | 0.018781 | 42.39% |

第二列是实际已有验收数据，第三列是只替换算术公式的反事实诊断量；它不代表修复后重跑结果。原先首步超过 0.03 的四条路径在该算术诊断中均降到阈值内。所有六条路径第一步梯度都通过已有梯度容差，但 epsilon 差异会把接近零的梯度放大成可见的更新差。

例如用户历史路径的 `user_history_encoder.multihead_attn_layers.1.in_proj_weight` 某分量，源/目标梯度分别为 3.3102367e-8 和 3.3102438e-8，实际更新分别为 -7.6800585e-4 和 -9.4771385e-5。梯度近乎相同，更新差主要由稳定项位置解释。位置去偏的同一参数组及 `user_features_arch.0.weight` 分别占更新差平方的 58.03% 和 21.08%。基础路径的 `item_tower_arch.bias` 是另一种情况：源/目标约 7.45e-9/-7.45e-9 的异号舍入梯度产生相反更新。第三列基础路径误差上升，说明统一优化器后仍需处理真实的跨框架数值敏感性。

合理接入方式优先让候选控制目标优化器构造，并公开统一源合同：初始动量、学习率、beta、epsilon 的数学位置、权重衰减及步数；评估器核对原生求导、参数覆盖及实际更新。这样优化器迁移成为所有方法可以完成且会被检验的一部分。另一种实验定义是比较在同一数学更新规则下的模型语义，由测量器为所有方法提供经独立小规模核验的等价目标更新器，并明确这部分不属于 agent 修复成果。两种定义应选定其一后冻结；现有强制目标原生 Adam 的接口不能同时承担“自由迁移完整训练语义”的结论。

单纯把 MindSpore eps 改成某个较小常数只能匹配某一步：若沿用该底层公式，匹配源语义所需的稳定项为 `eps_source*sqrt(1-beta2**t)`，随步数变化。不能把首步常数调整当作三步正确性证明。此次没有修改目标候选、测量器、阈值或任何参数。

以下可在远端证据根目录执行，复算首步公式、路径误差和主要参数贡献；命令只读取记录并做算术：

```bash
/media/main/whj/miniconda3/envs/mstorch/bin/python - <<'PY'
import json
from pathlib import Path
import numpy as np

root = Path('.')  # repository_twotower_20260920 证据根目录
source = json.loads((root / 'references/101.json').read_text())
target = json.loads((root / 'continuation/evidence/measurement_0009/result.json').read_text())
assert source['request']['seed'] == target['request']['seed'] == 101
for case in ('base', 'history', 'position', 'user', 'debias', 'reward'):
    initial = source['request']['cases'][case]['initial_state']
    s = source['cases'][case]['training']['steps'][0]
    t = target['cases'][case]['training']['steps'][0]
    source_updates, target_updates, counterfactual = [], [], []
    source_residuals, target_residuals, contributions = [], [], []
    for name in sorted(initial):
        p = np.asarray(initial[name], dtype=float)
        gs = np.asarray(s['gradients'][name], dtype=float)
        gt = np.asarray(t['gradients'][name], dtype=float)
        us = np.asarray(s['state'][name], dtype=float) - p
        ut = np.asarray(t['state'][name], dtype=float) - p
        source_formula = -.001 * gs / (np.abs(gs) + 1e-8)
        target_formula = -.001 * gt / (np.abs(gt) + 1e-8 / np.sqrt(.001))
        same_formula = -.001 * gt / (np.abs(gt) + 1e-8)
        source_updates.extend(us.ravel())
        target_updates.extend(ut.ravel())
        counterfactual.extend(same_formula.ravel())
        source_residuals.extend((us - source_formula).ravel())
        target_residuals.extend((ut - target_formula).ravel())
        contributions.append((float(np.sum((ut - us) ** 2)), name))
    us, ut, cf = map(np.asarray, (source_updates, target_updates, counterfactual))
    relative = lambda value: float(np.linalg.norm(value - us) / np.linalg.norm(us))
    total = sum(value for value, _ in contributions)
    print(case, 'recorded', relative(ut), 'same_formula', relative(cf),
          'reconstruction_max', np.max(np.abs(source_residuals)),
          np.max(np.abs(target_residuals)))
    print([(name, value / total) for value, name in sorted(contributions, reverse=True)[:3]])
PY
```

这项首步核查改变了下一步优先级：先冻结能够表达源优化器语义的公平接口，完成无模型算术与接入检查，再考虑追加模型预算。已有候选仍按旧协议保留失败记录；未来新接口下的完整数值结果需重新测量，不能用反事实首步算术替代三步及多种子验收。
