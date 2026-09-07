# Experiment B: Fixed60 formal results

- commit: `f065b612e31520b26b4ae233dc117b77341fab79`
- pool: 60 instances / 30 fault categories / two models per category
- layers: execution 20, numerical 14, gradient/update 18, mixed 8
- model: `deepseek-v4-flash`; blind; Repair@1/2/4; four logical attempts

| Baseline | Repair@1 | Repair@2 | Repair@4 | Strict | LLM calls | Tokens | Wall time |
|---|---:|---:|---:|---:|---:|---:|---:|
| `r_exec` | 68.3% | 68.3% | 70.0% | 42/60 | 61 | 348940 | 8399.3s |
| `r_flat` | 70.0% | 73.3% | 73.3% | 44/60 | 54 | 549927 | 12118.2s |
| `r_hier` | 78.3% | 85.0% | 90.0% | 54/60 | 51 | 399653 | 5970.6s |
| `r_direct` | 78.3% | 90.0% | 90.0% | 54/60 | 85 | 2502021 | 10574.0s |
| `r_swe` | 63.3% | 70.0% | 71.7% | 43/60 | 102 | 8631619 | 13054.4s |
| `r_matchfix` | 88.3% | 91.7% | 96.7% | 58/60 | 75 | 7376586 | 19091.2s |

`instances.csv` contains all 360 per-instance rows; `raw.json` preserves the unified raw view; `fixed50_comparison.csv` audits the original 50 instances against the old Fixed50 run.
