# Autonomous repair grid completed, 2026-09-18

The declared 610-condition repair grid is complete. Raw request/response usage
matches every selected ledger, with zero accounting discrepancies. The new
main-text component ablations and the additional 64-condition training-signal
study have also completed. They are summarized with the other reruns in
`docs/maintext-results-20260918.md`; their denominators remain separate from
this 610-condition comparison.

## Acceptance

Fixed50 uses the original fault-specific checks and four external submissions.
Natural10 contains five initially faulty and five initially healthy translations.
All listed Natural10 methods retain all five healthy inputs. Each table cell
comes from one complete configuration; no result is assembled across versions.

| Configuration | Fixed50 accepted | Natural10 accepted | Natural faults repaired |
| --- | ---: | ---: | ---: |
| v3 evidence handoff | 42/50 | 8/10 | 3/5 |
| v3 native history | 42/50 | 7/10 | 2/5 |
| v3 autonomous category output | 46/50 | 8/10 | 3/5 |
| SWE-agent 1.1.0 | 29/50 | 5/10 | 0/5 |
| Direct shared-tools control | 35/50 | 5/10 | 0/5 |
| MatchFix upstream orchestration with shared backend | n/a | 5/10 | 0/5 |
| v4 evidence handoff | 41/50 | 9/10 | 4/5 |
| v4 native history | 44/50 | 8/10 | 3/5 |
| v5 extended repair window, native history | 43/50 | 6/10 | 1/5 |
| v6 last repair call retains tools | 45/50 | 9/10 | 4/5 |
| v7 corrected last-call prompt | 44/50 | 7/10 | 2/5 |

The v4 evidence configuration is the frozen reference for the new component
ablations. Against SWE-agent and Direct, its Fixed50 acceptance is higher by
24 and 12 percentage points, respectively. On Natural10 it repairs four
initial faults; the three external comparison conditions repair none.
The Direct shared-tools control is a distinct protocol from historical Direct
LLM. MatchFix preserves its upstream orchestration with the documented DeepSeek
coding-backend adaptation; the table does not assert a native CLI replication.

The v3 category condition gains four Fixed50 cases relative to the v3 evidence
configuration and loses none. This run supports retaining autonomous
classification as an empirical question. It supplies no category truth to the
agent. The v6 progress prompt contains the documented contradictory last-call
instruction; v7 corrects that instruction. Both complete results remain visible.
These versions were developed on the same task pools and are development
comparisons, not an independently selected final test.

## Cost And Mechanism

The selection protocol reuses 501 normally completed conditions, independently
restarts 90 infrastructure failures, and starts the remaining 19 conditions.
The 90 interrupted episodes are retained, so the original grid and recovery
contain 700 recorded episodes. Restarted episodes have their own original-size
budget. The report separates selected-episode cost, interrupted cost, and their
sum; unknown provider usage stays unknown.

For complete selected Fixed50 episodes, v4 evidence uses 38,028,388 tokens,
SWE-agent 42,579,064, and Direct 12,459,013. Tokens per accepted repair for v4
are 0.632 times SWE-agent and 2.606 times Direct. Interrupted baseline calls
have unknown usage, so the corresponding all-attempt cost ratios are unavailable.
Natural10 v4 evidence uses 15,547,813 tokens in total. Its acceptance denominator
includes the five healthy tasks, which remain separately identified.

The selected 610 episodes contain 13,519 recorded model calls. Every response
identifies `deepseek-flash`, requested as `deepseek-v4-flash`. The complete
profile finds zero `evidence_memory` compression events. Differences between
evidence and native history therefore concern the actual verifier-to-fixer
handoff; they do not establish a tool-evidence compression benefit.

## Diagnosis Assessment

All 500 planned diagnosis records were processed. Of these, 332 passed both
assessment stages and evidence validation. The remaining records comprise
43 phase-one schema errors, 46 phase-two schema errors, 76 phase-one input-size
failures, one phase-two input-size failure, and two provider-truncated outputs.
These missing assessments do not count as incorrect diagnoses. Per-method
coverage ranges from 25 to 39 of 50 tasks.

The independent evaluation activity records 930 API attempts and 158,052,123
known tokens; 114 attempts lack provider usage. Its total cost is therefore
unavailable. These costs are separate from repair costs. Scores are exploratory
DeepSeek judgments over pre-edit evidence. The previously documented semantic
review flags remain unresolved; the aggregate is not adjudicated localization
accuracy and does not replace the old 48/50 first-failing-stage agreement.

## Evidence And Verification

Local artifacts are under `output/autonomous-verifier-20260917/`:

- `autonomous_recovery_final.{json,md}`: complete selection and raw-ledger audit.
- `autonomous_recovery_comparison_final.{json,md}`: per-task comparisons,
  cumulative acceptance at one, two and four submissions, and cost ratios.
- `autonomous_recovery_profile_final.json`: all selected requests and actual
  memory events, checked against the usage ledger.
- `diagnosis_recovery_final.{json,md}`: scores, coverage, missing causes and
  all evaluator costs.
- `recovery_finalization.json`: completed dispatcher and archive provenance.

Both recovery archives passed local archive-level and member-level checks:

| Archive | Files checked | SHA-256 |
| --- | ---: | --- |
| `autonomous_repair_recovery_round1.tar.gz` | 95,910 | `7b8cf0385bf0bc5b29c2e362a4f12fad345e7db27ba873725e2e1e8e6a3b727f` |
| `autonomous_diagnosis_recovery_round1.tar.gz` | 12,960 | `c91619dbb0810a0ac688ea2c3fdbbfec478bf61a399ae7213a7b0d117f9fa061` |

Their `.verification.json` records are beside the archives. The eleven original
archives had already passed verification for 472,821 files. This report changes
no manuscript, figure, frozen input, method, acceptance predicate or original
result.
