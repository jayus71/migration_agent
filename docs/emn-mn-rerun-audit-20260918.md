# M/N evidence and minimum rerun audit

Audit date: 2026-09-18. Scope: existing code, protocols, manifests, and result
summaries only. No model calls or experiments were executed. E and native baseline
implementation are tracked separately. This document does not change manuscript
results or authorize a rerun.

## Reviewed revision and path convention

The reviewed branch is `codex/experiments-emn-integration`, at
`c21dadcf6e5e82665fa163b90c9dccb1ea15c4ef`. Its isolated remote checkout is
`/media/main/whj/projects/torch4ms/ascend-torch4ms-emn-audit-20260918`.
Code paths below are relative to that checkout. Artifact paths are relative to
`/media/main/whj/projects/torch4ms/`. Directory suffixes are not reliable evidence
of the code revision that produced their contents; use recorded commits and
command lines.

## Main assessment

M can test whether diagnostic feedback improves an external repair agent. Its
current implementation still generates rule-based stage feedback and supplies
preselected repair locations. A v4 autonomous-diagnosis claim therefore requires
a new adapter and paired runs under a frozen, common input contract.

N contains two distinct experiments: injected Python/PyTorch-to-Java/DJL repair,
and N18 Java/DJL-to-Python/PyTorch translation of upstream training sources.
Their directions, task pools, and acceptance scopes must remain separate. N18
has useful frozen sources, reference evidence, and a completed recent Direct
phase, but no complete current six-method comparison.

## M: definition, implementation, and historical results

Source: `experiments/experiment_request_20260820/15_experiment_M_diagnosis_plugin/`
(`README.md`, `protocol.json`, `run_experiment.py`). Protocol `experiment_m_v3`
specifies Fixed50, two hosts (SWE-agent and MatchFix), three conditions
(`original`, `measurements`, `layered_diagnosis`), and four repair attempts:
50 x 2 x 3 = 300 episodes. It uses `deepseek-v4-flash`, temperature 0.1, the
original strict fault-specific probes, and candidate-only edit scope. The
declared AutoFix base is `a9e93d91f0cd986eb453ee40ef69740dd849d1e2`; the frozen
Fixed50 core is `a506ecc6810024009d96837015e83050baae077b`.

The verifier in `autofix/verifiers/probe_pair.py` classifies difference paths by
keywords, selects the first mismatching stage, and includes the supplied candidate
path as a location or recommended target. Its root-cause text explicitly says
that the evidence does not establish a root cause. The runner supplies
`episode["candidate_rel"]` to this verifier. This is runtime-derived rule
feedback, without autonomous investigation by an LLM.

`autofix/external_repair.py` delegates to the legacy
`autofix/examples/run_external_repair_pilot.py`. The legacy pilot calls
`get_matchfix_references(fault_id)` and selects source and target symbols; the M
runner turns those references into `source_target_fragment` inputs. Removing
fault IDs from visible reports leaves this preselection in the host inputs.
An autonomous localization comparison must resolve both the candidate-path hint
and this symbol-selection dependency.

Historical summary values are shown below. Condition order is original,
all_measurements, layered_diagnosis. The historical `all_measurements` name must
be mapped explicitly to the newer `measurements` contract before reuse.

| Artifact / host | Accepted | Valid episodes | Accepted at attempt 1 | Total tokens |
| --- | --- | --- | --- | --- |
| M formal / MatchFix | 47, 47, 48 of 50 | 50, 50, 50 | 39, 41, 43 | 5,317,850; 3,958,073; 3,796,791 |
| M formal / SWE | 46, 45, 45 of 50 | 46, 45, 45 | Not extracted in this audit | 2,231,857; 3,734,269; 3,105,296 |
| M formal_v2 / SWE | 48, 48, 47 of 50 | 50, 50, 50 | 42, 47, 43 | 5,792,747; 4,809,679; 6,636,490 |

Sources are `summary.json` and `manifest.json` under:

- `ascend-torch4ms-exp-m-2a1b78e/artifacts/experiment_m/formal/`, recorded commit
  `2a1b78efc04f34d2c8fe8c8d6ba643b5e30a8b00`.
- `ascend-torch4ms-exp-m-v2-3699194/artifacts/experiment_m/formal_v2/`, recorded
  commit `3699194265a98835ccb7c7bed86e92376d7c6e31`.

The first SWE batch has 4, 5, and 5 infrastructure errors. The second batch adds
one fresh-episode recovery for qualifying execution errors, archives both runs,
and includes their costs, with four submissions per episode. That recovery
policy affects effective resource use and must accompany any reported values.
The manifests record the same model, temperature, and frozen core as above.

## N injected: controlled cross-language repair

Source: `experiments/experiment_request_20260820/14_experiment_N_real_cross_language/injected_faults/`.
The current protocol defines 12 faults: four execution, four forward, and four
backward faults. It compares two hosts and three feedback conditions, yielding
72 episodes with at most four patches. Visible seed 101 and held-out seeds 202
and 303 are used for final acceptance. The model is `deepseek-v4-flash` with
131072 maximum output tokens. Healthy Java and evaluator fault definitions are
excluded from model-visible inputs.

Fault mechanisms include missing Java types or malformed syntax, changed
activation or arithmetic operations, and `p.mul(2).sub(p.stopGradient())`, which
preserves parameter values while doubling their derivative. Feedback comes from
the older unified verifier; its layered mode supplies cause/location/hints.
The 72-check preflight counts healthy and faulty candidates across 12 cases and
three seeds, without model calls.

The available older controlled result is a different 24-case pool:
`ascend-torch4ms-exp-n-controlled-b8e1487/artifacts/n_controlled_expanded/`.
Its manifest extends 12 L cases with six hard single faults and six double faults.
Its pool hash is
`db7b4c966d51507e9a54c19212a196f6064eafd634563a22944356d9895c79c3`.
All 144 episodes are present. SWE accepts 24/24 in each feedback condition;
MatchFix accepts 23/24 in each condition, with no recorded infrastructure errors.
This supports little outcome separation on that pool. It is not the current
12-case, 72-episode result. Targeted artifact discovery found injected preflight
directories in `ascend-torch4ms-n-audit-4a56fe6`, but did not establish a completed
current 72-episode run.

## N18: real source translation

Source: `experiments/experiment_request_20260820/14_experiment_N_real_cross_language/n18/`.
The frozen pool contains 18 complete upstream Java/DJL sources, selected before
translation outcomes: ten DJL examples and eight d2l-java sources. The source
manifest pins DJL to `f3782179ff48a1bd31382667dbfae1f568891a55` and d2l-java to
`02320b5970ead1227090af14fa005a334d1f207f`. Sentiment and Amazon ranking were
excluded because independent calibration was incomplete.

Acceptance measures two consecutive post-preprocessing training steps, including
outputs, loss, gradients, parameter updates, and observed optimizer state. This
scope leaves preprocessing, whole-epoch evaluation, and checkpoints unmeasured.
Visible seed 101 and held-out seeds 202/303 apply. Checkpoints are 0, 1, 2, and 4.
The six methods are full_method, direct_llm, direct_llm_test_repair,
direct_llm_sweagent, direct_llm_matchfixagent, and intertrans: 108 outcomes.
Repair variants share the initial Direct candidate. The current protocol requires
immutable candidates generated under the common training interface.

`pairing/full_method_adapter.py` invokes `autofix.orchestrator.run_orchestration`
with training_trace, max_iters 5, and repair_budget 4. Its training-trace verifier
uses `_diagnose_generic_payload` in `autofix/agents/verifier.py`. These paths use
the older translator/verifier/fixer pipeline and rule diagnosis, so old full_method
outcomes cannot establish current v4 autonomous performance.

### Older completed batch

Root: `ascend-torch4ms-n18-348e8cd/artifacts/n18_training/`. Although batch status
is finished, the recorded command invokes a runner in `ascend-torch4ms-n18-7b72628`.
The six summaries each contain 18 rows:

| Method | Recorded accepted | Other status evidence |
| --- | --- | --- |
| Direct | 2 | 17 evaluated, 1 unavailable/infrastructure |
| Full | 6 | 12 STOP_PROVIDER_FAILURE, 6 SUCCESS |
| Test repair | 7 | 1 unavailable |
| SWE | 2 | 16 unavailable: 15 infrastructure plus 1 initial infrastructure |
| MatchFix | 6 | 16 evaluated, 2 unavailable |
| InterTrans | 0 | 18 search_exhausted |

Provider failures and unavailable evaluations require separate status accounting;
they do not provide measured zero accuracy for otherwise completed repairs.

### Latest prepared batch

Root: `ascend-torch4ms-n18-remediation-3eb9150/artifacts/n18_prepared_20260917/`.
`batch_status.json` and `pause_by_user_128k_01.json` record a user pause in the full
phase. Direct completed 18 evaluated tasks with 1 accepted. Full contains only
15 rows: 4 accepted, 12 evaluated, and 3 generation errors. The remaining phases
do not establish a complete current comparison.

`preflight_audit.json` records all six phases, zero real model calls, and code SHA
`19583636688e00f6378142c58ec0626a5795f7de`. `interface_calibration.json` reports
108 passing controls: 54 healthy across three seeds, 18 forward, 18 backward,
and 18 optimizer controls. These are calibration outcomes, not migration repairs.
The frozen interface hash is
`558679919e612561bc98e7e47fd387d3b02232a4168aada690cb98978a63c052`;
the reviewed branch's `training_interface.txt` has that exact hash.
The frozen protocol hash is
`75ea3fc4b07f2140551bc8344072e50cec5c89fc179f29ade190cdb42f1d6fa6`;
the reference index hash is
`e870e4db09b44892705d01cca69b37ad3a3d7f47d8c9c74b43684db3229d5d69`.
The index path is
`ascend-torch4ms-n18-348e8cd/artifacts/evidence_index.json`.

## Reuse gates and minimum rerun scope

1. Freeze source hashes, candidate hashes, verifier/threshold versions, hidden
   evidence isolation, native host configurations, edit scope, attempt accounting,
   and provider retry accounting before any new calls. Run current-commit fake
   transport/isolation checks and the relevant calibration after adapter changes.
2. For M, reuse the Fixed50 pool and original probes after identity checks. Feed
   v4 diagnostic evidence into the native host without replacing its parser or
   history. Remove fault-indexed symbol selection and evaluator-provided location
   hints from an autonomous-location condition. A focused one-host paired study
   needs 50 x 2 = 100 episodes; an existing baseline can cover 50 only if all input,
   scope, budget, and native configuration contracts match exactly. Retaining the
   full original two-host/three-condition question requires 300 episodes. A reduced
   study must have an explicitly separate protocol. MatchFix requires a genuine
   usable source mapping; unsupported cases need status accounting, not failures.
3. For N18 repair-only evaluation, the completed Direct candidates are a potential
   reusable 18-case frozen pool. Interface equality is confirmed here; source,
   candidate, prompt, reference, and verifier equivalence remain to be checked.
   Include all 18 candidates, including the initially accepted one. Applying v4
   to this pool estimates repair performance conditional on those candidates.
4. An end-to-end N18 comparison requires compatible current candidate generation
   and v4 repair on all 18 sources. Reference traces and controls can be reused
   after hash and environment checks. Six-method claims require all 108 valid
   method/task outcomes under the frozen protocol, with unavailable outcomes
   explicitly separated. The paused partial full phase is development evidence.
5. The injected N track is optional for a revision already supported by M and
   N18 unless its distinct Java-target claim is needed. A one-host paired pilot
   needs 12 x 2 = 24 episodes under a new reduced protocol; the current full
   injected protocol remains 72. The historical 144-episode pool must retain its
   own identity and cannot fill those cells.

This audit checked existing summaries and source contracts. It did not reconcile
every trajectory or raw usage record, regenerate calibrations, or inspect a newly
built manuscript. No existing paper number or attempt budget was changed.
