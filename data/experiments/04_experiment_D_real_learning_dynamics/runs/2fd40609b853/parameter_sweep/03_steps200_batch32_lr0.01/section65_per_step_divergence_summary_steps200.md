# Section 6.6 Faulted Per-Step Divergence

This report records fault-conditioned PyTorch/torch4ms divergence for teacher-forced and free-running coupling.

## Self-checks

- `row_count`: ok=True; expected=800, observed=800
- `complete_grid`: ok=True; expected_combinations=4, observed_combinations=4, malformed_groups={}
- `no_nan_or_infinity`: ok=True; violations=[]
- `none_reproduces_section66`: ok=True; max_loss_abs_diff=3.814697265625e-06, max_param_update_rel_l2=2.5654652732602742e-05

## Divergence summary

| Coupling | Fault | Model | Rows | Failed rows | First loss > threshold | First grad > threshold | First update > threshold | Max loss diff | Max update rel L2 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| free-running | none | cnn | 200 | 0 | None | None | None | 3.5762786865234375e-07 | 2.5654652732602742e-05 |
| free-running | none | mlp | 200 | 0 | None | None | None | 1.7881393432617188e-06 | 1.0647265539109452e-05 |
| free-running | none | tiny_causal_lm | 200 | 0 | None | None | None | 3.814697265625e-06 | 9.157131306089088e-06 |
| free-running | none | transformer | 200 | 0 | None | None | None | 2.384185791015625e-07 | 2.2445821336680033e-05 |

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
