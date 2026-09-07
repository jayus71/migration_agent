# T-CTE Baseline Summary

T-CTE = CodeTransEngine Direct Translation。不给仓库 guide，不给 verifier 诊断，不执行 Fixer 修复循环。

| 模型 | 运行数 | Strict 成功率 | 编译成功率 | 执行成功率 | 训练成功率 | 后端路径 |
|---|---:|---:|---:|---:|---:|---|
| Image MLP | 3 | 33.3% | 100.0% | 100.0% | 100.0% | MindSpore:3 |
| CNN | 3 | 33.3% | 100.0% | 33.3% | 33.3% | MindSpore:3 |
| ResNet | 3 | 100.0% | 100.0% | 100.0% | 100.0% | MindSpore:3 |
| Transformer classifier | 3 | 0.0% | 100.0% | 66.7% | 66.7% | MindSpore:3 |
| Tiny causal LM | 3 | 100.0% | 100.0% | 100.0% | 100.0% | MindSpore:3 |
| Macro average | 15 | 53.3% | 100.0% | 80.0% | 80.0% | MindSpore:15 |

## 单次运行

| 任务 | repeat | seed | 后端 | Strict | Compile | Execution | Training | 失败分类 | 错误摘要 |
|---|---:|---:|---|---:|---:|---:|---:|---|---|
| image_mlp | 1 | 642 | MindSpore | False | True | True | True | valid_experiment_failure | strict_metrics: loss_diff=2.4437904357910156e-05, grad_diff=0.00026357173919677734, param_update_rel_l2=2.162433624267578, buffer_state=matched |
| image_mlp | 2 | 643 | MindSpore | False | True | True | True | valid_experiment_failure | strict_metrics: loss_diff=1.6450881958007812e-05, grad_diff=0.0002315044403076172, param_update_rel_l2=2.161834478378296, buffer_state=matched |
| image_mlp | 3 | 644 | MindSpore | True | True | True | True | none |  |
| cnn | 1 | 642 | MindSpore | True | True | True | True | none |  |
| cnn | 2 | 643 | MindSpore | False | True | False | False | environment_or_upstream | execution: ValueError: For 'Conv2D', the 'pad' must be zero when 'pad_mode' is not 'pad', but got 'pad': 1 and 'pad_mode': same. |
| cnn | 3 | 644 | MindSpore | False | True | False | False | environment_or_upstream | execution: ValueError: For 'Conv2D', the 'pad' must be zero when 'pad_mode' is not 'pad', but got 'pad': 1 and 'pad_mode': same. |
| resnet | 1 | 642 | MindSpore | True | True | True | True | none |  |
| resnet | 2 | 643 | MindSpore | True | True | True | True | none |  |
| resnet | 3 | 644 | MindSpore | True | True | True | True | none |  |
| transformer_classifier | 1 | 642 | MindSpore | False | True | True | True | valid_experiment_failure | strict_metrics: loss_diff=1.1920928955078125e-07, grad_diff=4.827976226806641e-06, param_update_rel_l2=2.1600728034973145, buffer_state=matched |
| transformer_classifier | 2 | 643 | MindSpore | False | True | True | True | valid_experiment_failure | strict_metrics: loss_diff=1.1920928955078125e-07, grad_diff=4.649162292480469e-06, param_update_rel_l2=2.159533977508545, buffer_state=matched |
| transformer_classifier | 3 | 644 | MindSpore | False | True | False | False | valid_experiment_failure | execution: ValueError: For 'Split', x_shape[2] must be divisible by output_num = 3, but got 20  ---------------------------------------------------- - C++ Call Stack: (For framework developers) ---------------------------------------------- |
| tiny_causal_lm | 1 | 642 | MindSpore | True | True | True | True | none |  |
| tiny_causal_lm | 2 | 643 | MindSpore | True | True | True | True | none |  |
| tiny_causal_lm | 3 | 644 | MindSpore | True | True | True | True | none |  |
