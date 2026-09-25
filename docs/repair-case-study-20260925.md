# 已保存翻译中的 Tanh 修复案例

建议把正文分析实验第二部分改为真实翻译的诊断与修复案例。首选保存的自编码器分类模型：loss 检查通过，Tanh 前一层的梯度却为零。LaDiM 根据梯度分布确定调查位置，用针对性测试确认问题，再补齐高层 Tanh 的 MindSpore 映射。三种方法从相同代码和观测出发；LaDiM 用24次调用完成修复，SWE-agent与MatchFixAgent用满40次调用时仍未修复。这个案例把训练信号、具体故障位置和具名方法的修复成本连在一起，适合承接原检测图想表达的机制。

本轮交付证据核对与正文候选方案，正式论文、图形和附录尚未修改。审阅版本为 `f36bc62fb7f8d73d6f82c20f27f9f03edfee5d17`，分支为 `codex/iclr-2027-template`。

模型编码器为 `Linear(15,10) → Tanh → Linear(10,4)`，其后有decoder和分类head。源程序属于冻结的自编码器类训练程序；故障自然存在于保存的首轮翻译及支持库中，来源审计明确记录没有人工注入。初始代码能够执行，loss绝对差仅为1.43×10⁻⁶，逐层前向均值差最大为1.49×10⁻⁸。编码器第一层weight/bias的目标梯度为零，其余六个参数的梯度差不超过6.16×10⁻⁷。第一层更新只有很小的非零值，与AdamW权重衰减一致。

根因在支持库的算子注册：低层 `aten.tanh` 已有实现，高层 `torch.tanh` 与 `torch.nn.functional.tanh` 缺少映射，因此进入把MindSpore张量复制成PyTorch张量的fallback路径，切断了MindSpore计算图。LaDiM的已执行probe显示，native MindSpore Tanh的输入梯度绝对值之和为4.894132，而经torch4ms路径分派的Tanh为零；同一probe中的ReLU、Sigmoid和乘法仍有非零梯度。最终生产代码只增加下面四行有效代码，另有两行空行；源程序、候选程序和其余支持库文件保持。

```python
@register_function(torch.tanh)
@register_function(torch.nn.functional.tanh)
def functional_tanh(input):
    return mops.tanh(input)
```

| 同一次训练步的检查 | 初始翻译 | 修复后 | 阈值 |
| --- | ---: | ---: | ---: |
| Loss绝对差 | 1.4305×10⁻⁶ | 1.4305×10⁻⁶ | 0.02 |
| 梯度向量L2差 | 0.359314 | 1.0121×10⁻⁶ | 0.05 |
| 参数更新相对L2差 | 0.771127 | 6.4239×10⁻⁶ | 0.03 |

表中使用公开seed 42；修复后的1042和2042两个确认seed也通过全部验收，包括目标后端与源程序不可变检查。梯度范数的绝对差初始为0.045961，尚未超过0.05；本例触发拒绝的是梯度向量差及参数更新检查。图和正文应使用“梯度向量差”，保持它与梯度范数差的区别。

| 方法 | 完整调查与修复调用 | 总token | 最终验收 | 记录墙钟秒数 |
| --- | ---: | ---: | --- | ---: |
| LaDiM | 24 | 1,488,495 | 三个seed全部通过 | 508.96 |
| SWE-agent | 40 | 1,606,058 | 预算结束，未修复 | 491.59 |
| MatchFixAgent | 40 | 2,340,608 | 预算结束，未修复 | 344.90 |

LaDiM使用的调用数少40%，总token相对SWE-agent减少7.32%，相对MatchFixAgent减少36.41%。成本包括全部调查、失败阶段、代码编辑和最终报告；保存的初译生成成本不在这项修复研究的计费范围中。其墙钟耗时高于两个基线，因此本例支持更少调用和token内完成修复。三个方法的初始异常观测完全相同；案例展示从异常到有效补丁的效率，初始检测不作方法间排名。两种baseline的后续轨迹也出现了正确根因和相似补丁建议，终态代码快照确认它们尚未实施生产修改。

| LaDiM的已记录节点 | 调用数 | 累计token | 证据含义 |
| --- | ---: | ---: | --- |
| 提出Tanh前的梯度边界假说 | 8 | 141,055 | 当时尚未以probe证实具体注册缺失 |
| 执行Tanh与其他激活的梯度probe | 17 | 735,675 | 工具返回证实分派后的Tanh输入梯度为零 |
| 补齐高层Tanh映射 | 22 | 1,258,998 | 编辑工具成功，最终补丁一致 |
| 公开验收通过 | 23 | 1,384,401 | loss、梯度向量、更新及其他检查通过 |
| 最终报告，随后完成外部三seed验收 | 24 | 1,488,495 | 完整任务成本；第二次外部提交接受 |

建议图分为两个面板。左侧画编码器的三层计算路径，标出Tanh前一层的梯度为零、后层梯度匹配，并列修复前后梯度向量与更新误差。右侧画三种方法按累计token推进的调查修复轨迹；LaDiM标probe、补丁、公开验收及完整结束，两个baseline标出40次调用的预算结束与未修复。这样左侧解释定位依据，右侧解释具体修复成本；图注只需引用已有自然翻译修复协议。原受控检测图和阈值敏感性仍可留在附录。这里没有新增或试排图形，最终占高须以实际LaTeX编译结果决定。

下面是可以替换原第二部分的英文候选段落；它保留少量关键数字，完整轨迹放图注或附录，尚未写入正式稿。

**Diagnosing and Repairing a Training Error.** A saved autoencoder translation illustrates how training signals guide repair. Its loss differs from the source by only 1.43 × 10⁻⁶, but the layer before Tanh receives zero gradients while downstream gradients agree. LaDiM follows this pattern to the activation and confirms the gradient break with a focused test. The high-level Tanh operation lacks a MindSpore mapping and falls back to execution on copied PyTorch tensors, breaking the target differentiation graph. Adding the mapping reduces the gradient vector difference from 0.359 to 1.01 × 10⁻⁶ and the relative parameter update difference from 0.771 to 6.42 × 10⁻⁶, with acceptance confirmed on three seeds. LaDiM completes the repair in 24 calls and 1.488 million tokens. Starting from the same code and initial observations, SWE-agent and MatchFixAgent exhaust 40 calls without repairing the candidate, using 1.606 and 2.341 million tokens, respectively.

筛选范围包括现有统一迁移比较与自然翻译修复记录。统一MindSpore集合中的初始失败主要是执行错误；自然翻译中的Tanh和GroupNorm能够体现loss接近而反向错误。对这两例的三种方法下载完整记录并深入核对。GroupNorm也被LaDiM修好，但其2,424,017 token高于SWE-agent的2,113,876，Tanh更适合本次要求的具名方法成本比较。该选择用于解释具体机制，不作为新的总体定位准确率或平均检测延迟统计。旧guided故障记录未纳入自主定位证据。

正式数值来自当前主表已选配置：LaDiM对应 `output/maintext-ablations-20260918/recovery_final.json` 中 `natural10_v3 / without_edit_format_feedback` 的 `task_008`；基线对应 `output/autonomous-verifier-20260917/autonomous_recovery_final.json` 的 `Natural10 / formal_v3`。源程序对应Experiment I的I-08。上述内部标识仅用于本文件的来源追踪。

已核对2550个下载文件的大小与SHA-256，源程序和任务配置在三方法间逐字一致，44个初始候选及库文件逐字一致，源程序哈希匹配原无故障注入清单。104次模型响应的usage独立累加后与三份最终预算账完全一致。三个关键工具事件、全部数值观测、三seed验收、补丁和来源哈希保存在[审计证据](review-evidence/tanh-case-20260925/summary.json)、[调用账](review-evidence/tanh-case-20260925/calls.csv)、[工具记录](review-evidence/tanh-case-20260925/tool-evidence.json)、[补丁](review-evidence/tanh-case-20260925/repair.patch)及[来源清单](review-evidence/tanh-case-20260925/source-manifest.json)。模型完整请求与推理记录留在本地忽略目录，未复制入文稿或本审计包。

本轮运行的是[已有证据审计脚本](../scripts/audit_saved_tanh_case.py)：`.venv/bin/python scripts/audit_saved_tanh_case.py`。重建需要本地下载目录；来源清单保留远端原始文件位置。未执行模型调用、训练或新实验。
