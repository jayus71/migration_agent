# Paper Experiment Results Index

This index keeps only the latest paper-facing result for each experiment. Historical,
superseded, and smoke-result directories are intentionally omitted.

> **Updated 2026-08-14.** The paper's two main comparison tables now come from result
> bundles that live on **separate branches**, not on the branch this index originally
> assumed. Read the "Result branches" section below before resolving any path.
> Superseded entries are kept and marked rather than deleted, so the provenance of
> earlier drafts stays traceable.

## Result branches

Experiment repository: `https://gitee.com/feixiao13/ascend-torch4ms.git`

| Branch | Commit | Contains | Used by paper |
|---|---|---|---|
| `codex/llm-fixer-capability` | `f66cafe` | Sections 6.3–6.6 bundles, old 6.7 pilots | Yes (6.3–6.6) |
| `codex/track-b-repair-baselines` | `365652d` | `experiments/baselines/track_a/`, `experiments/baselines/full_hier_fixed50/` | Yes (`tab:end-to-end-results`, `tab:baseline-comparison`) |
| `codex/track-c-torchax-autofix` | `3352f71` | `experiments/baselines/track_c/` | Yes (`tab:track-c`) |

The paper repository's submodule pointer is pinned at `f66cafe`, which **predates**
Track A/B (2026-07-28) and Track C (2026-08-01). A plain clone plus `submodule update`
therefore does not retrieve the data behind the paper's current main tables.

## Selected Results


| Section       | Use in paper                                | Main local path                                                                                        | Notes                                                                  |
| ------------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------- |
| 6.3           | feedback granularity ablation               | `experiments/paper_section_63_64/results/section63_feedback_ablation_nu04_clean_alias_rerun_20260715/` | latest real-LLM rerun; clean-alias sentinel set: EX-01 / NU-04 / GR-07 |
| 6.4.1         | multi-scope feedback x Fixer-guide ablation | `experiments/paper_section_63_64/results_section641_multiscope_v1/`                                    | real LLM, candidate / core operator / core autograd-optimizer scopes   |
| 6.4.2         | Translator guide ablation                   | `experiments/paper_section_63_64/results_section642_translator_guide_ablation_v4/`                     | one-shot Translator, Fixer disabled, held-out migration tasks          |
| 6.5 signal    | verifier signal effectiveness               | `experiments/paper_section_65_66/results_section65_signal_sanity_current/`                             | execution / numerical / gradient-update signal separation              |
| 6.5 repair    | **superseded** — was fixed50 repair source  | `experiments/paper_section_65_66/results_section65_fixed50_full_real/`                                 | 46/50 = 92.0%. **No longer the paper's number**; superseded by Track B `r_hier` (50/50). Retained for provenance. |
| 6.6 real-data | real-data training consistency              | `experiments/paper_section_65_66/results_realdata_66/`                                                 | CIFAR-10 and AG News, 50-step trajectories                             |
| 6.7 signal    | **superseded** — torchax signal pilot       | `autofix/reports/torchax_verifier_current_signal_synced/`                                              | superseded by Track C; old 6.7 tables removed from the paper           |
| 6.7 repair    | **superseded** — torchax repair pilot       | `experiments/paper_section_67/results_fixer_torchax/`                                                  | superseded by Track C. The old 6.7 runner never imported TorchAX/JAX (see `EXPERIMENT_INTEGRITY_AUDIT_20260731.md` §5) |

### Track results (branches above)

| Track | Use in paper | Path | Branch | Notes |
|---|---|---|---|---|
| Track A | **not in paper** | `experiments/baselines/track_a/` | `codex/track-b-repair-baselines` | 5 migration baselines x 15 runs, complete. T-HIER 100% vs T-DIRECT / T-CTE / T-MSA / T-X2MS all 0%. Blocked from paper use: `raw/`, `candidates/`, `logs/` hold only `.gitkeep`; see audit §1, §2, §6 |
| Track B | `tab:end-to-end-results`, `tab:baseline-comparison` | `experiments/baselines/full_hier_fixed50/` | `codex/track-b-repair-baselines` | Fixed50, 6 baselines. Paper reports R-EXEC 33/50, R-FLAT 34/50, Direct 40/50, SWE-agent 46/50, R-HIER 50/50 |
| Track B | `tab:baseline-comparison` (added 2026-08-14) | `experiments/baselines/full_hier_fixed50/r_matchfix/` | `codex/track-b-repair-baselines` | MatchFixAgent 47/50 = 94.0%, the strongest external baseline. Now reported in the paper with a dagger footnote stating that its fragment-pair interface supplies the healthy implementation of the changed function (`run_external_repair_pilot.py:932-934,959-967`), so its rate is an upper bound rather than a blind-repair result |
| Track C | `tab:track-c` | `experiments/baselines/track_c/` | `codex/track-c-torchax-autofix` | PyTorch→JAX. R-HIER 6/6, Direct LLM 5/6, Ivy 0/6, torch2jax 0/6. Runner genuinely uses TorchAX + JAX + Optax |

### Metric definition note

Track B `Repair@1` in `tab:end-to-end-results` uses the runner's `effective_rounds`
field, matching `summary.json`'s `repair_at_1 = 0.84`. Recomputing from the `attempts`
column instead yields different values (execution 80.0%, core operator 65.0%,
overall 80.0%), because `EX-06-A` and `EX-06-B` record `attempts=0` with
`effective_rounds=1` and `patch_count=1`. `effective_rounds` is the self-consistent
definition; use it when reproducing the table.


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


