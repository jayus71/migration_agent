# Section 6.5.2 Final Fixer Classification Repair Evaluation

This paper-facing experiment evaluates the final layered verifier and final LLM fixer on a fixed 25-category, 50-instance controlled fault pool. Each category is represented by two model-assigned instances.

- mode: `real_llm`
- blind: `True`
- instance suite: `fixed50`
- total instances: 50
- strict success: 35
- failed: 15
- strict repair rate: 70.0%
- valid model bindings: 50/50
- distinct workload fingerprints: 50
- diagnosis layer accuracy: 96.0%

## Table 1. By Failure Layer

| Failure layer | Categories | Instances | Strict success | Strict repair rate | Repair@1 | Repair@2 | Repair@4 | Median rounds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `execution` | 10 | 20 | 16 | 80.0% | 55.0% | 60.0% | 80.0% | 1 |
| `numerical` | 7 | 14 | 7 | 50.0% | 42.9% | 42.9% | 50.0% | 1 |
| `gradient_update` | 8 | 16 | 12 | 75.0% | 75.0% | 75.0% | 75.0% | 1 |
| `mixed` | 0 | 0 | 0 | 0.0% | 0.0% | 0.0% | 0.0% |  |
| `overall` | 25 | 50 | 35 | 70.0% | 58.0% | 60.0% | 70.0% | 1 |

## Table 2. By Repair Scope

| Repair scope | Instances | Strict success | Repair rate | Repair@1 | Median rounds |
|---|---:|---:|---:|---:|---:|
| `candidate_level` | 26 | 26 | 100.0% | 100.0% | 1 |
| `core_autograd_optimizer` | 4 | 0 | 0.0% | 0.0% |  |
| `core_operator` | 20 | 9 | 45.0% | 15.0% | 3 |

## Table 3. Category Coverage

| Layer | Total categories | Categories repaired | Category coverage |
|---|---:|---:|---:|
| `execution` | 10 | 8 | 80.0% |
| `numerical` | 7 | 4 | 57.1% |
| `gradient_update` | 8 | 6 | 75.0% |
| `mixed` | 0 | 0 | 0.0% |
| `overall` | 25 | 18 | 72.0% |

## Table 4. Failure Reasons

| Failure reason | Execution | Numerical | Gradient/update | Mixed | Total |
|---|---:|---:|---:|---:|---:|
| `invalid_model_binding` | 0 | 0 | 0 | 0 | 0 |
| `wrong_repair_scope` | 0 | 0 | 0 | 0 | 0 |
| `wrong_root_cause_hypothesis` | 2 | 0 | 0 | 0 | 2 |
| `invalid_patch` | 0 | 0 | 0 | 0 | 0 |
| `numerical_mismatch_remained` | 0 | 0 | 0 | 0 | 0 |
| `gradient_update_mismatch_remained` | 0 | 0 | 4 | 0 | 4 |
| `regression_failure` | 0 | 0 | 0 | 0 | 0 |
| `repair_budget_exhausted` | 2 | 7 | 0 | 0 | 9 |

## Per-instance Results

| Instance | Fault | Model label | Workload | Bound | Expected layer | Predicted layer | Correct | Scope | Success | Attempts | Validation | Restore | Failure reason |
|---|---|---|---|---:|---|---|---:|---|---:|---:|---|---|---|
| `EX-01-A` | `EX-01` | `M1 CNN` | `cnn` | 1 | `execution` | `execution` | 1 | `candidate` | 1 | 1 | `verified_restored` | `True` | `` |
| `EX-01-B` | `EX-01` | `M2 Image MLP` | `mlp` | 1 | `execution` | `execution` | 1 | `candidate` | 1 | 1 | `verified_restored` | `True` | `` |
| `EX-02-A` | `EX-02` | `M1 CNN` | `cnn` | 1 | `execution` | `execution` | 1 | `candidate` | 1 | 1 | `verified_restored` | `True` | `` |
| `EX-02-B` | `EX-02` | `M3 Transformer Classifier` | `transformer` | 1 | `execution` | `execution` | 1 | `candidate` | 1 | 1 | `verified_restored` | `True` | `` |
| `EX-03-A` | `EX-03` | `M1 CNN` | `cnn` | 1 | `execution` | `execution` | 1 | `candidate` | 1 | 1 | `verified_restored` | `True` | `` |
| `EX-03-B` | `EX-03` | `M4 Tiny Causal LM` | `causal_lm` | 1 | `execution` | `execution` | 1 | `candidate` | 1 | 1 | `verified_restored` | `True` | `` |
| `EX-04-A` | `EX-04` | `M2 Image MLP` | `mlp` | 1 | `execution` | `execution` | 1 | `candidate` | 1 | 1 | `verified_restored` | `True` | `` |
| `EX-04-B` | `EX-04` | `M3 Transformer Classifier` | `transformer` | 1 | `execution` | `execution` | 1 | `candidate` | 1 | 1 | `verified_restored` | `True` | `` |
| `EX-05-A` | `EX-05` | `M2 Image MLP` | `mlp` | 1 | `execution` | `execution` | 1 | `candidate` | 1 | 1 | `verified_restored` | `True` | `` |
| `EX-05-B` | `EX-05` | `M4 Tiny Causal LM` | `causal_lm` | 1 | `execution` | `execution` | 1 | `candidate` | 1 | 1 | `verified_restored` | `True` | `` |
| `EX-06-A` | `EX-06` | `M3 Transformer Classifier` | `transformer` | 1 | `execution` | `execution` | 1 | `core_operator` | 0 | 0 | `` | `True` | `wrong_root_cause_hypothesis` |
| `EX-06-B` | `EX-06` | `M4 Tiny Causal LM` | `causal_lm` | 1 | `execution` | `execution` | 1 | `core_operator` | 0 | 0 | `` | `True` | `wrong_root_cause_hypothesis` |
| `EX-07-A` | `EX-07` | `M1 CNN` | `cnn` | 1 | `execution` | `execution` | 1 | `core_operator` | 1 | 2 | `verified_restored` | `True` | `` |
| `EX-07-B` | `EX-07` | `M2 Image MLP` | `mlp` | 1 | `execution` | `execution` | 1 | `core_operator` | 1 | 3 | `verified_restored` | `True` | `` |
| `EX-08-A` | `EX-08` | `M1 CNN` | `cnn` | 1 | `execution` | `execution` | 1 | `core_operator` | 0 | 4 | `` | `True` | `repair_budget_exhausted` |
| `EX-08-B` | `EX-08` | `M3 Transformer Classifier` | `transformer` | 1 | `execution` | `execution` | 1 | `core_operator` | 0 | 4 | `` | `True` | `repair_budget_exhausted` |
| `EX-09-A` | `EX-09` | `M1 CNN` | `cnn` | 1 | `execution` | `execution` | 1 | `core_operator` | 1 | 3 | `verified_restored` | `True` | `` |
| `EX-09-B` | `EX-09` | `M4 Tiny Causal LM` | `causal_lm` | 1 | `execution` | `execution` | 1 | `core_operator` | 1 | 3 | `verified_restored` | `True` | `` |
| `EX-10-A` | `EX-10` | `M2 Image MLP` | `mlp` | 1 | `execution` | `execution` | 1 | `core_operator` | 1 | 3 | `verified_restored` | `True` | `` |
| `EX-10-B` | `EX-10` | `M3 Transformer Classifier` | `transformer` | 1 | `execution` | `execution` | 1 | `core_operator` | 1 | 1 | `verified_restored` | `True` | `` |
| `NU-01-A` | `NU-01` | `M2 Image MLP` | `mlp` | 1 | `numerical` | `numerical` | 1 | `candidate` | 1 | 1 | `verified_restored` | `True` | `` |
| `NU-01-B` | `NU-01` | `M4 Tiny Causal LM` | `causal_lm` | 1 | `numerical` | `numerical` | 1 | `candidate` | 1 | 1 | `verified_restored` | `True` | `` |
| `NU-02-A` | `NU-02` | `M3 Transformer Classifier` | `transformer` | 1 | `numerical` | `numerical` | 1 | `candidate` | 1 | 1 | `verified_restored` | `True` | `` |
| `NU-02-B` | `NU-02` | `M4 Tiny Causal LM` | `causal_lm` | 1 | `numerical` | `numerical` | 1 | `candidate` | 1 | 1 | `verified_restored` | `True` | `` |
| `NU-03-A` | `NU-03` | `M1 CNN` | `cnn` | 1 | `numerical` | `numerical` | 1 | `core_operator` | 0 | 4 | `` | `True` | `repair_budget_exhausted` |
| `NU-03-B` | `NU-03` | `M2 Image MLP` | `mlp` | 1 | `numerical` | `numerical` | 1 | `core_operator` | 0 | 4 | `` | `True` | `repair_budget_exhausted` |
| `NU-04-A` | `NU-04` | `M1 CNN` | `cnn` | 1 | `numerical` | `numerical` | 1 | `core_operator` | 0 | 4 | `rolled_back` | `False` | `repair_budget_exhausted` |
| `NU-04-B` | `NU-04` | `M3 Transformer Classifier` | `transformer` | 1 | `numerical` | `numerical` | 1 | `core_operator` | 0 | 4 | `rolled_back` | `False` | `repair_budget_exhausted` |
| `NU-05-A` | `NU-05` | `M1 CNN` | `cnn` | 1 | `numerical` | `numerical` | 1 | `core_operator` | 0 | 4 | `` | `True` | `repair_budget_exhausted` |
| `NU-05-B` | `NU-05` | `M4 Tiny Causal LM` | `causal_lm` | 1 | `numerical` | `numerical` | 1 | `core_operator` | 1 | 4 | `verified_restored` | `True` | `` |
| `NU-06-A` | `NU-06` | `M2 Image MLP` | `mlp` | 1 | `numerical` | `numerical` | 1 | `core_operator` | 1 | 1 | `verified_restored` | `True` | `` |
| `NU-06-B` | `NU-06` | `M3 Transformer Classifier` | `transformer` | 1 | `numerical` | `numerical` | 1 | `core_operator` | 1 | 1 | `verified_restored` | `True` | `` |
| `NU-07-A` | `NU-07` | `M2 Image MLP` | `mlp` | 1 | `numerical` | `execution` | 0 | `core_operator` | 0 | 4 | `` | `True` | `repair_budget_exhausted` |
| `NU-07-B` | `NU-07` | `M4 Tiny Causal LM` | `causal_lm` | 1 | `numerical` | `execution` | 0 | `core_operator` | 0 | 4 | `` | `True` | `repair_budget_exhausted` |
| `GR-01-A` | `GR-01` | `M3 Transformer Classifier` | `transformer` | 1 | `gradient_update` | `gradient_update` | 1 | `candidate` | 1 | 1 | `verified_restored` | `True` | `` |
| `GR-01-B` | `GR-01` | `M4 Tiny Causal LM` | `causal_lm` | 1 | `gradient_update` | `gradient_update` | 1 | `candidate` | 1 | 1 | `verified_restored` | `True` | `` |
| `GR-02-A` | `GR-02` | `M1 CNN` | `cnn` | 1 | `gradient_update` | `gradient_update` | 1 | `candidate` | 1 | 1 | `verified_restored` | `True` | `` |
| `GR-02-B` | `GR-02` | `M2 Image MLP` | `mlp` | 1 | `gradient_update` | `gradient_update` | 1 | `candidate` | 1 | 1 | `verified_restored` | `True` | `` |
| `GR-03-A` | `GR-03` | `M1 CNN` | `cnn` | 1 | `gradient_update` | `gradient_update` | 1 | `candidate` | 1 | 1 | `verified_restored` | `True` | `` |
| `GR-03-B` | `GR-03` | `M3 Transformer Classifier` | `transformer` | 1 | `gradient_update` | `gradient_update` | 1 | `candidate` | 1 | 1 | `verified_restored` | `True` | `` |
| `GR-04-A` | `GR-04` | `M1 CNN` | `cnn` | 1 | `gradient_update` | `gradient_update` | 1 | `candidate` | 1 | 1 | `verified_restored` | `True` | `` |
| `GR-04-B` | `GR-04` | `M4 Tiny Causal LM` | `causal_lm` | 1 | `gradient_update` | `gradient_update` | 1 | `candidate` | 1 | 1 | `verified_restored` | `True` | `` |
| `GR-05-A` | `GR-05` | `M2 Image MLP` | `mlp` | 1 | `gradient_update` | `gradient_update` | 1 | `core_autograd_optimizer` | 0 | 4 | `` | `True` | `gradient_update_mismatch_remained` |
| `GR-05-B` | `GR-05` | `M3 Transformer Classifier` | `transformer` | 1 | `gradient_update` | `gradient_update` | 1 | `core_autograd_optimizer` | 0 | 4 | `` | `True` | `gradient_update_mismatch_remained` |
| `GR-06-A` | `GR-06` | `M2 Image MLP` | `mlp` | 1 | `gradient_update` | `gradient_update` | 1 | `candidate` | 1 | 1 | `verified_restored` | `True` | `` |
| `GR-06-B` | `GR-06` | `M4 Tiny Causal LM` | `causal_lm` | 1 | `gradient_update` | `gradient_update` | 1 | `candidate` | 1 | 1 | `verified_restored` | `True` | `` |
| `GR-07-A` | `GR-07` | `M3 Transformer Classifier` | `transformer` | 1 | `gradient_update` | `gradient_update` | 1 | `core_autograd_optimizer` | 0 | 4 | `dry_run_failed` | `True` | `gradient_update_mismatch_remained` |
| `GR-07-B` | `GR-07` | `M4 Tiny Causal LM` | `causal_lm` | 1 | `gradient_update` | `gradient_update` | 1 | `core_autograd_optimizer` | 0 | 4 | `` | `True` | `gradient_update_mismatch_remained` |
| `GR-08-A` | `GR-08` | `M1 CNN` | `cnn` | 1 | `gradient_update` | `gradient_update` | 1 | `candidate` | 1 | 1 | `verified_restored` | `True` | `` |
| `GR-08-B` | `GR-08` | `M2 Image MLP` | `mlp` | 1 | `gradient_update` | `gradient_update` | 1 | `candidate` | 1 | 1 | `verified_restored` | `True` | `` |
