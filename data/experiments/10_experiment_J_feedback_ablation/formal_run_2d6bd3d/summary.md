# Experiment J summary

`r_exec` is execution-only. `r_binary` retains full E/N/G detection but gives the Fixer only one aggregate strict pass/fail bit.

- commit: `2d6bd3dfd4f3aefdcc1dc6d4d91277f181b141a8`
- model: `deepseek-v4-flash`
- temperature: `0`
- repair attempts: `4`
- timeout: `300s`

This local consolidated view keeps `r_exec`, `r_binary`, `r_stage`, and
`r_flat` from `formal_run_2d6bd3d`, and replaces `r_hier` and `r_reverse` with
the independently completed third repeat `confirmatory_repeat3_hier_first`.
The per-condition source mapping is recorded in `manifest.json`.

| Condition | Strict repair | Repair@1 | Repair@2 | Repair@4 | LLM calls | Tokens | Wall time |
|---|---:|---:|---:|---:|---:|---:|---:|
| `r_exec` | 33/50 | 64.00% | 64.00% | 66.00% | 47 | 235952 | 8282.72s |
| `r_binary` | 34/50 | 64.00% | 68.00% | 68.00% | 44 | 747802 | 13964.31s |
| `r_stage` | 34/50 | 64.00% | 66.00% | 68.00% | 45 | 628216 | 11614.20s |
| `r_flat` | 34/50 | 64.00% | 68.00% | 68.00% | 44 | 430400 | 12143.67s |
| `r_hier` | 48/50 | 72.00% | 88.00% | 96.00% | 42 | 327312 | 4810.85s |
| `r_reverse` | 48/50 | 70.00% | 82.00% | 96.00% | 46 | 304188 | 5121.10s |

## Baseline meanings

- `r_exec`: Execution-only feedback: the Fixer sees runtime success/failure, exception type, and traceback. Numerical and gradient/update defects that execute normally do not trigger repair.
- `r_binary`: Strict aggregate binary feedback: the verifier checks execution, numerical, and gradient/update signals, then exposes only one overall pass/fail bit to the Fixer. It exposes no failing stage, metric, step, tensor, parameter, or repair route.
- `r_stage`: Stage-label feedback: the verifier checks all three layers and exposes only the first failing stage label, without numerical or tensor/parameter details.
- `r_flat`: Flat full feedback: execution, numerical, and gradient/update evidence is exposed as an unordered metric collection, without first-failure localization or routing.
- `r_hier`: Hierarchical LADDER feedback: full evidence is ordered execution -> numerical -> gradient/update with first-failure localization and repair routing.
- `r_reverse`: Reverse hierarchical feedback: the same full evidence and routing as r_hier is presented gradient/update -> numerical -> execution.
