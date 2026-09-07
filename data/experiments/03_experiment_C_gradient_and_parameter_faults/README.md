# Experiment C: Incorrect Gradients and Incorrect Parameter Updates

Status: complete.

The experiment adds two measurable candidate-side faults to the Section 6.6
per-step divergence grid:

- `grad_wrong`: scales every candidate gradient by 1.5 after backward and before
  gradient measurement and `optimizer.step()`;
- `param_wrong`: measures the correct gradients, then suppresses every other
  parameter update before `optimizer.step()`.

## Grid and validation

The complete grid contains 3,600 rows: 4 models × 3 seeds × 2 coupling modes ×
3 faults × 50 steps. The request document states 1,800 rows, but the factors
listed in that same document multiply to 3,600; no factor was dropped to force
the incorrect total.

All built-in self-checks passed:

| Check | Result |
|---|---:|
| Complete 72-combination grid | pass |
| No NaN or infinity | pass |
| Clean candidate reproduces prior Section 6.6 | pass |
| `grad_wrong` teacher-forced contract | 600/600 pass |
| `param_wrong` teacher-forced contract | 600/600 pass |

The most conservative observed values were:

| Fault | max `loss_abs_diff` | gradient statistic | min `param_update_rel_l2` |
|---|---:|---:|---:|
| `grad_wrong`, teacher-forced | 3.815e-6 | min Δgrad = 0.09916 | 0.499996 |
| `param_wrong`, teacher-forced | 3.815e-6 | max Δgrad = 1.192e-7 | 0.042761 |

Thus `grad_wrong` preserves the forward path while producing present but wrong
gradients, and `param_wrong` preserves both forward and measured gradients while
changing the updated parameter subset.

Paper-facing raw data, CSV, and the generated summary are in `results_per_step/`.
The exact command is recorded in `reproduce.md`.
