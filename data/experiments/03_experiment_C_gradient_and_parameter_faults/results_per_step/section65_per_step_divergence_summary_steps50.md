# Section 6.6 Faulted Per-Step Divergence

This report records fault-conditioned PyTorch/torch4ms divergence for teacher-forced and free-running coupling.

## Self-checks

- `row_count`: ok=True; expected=3600, observed=3600
- `complete_grid`: ok=True; expected_combinations=72, observed_combinations=72, malformed_groups={}
- `no_nan_or_infinity`: ok=True; violations=[]
- `none_reproduces_section66`: ok=True; max_loss_abs_diff=3.814697265625e-06, max_param_update_rel_l2=4.852178220524941e-06
- `grad_wrong_teacher_forced`: ok=True; violations=0
- `param_wrong_teacher_forced`: ok=True; violations=0

## Divergence summary

| Coupling | Fault | Model | Rows | Failed rows | First loss > threshold | First grad > threshold | First update > threshold | Max loss diff | Max update rel L2 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| free-running | grad_wrong | cnn | 150 | 0 | None | 1 | 1 | 0.010042071342468262 | 0.5110113008964731 |
| free-running | grad_wrong | mlp | 150 | 0 | None | 1 | 1 | 0.008316993713378906 | 0.7640777280155095 |
| free-running | grad_wrong | tiny_causal_lm | 150 | 0 | 10 | 1 | 1 | 0.11441564559936523 | 0.5028086971166866 |
| free-running | grad_wrong | transformer | 150 | 0 | None | 1 | 1 | 0.012206315994262695 | 0.5334699646133747 |
| free-running | none | cnn | 150 | 0 | None | None | None | 2.9802322387695312e-06 | 4.807672668209247e-06 |
| free-running | none | mlp | 150 | 0 | None | None | None | 2.0265579223632812e-06 | 3.862476270318606e-06 |
| free-running | none | tiny_causal_lm | 150 | 0 | None | None | None | 3.814697265625e-06 | 2.7654417143470533e-06 |
| free-running | none | transformer | 150 | 0 | None | None | None | 2.384185791015625e-07 | 2.434423607619712e-06 |
| free-running | param_wrong | cnn | 150 | 0 | None | None | 1 | 0.00025451183319091797 | 0.18580803920172562 |
| free-running | param_wrong | mlp | 150 | 0 | None | None | 1 | 0.010054469108581543 | 0.9141554196670687 |
| free-running | param_wrong | tiny_causal_lm | 150 | 0 | 6 | None | 1 | 0.22623062133789062 | 0.9962489630048351 |
| free-running | param_wrong | transformer | 150 | 0 | 20 | None | 1 | 0.02383744716644287 | 0.9820194392251416 |
| teacher-forced | grad_wrong | cnn | 150 | 0 | None | 1 | 1 | 2.9802322387695312e-06 | 0.5000007803272117 |
| teacher-forced | grad_wrong | mlp | 150 | 0 | None | 1 | 1 | 2.0265579223632812e-06 | 0.5000006961055175 |
| teacher-forced | grad_wrong | tiny_causal_lm | 150 | 0 | None | 1 | 1 | 3.814697265625e-06 | 0.5000046617131648 |
| teacher-forced | grad_wrong | transformer | 150 | 0 | None | 1 | 1 | 2.384185791015625e-07 | 0.5000020166638485 |
| teacher-forced | none | cnn | 150 | 0 | None | None | None | 2.9802322387695312e-06 | 4.852178220524941e-06 |
| teacher-forced | none | mlp | 150 | 0 | None | None | None | 2.0265579223632812e-06 | 3.7765330217576477e-06 |
| teacher-forced | none | tiny_causal_lm | 150 | 0 | None | None | None | 3.814697265625e-06 | 2.7653426685045875e-06 |
| teacher-forced | none | transformer | 150 | 0 | None | None | None | 2.384185791015625e-07 | 2.3009891954307467e-06 |
| teacher-forced | param_wrong | cnn | 150 | 0 | None | None | 1 | 2.9802322387695312e-06 | 0.18580192207990165 |
| teacher-forced | param_wrong | mlp | 150 | 0 | None | None | 1 | 2.0265579223632812e-06 | 0.9141554196670687 |
| teacher-forced | param_wrong | tiny_causal_lm | 150 | 0 | None | None | 1 | 3.814697265625e-06 | 0.9962489630048351 |
| teacher-forced | param_wrong | transformer | 150 | 0 | None | None | 1 | 2.384185791015625e-07 | 0.9820091417938026 |

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
