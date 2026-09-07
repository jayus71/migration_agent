# T-DIRECT Baseline Summary

T-DIRECT = 单次 Direct LLM。不给仓库 guide，不给 verifier 诊断，不执行 Fixer 修复循环。

| 模型 | 运行数 | Strict 成功率 | 编译成功率 | 执行成功率 | 训练成功率 | 后端选择 |
|---|---:|---:|---:|---:|---:|---|
| Image MLP | 3 | 0.0% | 100.0% | 100.0% | 100.0% | MindSpore:3 |
| CNN | 3 | 33.3% | 100.0% | 33.3% | 33.3% | MindSpore:3 |
| ResNet | 3 | 100.0% | 100.0% | 100.0% | 100.0% | MindSpore:3 |
| Transformer classifier | 3 | 0.0% | 100.0% | 100.0% | 100.0% | MindSpore:3 |
| Tiny causal LM | 3 | 100.0% | 100.0% | 100.0% | 100.0% | MindSpore:3 |
| Macro average | 15 | 46.7% | 100.0% | 86.7% | 86.7% | MindSpore:15 |

## 单次运行

| 任务 | repeat | seed | 后端 | Strict | Compile | Execution | Training | 错误摘要 |
|---|---:|---:|---|---:|---:|---:|---:|---|
| image_mlp | 1 | 642 | MindSpore | False | True | True | True | strict_metrics: loss_diff=2.4437904357910156e-05, grad_diff=0.00026357173919677734, param_update_rel_l2=2.162433624267578, buffer_state=matched |
| image_mlp | 2 | 643 | MindSpore | False | True | True | True | strict_metrics: loss_diff=1.6450881958007812e-05, grad_diff=0.0002315044403076172, param_update_rel_l2=2.161834478378296, buffer_state=matched |
| image_mlp | 3 | 644 | MindSpore | False | True | True | True | strict_metrics: loss_diff=2.6226043701171875e-06, grad_diff=0.0003561973571777344, param_update_rel_l2=2.161710262298584, buffer_state=matched |
| cnn | 1 | 642 | MindSpore | False | True | False | False | execution: ValueError: incomplete trainable-parameter initialization mapping: {'reference_count': 6, 'candidate_count': 4, 'mapping_strategy': None, 'mapped_count': 0, 'complete': False, 'unmatched_reference': ['stem.weight', 'stem.bias', ' |
| cnn | 2 | 643 | MindSpore | True | True | True | True |  |
| cnn | 3 | 644 | MindSpore | False | True | False | False | execution: ValueError: incomplete trainable-parameter initialization mapping: {'reference_count': 6, 'candidate_count': 4, 'mapping_strategy': None, 'mapped_count': 0, 'complete': False, 'unmatched_reference': ['stem.weight', 'stem.bias', ' |
| resnet | 1 | 642 | MindSpore | True | True | True | True |  |
| resnet | 2 | 643 | MindSpore | True | True | True | True |  |
| resnet | 3 | 644 | MindSpore | True | True | True | True |  |
| transformer_classifier | 1 | 642 | MindSpore | False | True | True | True | strict_metrics: loss_diff=1.1920928955078125e-07, grad_diff=4.827976226806641e-06, param_update_rel_l2=2.0733773708343506, buffer_state=matched |
| transformer_classifier | 2 | 643 | MindSpore | False | True | True | True | strict_metrics: loss_diff=1.1920928955078125e-07, grad_diff=4.649162292480469e-06, param_update_rel_l2=2.159533977508545, buffer_state=matched |
| transformer_classifier | 3 | 644 | MindSpore | False | True | True | True | strict_metrics: loss_diff=3.5762786865234375e-07, grad_diff=2.7418136596679688e-06, param_update_rel_l2=2.1566805839538574, buffer_state=matched |
| tiny_causal_lm | 1 | 642 | MindSpore | True | True | True | True |  |
| tiny_causal_lm | 2 | 643 | MindSpore | True | True | True | True |  |
| tiny_causal_lm | 3 | 644 | MindSpore | True | True | True | True |  |
