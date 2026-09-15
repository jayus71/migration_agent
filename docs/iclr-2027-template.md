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
.venv/bin/python figures/make_repair_comparison.py
.venv/bin/python -m unittest discover -s tests
latexmk -pdf -interaction=nonstopmode -halt-on-error conference_101719.tex
```

The main result table places methods in columns and measures in rows to fit the
single-column width while retaining all original values. The cost and cumulative
acceptance figure is generated at the ICLR text width to preserve readable
labels. Figure 1 keeps its two stacked panels and is included at 68% of the text
width. The method overview continues to use the existing vector PDF.

The compiled PDF has 13 pages; the main text and conclusion extend onto page 10.
The initial-submission limit is nine pages, so shortening the main text or moving
material to an appendix remains necessary before submission. The template's
margins, body font sizes, and line spacing have not been changed to reduce the
page count. References and the AI use statement do not count toward that limit.

The [AI Policy for Authors](https://iclr.cc/Conferences/2027/AIPolicyForAuthors)
requires an AI use statement. Its contents remain for the authors to supply.
No experiments were rerun during the template migration.
