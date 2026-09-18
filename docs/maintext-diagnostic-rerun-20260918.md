# Main-text diagnostic rerun, 2026-09-18

## Scope and protocol

This audit covers the non-LLM measurements in Diagnosis Analysis and Figure 1.
It does not run repair agents, localization or appendix experiments. The paper,
figure inputs and archived experiment directories are unchanged.

The isolated remote root is
`/media/main/whj/projects/torch4ms/maintext-diagnostics-20260918/`.
The runner is `scripts/run_maintext_diagnostics_20260918.py`.
The experiment source is a fresh Git archive of
`81181da81efa6c6c7dbbd9b0eae0f370ca7a4b2b`, from the archived experiment
worktree. The archive, Python sources, input data and runtime observer are
hashed in `provenance.json` before the first trajectory executes. PyTorch and
MindSpore versions, arguments and timestamps are recorded there. The runner
uses one CPU computation worker and one OpenMP/BLAS thread.

The observed environment is Python 3.9.25, PyTorch 2.8.0+cu128 and MindSpore
2.7.2, with MindSpore configured for CPU. Its own CPU thread pool retains the
environment defaults. The executed wrappers are preserved as
`runner_executed.py` and `signal36_runner_executed.py` beside the results;
their hashes match the respective provenance files. The maintained runner
also provides `--summarize OUTPUT_DIRECTORY` to recompute analysis locally.

The main run preserves four models, seeds 300--302, 50 steps, batch size 4,
SGD learning rate 0.01 and thresholds 0.02 for loss difference, 0.05 for
gradient-norm difference and 0.03 for update relative L2 difference.

- `experiment_c/`: clean, gradient scaling by 1.5 and alternate-parameter
  update suppression, under per-step synchronization and free-running
  training. This is the original 72-trajectory, 3,600-row Experiment C grid.
- `diagnostic_three_classes/`: execution, forward-value and missing-backward
  faults under per-step synchronization, 36 trajectories and 1,800 rows.
  Execution faults are injected before step 20. The preceding 19 steps remain
  measurements; candidate numerical measurements from step 20 onward are absent.
- `historical_signal36/`: the separate original single-step synthetic grid,
  using seeds 200--202 and the recovered `a30e411` signal-effectiveness driver.
  Dependencies use the frozen `81181da` source; both revisions are recorded.

## Measurement audit

The original 36-record table under
`data/paper_section_65_66/results_section65_signal_sanity_current/` contains
single-step synthetic measurements at seeds 200--202. The later real-data
trajectory study uses seeds 300--302 and 50 steps. The current manuscript
combines these protocols in one sentence. They should be described separately,
or the new 36-trajectory synchronized run should be explicitly identified.

Figure 1 uses the 24 free-running trajectories from Experiment C. Its 31/18
step annotations concern the crossing of the mean loss-difference curve.
Per-run loss detection times are separate measurements. The direct diagnostic
signals are the gradient-norm difference for `grad_wrong` and update relative
L2 difference for `param_wrong`. They do not measure full gradient-vector
agreement, repair acceptance or localization.

The archived runner uses the torch4ms autograd bridge and MindSpore gradient
computation, followed by the supported PyTorch-backed optimizer writeback.
The added observer records real MindSpore gradient tensors returned for the
evaluated model and checks their loss against that step's returned loss. It
also records the target tensor backing each forward loss. For deliberately
suppressed backward calls, absent backward evidence is expected; for injected
execution failure, no numerical measurement is expected after the failing step.
These observations distinguish backend execution from imports or configuration.
They do not trace every operation or the entire optimizer causal chain.

The original data validator verifies the CIFAR archive MD5 but checks only
the existence of an extracted batch. This rerun additionally matches all five
consumed CIFAR batches against the validated tar members, then freezes SHA-256
hashes for the data files. AG News train/test MD5 checks are preserved.

No experiment computation or threshold has been changed. The observer wraps
measurement boundaries without modifying the candidate model, gradients,
updates or faults. The historical self-checks and an independent summary are
both retained. Missing observations never count as clean passes.

## Results

The historical single-step replay completed: 36/36 faults are detected by
their intended signal. Every field in all 36 result records exactly matches
the archived table's JSON records. All 12 forward-value faults have genuine
MindSpore backward evidence. All 12 suppressed-backward cases have target
forward tensors and no backward evidence, as the injection requires.
The 12 execution faults stop before forward evaluation.

The tiny causal LM forward faults have gradient-norm differences 0.020800,
0.010961 and 0.021305, all below 0.05, while loss differences 0.074070,
0.027035 and 0.080454 exceed 0.02. This reproduces the complementary-signal
example in the main text.

Experiment C's 72 trajectories and 3,600 rows are complete. All six archived
self-checks pass. Both clean coupling modes pass all 600 measured steps.
The maximum clean loss difference is 3.814697265625e-6. Under per-step
synchronization the mean gradient-norm difference is 2.359350522359212e-8 and
mean update relative L2 difference is 1.3408061385128765e-6.

| Free-running result | Gradient scaling | Partial update suppression |
| --- | ---: | ---: |
| Direct-signal detection at step 1 | 12/12 | 12/12 |
| Mean loss difference first crosses 0.02 | 31 | 18 |
| Runs whose loss crosses within 50 steps | 3/12 | 4/12 |
| Individual first loss-crossing steps | 10, 11, 10 | 20, 6, 7, 7 |

These detection counts and crossing steps reproduce Figure 1. Of the 3,600
CSV records, 706 differ in at least one serialized value from the archive.
The maximum absolute changes are 1.1920928955078125e-7 for loss difference,
1.1920928955078125e-7 for gradient-norm difference, and
1.4954008827026263e-6 for update relative L2 difference. The rerun retains
these measured differences; no archived value is substituted.

The synchronized three-class 50-step replay also completed: 36/36 trajectories
are detected by the intended signal, and all six archived self-checks pass.
Execution failure occurs at step 20 in all 12 execution-fault trajectories;
the 372 candidate measurement rows from step 20 onward correctly remain unavailable.
The forward and missing-backward contracts each hold over all 600 steps.

Comparison against the earlier synchronized archive normalizes its `nlp`
label to `mlp`: `625d06c::_display_model` explicitly documents this as the
same image MLP. After this documented alias conversion, 179 of 1,800 rows
differ in serialized values. Maximum changes are the same as above. Across
both 50-step studies, all 5,400 rows retain their archived threshold decisions
and measurement-presence patterns.

Runtime evidence records 108 trajectories, 5,028 target forward computations
and 4,428 corresponding MindSpore backward computations. The 600 intentionally
suppressed backward steps have no backward evidence; there are no unexpected
missing backward observations. Source and data hashes remain unchanged after
execution. The trajectory runner and historical single-step runner both
exited successfully; the full trajectory run took 1,555 seconds.

Fresh measurements are under `output/maintext-diagnostics-20260918/`:

- `analysis.json`: independent run counts and per-run/mean detection latency.
- `archive_comparison.json`: keyed comparisons, maximum numeric changes,
  threshold-decision changes and input/output CSV hashes.
- `runtime_backend.json`: per-step target-backend observations.
- `provenance.json` and `outcomes.json`: frozen inputs, environment and completion.
- `experiment_c/`, `diagnostic_three_classes/`, `historical_signal36/`: complete
  fresh CSV/JSON measurements and the original self-check reports.

The full frozen Git archive remains in the remote root. The local evidence
includes its checksum, all Python source hashes, the executed wrappers,
observer, recovered single-step driver and execution logs.

## Verification

Three focused regression checks for the independent summary pass: unavailable
measurements cannot pass a clean trajectory, direct-signal latency remains
separate from loss latency, and execution failure cannot count as intended
gradient-fault detection. The paper and figures were not edited or compiled.
