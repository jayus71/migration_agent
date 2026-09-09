# Inputs for manuscript figures and tables

These CSV files are byte-for-byte copies of original experiment summaries. They
make the figure scripts runnable from this repository without the ignored local
`ascend-torch4ms` checkout. No result values or validation decisions were changed.

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

## JAX main-table rows

The JAX snapshot comes from `codex/track-c-torchax-autofix` at `3352f71` in the
experiment repository. It contains 24 records, one for each of four methods on
six MLP/CNN tasks. The per-instance model, stage, acceptance, attempts, and token
counts were checked against all 24 original JSON reports. Each accepted repair
passes training verification on three seeds. This is separate from the Fixed50
fault-specific acceptance criterion.

Run `python figures/make_jax_table.py` to regenerate `figures/TABLE_jax_rows.tex`,
which the manuscript includes in the lower part of the main table. All numeric
cells come from the snapshot. The repair-location mapping follows
`autofix/faults/injection.py::_prepare_torchax_compat`, which accepts only
candidate-program faults. Adapter operator, autodiff/optimizer, Transformer,
and language-model categories have no JAX instances. The JAX panel omits those
columns and states the common candidate-program scope in the table note.

The Track C README and each method's `summary.json` record different budgets.
LADDER allows up to three rounds; Direct LLM and each converter run once. All
accepted results finish in round one. The CSV's `repair_at_4` field is computed
from the successful round index; it does not record a shared four-attempt run.
The table therefore reports first-attempt and overall acceptance, with the
budgets stated in its note.

Token cost includes all attempted instances. LADDER uses 17,543 / 6 = 2,923.8
tokens per accepted repair (2.9K in the table); Direct LLM uses 74,841 / 5 =
14,968.2 (15.0K). Ivy and torch2jax use no LLM tokens and accept no repairs, so
their cost per accepted repair is undefined and marked `n/a`.

## Other inputs

Other figure inputs already tracked in this repository:

- Original per-step controls and faults: `data/paper_section_65_66/`.
- Gradient and parameter faults: Experiment C's `results_per_step/` CSV.
- Localization counts: Experiment K's `section65_fault_pool_localization_confusion_matrix.csv`.

The diagnostic matrix shows threshold crossings for at least one measured run.
Missing metrics after an execution failure are marked `n/a`, not zero.
The localization matrix measures diagnosis accuracy, separately from repair acceptance.
