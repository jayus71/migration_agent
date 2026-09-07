# Section 6.5 Signal Effectiveness

This report evaluates which verifier signal detects each controlled fault. It does not claim automatic repair success.

| Model | Fault | Runs | Expected signal detection | Minimal signal sets |
|---|---|---:|---:|---|
| `cnn` | `execution` | 3 | 1.000 | `exec` |
| `cnn` | `numeric` | 3 | 1.000 | `numeric+grad+param_update` |
| `cnn` | `training` | 3 | 1.000 | `grad+param_update` |
| `mlp` | `execution` | 3 | 1.000 | `exec` |
| `mlp` | `numeric` | 3 | 1.000 | `numeric+grad+param_update` |
| `mlp` | `training` | 3 | 1.000 | `grad+param_update` |
| `tiny_causal_lm` | `execution` | 3 | 1.000 | `exec` |
| `tiny_causal_lm` | `numeric` | 3 | 1.000 | `numeric+param_update` |
| `tiny_causal_lm` | `training` | 3 | 1.000 | `grad+param_update` |
| `transformer` | `execution` | 3 | 1.000 | `exec` |
| `transformer` | `numeric` | 3 | 1.000 | `numeric+grad+param_update` |
| `transformer` | `training` | 3 | 1.000 | `grad+param_update` |
