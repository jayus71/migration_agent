# Paper Experiment Results Index

This index keeps only the latest paper-facing result for each experiment. Historical,
superseded, and smoke-result directories are intentionally omitted.

Local experiment root:

```text
F:\torchax\autofix\ascend-torch4ms
```

Manuscript source:

```text
F:\torchax\autofix\torch4ms_paper\conference_101719.tex
```

## Selected Results


| Section       | Use in paper                                | Main local path                                                                                        | Notes                                                                  |
| ------------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------- |
| 6.3           | feedback granularity ablation               | `experiments/paper_section_63_64/results/section63_feedback_ablation_nu04_clean_alias_rerun_20260715/` | latest real-LLM rerun; clean-alias sentinel set: EX-01 / NU-04 / GR-07 |
| 6.4.1         | multi-scope feedback x Fixer-guide ablation | `experiments/paper_section_63_64/results_section641_multiscope_v1/`                                    | real LLM, candidate / core operator / core autograd-optimizer scopes   |
| 6.4.2         | Translator guide ablation                   | `experiments/paper_section_63_64/results_section642_translator_guide_ablation_v4/`                     | one-shot Translator, Fixer disabled, held-out migration tasks          |
| 6.5 signal    | verifier signal effectiveness               | `experiments/paper_section_65_66/results_section65_signal_sanity_current/`                             | execution / numerical / gradient-update signal separation              |
| 6.5 repair    | final fixed50 repair evaluation             | `experiments/paper_section_65_66/results_section65_fixed50_full_real/`                                 | real LLM, 25 categories / 50 instances                                 |
| 6.6 real-data | real-data training consistency              | `experiments/paper_section_65_66/results_realdata_66/`                                                 | CIFAR-10 and AG News, 50-step trajectories                             |
| 6.7 signal    | torchax cross-bridge signal pilot           | `autofix/reports/torchax_verifier_current_signal_synced/`                                              | torchax signal-only verification                                       |
| 6.7 repair    | torchax candidate-level repair pilot        | `experiments/paper_section_67/results_fixer_torchax/`                                                  | bounded candidate-level fixer on EX-01 / NU-01 / GR-01                 |


## 6.3 NU-04 Feedback Granularity

Path:

```text
experiments/paper_section_63_64/results/section63_feedback_ablation_nu04_clean_alias_rerun_20260715/
```

Key files:

```text
section63_summary.json
section63_episode_results.csv
section63_summary_by_fault_type.csv
section63_summary_by_feedback.csv
```

Summary:


| Item                | Value                                                  |
| ------------------- | ------------------------------------------------------ |
| mode                | real_llm                                               |
| models              | CNN, Image MLP, Transformer Classifier, Tiny Causal LM |
| selected faults     | EX-01, NU-04, GR-07                                    |
| feedback conditions | exec_only, exec_num, exec_num_grad                     |
| total episodes      | 36                                                     |
| strict success      | 24                                                     |



| Feedback condition | Tasks | Strict success | Repair@1 | Repair@4 | Median rounds |
| ------------------ | ----- | -------------- | -------- | -------- | ------------- |
| exec_only          | 12    | 4              | 33.3%    | 33.3%    | 1             |
| exec_num           | 12    | 8              | 66.7%    | 66.7%    | 1             |
| exec_num_grad      | 12    | 12             | 100.0%   | 100.0%   | 1             |


## 6.4.1 Multi-Scope Feedback x Fixer-Guide Ablation

Path:

```text
experiments/paper_section_63_64/results_section641_multiscope_v1/
```

Key files:

```text
section641_multiscope_raw.json
section641_tasks.csv
section641_scope_summary.csv
section641_summary.md
section641_private_manifest.json
```

Summary:


| Scope                   | Feedback | Guide | Tasks | Strict success | Repair@1 | Repair@4 | OOS edit rate |
| ----------------------- | -------- | ----- | ----- | -------------- | -------- | -------- | ------------- |
| candidate               | binary   | off   | 12    | 0/12           | 0.0%     | 0.0%     | 0.0%          |
| candidate               | layered  | off   | 12    | 12/12          | 100.0%   | 100.0%   | 0.0%          |
| candidate               | binary   | on    | 12    | 0/12           | 0.0%     | 0.0%     | 0.0%          |
| candidate               | layered  | on    | 12    | 8/12           | 58.3%    | 66.7%    | 0.0%          |
| core operator           | binary   | off   | 8     | 0/8            | 0.0%     | 0.0%     | 0.0%          |
| core operator           | layered  | off   | 8     | 6/8            | 50.0%    | 75.0%    | 12.5%         |
| core operator           | binary   | on    | 8     | 0/8            | 0.0%     | 0.0%     | 0.0%          |
| core operator           | layered  | on    | 8     | 6/8            | 50.0%    | 75.0%    | 0.0%          |
| core autograd/optimizer | binary   | off   | 4     | 0/4            | 0.0%     | 0.0%     | 0.0%          |
| core autograd/optimizer | layered  | off   | 4     | 0/4            | 0.0%     | 0.0%     | 0.0%          |
| core autograd/optimizer | binary   | on    | 4     | 0/4            | 0.0%     | 0.0%     | 0.0%          |
| core autograd/optimizer | layered  | on    | 4     | 0/4            | 0.0%     | 0.0%     | 0.0%          |


The latest run contains 24 base tasks and 96 condition runs with a four-round
budget. Core conditions use isolated worktrees and FaultSpec-authorized edit
paths.

## 6.4.2 Translator Guide Ablation

Path:

```text
experiments/paper_section_63_64/results_section642_translator_guide_ablation_v4/
```

Key files:

```text
section642_translator_guide_ablation_raw.json
section642_translator_guide_ablation_tasks.csv
section642_translator_guide_ablation_summary.md
```

Summary:


| Condition            | Models | Runs | Compile | Execution | Training | Translation Success@1 |
| -------------------- | ------ | ---- | ------- | --------- | -------- | --------------------- |
| Translator guide off | 5      | 15   | 13.3%   | 13.3%     | 0.0%     | 0.0%                  |
| Translator guide on  | 5      | 15   | 100.0%  | 100.0%    | 100.0%   | 100.0%                |


Fixer is disabled in this experiment. Each run makes one Translator call and
evaluates the resulting `patch_v0` on held-out Image MLP, CNN, ResNet,
Transformer-classifier, and tiny-causal-LM tasks.

## 6.5 Signal Effectiveness

Path:

```text
experiments/paper_section_65_66/results_section65_signal_sanity_current/
```

Key files:

```text
section65_signal_effectiveness_raw.json
section65_signal_effectiveness_table.csv
section65_signal_effectiveness_summary.md
```

Summary:


| Model          | Fault types                    | Runs per type | Expected signal detection |
| -------------- | ------------------------------ | ------------- | ------------------------- |
| CNN            | execution / numeric / training | 3             | 100.0%                    |
| MLP            | execution / numeric / training | 3             | 100.0%                    |
| Tiny Causal LM | execution / numeric / training | 3             | 100.0%                    |
| Transformer    | execution / numeric / training | 3             | 100.0%                    |


## 6.5 Fixed50 Repair

Path:

```text
experiments/paper_section_65_66/results_section65_fixed50_full_real/
```

Key files:

```text
section65_fault_pool_repair_raw.json
section65_fault_pool_repair_summary.md
section65_fault_pool_repair_table.csv
section65_fault_pool_repair_layer_summary.csv
section65_fault_pool_repair_scope_summary.csv
section65_fault_pool_repair_category_coverage.csv
section65_fault_pool_repair_failure_reasons.csv
```

Summary:


| Failure layer   | Categories | Instances | Strict success | Strict repair rate | Repair@1 | Repair@2 | Repair@4 | Median rounds |
| --------------- | ---------- | --------- | -------------- | ------------------ | -------- | -------- | -------- | ------------- |
| execution       | 10         | 20        | 19             | 95.0%              | 65.0%    | 95.0%    | 95.0%    | 1             |
| numerical       | 7          | 14        | 13             | 92.9%              | 50.0%    | 71.4%    | 92.9%    | 1             |
| gradient_update | 8          | 16        | 14             | 87.5%              | 62.5%    | 87.5%    | 87.5%    | 1             |
| overall         | 25         | 50        | 46             | 92.0%              | 60.0%    | 86.0%    | 92.0%    | 1             |



| Repair scope            | Instances | Strict success | Repair rate | Repair@1 | Median rounds |
| ----------------------- | --------- | -------------- | ----------- | -------- | ------------- |
| candidate_level         | 26        | 25             | 96.2%       | 84.6%    | 1             |
| core_operator           | 20        | 19             | 95.0%       | 40.0%    | 2             |
| core_autograd_optimizer | 4         | 2              | 50.0%       | 0.0%     | 2             |


## 6.6 Real-Data Training Consistency

Path:

```text
experiments/paper_section_65_66/results_realdata_66/
```

Key files:

```text
section66_realdata_training_consistency_raw_steps50.json
section66_realdata_training_consistency_steps_steps50.csv
section66_realdata_training_consistency_summary_steps50.md
figures/loss_trend_steps50.png
figures/grad_norm_diff_steps50.png
figures/param_update_diff_steps50.png
```

Summary:


| Model          | Runs | Strict pass rate | Mean loss diff         | Max loss diff          | Mean grad diff         | Mean param update rel L2 |
| -------------- | ---- | ---------------- | ---------------------- | ---------------------- | ---------------------- | ------------------------ |
| cnn            | 3    | 1.000            | 4.569689432779948e-07  | 2.9802322387695312e-06 | 1.509984334309896e-08  | 1.146376709859271e-06    |
| nlp            | 3    | 1.000            | 6.167093912760416e-07  | 1.6689300537109375e-06 | 1.4413769046465556e-08 | 3.825308604689108e-06    |
| tiny_causal_lm | 3    | 1.000            | 1.7452239990234376e-06 | 3.814697265625e-06     | 3.83456548055013e-08   | 1.126530534752786e-06    |
| transformer    | 3    | 1.000            | 5.642573038736979e-08  | 2.384185791015625e-07  | 1.7484029134114583e-08 | 7.912662454727441e-07    |


## 6.7 Torchax Signal

Path:

```text
autofix/reports/torchax_verifier_current_signal_synced/
```

Key files:

```text
torchax_verifier_summary.json
torchax_verifier_summary.md
```

Summary:


| Fault type      | Tasks | Correct first-layer detection | Accuracy |
| --------------- | ----- | ----------------------------- | -------- |
| execution       | 2     | 2                             | 100.0%   |
| numerical       | 2     | 2                             | 100.0%   |
| gradient_update | 2     | 2                             | 100.0%   |
| overall         | 6     | 6                             | 100.0%   |


## 6.7 Torchax Repair

Path:

```text
experiments/paper_section_67/results_fixer_torchax/
```

Key files:

```text
section67_fixer_torchax_raw.json
section67_fixer_torchax_tasks.csv
section67_fixer_torchax_summary.md
```

Summary:


| Metric                 | Value  |
| ---------------------- | ------ |
| tasks                  | 6      |
| clean pass             | 2/2    |
| layer accuracy         | 100.0% |
| diagnosis completeness | 100.0% |
| repair success         | 100.0% |
| final strict pass      | 100.0% |
| Repair@1               | 100.0% |
| Repair@3               | 100.0% |
| median rounds          | 1.0    |


