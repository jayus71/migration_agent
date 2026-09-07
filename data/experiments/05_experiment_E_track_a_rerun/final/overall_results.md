# Experiment E: Track A final results

Updated on 2026-09-06 from the current per-condition `summary.json` files. All rates below were recomputed from 5 tasks × seeds 642/643/644. `N/A` denotes an unmeasurable environment-blocked method and is not counted as failure.

| Method | Conditions | Compile | Execute | Training-valid | Strict | Main table |
|---|---:|---:|---:|---:|---:|---|
| T-HIER | 15/15 | 15/15 (100.0%) | 15/15 (100.0%) | 15/15 (100.0%) | 15/15 (100.0%) | yes |
| T-CTE | 15/15 | 15/15 (100.0%) | 12/15 (80.0%) | 12/15 (80.0%) | 8/15 (53.3%) | yes |
| T-DIRECT | 15/15 | 15/15 (100.0%) | 13/15 (86.7%) | 13/15 (86.7%) | 7/15 (46.7%) | yes |
| T-MSA | 15/15 | 15/15 (100.0%) | 15/15 (100.0%) | 15/15 (100.0%) | 0/15 (0.0%) | yes |
| T-X2MS | 0/15 | N/A | N/A | N/A | N/A | no (blocked) |

## Strict results by task

| Method | Image MLP | CNN | ResNet | Transformer classifier | Tiny causal LM |
|---|---:|---:|---:|---:|---:|
| T-HIER | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| T-CTE | 1/3 | 1/3 | 3/3 | 0/3 | 3/3 |
| T-DIRECT | 0/3 | 1/3 | 3/3 | 0/3 | 3/3 |
| T-MSA | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 |

## Interpretation and provenance limits

- T-HIER uses commit `b32d9f4a27ed90646943b671d43f8616b4ad73fe` and passed all 15 independent strict-verifier conditions.
- T-DIRECT and T-CTE use commit `4508d0e962d1f27a582b2fcb0a53f1edea5bfb0f`. Neither route supplied an explicit `max_tokens` cap. Both generated native MindSpore candidates.
- T-MSA uses commit `52615295ceea067371216564f4310425871b583d` with the recorded generic CPU compatibility patch. It trained in all conditions but failed semantic strictness in all conditions.
- T-X2MS remains environment-blocked and is excluded from success-rate comparisons.
- Two T-CTE CNN rows are labeled `environment_or_upstream` in the immutable raw output, but their errors are invalid generated MindSpore arguments (`pad_mode="same"` together with `pad=1`). They are measurable candidate/method failures in this aggregate table.
- The results support a comparison of the complete T-HIER workflow against the listed baselines. They do not isolate the causal contribution of the Torch4MS bridge layer alone.

## Source-of-truth directories

- `T-HIER/formal_b32d9f4_strict_sync_5x3_20260906/`
- `T-CTE/formal_4508d0e_no_token_cap_5x3_20260906/`
- `T-DIRECT/formal_4508d0e_no_token_cap_5x3_20260906/`
- `T-MSA/formal_patched_5261529_5x3/`
- `T-X2MS/summary.json`

`T-CTE/summary.json` is a retained historical 2026-09-01 result and is not a current source of truth.
