# Introduction figure: observed training discrepancy

## Visual references inspected

- [ExeCoder, Figure 1](https://aclanthology.org/2025.emnlp-main.362/),
  EMNLP 2025, paper page 1. The figure isolates one concrete translation error
  and shows the relevant source and target operations. The new diagram uses
  this focus on a single failure location.
- [Domain-Agnostic Mutual Prompting, Figure 1](https://arxiv.org/abs/2403.02899),
  paper page 1. Aligned comparisons pair a mechanism illustration with selected
  measurements. The new diagram similarly places observed signals beside the
  source and translated computations.
- [MatchFixAgent, Figure 1](https://arxiv.org/abs/2509.16187), paper page 2.
  This figure presents the agent architecture. Our manuscript already has a
  method overview, so the introduction diagram concentrates on the training
  discrepancy that motivates verification.

Reference page renders are under `tmp/intro-figure-references/`. The ExeCoder
PDF was retrieved from ACL Anthology; the other two PDFs were already in the
local literature collection. No visual elements are copied from these papers.

## Evidence and interpretation

The diagram uses I-09 from Experiment I, a natural LLM translation with no
injected fault. The translator is `deepseek-v4-flash`; the target executes through
the torch4ms adapter on MindSpore. The initial paired probe synchronizes model
state and executes one training step. Its observed loss difference is
`4.76837158203125e-7`, gradient norm difference `0.418631911277771`, and parameter
update relative L2 difference `0.9252656699732557`. The corresponding comparison
thresholds are `0.02`, `0.05`, and `0.03`.

All six parameter tensors in `value`, `gate`, and `norm` have zero target
updates and nonzero source updates. The two `head` parameter updates match the
source. These are tensor counts, not counts of individual scalar parameters.
The output depicted is loss; the archive does not contain an elementwise
comparison of every output tensor.

`data/paper_figures/intro_motivation_evidence.json` stores the measured values,
parameter diagnostics, source path, and SHA-256. Recreate it with
`python scripts/extract_intro_motivation_evidence.py`. This script reads the
archived JSON and does not execute training or repair.

The marked GroupNorm boundary comes from the static code review in
`docs/natural-translation-cause-review-20260916.md`: the high-level mapping is
absent, and the fallback copies values through NumPy without a backward bridge
between frameworks. The illustration identifies that adapter path. The archive
does not contain a per-operator dynamic trace or a successful repair of this
case; LaDiM ends at `STOP_NO_PROGRESS`. The diagram therefore shows detection,
with no successful-repair panel or baseline-specific outcome.

## Layout revision

The user supplied a paper figure as an alignment reference. The selected
generated design is `output/imagegen/intro-layout-reference-v3.png`. It uses a
wide canvas with a single migration panel on the left and two comparison panels
stacked on the right. Both columns share their top and bottom boundaries; the
two right panels have equal widths and heights in the editable reconstruction.
All title bars, insets, and gaps follow a common grid. Experiment identifiers,
the concluding banner, and the detailed mechanism inset are omitted.

The comparison titles are `SWE-agent / MatchFixAgent` and `LaDiM (Ours)`.
The named baselines use code, tests, or semantic analyses; their panel depicts
repair feedback and inference of the fault location. The archived natural case
does not establish that both named baselines accepted this faulty program.
The figure therefore does not assign them an execution-only stopping rule or
a measured failure outcome. The LaDiM panel shows the observed signal mismatch.

The generated reference is a layout draft. The editable reconstruction preserves
all forward network connections and places the red break on a separate backward
arrow, with the output head still connected.

## Caption draft

Training verification in code migration. An LLM translation from PyTorch to
MindSpore executes with nearly matching loss, while six parameter tensors
receive zero updates. The baseline panel summarizes the code, testing, and
semantic feedback used to infer a repair location. LaDiM checks execution,
loss, gradients, and parameter updates in order and identifies the failing
training stage. The reported loss difference and unchanged parameter tensors
are observations from the first training step with synchronized initialization.

The editable source is `figures/repair_cases.pptx`; the manuscript asset is
`figures/training_repair.pdf`. Export and layout details are in
`figures/REPAIR_CASES.md`.
