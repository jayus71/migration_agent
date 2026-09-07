# Experiment H final results

This directory is the canonical, credential-free result package for Experiment H. It contains 27 conditions (3 backbone groups × 3 methods × 3 seeds), with 50 Fixed50 instances per condition and 1,350 canonical instance records in total. The final audit found no terminal provider or environment errors.

## Main results

Repair rates are pooled over three seeds (150 instances per row). `±` is the sample standard deviation of the three seed-level Repair@4 values, in percentage points.

| Backbone group | Method | Repair@1 | Repair@2 | Repair@4 | Repair@4 seed mean ± SD | Successes | LLM calls | Total tokens | Wall time |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| DeepSeek V4 Flash | R-HIER | 86.67% | 92.67% | **95.33%** | 95.33 ± 1.15 | 143/150 | 112 | 666,220 | 2.01 h |
| DeepSeek V4 Flash | R-EXEC | 66.00% | 66.67% | 67.33% | 67.33 ± 1.15 | 101/150 | 132 | 549,064 | 5.23 h |
| DeepSeek V4 Flash | Direct LLM Repair | 80.67% | 84.67% | 86.67% | 86.67 ± 1.15 | 130/150 | 224 | 5,861,756 | 6.53 h |
| Qwen 3.7 Plus | R-HIER | 60.00% | 68.67% | 74.00% | 74.00 ± 5.29 | 111/150 | 153 | 1,101,204 | 7.53 h |
| Qwen 3.7 Plus | R-EXEC | 58.67% | 62.00% | 64.00% | 64.00 ± 0.00 | 96/150 | 156 | 551,777 | 4.97 h |
| Qwen 3.7 Plus | Direct LLM Repair | 80.67% | 83.33% | **87.33%** | 87.33 ± 1.15 | 131/150 | 225 | 4,934,141 | 5.40 h |
| GLM family (mixed; see warning) | R-HIER | 72.00% | 78.00% | 84.00% | 84.00 ± 8.72 | 126/150 | 131 | 502,444 | 3.07 h |
| GLM family (mixed; see warning) | R-EXEC | 63.33% | 64.00% | 64.00% | 64.00 ± 0.00 | 96/150 | 145 | 350,970 | 4.05 h |
| GLM 5.3 Flash | Direct LLM Repair | 87.33% | 88.00% | **88.67%** | 88.67 ± 1.15 | 133/150 | 204 | 4,115,609 | 12.31 h |

No API price or monetary-cost estimate is reported. Token counts and wall time are retained as provider-neutral efficiency measurements.

## Interpretation

- On DeepSeek V4 Flash, R-HIER is the strongest method: Repair@4 is 95.33%, 8.66 percentage points above Direct LLM Repair, while using about 89% fewer tokens.
- On Qwen 3.7 Plus, Direct LLM Repair is strongest at 87.33%; R-HIER reaches 74.00% and R-EXEC 64.00%. Hierarchical feedback therefore does not transfer uniformly across backbones.
- In the mixed GLM completion set, Direct reaches 88.67%, R-HIER 84.00%, and R-EXEC 64.00%. This is useful completion evidence but not a strict single-model three-seed comparison.
- Across all three backbone groups, R-HIER consistently outperforms R-EXEC. Its advantage over Direct is backbone-dependent.

## Configuration and validity warnings

The package preserves actual observed run metadata rather than silently normalizing it:

| Group | Exact model coverage | Temperature | Reasoning effort | Status |
|---|---|---|---|---|
| DeepSeek | `deepseek-v4-flash`, all 9 conditions | 0.1 for seeds 101/202; 0.0 for seed 303 | not explicitly recorded | Complete, but temperature is not identical across seeds |
| Qwen | `qwen3.7-plus`, all 9 conditions | 0.0 | not explicitly recorded | Complete |
| GLM | GLM 5.2 for seed 101/202 R-HIER and R-EXEC; GLM 5.3 Flash for all Direct conditions and seed 303 R-HIER/R-EXEC | 0.0 | `high` | Complete mixed-version set |

Consequently, the DeepSeek rows should not be described as a perfectly fixed-temperature three-seed experiment. The GLM rows must be labelled as mixed-version unless the four GLM 5.2 conditions are rerun with GLM 5.3 Flash (or vice versa).

The original DeepSeek manifest reports only 7/9 valid conditions because it scanned historical failed candidate files. The final validator instead checks the canonical raw artifact for internal methods and the canonical 50-row summary/raw set for Direct. All nine DeepSeek conditions pass that canonical check.

## Files

- `condition_summary.csv`: one row per seed/backbone/method condition.
- `aggregate_by_backbone_method.csv`: pooled metrics and seed-level Repair@4 dispersion.
- `manifest.json`: machine-readable provenance, validation results, source paths, and per-condition metrics.
- `_source_manifests/`: immutable copies of the four source-run manifests.
- `<exact-model>/seed_<seed>/<method>/`: canonical raw data, summaries, logs, localization output, and Direct candidate records. Retry staging, recovery backups, and mutable workspaces are excluded.

## Provenance

| Result subset | Runner commit |
|---|---|
| DeepSeek V4 Flash | `faa71754875e3b69af88d6d4405f9b9a24233827` |
| Qwen 3.7 Plus | `9fe890436e7c1d834a64fd24685cec2f5e2126f1` |
| GLM 5.2 | `df374a9839157a68dafa145f5c2d529b60752e72` |
| GLM 5.3 Flash final recovery | `58e9f52054a062157899496cdb865565f5128cfd` |

## Reproduce the summary

From the repository root, regenerate and validate all final tables without any API credentials:

```bash
python experiments/experiment_request_20260820/08_experiment_H_multi_llm/summarize_final_results.py
```

The command fails if the package no longer contains exactly 27 conditions, if a condition does not contain exactly 50 canonical instances, or if a terminal provider/environment error is present. Instructions for launching a fresh API-backed matrix are in the parent `reproduce.md`; API credentials and machine-specific absolute paths are intentionally omitted.
