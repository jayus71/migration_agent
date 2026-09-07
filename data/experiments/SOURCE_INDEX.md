# 结果来源索引

本次只复制结果，没有合并分支。

| 包 | 本地来源 worktree / 远端来源 | 来源 worktree HEAD 或运行 commit | 本地归档位置 |
|---|---|---|---|
| A | `experiment-ab-fixed60` | `81181da81efa6c6c7dbbd9b0eae0f370ca7a4b2b` | `01_experiment_A_paired_threshold_revalidation/formal_final` |
| B | `experiment-ab-fixed60` | worktree HEAD `81181da…`；包内记录运行 commit `f065b612e31520b26b4ae233dc117b77341fab79` | `02_experiment_B_fixed60/formal_summary_f065b61` |
| C | `experiment-ab-fixed60` | `81181da81efa6c6c7dbbd9b0eae0f370ca7a4b2b` | `03_experiment_C_gradient_and_parameter_faults` |
| D | `experiment-d-real-learning-dynamics` | worktree HEAD `b7fe540e842033a66a357fd0520c32e4ee8a9931`；汇总包记录 commit `2fd40609b85314400d951a7d6897bfb66a5af558` | `04_experiment_D_real_learning_dynamics/runs/2fd40609b853` |
| E normalized | `experiment-e-cte-msadapter` | `b2f2485a9e6cbe5670ad1a308ef8a5b1c3b97aae` | `05_experiment_E_track_a_rerun/final` |
| E T-MSA patched | `experiment-e-msa-fix` | `6bce039f00603df2ed224917dd96849efcaf336d` | `05_experiment_E_track_a_rerun/T-MSA/formal_patched_5261529_5x3` |
| E T-HIER strict-sync rerun | `experiment-e-thier-strict-sync-fix`; remote `ascend-torch4ms-exp-e-thier-sync-b32d9f4` | run `b32d9f4a27ed90646943b671d43f8616b4ad73fe`; summary renderer `18bbf43a70611bf82f930590a7172d0e19b9523e` | `05_experiment_E_track_a_rerun/T-HIER/formal_b32d9f4_strict_sync_5x3_20260906` |
| F | 实验要求指定并入 D/I | 无独立 commit | `06_experiment_F_merged_into_D_and_I` |
| G | `experiment-ab-fixed60` | `81181da81efa6c6c7dbbd9b0eae0f370ca7a4b2b`；各方法运行 provenance 见包内文件 | `07_experiment_G_multi_fault/results_six_methods_corrected` |
| H | `llm-fixer-per-step` | worktree HEAD `1ef469109ce09ba5f4773eac634bcd270e821be2`；实际子集运行 commits 见包内 manifest | `08_experiment_H_multi_llm/final_results` |
| I | 远端 `/media/main/whj/projects/torch4ms/ascend-torch4ms-exp-i-core-8c5c635/.../runs_real_core_v3` | `8c5c635b0c5c718fab052b885966be8980eea6ad` | `09_experiment_I_real_translation/runs_real_core_v3` |
| J | `experiment-j-baselines`；前四条件来自 `formal_run_2d6bd3d`，`r_hier/r_reverse` 来自 `confirmatory_repeat3_hier_first` | 两个来源均使用 `2d6bd3dfd4f3aefdcc1dc6d4d91277f181b141a8`；`r_binary` 的原始导入 provenance 仍见包内 manifest | `10_experiment_J_feedback_ablation/formal_run_2d6bd3d` |
| K | `experiment-ab-fixed60` | worktree HEAD `81181da…`；包内记录正式运行 commit `0d71f58` | `11_experiment_K_layer_localization` |

H 的实际运行 provenance：DeepSeek `faa71754875e3b69af88d6d4405f9b9a24233827`，Qwen `9fe890436e7c1d834a64fd24685cec2f5e2126f1`，GLM 5.2 `df374a9839157a68dafa145f5c2d529b60752e72`，GLM 5.3 Flash recovery `58e9f52054a062157899496cdb865565f5128cfd`。
