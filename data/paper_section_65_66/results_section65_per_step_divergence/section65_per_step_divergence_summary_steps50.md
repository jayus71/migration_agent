# Section 6.6 Faulted Per-Step Divergence

This report records fault-conditioned PyTorch/torch4ms divergence for teacher-forced and free-running coupling.

## Self-checks

- `row_count`: ok=True; expected=4800, observed=4800
- `complete_grid`: ok=True; expected_combinations=96, observed_combinations=96, malformed_groups={}
- `no_nan_or_infinity`: ok=True; violations=[]
- `none_reproduces_section66`: ok=True; max_loss_abs_diff=3.814697265625e-06, max_param_update_rel_l2=4.852178220524941e-06
- `training_teacher_forced`: ok=True; violations=0
- `training_free_running`: ok=True; bad_first_step=[], no_later_growth=[]
- `numeric_exceeds_loss_threshold`: ok=True; violations=0
- `execution_breaks_at_configured_step`: ok=True; fault_step=20, violations=0

## Divergence summary

| Coupling | Fault | Model | Rows | Failed rows | First loss > threshold | First grad > threshold | First update > threshold | Max loss diff | Max update rel L2 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| free-running | execution | cnn | 150 | 93 | None | None | None | 2.2649765014648438e-06 | 2.6985889661825346e-06 |
| free-running | execution | nlp | 150 | 93 | None | None | None | 2.0265579223632812e-06 | 3.862476270318606e-06 |
| free-running | execution | tiny_causal_lm | 150 | 93 | None | None | None | 3.814697265625e-06 | 2.1145946078187e-06 |
| free-running | execution | transformer | 150 | 93 | None | None | None | 1.1920928955078125e-07 | 2.25674711343645e-06 |
| free-running | none | cnn | 150 | 0 | None | None | None | 2.9802322387695312e-06 | 4.807672668209247e-06 |
| free-running | none | nlp | 150 | 0 | None | None | None | 2.0265579223632812e-06 | 3.862476270318606e-06 |
| free-running | none | tiny_causal_lm | 150 | 0 | None | None | None | 3.814697265625e-06 | 2.7654417143470533e-06 |
| free-running | none | transformer | 150 | 0 | None | None | None | 2.384185791015625e-07 | 2.434423607619712e-06 |
| free-running | numeric | cnn | 150 | 0 | 1 | 1 | 1 | 0.7399225234985352 | 1.626831105574557 |
| free-running | numeric | nlp | 150 | 0 | 1 | 1 | 1 | 0.8207583427429199 | 1.7075660558014225 |
| free-running | numeric | tiny_causal_lm | 150 | 0 | 1 | None | 1 | 0.07963800430297852 | 0.16144197477232522 |
| free-running | numeric | transformer | 150 | 0 | 1 | 1 | 1 | 1.1465837955474854 | 2.839557483926257 |
| free-running | training | cnn | 150 | 0 | 25 | None | 1 | 0.020601272583007812 | 1.0 |
| free-running | training | nlp | 150 | 0 | None | None | 1 | 0.01847851276397705 | 1.0 |
| free-running | training | tiny_causal_lm | 150 | 0 | 6 | None | 1 | 0.2302851676940918 | 1.0 |
| free-running | training | transformer | 150 | 0 | 20 | None | 1 | 0.024947643280029297 | 1.0 |
| teacher-forced | execution | cnn | 150 | 93 | None | None | None | 2.2649765014648438e-06 | 2.9958847791891246e-06 |
| teacher-forced | execution | nlp | 150 | 93 | None | None | None | 2.0265579223632812e-06 | 3.7765330217576477e-06 |
| teacher-forced | execution | tiny_causal_lm | 150 | 93 | None | None | None | 3.814697265625e-06 | 2.1142530522004963e-06 |
| teacher-forced | execution | transformer | 150 | 93 | None | None | None | 1.1920928955078125e-07 | 2.2567786058517945e-06 |
| teacher-forced | none | cnn | 150 | 0 | None | None | None | 2.9802322387695312e-06 | 4.852178220524941e-06 |
| teacher-forced | none | nlp | 150 | 0 | None | None | None | 2.0265579223632812e-06 | 3.7765330217576477e-06 |
| teacher-forced | none | tiny_causal_lm | 150 | 0 | None | None | None | 3.814697265625e-06 | 2.7653426685045875e-06 |
| teacher-forced | none | transformer | 150 | 0 | None | None | None | 2.384185791015625e-07 | 2.3009891954307467e-06 |
| teacher-forced | numeric | cnn | 150 | 0 | 1 | 1 | 1 | 0.7432374954223633 | 1.6592939197536216 |
| teacher-forced | numeric | nlp | 150 | 0 | 1 | 1 | 1 | 0.825253963470459 | 1.781728801109199 |
| teacher-forced | numeric | tiny_causal_lm | 150 | 0 | 1 | None | 1 | 0.07963800430297852 | 0.1639610872062328 |
| teacher-forced | numeric | transformer | 150 | 0 | 1 | 1 | 1 | 1.1647796630859375 | 2.959119955320132 |
| teacher-forced | training | cnn | 150 | 0 | None | None | 1 | 2.9802322387695312e-06 | 1.0 |
| teacher-forced | training | nlp | 150 | 0 | None | None | 1 | 2.0265579223632812e-06 | 1.0 |
| teacher-forced | training | tiny_causal_lm | 150 | 0 | None | None | 1 | 3.814697265625e-06 | 1.0 |
| teacher-forced | training | transformer | 150 | 0 | None | None | 1 | 2.384185791015625e-07 | 1.0 |

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
  "couplings": {
    "teacher-forced": "load the cloned PyTorch pre-step state before every candidate step",
    "free-running": "retain the candidate state produced by its preceding step"
  }
}
```
