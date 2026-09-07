# 当前主要问题

## 1. Torch4MS 真实规模长期轨迹漂移

- D 的 10-step 最大 minibatch paired residual 为 0.0897305，超过 0.02。
- 50-step 诊断中 ResNet18 和 MobileNetV2 都越界。
- MobileNetV2 的 dispatched fixed-probe 与退出 dispatch 后的 native validation 差异很大，优先检查 BatchNorm inference buffer 转换、wrapper 参数/buffer 刷新和 eval dispatch 路径。
- 当前结果说明训练确实发生，但不能说明真实规模 Torch4MS 与 PyTorch 轨迹足够一致。

## 2. Graph Mode 仍不是正式主模式

D 最小回归 8 条件中，PyNative 4/4 training-valid；Graph Mode 4 条件仅 1 条 training-valid，3 条为不支持。正式真实规模采用明确记录的 PyNative。Graph Mode 只可作为附加 smoke test，不能用退出成功替代训练有效。

## 3. Experiment I 暴露的算子与桥接缺口

- I-02：缺少 LSTM lowering。
- I-03：缺少 GRU lowering。
- I-07：Tensor slicing 触发 `Tensor.__getitem__` recursion；路由还把它误分到 environment/harness，导致只写 blocker 文档。
- I-08：首个 encoder layer 更新接近零，怀疑 autograd/optimizer bridge。
- I-09：value/gate/norm 参数不更新、head 更新，怀疑稳定参数名映射或梯度桥接。

这些问题解释了为什么纯 PyTorch reference 能训练并不自动保证 Torch4MS 候选可用：对照证明任务本身和数据流程可训练，候选仍需经过算子 lowering、autograd、参数/optimizer 映射及 buffer 同步链路。

## 4. Experiment E 的剩余基线问题

T-HIER 的旧 `0/15` 已被严格复验器初始化错位解释并由修复后全新重跑纠正为 `15/15`。最新 T-MSA 的 15 个条件均可编译、执行并产生训练更新，但 strict 仍为 0/15，主要是参数更新相对漂移很大（约 1.38–2.81）。这不再是“没有训练”，而是“训练轨迹不匹配”。T-X2MS 仍缺少可测矩阵，完整五方法主表不能宣称完成。

## 5. Experiment H 的跨模型配置混杂

- DeepSeek seed 101/202 温度 0.1，seed 303 温度 0.0。
- GLM 条件混用 GLM 5.2 和 GLM 5.3 Flash。
- 因此可报告已观测结果，但不能包装成严格固定单一模型、固定温度的三种子比较。
- Direct 在 Qwen 和 GLM 组高于 R-HIER，说明 R-HIER 相对 Direct 的优势具有 backbone 依赖性。

## 6. Experiment J 不支持既定层序优越性

首轮 `r_hier=44/50`、`r_reverse=49/50`，但两轮确认结果分别为 `47/50 vs 46/50` 和 `48/50 vs 48/50`。三轮合计为 HIER 139/150、reverse 143/150，轮次差值为 reverse 相对 hier `+5/-1/0`；首轮 reverse 优势没有稳定复现。当前本地正式视图采用第三轮数据，因此 HIER 与 reverse 均为 48/50。现有证据只能支持完整层级反馈优于粗粒度反馈，不能证明“execution → numerical → gradient/update”或反序是唯一、最优排序。

## 7. 版本冻结与补算子

实验 D 的 core 修复是独立 commit/worktree 范围内的变更，不应静默混入冻结在旧 commit 的其他实验。补一个算子的直接影响通常局部，但它可能改变翻译覆盖率、执行路径甚至梯度行为；任何跨实验复用都必须记录 commit，并按对应实验的冻结版本重新验证，不能默认“影响不大”后直接合并统计。
