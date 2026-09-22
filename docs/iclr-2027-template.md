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

## Current build and layout (2026-09-21)

Build commands are maintained in [README.md](../README.md#figures-and-pdf).
The entry point includes `sections/experiments.tex` and
`sections/supplementary_experiments.tex`. The consolidated comparison table has
MindSpore, cross-language, time series repository, and recommendation repository
panels. Its program panels include input/output token breakdowns; repository
panels show counts of passed checks, training signals, and entry points or tests.
Two further main tables cover natural fault repair and training signal ablation.
Figure 3 shows stacked total agent tokens and 29 signed per-input token savings
bars, with separate sorting for initially accepted and initially faulty inputs.
Acceptance at one, two, and four submissions remains in the prose. The method
overview remains a placeholder; work on it stopped at the user's request.

The main chapters are Introduction, Related Work, LaDiM, Experiments, and
Conclusion. LaDiM includes the repository coordination and context mechanism.
The experiment sections are Experimental Setup, Main Experiments, Analysis
Experiments, and Ablation Studies. Generalization Across Frameworks retains
its heading. Supplementary sections contain task construction and protocols,
component matrices for the common collection and natural faults, repository
checks and costs, and context reconstruction details.

The compiled PDF has 17 pages. The main text ends on page 9. The official style,
margins, body font, and line spacing are unchanged, within the nine-page main
text limit.
The AI use statement remains blank for the authors to complete.

The [revision record](paper-revision-execution-20260921.md) lists evidence sources and the
data, layout, compilation, and visual checks. This revision uses completed
experiments and makes no model calls.
