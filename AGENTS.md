# Manuscript and evidence

Read `README.md`, `data/paper_figures/README.md`, and the relevant experiment
provenance before editing the paper or its figures. The manuscript is
`conference_101719.tex`. Make paper changes on the branch requested by the user.
Preserve existing work. Commit, push, open a PR, or merge only as requested.

## Writing

Use clear paragraphs with one main point each. State the point early, use
concrete subjects and verbs, and prefer active voice. Use lists when the items
need comparison or have an explicit order. Avoid nested lists, filler,
inflated claims, invented terminology, repeated contrast formulas, and dense
hyphenated modifiers. In the abstract, avoid colon-led enumerations and
mechanical closing summaries.

Review the whole manuscript with `.claude/skills/humanizer/SKILL.md`, including
captions, headings, and table notes. Keep supported claims and confirmed wording.
Do not add defensive qualifications during prose editing. Preserve the abstract's
cross-framework conclusion and the heading `Generalization Across Frameworks`.

Use `literature/zhekai-du/Academic-Writing-DNA.md` for the requested writing style.
Its corpus contains first-author papers only. Apply the same plain writing
standards to the DNA itself; do not infer an author's contribution from other
coauthored papers. The repository's skill sources are under `.claude/skills/`;
install copies under the active Codex user's `skills/` directory when needed.

Use consistent names for execution, forward values, gradients and parameter
updates, repair location, and the LLM used for repair across prose and figures.
Describe per-step synchronization directly; do not call it teacher forcing.
Use complete terms in prose, figures, and table headings. Do not shorten them
to labels such as `Grad./upd.` or `optim.`; use line breaks and suitable column
widths. Experimental prose should analyze the patterns and mechanisms supported
by the results, using selected numbers as evidence instead of repeating table rows.

## Results and figures

This revision uses the original 50-instance main experiment. Preserve 50/50
acceptance within four attempts, 84% first-attempt acceptance, and approximately
29-fold lower tokens per accepted repair than MatchFixAgent. Do not rerun or
expand experiments unless requested. Keep fault-specific repair acceptance,
paired-threshold verification, localization accuracy, and detection latency
distinct. Missing measurements after execution failure are `n/a`, never zero
or a passing check. Do not alter numbers, denominators, or attempt budgets.

Each figure should support a distinct claim. Use the existing cost and cumulative
acceptance comparison at the measured budgets of 1, 2, and 4 attempts. Update
generation scripts, labels, captions, and included assets together. Check figures
at their actual manuscript size for readable text, overlap, and clipping.

In Figure 1, panel (a) contains loss and gradient differences; panel (b) contains
loss and update differences. Put panel names inside the plot. Use arrows for
step-1 detection and the mean loss difference crossing at steps 31 and 18.
Label the detection threshold and use `Loss difference`. The caption must
distinguish the mean curve's crossing from detection times in individual runs.

The method overview should show the current repair procedure and both target
frameworks. Keep its PowerPoint text, shapes, and connectors editable and export
a vector PDF for LaTeX from the same diagram.

## Verification and collaboration

Run the relevant existing data and layout checks after changing figure scripts.
Compile the manuscript with `latexmk` and inspect the resulting PDF. Do not claim
an experiment was rerun when only analysis or typesetting was checked.

Use subagents only when requested. When requested, use `gpt-6-astra`.
