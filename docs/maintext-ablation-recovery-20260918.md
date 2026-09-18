# Main-text ablation recovery and corrected history control

The recovery is complete: 143/143 replacement conditions, producing 276/276
selected component and original-fixture signal conditions. The final report
has zero ledger mismatches and treatment violations. Local archive verification
checked all 135,522 files; archive SHA-256 is
`4418d13309523a45187687e7d583010259f23a6c0b86626be4618f8e35b75da0`.
Results and source links are in `docs/maintext-results-20260918.md`.
The following sections retain the preparation and recovery history.

The first component grid dispatched all 240 conditions. It recorded 143 normal
completions and 97 infrastructure failures. The separate original-fixture
signal grid recorded 25 normal completions and 11 infrastructure failures.
Every original result and request remains in its original directory.

The frozen v4 client saved only `error_type=RuntimeError` for these failed
requests. The first component/signal dispatchers searched for HTTP codes in
the saved errors, so their provider-error stop rule could not recognize these
records and continued dispatching. The logs do not establish a specific HTTP
status or whether increased concurrency contributed. Those episodes are
infrastructure failures, not functional repair failures. This is an experiment
orchestration defect and is separate from any baseline algorithm.

A single recorded health call at 2026-09-18 03:14:49 UTC returned HTTP 200,
`deepseek-flash`, and 59 tokens. No backend model was changed. Its record is
`transport_health_20260918T031449Z.json` in the remote study root.

## Declared replacement policy

The `without_repair_history` treatment clears prior repair conversation but
its original system prompt claimed conversation persistence. The corrected
treatment replaces that statement with an accurate description of retained
initial investigation, latest observations and current workspace. Every one
of its 50 Fixed50 and 10 Natural10 tasks is rerun in a new directory. The
original 35 normal completions and 25 interrupted conditions remain a separate
defective treatment; no successful result is selected from it.

The other three component treatments require only their infrastructure
restarts: 71 Fixed50 and one Natural10 condition. The original signal study
requires 11 such restarts. The declared batch therefore contains 83 independent
infrastructure restarts and 60 corrected-history conditions, 143 in total.
Each restart begins from the exact frozen original input with its original
single-episode budget. Prior costs are additional and are retained separately.
No normally completed functional failure is restarted.

`scripts/recover_maintext_ablations.py` freezes the job selection, original
result hashes, copied manifests and input inventories before execution. The
copied old treatment runners and agent snapshots are byte-identical. The
history control alone uses the new treatment runner. A wrapper records only
numeric HTTP status and exception type outside the frozen client and rethrows
the same failure. It does not retry requests or change request payloads.
Any transport failure or nonnormal worker termination stops new dispatch.

Seven component tests and three recovery checks passed before preparation.
They check actual history reset, accurate context description, preserved
workspace and lifetime budgets, exclusion of completed successes and failures,
refusal to overwrite, and credential-free preservation of HTTP 402 evidence.
The batch starts with six workers. All selected, original and corrected-history
costs are included by `scripts/report_maintext_recovery.py`.

Remote root:
`/media/main/whj/projects/torch4ms/maintext-ablations-20260918/recovery_round1`.

## Additional measured training-signal study

The corrected old signal runner still measures three original fixtures repeated
four times. Its GR-07 fixture fails during gradient assignment, so that pool
does not contain an initially executable gradient-only fault. A separate
study is being prepared from the actual CNN, image MLP, Transformer classifier
and tiny causal LM definitions preserved in the completed diagnostic replay.
It uses four program mutations and four cumulative feedback settings, 64
conditions. The added feedback settings distinguish gradient from update
measurements. Healthy and faulty programs are checked on three seeds before
any model call is authorized by the prepared manifest.

The first offline preparation used a class-logit bias for its forward mutation.
The MLP's loss difference on one seed stayed below the declared threshold even
though gradients differed. `training_signal16_v1` preserves that failed
preflight. The second preparation uses a common additive loss offset inside
the differentiated loss closure, giving an explicit forward-computation fault.
It does not change recorded measurements or thresholds. Both preparations
precede any repair-model results. The second preparation passed all 60 checks:
four healthy programs and sixteen faulty programs, each on three seeds. The
execution, forward, gradient and update mutations showed their declared first
failing signal on every seed. Four masking tests and a two-setting fake-transport
lifecycle check also passed. The latter confirmed that visible acceptance can
stop repair while hidden full scoring still records an unrepaired update fault.
It made zero API calls.

The frozen `training_signal16_v2` grid has now started with four workers, alongside
the six-worker recovery. Its 64 conditions use the same generic v4 agent, model
and per-condition budgets. The original diagnostic model definitions, complete
copied inputs, preflight evidence, task grid and runner hashes are saved before
the first formal request.

This signal study measures how available public checks trigger and guide repair.
The controller stops on its visible checks; final scoring uses all signals on
three seeds. Hidden failures never become a public aggregate failure flag.
Every setting exposes the same public program and permits additional scratch
tests. The PyTorch optimizer writeback used by the adapter is retained and
described alongside actual MindSpore forward and backward evidence.

The new 64-condition grid completed at 2026-09-18 04:07 UTC. Full three-seed
acceptance is 4/16 with execution feedback, 8/16 after adding forward values,
12/16 after adding gradients, and 16/16 with parameter updates also available.
All 690 request/response ledgers match, with zero unknown-usage calls. Independent
review checked all 40 accepted patches and 120 final target-backward records;
see `docs/maintext-training-signal-independent-review-20260918.md`.

Its complete archive and manifest are under
`output/maintext-ablations-20260918/archives/training_signal16_v2_complete`.
Local verification checked all 27,462 files and the archive hash
`c7025931f3f845854d84506be64b4149c7210b1e286713403641164862c29569`.
The companion `training_signal16_call_count_audit.json` independently checks
request counts and unknown-usage accounting in every condition.

The manuscript and appendix are unchanged by this report.
