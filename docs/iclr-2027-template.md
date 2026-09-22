# ICLR 2027 manuscript template

The manuscript entry point remains `conference_101719.tex`. It uses the official
ICLR 2027 single-column style, anonymous review header, line numbers, and
author-year citations. The funding acknowledgment and project repository link
are included only when `\iclrfinalcopy` is enabled. That switch remains disabled.
The AI use statement is intentionally empty at the author's request.

## Template source

The template comes from the supplied `docs/iclr-2027-style-files.zip`, linked by
the [ICLR 2027 Author Guidelines](https://iclr.cc/Conferences/2027/AuthorGuidelines).
These four files are copied without modification to the repository root:

- `iclr2027_conference.sty`
- `iclr2027_conference.bst`
- `natbib.sty`
- `fancyhdr.sty`

The bundled `fancyhdr.sty` preserves the review header defined by the official
template. The example manuscript, bibliography, and optional math macros are not
needed by this paper. `conference_101719.bbl` is regenerated from `ref.bib` using
the official bibliography style.

## Current build and layout (2026-09-22)

Build commands are maintained in [README.md](../README.md#figures-and-pdf).
The entry point includes `sections/experiments.tex` and
`sections/supplementary_experiments.tex`. The consolidated comparison table has
MindSpore, cross-language, time series repository, and recommendation repository
panels. Its program panels include input/output token breakdowns; repository
panels show counts of passed checks, training signals, and entry points or tests.
Further main tables cover saved initial translation repair, six JAX repair and
native conversion controls, and a three-panel ablation table. The ablation panels
contain training signals, repair history and independent evidence handoff on saved
translations, and two separate repository context and structural analysis pairs.
Figure 3 shows stacked total tokens for LaDiM, MatchFixAgent, and SWE-agent beside
29 signed per-input token savings bars for the LaDiM/MatchFixAgent pair, sorted
within the two initial-check groups.
Acceptance at one, two, and four submissions remains in the prose. The method
overview is maintained by the author and is preserved outside this revision.

The main chapters are Introduction, Related Work, Methods, Experiments, and
Conclusion. Methods defines program repair history, independent evidence handoff,
and the repository coordination and context mechanism before their ablations.
The experiment sections are Experimental Setup, Main Results, Analysis
Experiments, and Ablation Studies. Generalization Across Frameworks retains
its heading. Supplementary sections contain task construction and protocols,
component matrices for the common collection and natural faults, repository
checks and costs, context reconstruction details, complete repository component
results, and the separate native JAX study with consecutive training steps.

The compiled PDF has 22 pages. The main text ends on page 11, where references
begin; the appendix starts on page 14. The official style, margins, body font,
and line spacing are unchanged. The user deferred compression to the nine-page
main-text limit for this content revision.
The AI use statement remains blank for the authors to complete.

The [revision record](paper-clarity-execution-20260922.md) lists evidence sources and the
data, layout, compilation, and visual checks. This revision uses completed
experiments and makes no model calls.
