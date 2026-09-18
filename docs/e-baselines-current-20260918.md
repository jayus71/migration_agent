# 实验 E：四方法 60 条离线验收归档

后续原版核对发现：本页 CodeTransEngine 的历史 8/15 使用过“未提供测试时跳过”的接入补丁。新的统一主实验已恢复干净上游，并提供其接口要求的公开测试和运行环境；本页结果保留历史身份，不填入新主表。详见 [正式运行前审查](unified-experiments-preflight-review-20260918.md)。

已完成四种方法的 60 条离线验收归档。MSAdapter 使用干净上游原版，其余三种方法复用全部既有候选。本次离线验收新增 API 调用、输入 token 和输出 token 均为 0；45 条模型候选的接受判定全部与历史结果一致。此次接替工作只下载、核对和汇总结果，没有重复执行实验或修改论文。

| 方法 | 严格接受 | 前向完成 | 训练完成 | 本次 API token | 原生成 token |
| --- | ---: | ---: | ---: | ---: | ---: |
| MSAdapter 0.6.0 原版，CPU | 0/15 | 15/15 | 0/15 | 0 | 0 |
| CodeTransEngine，translation-only 配置 | 8/15 | 12/15 | 12/15 | 0 | 33,702，文本长度估算 |
| Direct，native MindSpore | 7/15 | 13/15 | 13/15 | 0 | 361,566，历史 usage |
| Frozen Translator，torch4ms | 15/15 | 15/15 | 15/15 | 0 | 287,550，历史 usage |

五个任务为 Image MLP、CNN、ResNet、Transformer classifier、Tiny causal LM，执行种子为 642、643、644。接受阈值保持损失绝对差 0.02、梯度范数绝对差 0.05、参数更新相对 L2 差 0.03，并保留已有缓冲区一致性检查。

MSAdapter 每任务一个由统一 import 替换产生的候选，各测三个种子，共 5 份不同候选、15 条条件。CodeTransEngine、Direct、Frozen Translator 每任务三个既有独立生成候选，各测原对应的一个种子；三种方法分别有 15 个不同候选 SHA-256。总计 50 份候选、60 条条件。后三者的三次重复同时包含候选生成差异和执行种子差异，没有做每个候选与三个种子的交叉实验；因此本表分母应称为“任务与重复条件”，不能将其解释为 15 个不同任务或纯运行种子稳定性实验。

642、643、644 是验收器的执行种子。归档的 Direct 历史 runner 未把它们传给模型 API；Frozen Translator 的历史 `llm_config.seed` 为 null、temperature 为 0.1。CTE 的本地请求记录含执行 seed，gRPC 请求构造不传这个整数为模型采样种子。三个模型方法均记录请求模型名 `deepseek-v4-flash`。

四方法统一结果为 [summary.json](../output/e-baselines-current-20260918/four_methods/summary.json)，方法表为 [summary.csv](../output/e-baselines-current-20260918/four_methods/summary.csv)，60 条明细为 [conditions.csv](../output/e-baselines-current-20260918/four_methods/conditions.csv)，分任务表为 [per_task.csv](../output/e-baselines-current-20260918/four_methods/per_task.csv)。原两方法记录完整保留在 `formal/`，新增两方法记录在 `e-existing-translations-20260918/`；每条均保留源程序、候选、验收 JSON、标准输出和错误输出。

## Direct 与 Frozen Translator

Direct 历史来源为 `4508d0e962d1f27a582b2fcb0a53f1edea5bfb0f` 的 T-DIRECT 正式运行，配置为无 guide、无 diagnosis、无 repair loop。15 份候选全部复验。CNN 的 seed 642、644 候选缺少卷积偏置，参考模型有 6 个可训练参数而候选仅 4 个，初始化映射拒绝后记为执行失败，后续数值测量为 null。Image MLP 的三条与 Transformer classifier 的三条均完成训练，损失和梯度范数差通过，但参数更新相对 L2 差约为 2.07–2.16，超过 0.03 阈值。

Frozen Translator 复用 `b32d9f4` 的 15 份初译，全部通过当前同一验收器。每份候选与历史 patch_v0 一致，`fixer_calls=0`、`final_iter=0`；它们在此次验收之前已经通过历史检查。本表方法名称固定为 Frozen Translator，15/15 表示旧初译在当前验收下保持有效，不归因于新 slim-v4 修复。

| 任务 | MSAdapter | CTE translation-only | Direct | Frozen Translator |
| --- | ---: | ---: | ---: | ---: |
| Image MLP | 0/3 | 1/3 | 0/3 | 3/3 |
| CNN | 0/3 | 1/3 | 1/3 | 3/3 |
| ResNet | 0/3 | 3/3 | 3/3 | 3/3 |
| Transformer classifier | 0/3 | 0/3 | 0/3 | 3/3 |
| Tiny causal LM | 0/3 | 3/3 | 3/3 | 3/3 |

分析时建议分别报告执行失败与训练后的严格失败：MSAdapter 有 15 条训练异常；CTE 有 3 条执行失败与 4 条数值失败；Direct 有 2 条初始化失败与 6 条数值失败。CTE 比 Direct 多通过的一条来自 Image MLP。两者都在 ResNet 和 Tiny causal LM 全部通过，而 Image MLP 与 Transformer classifier 的失败主要暴露参数更新检查的必要性。Frozen Translator 使用统一迁移 guide 和 torch4ms 目标路径，Direct/CTE 使用 native MindSpore；这组比较描述各完整迁移配置的结果，无法单独分离 guide 或后端的贡献。修复收益应由另有初始失败及修复轨迹的实验支持。

Direct 与 Frozen Translator 的历史 token 使用原记录字段汇总；CTE 使用文本长度估算。成本表应保留这一区别，不把 CTE 估算与历史 API usage 混合计算成本倍数。本次归档没有新增模型费用。

## 评分器修正

此次只修改我们的评分实现，三个缺陷均在正式验收前修正。

1. MSAdapter 原路径独立随机采样输入，只重置 seed。现在把原生 PyTorch 参考实际使用的输入、标签、初始参数和缓冲区复制到目标模型，之后逐项核对数值完全相同。15 次 MSAdapter 验收的输入和完整初态均精确一致。进入训练阶段的 12 次 CodeTransEngine 验收也逐项确认参数初态一致。
2. 缓冲区检查原来仅忽略参考端的 `num_batches_tracked`，会使完全相同的 PyTorch ResNet 被误判不一致。现在对两端按同一规则处理；BatchNorm 的 running mean/variance 继续检查。
3. 训练入口原来捕获整个训练过程的 `TypeError` 后换为位置参数重跑，可能在实际训练失败后执行第二遍。现在用函数签名选择调用方式，函数内部异常只记录一次。

缺失的损失、梯度和更新测量保留 null，参数更新未测量时也为 null。没有将训练失败后的缺失测量填零。

预检包含五个原生 PyTorch 健康对照、五个 native MindSpore golden 候选、五个取消更新的 mutant，以及歧义参数映射拒绝检查，全部通过。相关现有测试 `test_experiment_e_final_rerun.py` 和 `test_experiment_request_20260820.py` 共 30 项通过。初版预检发现的 ResNet 缓冲区错误记录保留在 `formal_v1/`；`formal_v2/` 是修复后的预检；只有 `formal/` 包含正式 30 次 baseline 验收。前两者均无 API 调用、无正式方法比较。

## MSAdapter 原版

上游提交固定为 `0a6d11d6d00243141e2bdd01f086782b37b49a21`，独立目录为 `/media/main/whj/projects/torch4ms/third_party/MSAdapter-native-e-20260918`。运行前后 tracked diff 都为空，每条记录都确认实际导入该目录中的 `msadapter`。没有应用旧 `_tensor.py` 和 `optim/sgd.py` 训练补丁，也没有 mean-to-sum 改写。

环境为 Python 3.9.25、MindSpore 2.7.2、PyTorch 2.8.0、NumPy 1.26.4。当前共享 mstorch 环境的 NumPy 已变为 2.0.2，本次在结果目录下安装独立 1.26.4 依赖层，通过明确的 PYTHONPATH 使用，未更改共享环境。两个 smoke 记录分别保留 2.0.2 和 1.26.4 下同样的训练异常。

15 次运行全部完成 MindSpore Tensor 前向，训练统一失败于上游交叉熵的 `loss.sum() / loss_weights.sum()`。CPU 除法分支把标量经过 NumPy 后交给 `Tensor.from_numpy`，产生 `TypeError: Expected a NumPy array.`。这是当前原版实现的实际异常，已经保留；没有替上游修复。其后数值指标均为 n/a。

正文可以列出 **MSAdapter 0.6.0 / MindSpore 2.7.2 CPU：0/15，全部训练异常**，用来描述本实验环境中的端到端可执行性。该版本上游 README 主要面向 Ascend，当前结果不代表 Ascend 硬件上的训练表现，也不能写成“15 个程序训练完成但数值不等价”。旧 patched 版本的 15/15 训练和 0/15 strict 保持历史身份，不与本次原版混用。

## CodeTransEngine 复用

复用 `4508d0e` 正式运行保存的全部 15 个候选。源程序 SHA-256 与原 summary 逐项一致，候选在本次验收前后哈希一致，没有重新请求模型或在功能失败后重试抽样。15 条接受与失败判定都与旧记录一致。

| 任务 | 严格接受 |
| --- | ---: |
| Image MLP | 1/3 |
| CNN | 1/3 |
| ResNet | 3/3 |
| Transformer classifier | 0/3 |
| Tiny causal LM | 3/3 |

两个 CNN 候选在 Conv2D 的 padding 参数上失败，一个 Transformer 候选在 Split 维度上失败；这些属于生成候选的实际错误，计入 15 条分母。另四条完成训练但参数更新误差超阈值。当前更新误差约 2.16，输入和参数初态已经对齐，因此不再来自旧的初始化差异。

正式名字应保留 **CodeTransEngine，translation-only 配置**。这个接口禁用中间翻译验证、没有执行容器，并在无测试集时跳过测试附加；它没有执行完整 InterTrans 多路径搜索。33,702 token 来自原 wrapper 对文本长度的估算，包含的内容也不同于 provider 完整计费字段，因此只能作为历史估算显示，不能用来计算与精确 API usage 的成本倍数。模型请求名为 `deepseek-v4-flash`；本次离线验收没有任何模型请求。

## 旧 T-HIER 初译能否复用

可以把它们复用为**旧 Translator 生成的固定初始候选**，不需要再次花费 token 生成。已核对全部 15 份 `translator_patch_v0.json`、`candidate.py` 和 `reference.py`：候选逐字等于初始 write patch，来源哈希全部一致，`fixer_calls=0`、`final_iter=0`。原生成总量为 287,550 token，请求模型 `deepseek-v4-flash`、temperature 0.1。详细记录见 [translator_reuse_audit.json](../output/e-baselines-current-20260918/translator_reuse_audit.json)。

其 Translator 来源为 `b32d9f4` 的 `autofix/agents/translator.py`，统一加载 `autofix/agents/guide.md`，guide SHA-256 为 `8763288c5d3c1ebee64483200ff29e39fd8f836513a0346c009edb54a547e08c`。guide 包含 torch4ms 模块路径、API 签名、完整训练骨架、典型异常解释和生成前检查项；system prompt 也直接要求 `Torch4msOptimizer`、`extract_and_wrap_loss_fn` 和正确的环境作用域。

这些内容对所有 E 任务相同，冻结 runner 没有按案例注入故障类别、定位答案或健康目标代码。它们仍属于显式迁移指导。原始请求全文没有保存在这份包里，本次根据冻结 Translator 源码、guide 哈希和源文件还原其输入范围。若沿用它们，方法应表述为“固定旧 Translator 初译 + 当前 slim v4 验收/修复”；不能把旧 15/15 写成由 slim v4 重新独立完成的端到端生成，也不能声称初译阶段完全没有迁移指导。旧候选已经全部通过验收，这一组主要检验有效迁移的保持，不提供新增修复收益证据。

## 实现与归档

独立分支为 `codex/e-baselines-current-20260918`，基于用户分支 `c21dadcf6e5e82665fa163b90c9dccb1ea15c4ef`。远端 worktree 为 `/media/main/whj/projects/torch4ms/ascend-torch4ms-e-baselines-current-20260918`，结果根目录为 `/media/main/whj/projects/torch4ms/e-baselines-current-20260918`。修改的评分器与新增脚本本地副本位于 `output/e-baselines-current-20260918/code/`；评分器补丁为 `evaluator.patch`。

归档 `e-baselines-current-20260918-complete.tar.gz` 保存正式结果、预检失败与修正记录、smoke、初译来源审计和评分器补丁，共 169 个文件；SHA-256 为 `ba487c28a5e7218e8da0f9ba9df0cf563c0ea2591596d0229394f2c888acd008`。NumPy 依赖安装目录不打包，版本已记录，可按 `numpy==1.26.4` 重建。没有提交、推送或修改论文。
