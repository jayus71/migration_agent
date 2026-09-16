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

## Build and layout

From the repository root in Ubuntu/WSL:

```bash
.venv/bin/python figures/make_gradient_drift.py
.venv/bin/python figures/make_repair_comparison.py
.venv/bin/python figures/make_jax_table.py
.venv/bin/python figures/make_results_tables.py
.venv/bin/python figures/update_overview_labels.py
.venv/bin/python -m unittest discover -s tests
latexmk -pdf -interaction=nonstopmode -halt-on-error conference_101719.tex
```

The main result table places methods in rows and four acceptance/cost metrics in
columns. MindSpore and JAX occupy separate panels with their own denominators,
acceptance criteria, and recorded attempt budgets. The original fault-stage,
repair-location, and model breakdown is preserved in Appendix B. The cost and cumulative
acceptance figure is generated at the ICLR text width to preserve readable
labels. Figure 1 uses two side-by-side panels at the full text width, with
in-panel names and separate arrows for fault detection and the mean loss
crossing. Its caption distinguishes these measurements. The method overview
uses a vector PDF exported from `figures/架构图0914.svg` at full text width;
its code examples remain small. The SVG, PDF, and PNG use the current LaDiM name.

Related Work uses three run-in category headings: Code Translation and Framework
Migration, Differential Testing and Deep Learning Verification, and Automated
Program Repair and LLM Agents. Each category has one substantive paragraph,
ending with the corresponding distinction of LaDiM. The closest repair comparison
with MatchFixAgent is developed in the third paragraph. Related Work spans
pages 2--3.

The experiment section uses five topic headings: Experimental Setup, Repair
Effectiveness and Efficiency, Generalization Across Frameworks, Diagnosis
Analysis, and Ablation Study. The JAX results share the main table with the MindSpore repair
comparison, followed by the framework discussion. The feedback ablation table
uses the archived feedback study and leaves three unmeasured controls open.
It places variants in rows and acceptance, first-attempt acceptance, token cost,
and elapsed time in columns; the variant definitions appear in the prose. Its analysis begins
on page 7, and the table appears at the top of page 8. Table notes use full-width minipages. The manuscript
uses continuous prose within these sections, without paragraph-level headings.
Connected descriptions of agent roles, repair control, and experimental
conditions and results share paragraphs.

Appendix A contains the separate repair and translator documentation studies,
with a short discussion and appendix reference in the main-text ablation section.
Both documentation panels span the text width, with spacing between repair
locations and a shared two-row label for automatic differentiation and optimizer
code. The original experimental values and figure assets are preserved. Appendix B
retains the original feedback comparison used by Figure 3. Appendix C reports
the 12-task signal study and all three feedback-presentation repeats.

The compiled PDF has 13 pages. The main text and conclusion end on page 8;
the AI use statement and references occupy pages 8--10, and Appendix A occupies
page 11. Appendices B and C occupy pages 12 and 13. The template's margins, body font sizes, and line spacing are unchanged. The
[author guidelines](https://iclr.cc/Conferences/2027/AuthorGuidelines) specify
nine main-text pages for initial submission and ten for discussion/rebuttal and
camera-ready versions. References and the AI use statement do not count toward
that limit. The main text fits the initial-submission page limit.

The [AI Policy for Authors](https://iclr.cc/Conferences/2027/AIPolicyForAuthors)
requires an AI use statement. Its contents remain for the authors to supply.
The section reorganization was checked with `latexmk`, the eight existing paper
data checks, comparison of all table cells and protected asset hashes, and visual
inspection of the rendered PDF. Paragraph consolidation was checked with
`latexmk`, comparison of the complete table and figure environments, equations,
citations, numerical values, and protected asset hashes, and inspection of all
12 rendered pages. The subsequent related-work revision was checked with
`latexmk`, preservation of all cited works and protected assets, and visual
inspection of all 11 pages. The revision changes Related Work and restores a
space after a conditional footnote in the adapter description. No experiments
were rerun.

The metrics and component-ablation revision was checked with 34 data and layout
tests, `latexmk`, preservation of the original snapshots and figure assets, and
visual inspection of the main tables and appendix tables. The main text still
ends on page 8. This revision reuses archived experiments. Metric definitions,
literature sources, and measurement gaps are recorded in
`docs/metrics-and-ablation-revision.md`.

The ablation presentation revision follows the component comparisons in the
provided MatchFixAgent paper (Section 3.4 and Figure 4) and ExeCoder (Tables 2–7).
Internal experiment identifiers and source revisions are confined to the data
documentation. The manuscript gives the evaluation protocol and repeated-run
results. The revised result table was compiled in a separate build directory and
visually checked before replacing the workspace PDF.
