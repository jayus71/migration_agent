# Inputs for manuscript figures and tables

## Current autonomous comparison (2026-09-18)

The main manuscript now selects slim v4 (`without_edit_format_feedback`).
`scripts/build_maintext_results_bundle.py` exports the audited selected runs to
`output/maintext-results-20260918/slim_main.csv` and paired baseline overlap to
`slim_baseline_overlap.csv`. Its `evidence_index.json` records source hashes.
Run the exporter with `--recovery output/maintext-ablations-20260918/recovery_final.json`,
then run `figures/make_slim_results.py` (also invoked by
`figures/make_repair_comparison.py`) to regenerate the main table and figure.
The cumulative Fixed50 counts are 29, 41, and 45 at one, two, and four submissions.
Natural10 includes five initially healthy programs and four actual repairs.
JAX and training-signal evidence still uses original v4. New MatchFixAgent and
InterTrans results remain pending and are excluded from the new main comparison.

`figures/make_slim_v4_overview.py` defines the current method diagram and creates
both the editable PowerPoint and SVG. `figures/update_overview_labels.py` exports
its vector PDF and PNG. The diagram shows autonomous investigation, evidence
handoff, retained repair history and external acceptance, without deterministic
category routing or score-based rollback.

## Historical guided snapshots

These CSV files are byte-for-byte copies of original experiment summaries. They
make the figure scripts runnable from this repository without the ignored local
`ascend-torch4ms` checkout. No result values or validation decisions were changed.

The manuscript now names the method LaDiM (Layered Diagnosis for Multi-Agent Code Migration). Its
archived identifiers remain `r_hier`, `c_hier`, and `T-HIER`; earlier drafts
called the same method MARS and LADDER. Only presentation labels are renamed.

| Snapshot | Original path in the experiment repository | SHA-256 |
| --- | --- | --- |
| `fixed50_original_summary.csv` | `experiments/baselines/full_hier_fixed50/summary.csv` | `db4dd52fa1892ee53ec377ff3c5907779611689692d59b75e9c3c01f0f2ddd0e` |
| `signal_ablation_by_fault.csv` | `experiments/paper_section_63_64/results/section63_feedback_ablation_nu04_clean_alias_rerun_20260715/section63_summary_by_fault_type.csv` | `ca2ba5a14e00716bdd35977b8b30e41096b4932f9e968c8e7f5bc72e4657c0f1` |
| `jax_original_instances.csv` | `experiments/baselines/track_c/instances.csv` | `de2a165be2f9cf4409a92ff4a23c3711a356e8fe4e5787d3be705857c4800a8d` |

The original Fixed50 summary records six methods on the same 50 instances. Its
`strict_success` field is the original task-specific acceptance decision, not a
claim that every accepted candidate passes paired loss, gradient, and update
revalidation. The figure labels and manuscript must preserve this distinction.
The later Experiment A revalidation remains available under
`data/experiments/01_experiment_A_paired_threshold_revalidation/formal_final/`.

Cost per accepted repair is `(prompt_tokens + completion_tokens) / strict_success`.
The approximately 29-fold ratio uses that original scoring denominator.

The budget plot reads `repair_at_1`, `repair_at_2`, and `repair_at_4` from the same
Fixed50 summary. Each rate uses all 50 instances as its denominator and counts
repairs accepted within the stated attempt budget. Only these three recorded
checkpoints are plotted; connecting lines do not supply a third-attempt result.

The signal ablation uses a separate set of 12 tasks per feedback condition.
Its 4/8/12 counts must not be combined with the Fixed50 pool.

## JAX repair rows

The JAX snapshot comes from `codex/track-c-torchax-autofix` at `3352f71` in the
experiment repository. It contains 24 records, one for each of four methods on
six MLP/CNN tasks. The per-instance model, stage, acceptance, attempts, and token
counts were checked against all 24 original JSON reports. Each accepted repair
passes training verification on three seeds. This is separate from the Fixed50
fault-specific acceptance criterion.

Run `python figures/make_jax_table.py` to regenerate `figures/TABLE_jax_rows.tex`,
which `make_results_tables.py` embeds in `TABLE_main_rows.tex` for the JAX panel
of the main repair table. Regenerate both files after a table-generator change. All numeric
cells come from the snapshot. The repair-location mapping follows
`autofix/faults/injection.py::_prepare_torchax_compat`, which accepts only
candidate-program faults. Adapter operator, autodiff/optimizer, Transformer,
and language-model categories have no JAX instances. The main table reports acceptance and cost, with the common candidate-program scope stated in the JAX panel note.

The Track C README and each method's `summary.json` record different budgets.
LaDiM allows up to three rounds; Direct LLM and each converter run once. All
accepted results finish in round one. The CSV's `repair_at_4` field is computed
from the successful round index; it does not record a shared four-attempt run.
The table reports accepted counts, first-attempt acceptance, tokens per accepted repair,
and seconds per accepted repair. Its note states the budgets and that all accepted
repairs finish in the first round.

Token cost includes all attempted instances. LaDiM uses 17,543 / 6 = 2,923.8
tokens per accepted repair (2.9K when rounded); Direct LLM uses 74,841 / 5 =
14,968.2 (15.0K). Ivy and torch2jax use no LLM tokens and accept no repairs, so
their cost per accepted repair is undefined. The table marks both token and time cost per accepted repair as `n/a` for these
methods. Elapsed time sums the tracked instance rows: 478.842334 seconds for
LaDiM and 885.591825 for Direct LLM, giving 79.8 and 177.1 seconds per accepted
repair, respectively. Failed attempts contribute to both totals.

## Main results and feedback ablations

`figures/make_results_tables.py` generates `TABLE_main_rows.tex` from the original
Fixed50 summary, `TABLE_signal_rows.tex` from the separate 12-task signal study,
and `TABLE_feedback_rows.tex` from the tracked Experiment J summary under
`data/experiments/10_experiment_J_feedback_ablation/formal_run_2d6bd3d/`.
The three inputs retain their own acceptance criteria, budgets, and denominators.

Experiment J uses temperature 0 and paired-threshold acceptance. The archived
summary uses the initial evaluation for execution-only, pass/fail, stage-label,
and flat feedback, and the third confirmation run for LaDiM and reverse
presentation. The main ablation table reports accepted repairs, first-attempt acceptance,
tokens per accepted repair, and seconds per accepted repair for LaDiM and four
reduced-feedback variants. The paper identifies the LaDiM result as its third run
and gives all three order comparisons in the appendix (44/49, 47/46, and 48/48,
each out of 50).
Reverse presentation preserves diagnosis and routing. The component table leaves
unmeasured guidance, repair-history, and rollback controls as `--`.

The original Fixed50 feedback table and fault/model/location breakdown remain in
the appendix. Figure 3 continues to use the original Fixed50 data for all curves.
See [metric definitions and evidence gaps](../../docs/metrics-and-ablation-revision.md)
for the source papers, metric choices, and proposed subset design.

## MindSpore translation rows

This comparison is excluded from the current manuscript. Its archived data and
generator remain available here. It is separate from the translator documentation
ablation retained in Appendix A.

`figures/make_mindspore_translation_table.py` reads the current `source_summary`
paths in `data/experiments/05_experiment_E_track_a_rerun/final/run_manifest.json`.
It generates `figures/TABLE_mindspore_translation_rows.tex` from the 15 measured
task--seed rows for each of Direct LLM, CodeTransEngine, MSAdapter, and LaDiM.
It checks the task grid, matching source-program hashes, recorded revisions,
and measured training and acceptance flags. Historical summaries outside those
indexed paths are not used. See Experiment E's `README.md` for source precedence.

This panel measures complete translation on five source tasks and three seeds.
It is separate from the original 50-instance repair pool. Training completion
requires gradients and parameter updates; acceptance additionally requires
paired numerical agreement. LaDiM permits four repair rounds after translation,
but its initial translations pass without invoking repair. The other methods
translate once; MSAdapter uses one candidate per task. X2MindSpore remains
unmeasured in this snapshot and is excluded from rate comparisons.

## Framework documentation studies

Appendix A retains both documentation panels from the original manuscript. The
repair panel uses the separate 24-task study in
`ascend-torch4ms/experiments/paper_section_63_64/results_section641_multiscope_v1/`.
It varies feedback and the repair guide across four conditions, each with a
four-attempt budget. Execution-only pass/fail feedback does not invoke repair
for numerical or gradient faults that complete execution. These conditions use
their own task configuration and feedback implementation, separate from Fixed50.

The translation panel uses
`ascend-torch4ms/experiments/paper_section_63_64/results_section642_translator_guide_ablation_v4/`.
It evaluates five held-out tasks with three repeats per documentation condition,
one translator call per run, and repair disabled. Training completion requires a
non-empty gradient and a non-zero parameter update; it does not measure paired
numerical agreement. See `docs/paper-revision-plan-and-data.md` for the original
source index. Moving these results to the appendix does not change any values.

## Other inputs

Other figure inputs already tracked in this repository:

- Original per-step controls and faults: `data/paper_section_65_66/`.
- Gradient and parameter faults: Experiment C's `results_per_step/` CSV.
- Localization counts: Experiment K's `section65_fault_pool_localization_confusion_matrix.csv`.

The diagnostic matrix shows threshold crossings for at least one measured run.
Missing metrics after an execution failure are marked `n/a`, not zero.
The localization matrix measures diagnosis accuracy, separately from repair acceptance.
