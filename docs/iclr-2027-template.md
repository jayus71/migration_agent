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

## Current build and layout (2026-09-20)

Build commands are maintained in [README.md](../README.md#figures-and-pdf).
The entry point includes `sections/experiments.tex` and
`sections/supplementary_experiments.tex`. The comparison table has separate
MindSpore and cross-language panels; the second main-text table reports the
training-signal ablation. Figure 3 shows total agent tokens and a matched
per-input LaDiM/MatchFixAgent cost scatter. Acceptance at the measured budgets
of one, two, and four submissions remains in the prose. The editable method
overview remains a simple placeholder for the author to replace.

The experiment sections are Experimental Setup, Main Experiments, Analysis
Experiments, and Ablation Studies. Generalization Across Frameworks retains its
heading. Supplementary sections cover complete protocols, component and host
integration results, and additional supplied-candidate repair studies.

The compiled PDF has 13 pages. The conclusion and main text end on page 9;
the AI use statement and references occupy pages 9–11, and supplementary
material occupies pages 12–13. The official style, margins, body font, and line
spacing are unchanged. This fits the nine-page initial-submission main-text limit.
The AI use statement remains blank for the authors to complete.

The [revision record](paper-revision-20260920.md) lists evidence sources and the
data, layout, compilation, and visual checks. This revision uses completed
experiments and makes no model calls.
