# ICLR 2027 manuscript template

The manuscript entry point remains `conference_101719.tex`. It uses the official
ICLR 2027 single-column style, anonymous review header, line numbers, and
author-year citations. The funding acknowledgment and project repository link
are included only when `\iclrfinalcopy` is enabled. That switch remains disabled.
The AI use statement is included in the anonymous review build. Acknowledgments
remain inside the final-only conditional so the review PDF stays anonymous.

## Template source

Latest layout check (2026-09-25, S69/S70): the main text ends on page 9 near review line 479; the AI use statement is also on page 9. References begin on page 10, appendices on page 14, and the complete PDF has 24 pages. The user explicitly selected local small text for algorithms and tables and removed the repository's default-size requirement. Official style files, body text size, page dimensions, and line spacing are unchanged. See the [compression record](manuscript-compression-20260925.md). The dated audits below preserve their original conclusions.

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
panels. Its program panels are adjacent; repository panels use shared method rows
and grouped task columns. Complete input/output token breakdowns and repository
gradient and parameter update checks appear in the appendix.
Further main tables cover saved initial translation repair, six JAX repair and
native conversion controls, and a three-panel ablation table. The ablation panels
contain training signals, repair history and independent evidence handoff on saved
translations, and two separate repository context and structural analysis pairs.
The first two panels sit side by side; each repository component occupies one
row with separate without/with columns. The JAX table groups method columns by
LLM repair or native conversion. Appendix repository ablations use shared condition
rows and separate columns for both repositories. These tables use the template's
default 10-point text following the September 23 formatting review.
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

The compiled PDF has 24 pages. The main text ends on page 10, references begin on
page 11, and the appendix starts on page 14. The official style, margins, body font,
and line spacing are unchanged. The user authorized horizontal table organization
after the content revision, preserving the prose and evidence. Further compression
to the nine-page main-text limit remains deferred.
The AI use statement is now present in the anonymous review build. The current
text describes the generative AI assistance used for software, experiments,
figures, literature search, and manuscript preparation, together with review
and author-responsibility language.

The [revision record](paper-clarity-execution-20260922.md) lists evidence sources and the
data, layout, compilation, and visual checks. This revision uses completed
experiments and makes no model calls.

## Official-file and main-TeX audit (2026-09-23)

The [Author Guidelines](https://iclr.cc/Conferences/2027/AuthorGuidelines) link
the [official archive](https://media.iclr.cc/Conferences/ICLR2027/iclr-2027-style-files.zip).
A fresh download on September 23 has SHA-256
`0d940dfa9398ae99a18f24a85a8a683f367204b6af6d17d2899e60a67102529e`.
The four style files listed above are byte-for-byte identical to that archive
in both the source and Overleaf repositories. Their Git history contains the
official-template import (`f77519b`) and no later edits.

The main TeX is also checked. `hidelinks` was an extra hyperlink option and is
removed at the user's request; the official example loads `hyperref` without
options. The user clarified that settings absent from the example are allowed
unless prohibited. URL line breaking, local hyphenation controls, pagination
guards, and figure/table placement are consequently retained. No page dimensions,
font-size definitions, paragraph spacing, or line-spacing definitions are
overridden in the main TeX or included sections.

The official example's [Final instructions](https://github.com/ICLR/Master-Template/blob/master/iclr2027/iclr2027_conference.tex#L318-L323)
say not to change font sizes, with a possible exception for references. It gives
no algorithm-specific exception. This revision therefore keeps pseudocode at
the default size and removes local reductions from tables and table notes.
Table widths and column spacing accommodate the default 10-point text without
changing data. The official style definitions remain untouched.

The body still ends on page 10; the initial-submission limit is nine pages.
Page-count reduction remains a content/layout task rather than a reason to
change the template. The AI use statement is present in the review build. These
outstanding submission tasks are separate from the
byte-level template verification.

## Official conditional macros audit (2026-09-25)

The official example source uses the public switch `\iclrfinalcopy`, which is
commented out for anonymous submission and enabled for a camera-ready paper.
The official `iclr2027_conference.sty` defines the switch internally with
`\newif\ificlrfinal` and uses `\ificlrfinal` for the review/final header and
author block. The root style file and `docs/template/iclr2027/iclr2027_conference.sty`
are byte-for-byte identical to the same file in the official ZIP.

The paper uses that official internal conditional only around acknowledgments:
the AI use statement is unconditional and therefore appears in the anonymous
review PDF, while funding and institutional acknowledgments remain final-only.
This conditional does not change page dimensions, font sizes, line spacing, or
other formatting parameters. The official example and the current paper both
leave `\iclrfinalcopy` commented out for review.

The preamble audit also found an unused `listings` style that set code text to
`\footnotesize`; no listing uses it. That dead definition and package import
were removed from the paper preamble so the submission source contains no
unneeded local font-size override.

The official example was compiled in an isolated copy with the tracked style
files. It produced a 7-page US Letter PDF and included the official AI use,
Ethics, and Reproducibility statement sections.
