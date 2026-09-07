# T-MSA Baseline Summary

T-MSA = uniform MSAdapter enablement. One candidate per task, verified on three seeds.

| Model | Runs | Candidates | Strict | Compile | Execution | Training | All Seeds |
|---|---:|---:|---:|---:|---:|---:|---:|
| Image MLP | 3 | 1 | 0.0% | 100.0% | 100.0% | 100.0% | False |
| CNN | 3 | 1 | 0.0% | 100.0% | 100.0% | 100.0% | False |
| ResNet | 3 | 1 | 0.0% | 100.0% | 100.0% | 100.0% | False |
| Transformer classifier | 3 | 1 | 0.0% | 100.0% | 100.0% | 100.0% | False |
| Tiny causal LM | 3 | 1 | 0.0% | 100.0% | 100.0% | 100.0% | False |
| Macro average | 15 | 5 | 0.0% | 100.0% | 100.0% | 100.0% | False |

## Runs

| Task | Seed | Strict | Compile | Execution | Training | Failure class | Error |
|---|---:|---:|---:|---:|---:|---|---|
| image_mlp | 642 | False | True | True | True | valid_experiment_failure | strict_metrics: loss_diff=0.020239710807800293, grad_diff=0.09347665309906006, param_update_rel_l2=1.4216119097799436 |
| image_mlp | 643 | False | True | True | True | valid_experiment_failure | strict_metrics: loss_diff=0.11299097537994385, grad_diff=0.30032825469970703, param_update_rel_l2=1.4071132660794694 |
| image_mlp | 644 | False | True | True | True | valid_experiment_failure | strict_metrics: loss_diff=0.13752472400665283, grad_diff=0.03830766677856445, param_update_rel_l2=1.4185075412761476 |
| cnn | 642 | False | True | True | True | valid_experiment_failure | strict_metrics: loss_diff=0.03887820243835449, grad_diff=0.313329815864563, param_update_rel_l2=2.01831809543643 |
| cnn | 643 | False | True | True | True | valid_experiment_failure | strict_metrics: loss_diff=0.06266212463378906, grad_diff=0.3286082148551941, param_update_rel_l2=1.7821519869375422 |
| cnn | 644 | False | True | True | True | valid_experiment_failure | strict_metrics: loss_diff=0.14952731132507324, grad_diff=0.4195643365383148, param_update_rel_l2=2.8098683289599826 |
| resnet | 642 | False | True | True | True | valid_experiment_failure | strict_metrics: loss_diff=0.30328261852264404, grad_diff=0.22558599710464478, param_update_rel_l2=1.4380749442979144 |
| resnet | 643 | False | True | True | True | valid_experiment_failure | strict_metrics: loss_diff=0.22748899459838867, grad_diff=0.06297802925109863, param_update_rel_l2=1.4079307608156544 |
| resnet | 644 | False | True | True | True | valid_experiment_failure | strict_metrics: loss_diff=0.007476449012756348, grad_diff=0.3610232472419739, param_update_rel_l2=1.4073295812041144 |
| transformer_classifier | 642 | False | True | True | True | valid_experiment_failure | strict_metrics: loss_diff=0.009459257125854492, grad_diff=0.14035195112228394, param_update_rel_l2=1.4782959056082763 |
| transformer_classifier | 643 | False | True | True | True | valid_experiment_failure | strict_metrics: loss_diff=0.10919368267059326, grad_diff=0.03235065937042236, param_update_rel_l2=1.42110448908233 |
| transformer_classifier | 644 | False | True | True | True | valid_experiment_failure | strict_metrics: loss_diff=0.1435868740081787, grad_diff=0.07440495491027832, param_update_rel_l2=1.4255705731108457 |
| tiny_causal_lm | 642 | False | True | True | True | valid_experiment_failure | strict_metrics: loss_diff=0.004890918731689453, grad_diff=0.012967824935913086, param_update_rel_l2=1.3825202877649028 |
| tiny_causal_lm | 643 | False | True | True | True | valid_experiment_failure | strict_metrics: loss_diff=0.004876613616943359, grad_diff=0.013995587825775146, param_update_rel_l2=1.4115920960738622 |
| tiny_causal_lm | 644 | False | True | True | True | valid_experiment_failure | strict_metrics: loss_diff=0.04205513000488281, grad_diff=0.05558282136917114, param_update_rel_l2=1.4690903031954472 |
