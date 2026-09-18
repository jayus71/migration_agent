# Main-text ablation recovery

| Study | Treatment | Completed/planned | Accepted | Actual faults repaired | Selected known tokens | All-attempt unknown calls |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| fixed50_v3 | continuous_role | 50/50 | 44 | 44 | 39,240,448 | 24 |
| fixed50_v3 | without_repair_history | 50/50 | 37 | 37 | 31,876,546 | 24 |
| fixed50_v3 | without_progress_prompt | 50/50 | 46 | 46 | 45,137,525 | 24 |
| fixed50_v3 | without_edit_format_feedback | 50/50 | 45 | 45 | 39,982,844 | 23 |
| natural10_v3 | continuous_role | 10/10 | 8 | 3 | 14,516,463 | 0 |
| natural10_v3 | without_repair_history | 10/10 | 5 | 0 | 10,851,537 | 1 |
| natural10_v3 | without_progress_prompt | 10/10 | 7 | 2 | 17,325,026 | 0 |
| natural10_v3 | without_edit_format_feedback | 10/10 | 9 | 4 | 13,206,863 | 1 |
| signal12_v3 | execution | 12/12 | 8 | 8 | 2,863,858 | 3 |
| signal12_v3 | execution_forward | 12/12 | 12 | 12 | 4,902,235 | 4 |
| signal12_v3 | all_observations | 12/12 | 12 | 12 | 3,427,626 | 4 |

Signal12 repeats three fixtures four times and lacks an initially execution-passing gradient-only failure. Continuous-role changes both role handoff and conversation representation. Format assistance includes prior examples and error feedback. Corrected history removes repair conversation, retaining workspace and initial handoff.

Every old episode is retained in total cost. Unknown usage is not zero. A selected episode uses its own original-size budget; earlier interrupted episodes are additional.
