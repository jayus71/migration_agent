# Main-text experiment audit and reruns

The user requested an audit and rerun of main-text experiments on 2026-09-18,
with priority on ablations. This request authorizes additional experiments;
610 describes the preceding repair grid and is not a cap. Appendix-only
experiments are outside this round. The manuscript and its existing data remain
unchanged while the replacement evidence is collected.

The preceding 610-condition grid has now completed and passed its raw-ledger
audit. Its complete results, diagnosis-assessment coverage and verified recovery
archives are recorded in
`docs/autonomous-repair-completed-20260918.md`. The full 13,519-call profile
found zero tool-evidence compression events. The separate JAX rerun is also
complete: v4 and Direct each accept 6/6, with Direct using fewer tokens and less
elapsed time. Its native converters retain their distinct faulted-input protocol.

The initial component/signal batches finished dispatching but contain 108
infrastructure failures. Current recovery reuses valid complete episodes,
restarts 83 eligible infrastructure failures and replaces the entire 60-task
history treatment after correcting its inaccurate history statement. See
`docs/maintext-ablation-recovery-20260918.md`. That recovery is now complete:
143/143 replacements and 276/276 selected conditions, with no ledger or
treatment discrepancies. The 135,522-file recovery archive is locally verified.
The new real-training signal grid
has completed all 64 conditions, after 60 offline healthy/fault checks before
launch. Full three-seed acceptance is 4/16, 8/16, 12/16 and 16/16 as forward,
gradient and update observations are added. All 690 calls, 40 accepted patches
and 120 final backend checks passed independent review. Its 27,462-file archive
has been downloaded and verified locally. This is separate from the corrected
original-fixture signal study. The current result tables and CSV exports are
indexed in `docs/maintext-results-20260918.md`.

## Evidence map

| Main-text claim or experiment | Evidence gap | Action |
| --- | --- | --- |
| Fixed50 repair acceptance, attempts and cost | Historical guided repair results do not measure the current autonomous procedure | Finish the frozen autonomous comparisons and declared infrastructure recovery; retain each version and all interrupted costs |
| Independent verifier and repair history | Old component rows were unmeasured | Run continuous-role and reset-repair-history controls on all 50 + 10 tasks against v4 evidence |
| Progress and edit-format feedback | v3 to v4 changes both together | Disable each separately on all 50 + 10 tasks |
| Rollback and targeted guidance | Current procedure has no rollback; oracle guidance was removed | Record these as obsolete method claims, not measurable current components |
| Evidence compression | Prior audits found zero tool-evidence compression events; reasoning handoff differs | Profile complete raw trajectories and identify the component actually exercised |
| Twelve-task signal coverage | Model labels repeat three fixtures; historical metrics and candidate visibility depend on fault labels | Replace the defective runner with common public inputs and genuine measured feedback; preserve original records and describe the actual task construction |
| JAX generalization | Historical workflow supplies stage and repair hints; budgets differ by method | Prepare autonomous reruns on the six frozen tasks; audit and retain native comparator protocols |
| Clean diagnostic controls and fault signals | Main text combines one-step and 50-step sources with different seeds | Replay the original diagnostic sources and separately record the synchronized 50-step trajectories |
| Figure 1 detection latency | Requires complete per-step trajectories and actual target execution | Replay all original model, seed, coupling and fault conditions with backend observations |
| Autonomous classification and localization | Old 48/50 measures deterministic stage agreement | Complete separate pre-edit diagnosis assessment; report coverage and raw LLM judgments separately from repair acceptance |
| Attention repair example | Current prose describes historical guided trajectories | Recheck any replacement example against complete current patches and measured observations after the repair grid finishes |

## Assigned work

- `maintext_ablation_rerun`: four component controls, 240 conditions, plus the
  signal-study runner audit and corrected experiment.
- `maintext_jax_rerun`: generic JAX integration, frozen-input checks and reruns.
- `maintext_diagnostic_rerun`: non-LLM diagnostic and latency reruns.
- Parent: finish existing repair and diagnosis queues, verify ledgers and
  archives, integrate the complete comparison and audit the replacement claims.

The four component controls use `progress_v4/autonomous_layered` as their
reference. Reference runs are reused as complete groups; successful tasks are
never assembled across versions. Existing v3 category, v3/v4 native-history,
v5 repair-window and v6/v7 last-call controls remain separately reported.

All repair and evaluator LLM calls use the configured DeepSeek backend. New
runs freeze their inputs, code and protocol before launch. Native baseline
algorithms, prompts, parsers, history and retries retain their own behavior.
Shared runtime or measurement defects are addressed in isolated integration
code and recorded before rerunning affected conditions.

## Initial execution snapshot

At 2026-09-17 18:01 UTC the preceding grid had completed 586/610 selected
conditions. Fixed50 v5 had completed 50/50, accepting 43; v7 had completed
49/50 and v6 27/50. The latter two partial groups have no final acceptance
rate yet. All Natural10 groups and the Fixed50 v3/v4 groups were complete.

The component runner had prepared independent inputs and passed five offline
behavior checks. Additional frozen-file and dispatch checks were in progress
before API launch. The non-LLM diagnostic rerun was running at
`/media/main/whj/projects/torch4ms/maintext-diagnostics-20260918` with one worker.
Detailed status and final evidence belong in each study's report, not in this
point-in-time snapshot.

At 2026-09-17 18:30 UTC the non-LLM diagnostic reruns had completed. Experiment
C produced 72 trajectories and 3,600 rows, the synchronized three-class study
produced 36 trajectories and 1,800 rows, and the historical single-step study
reproduced all 36 records. Both per-step self-checks passed. The old/new
comparison preserved every threshold decision and missing-value position;
the largest numerical change was approximately `1.50e-6`. See
`docs/maintext-diagnostic-rerun-20260918.md` for backend counts and the distinct
protocols.

The parent launched the frozen JAX `formal_v5` grid with two workers using
`launch_maintext_jax_parent_review.sh`, after five integration tests and a
dispatch regression check passed. The separate initial-state audit has four
passing tests. Its twelve LLM conditions compare the current autonomous method
with the current shared-tools Direct control; the historical one-call Direct
implementation remains a different protocol. Native converter evaluations are
reported separately.

After the original repair recovery finished all 109 replacement/new conditions,
the parent reallocated its released workers: both `fixed50_v3` and
`natural10_v3` now allow four component-ablation workers, eight in total.
`worker_slots.json` was atomically replaced; the original two-worker files and
`parent_resource_allocation.json` are preserved in the remote study root. The
same dispatchers continue, with no input, method, criterion or per-condition
budget changes. The signal study may use two released slots when either group
finishes. Existing grids must never receive a second dispatcher.

Sources: `conference_101719.tex` main text through the ablation section,
`README.md`, `data/paper_figures/README.md`,
`docs/maintext-ablation-rerun-20260918.md`, and the provenance cited in the
individual experiment reports. No manuscript compilation or figure regeneration
was required for this audit-only document.

## Current attention example

The main-text GQA example also needs revision when the new results are adopted.
The frozen Fixed50 manifest maps `NU-07-B` to `task_034`. In the complete current
runs, v4 evidence and native SWE-agent are accepted on external submission 1,
and the shared-tools Direct control is accepted on submission 2. All three
final probe records report a maximum absolute difference of
`9.94652509689331e-7`, below the original unit threshold. Their production edits
are in `torch4ms/ops/mtorch.py`.

Thus the old paragraph's baseline failures describe the historical experiment,
not these autonomous runs. The recorded SWE patch implements contiguous head
repetition with reshape/tile/reshape; Direct and v4 use `mnp.repeat` before the
attention matrix product. These are inspected existing results, not additional
executions or a new acceptance rule.

The existing complete v4 Natural10 patch review also provides candidate repair
examples for this same reference configuration. Tasks 002, 007, 008 and 009
repair actual target-library operations and pass seeds 42, 1042 and 2042.
Task 007 restores the MindSpore tanh registration and wrapper indexing; task
009 implements GroupNorm with target operations. Their candidate, source,
task contract and optimizer files remain unchanged. The complete production
diffs and backend evidence were already reviewed in
`output/autonomous-verifier-20260917/natural-workflow-and-patch-review-20260917.md`.
That review can support a v4 case study without substituting a different
method version's trajectory or rerunning these completed repairs.

Evidence under the implementation's `experiments/autonomous_fixed50_20260917`:
`formal_v3/conditions/task_034/{swe_native_isolated,direct_shared_tools}/result.json`
and `progress_v4/conditions/task_034/autonomous_layered/result.json`.
