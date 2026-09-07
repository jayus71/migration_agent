# Section 6.6 Faulted Per-Step Divergence

This report records fault-conditioned PyTorch/torch4ms divergence for teacher-forced and free-running coupling.

## Self-checks

- `row_count`: ok=True; expected=200, observed=200
- `complete_grid`: ok=True; expected_combinations=4, observed_combinations=4, malformed_groups={}
- `no_nan_or_infinity`: ok=True; violations=[]
- `none_reproduces_section66`: ok=True; max_loss_abs_diff=3.337860107421875e-06, max_param_update_rel_l2=2.104936054330947e-05

## Divergence summary

| Coupling | Fault | Model | Rows | Failed rows | First loss > threshold | First grad > threshold | First update > threshold | Max loss diff | Max update rel L2 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| free-running | none | cnn | 50 | 0 | None | None | None | 2.384185791015625e-07 | 2.104936054330947e-05 |
| free-running | none | mlp | 50 | 0 | None | None | None | 1.6689300537109375e-06 | 9.142865859039098e-06 |
| free-running | none | tiny_causal_lm | 50 | 0 | None | None | None | 3.337860107421875e-06 | 2.121445653128383e-06 |
| free-running | none | transformer | 50 | 0 | None | None | None | 2.384185791015625e-07 | 1.668227556594654e-05 |

## Fault injection

```json
{
  "none": {
    "method": "unmodified torch4ms candidate training"
  },
  "execution": {
    "method": "raise ControlledExecutionFault before the candidate forward pass",
    "fault_step": 20,
    "error": "ControlledExecutionFault: simulated torch4ms runtime/lowering failure"
  },
  "numeric": {
    "method": "apply the existing Section 6.5 perturb_output transform to candidate logits before loss",
    "logit_bias": 2.0,
    "state_restored": "model parameters are never modified by the perturbation"
  },
  "training": {
    "method": "run a valid candidate forward but suppress backward and optimizer update",
    "gradient_metrics": "unavailable and serialized as null/empty CSV cells",
    "candidate_update": "full-sized zero vector"
  },
  "grad_wrong": {
    "method": "scale every measured candidate gradient before optimizer.step",
    "scale": 1.5,
    "gradient_metrics": "measured after scaling"
  },
  "param_wrong": {
    "method": "measure correct gradients, then suppress updates for every other parameter",
    "gradient_metrics": "measured before corrupting optimizer routing"
  },
  "couplings": {
    "teacher-forced": "load the cloned PyTorch pre-step state before every candidate step",
    "free-running": "retain the candidate state produced by its preceding step"
  }
}
```
