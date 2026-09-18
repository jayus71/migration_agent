# I-08 / I-09 自然翻译故障的代码路径复核

本记录补充此前只核对探针结果的分析。检查归档源码、适配层注册与回退逻辑，未执行修复或训练实验。I-08 / I-09 没有注入故障；此前绘图所用 GR-01-B 的人为 `detach()` 故障属于另一组实验，已从新图中移除。

## 归档程序实际做了什么

I-09 的源程序和首次翻译都使用 `GroupNorm` 处理 value/gate 两支的乘积，再做空间均值和输出层。I-08 的两份程序都在第一个 encoder Linear 后使用 `nn.Tanh()`。首次翻译没有在这两处插入 `detach()`；训练函数末尾的 `loss.detach().item()` 发生在 backward 和 optimizer.step 之后，用于返回数值。

两例的 `condition_result.json` 均记录初始与最终候选哈希相同，初始与最终适配层树哈希也相同（`696557c9547e2bd3f80c966f71a1cd71817cd1f221363e86b2b1fd9b55bc4673`）。LaDiM 的前两轮没有应用编辑，第三轮只写出诊断材料，最终 `STOP_NO_PROGRESS`。

## 发现的梯度中断路径

归档目录根为 `experiment-results-local-20260906/09_experiment_I_real_translation/runs_real_core_v3/tasks/`，下列适配层文件在对应任务的 `r_hier/torch4ms/` 内。

1. I-09 调用 `torch.nn.functional.group_norm`；I-08 的 `nn.Tanh` 调用 `torch.tanh`。归档 `ops/mtorch.py` 未注册这两个高层函数。I-08 虽有 `ops/maten.py:457` 的 `aten.tanh` 实现，它与高层 `torch.tanh` 是不同注册键。
2. `tensor.py:1277` 的 `load_ops()` 载入注册项；`_get_op_or_decomp()`（第 1329 行）按函数对象、ATen overload 和名称匹配。ATen 的 `aten.tanh` 键没有补上高层 `tanh` 名称。GroupNorm 也没有相应高层映射。
3. `XLAFunctionMode.__torch_function__()` 在第 884–887 行捕获 `OperatorNotFound`，进入原生 PyTorch 回退。第 905、913 行把 torch4ms 张量转换为普通 PyTorch 张量，第 918 行执行原函数。
4. 该转换经 `ms2t_copy()` 调用 `ops/mappings.py:83` 的 `ms2t()`；第 92–95 行使用 `asnumpy()` 和 `torch.from_numpy()`。它传递数值，没有跨 MindSpore/PyTorch 的反向传播桥。回到已映射算子时，普通 PyTorch 张量再经 `t2ms()` 的 `detach().numpy()` 和 `ms.Tensor(...)` 转回目标张量。

这是保留前向数值、丢失参数依赖的具体代码机制。I-09 的 GroupNorm 回退涉及输入激活与 norm 参数，因此会切断 value/gate/norm 到后续目标框架计算的求导关系，后面的 head 仍在目标求导路径上。I-08 的 Tanh 回退位于第一个 encoder Linear 后，切断此前的参数依赖。

## 与记录的对应及验证状态

I-09 的初始探针中，value/gate/norm 的六个参数张量更新全部为零，head 的两个参数更新与参考相同；loss 差为 `4.76837158203125e-7`。这个位置分布与上述 GroupNorm 回退边界一致。I-08 的第一个 encoder 权重更新仅约 `1.8869e-5`，参考约 `0.012248`，后续层仍更新；其 loss 差为 `1.430511474609375e-6`。I-08 使用 AdamW，微小更新也可能包含权重衰减，不能把非零更新直接解释为有效梯度传播。

当前定位依据是归档代码的注册和调用链，以及探针中受影响参数的位置。归档没有逐算子运行跟踪，本次也未执行“只补齐相应映射后重跑”的反事实验证。因此可以明确指出这个梯度中断路径，但不把它记成已经通过运行验证的根因修复。

此前“尚未完成根因归因”来自 `manual_attribution.json` 中的 `status: not_reviewed`，以及当时尚未检查这条调用链。本次没有覆盖原始人工审阅状态或原始实验结果。
