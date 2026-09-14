# Inputs for manuscript figures and tables

These CSV files are byte-for-byte copies of original experiment summaries. They
make the figure scripts runnable from this repository without the ignored local
`ascend-torch4ms` checkout. No result values or validation decisions were changed.

The manuscript now names the method MARS (Multi-Agent Repair System). Its
archived identifiers remain `r_hier`, `c_hier`, and `T-HIER`; earlier drafts
called the same method LADDER. Only presentation labels are renamed.

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
which the manuscript includes in the JAX repair table. All numeric
cells come from the snapshot. The repair-location mapping follows
`autofix/faults/injection.py::_prepare_torchax_compat`, which accepts only
candidate-program faults. Adapter operator, autodiff/optimizer, Transformer,
and language-model categories have no JAX instances. The JAX table omits those
columns and states the common candidate-program scope in the table note.

The Track C README and each method's `summary.json` record different budgets.
MARS allows up to three rounds; Direct LLM and each converter run once. All
accepted results finish in round one. The CSV's `repair_at_4` field is computed
from the successful round index; it does not record a shared four-attempt run.
The table reports accepted counts by fault stage and overall. Its note states
the budgets and that all accepted repairs finish in the first round.

Token cost includes all attempted instances. MARS uses 17,543 / 6 = 2,923.8
tokens per accepted repair (2.9K when rounded); Direct LLM uses 74,841 / 5 =
14,968.2 (15.0K). Ivy and torch2jax use no LLM tokens and accept no repairs, so
their cost per accepted repair is undefined. The table omits the cost column;
it does not substitute zero for this undefined ratio.

## MindSpore translation rows

This comparison is excluded from the current manuscript. Its archived data and
generator remain available here. It is separate from the translator documentation
ablation retained in Table III(b).

`figures/make_mindspore_translation_table.py` reads the current `source_summary`
paths in `data/experiments/05_experiment_E_track_a_rerun/final/run_manifest.json`.
It generates `figures/TABLE_mindspore_translation_rows.tex` from the 15 measured
task--seed rows for each of Direct LLM, CodeTransEngine, MSAdapter, and MARS.
It checks the task grid, matching source-program hashes, recorded revisions,
and measured training and acceptance flags. Historical summaries outside those
indexed paths are not used. See Experiment E's `README.md` for source precedence.

This panel measures complete translation on five source tasks and three seeds.
It is separate from the original 50-instance repair pool. Training completion
requires gradients and parameter updates; acceptance additionally requires
paired numerical agreement. MARS permits four repair rounds after translation,
but its initial translations pass without invoking repair. The other methods
translate once; MSAdapter uses one candidate per task. X2MindSpore remains
unmeasured in this snapshot and is excluded from rate comparisons.

## Other inputs

Other figure inputs already tracked in this repository:

- Original per-step controls and faults: `data/paper_section_65_66/`.
- Gradient and parameter faults: Experiment C's `results_per_step/` CSV.
- Localization counts: Experiment K's `section65_fault_pool_localization_confusion_matrix.csv`.

The diagnostic matrix shows threshold crossings for at least one measured run.
Missing metrics after an execution failure are marked `n/a`, not zero.
The localization matrix measures diagnosis accuracy, separately from repair acceptance.
