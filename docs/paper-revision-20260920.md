# Unified migration results in the manuscript

The manuscript on `codex/iclr-2027-template` now follows the approved evidence
plan and the user's request to present the main result as 50/50. Main-table
acceptance uses the 50 frozen task identifiers; per-input token comparisons use
the 29 distinct source-and-contract pairs.
Experimental Setup explains that they correspond to 29 distinct source-and-contract
pairs from 24 source files. Identical conditions reuse one physical execution;
token totals count actual calls. No experiments or model calls were launched
for this revision.

## Paper content

- The abstract, introduction, and conclusion report LaDiM and MatchFixAgent at
  50/50 with 57.4% fewer end-to-end tokens for LaDiM.
- Table 1 contains all six methods on the MindSpore collection and all six
  methods on the 18-task cross-language collection in separate panels.
- Analysis covers initial-fault repair and healthy-program preservation,
  task-level token differences, measured submission budgets, training-signal
  detection latency, and use across languages and target frameworks.
- Table 2 reports the complete 16-instance training-signal experiment. The
  component and host-integration matrix appears in supplementary Table 3.
- Supplementary protocols distinguish the editing examples and format feedback
  used in the signal/JAX studies from the primary implementation. Additional
  supplied-target repair collections retain their original acceptance protocols.
- Guided historical outcomes remain in repository archives. Internal versions,
  experiment codes, run IDs, and operational labels are absent from paper text,
  table rows, and figure labels.
- The framework figure is a simple editable placeholder, as requested by the
  user, for later replacement by the author.

## Evidence and generated artifacts

`figures/make_unified_results.py` generates the comparison, signal, and component
tables, the total and per-input token plot, and `data/paper_figures/unified_results.json`.
That export records the SHA-256 hashes of the final audit, final summary, and
training-signal snapshot. The final audit retains all 391 conditions, including
the one SWE-agent integration interruption. Its unavailable final outcome never
inherits an earlier passing initial observation. InterTrans's observed cost
includes incomplete generation calls.

`data/paper_figures/autonomous_training_signals.csv` preserves the values in
`output/maintext-results-20260918/training_signals.csv`; the corresponding source
summary and provider audit hashes are in that directory's `evidence_index.json`.
Scientific interpretation is documented in
`maintext-training-signal-independent-review-20260918.md`. Detection and JAX
measurements follow their existing September 18 provenance documents.

The source/figure manifest and rendered review pages are saved locally under
`output/paper-revision-20260920/`. The frozen experiment inputs, baseline
implementations, acceptance decisions, and attempt budgets were not modified.

## Verification

Twenty-one relevant data and layout checks pass: six unified reporting checks and
fifteen existing paper-data/figure-layout checks. They cover common task IDs,
execution-group cost accounting, unavailable final outcomes, full-check signal
scoring, generated-data consistency, paired-cost coordinates, and label geometry.
`git diff --check` passes for the edited manuscript, figure, test, and supporting
documentation files. An unrelated pre-existing monitor JSON has CRLF whitespace
diagnostics and is unchanged by this revision.

`latexmk -pdf -interaction=nonstopmode -halt-on-error conference_101719.tex`
completes with no unresolved references, citations, or overfull boxes. The PDF
has 13 pages; the main text ends on page 8, references occupy pages 9–11, and
supplementary material occupies pages 12–13. All pages were rendered and reviewed,
with full-size inspection of the comparison table, total/per-input cost figure, signal
table, and supplementary component table. The official template is unchanged.

The editable placeholder retains its original native text, shapes, and
connectors. An attempted Artifact Tool import/export did not preserve connector
objects or apply multiline replacements. The final asset therefore uses the
original PPTX package with six text labels updated directly in its slide XML;
all other package members are preserved. The matching SVG provides the
manuscript's vector PDF. The author will replace this placeholder diagram.

## Concise abstract and revised cost analysis

The user's follow-up requests a concise abstract and introduction, with detailed
numerical analysis in the experiment section. The abstract now contains
162 words under the comparison document's counting convention,
retaining only 50/50 and the 57.4% token reduction as quantitative results.
Its final sentence attributes effectiveness to LaDiM. The shorter introduction
identifies MatchFixAgent as a state-of-the-art translation repair method and
cites the existing paper. Contribution 3 now reads: “We evaluate LaDiM across
frameworks and languages, and analyze its token use and training signals.”

At the user's request, Figure 3(b) replaces the largely flat submission-budget
curves with matched per-input token costs for LaDiM and MatchFixAgent. All 29
distinct pairs appear once, with both methods accepted. Coordinates sum unique
provider response IDs, including shared initial translation and all subsequent
calls, and reconcile exactly with the totals in panel (a). Symbols distinguish
the 20 initially accepted and 9 initially faulty pairs. LaDiM uses fewer tokens
on 19 and 8 pairs, respectively. The experimental prose explains this pattern
and retains the measured 1/2/4-submission outcomes. No model calls or experiment
reruns were added.

The earlier abstract/introduction comparison remains a snapshot of the first
results update. The current manuscript and PDF contain the subsequent concise
revision. The simple framework placeholder is unchanged.

## Abstract ending and introduction argument plan

The abstract now closes with effectiveness across frameworks and programming
languages, explicitly naming MindSpore, JAX, and Java-to-Python migration.
The introduction remains at the concise revision while its argument is discussed.
`docs/abstract-introduction-logic-20260920.md` records the proposed paragraph
functions and their evidence, informed by online MIT EECS, Stanford, CMU, and
UNC writing guidance and the MatchFixAgent paper. Retrieved source snapshots
are local under `tmp/writing-research-20260920/`.

After the abstract edit, `latexmk` succeeds and the PDF remains 13 pages.
The build has no unresolved references or citations and no overfull or
underfull boxes. The changed abstract and introduction pages were rendered
and visually inspected. The manuscript whitespace check passes. This update
changes no experimental results or figure assets and adds no experimental runs.

## Four-paragraph introduction and focused abstract

Following the author's approval of the argument and preference for fewer
paragraphs, the introduction now has four body paragraphs followed by the
existing three contributions. The paragraphs combine task context with prior
work, explain training-specific diagnosis, connect the central idea to the
repair method, and summarize evaluation and findings. MatchFixAgent is
identified as a state-of-the-art translation repair method at its first
introduction. Detailed detection times remain in the figure caption and
experimental analysis.

The abstract compresses the individual translator and orchestrator descriptions
into an account of evidence, autonomous investigation, repair, and external
training checks. It retains 50/50 acceptance, the 57.4% end-to-end token
reduction, and the conclusion about LaDiM's effectiveness across frameworks
and programming languages. The final abstract has 140 whitespace-delimited
words; the introduction and contributions have 497 after removing citations
and figure material. These counts use the validation script's whitespace
convention, separately from the historical comparison's word-token convention.

The overview's float placement now allows placement after the Method heading,
keeping the existing placeholder and caption together with their section.
All prose from Related Work onward is unchanged. The scientific figures,
experimental results, and contribution list are unchanged.

`latexmk` succeeds; the PDF has 13 pages and the main text ends on page 9,
within the nine-page limit. There are no unresolved citations or references
and no overfull boxes. Two underfull vertical-box notices concern pages 3
and 8; visual review confirms legible text and figures without clipping or
overlap. The revised front matter and affected pages were inspected at full
size, with an overview of all pages. The manuscript whitespace check passes.
The pre-edit snapshot, text diff, counts, build log, and rendered pages are
local under `tmp/writing-research-20260920/`.

## Main-table method references

The table exporter now includes method citations for SWE-agent, MatchFixAgent,
InterTrans, CodeTransEngine, and MSAdapter in both applicable panels.
CodeTransEngine's system-paper entry follows the citation supplied in
https://github.com/CodeTransEngine/CodeTransEngine; its authors are Marcos Macedo,
Yuan Tian, and Bram Adams, and its venue is the ICLR 2025 Third Workshop on Deep
Learning for Code. MSAdapter cites the official OpenI repository at version
0.6.0; the project's release list dates that version to 2025-12-30. Source
snapshots are local under `tmp/method-citations-20260920/`. The method description
uses the same corrected references.

Following the author's review, the main-table SWE-agent dagger and its table
note are removed. Direct LLM and test-guided repair have plain descriptive
labels; LaDiM is marked as ours. Acceptance decisions, denominators, and costs
remain unchanged, including the recorded incomplete SWE-agent outcome.

Six unified-data tests and seven figure-layout tests passed. The regenerated
result JSON is byte-identical to the pre-edit copy, and the original numerical
table cells were verified before the requested dagger removal. The manuscript
compiles without undefined citations or overfull boxes. The main table was
rendered and visually checked after the final label cleanup.

## Method and experiment revision (2026-09-21)

The approved [method and experiment plan](method-experiments-logic-20260920.md)
is implemented on `codex/iclr-2027-template`. At the start of this revision,
nine files had uncommitted changes. Their contents were preserved in the local
pre-edit snapshot, and the manuscript edits continued from that working state.
This revision remains uncommitted.

The method now defines the migration task and comparable training observations
together, then explains autonomous diagnosis and evidence-guided repair.
Translator remains the entry role in the overview and placeholder diagram.
The diagnosis section describes how observed discrepancies motivate code
inspection, hypotheses, and additional tests. The repair section explains the
independent handoff, retained workspace and conversation, and acceptance loop.
Related Work follows Experiments, and the MatchFixAgent input requirement is
stated there with its existing citation.

Main Experiments discusses both main-table panels. The framework comparison
explains repair and preservation at full acceptance; the language comparison
describes the additional accepted programs and token savings. The analysis
connects aggregate cost to matched input costs and submission behavior, then
examines detection latency and JAX repair. The signal ablation explains how
available observations affect repair initiation and stopping, with final full
verification. The complete component outcomes remain in the supplementary table.

Before prose polishing, the upstream Humanizer skill was checked through GitHub.
The latest commit affecting `SKILL.md` was
`9862685f575c65a8247f90369951df1b3416e3d6`, dated 2026-09-06. Its version is 3.0.0,
and the downloaded file, repository skill, and installed Codex skill have the
same SHA-256:
`e8269e236bed06ed0fe4824c274112e54950b0cb46b0bafe5e1576ef7c9f93d5`.
The humanizer review covered the abstract, introduction, method, experiments,
related work, conclusion, supplementary prose, captions, headings, and table
notes. It removed repeated explanations and tightened sentence structure while
retaining the main claims and the cross-framework and cross-language conclusion.

Six unified-result tests and seven figure-layout tests pass. The result JSON,
three numerical tables, figure assets and generator, and bibliography are
byte-identical to the pre-edit snapshot. All 27 citation keys used in the prose
are retained. `latexmk` builds a 13-page PDF without warnings, unresolved
references, or overfull or underfull boxes. The main text ends on page 8,
the AI use statement and references occupy pages 9--11, and the supplementary
material occupies pages 12--13. All pages were rendered; the complete montage
and the changed text and table/figure pages were visually inspected. No model
experiments were launched. Local snapshots, the skill update check, build log,
rendered pages, and validation record are under
`tmp/manuscript-revision-20260921/`.
