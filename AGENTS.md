# Manuscript and evidence

Read `README.md`, `data/paper_figures/README.md`, and the relevant experiment
provenance before editing the paper or its figures. The manuscript is
`conference_101719.tex`. Make paper changes on the branch requested by the user.
Preserve existing work. Before each new round of edits, inspect `git status`
and the current diff, then commit the existing task changes as a checkpoint.
When the relevant working tree is clean, the current commit is the checkpoint;
do not create empty commits. Check Git status after each substantial batch and
before delivery, and commit the completed, verified task changes. Keep unrelated
user files intact and out of task commits. Push, open a PR, or merge only as
requested.

Maintain the word-level manuscript comparison against the immutable baseline in
`data/manuscript_baselines/pre-6pro-20260921/`. After each manuscript revision,
run `scripts/update_manuscript_diff.py` and include the updated comparison with
the delivery. The LaTeX build also refreshes it through `.latexmkrc`. Keep this
baseline fixed unless the user explicitly selects another version.

Maintain `docs/manuscript-feedback-register.md` as the persistent manuscript
feedback register. Update it while reading the paper, receiving feedback,
resolving decisions, and editing. Before every revision, read all active items
and identify the applicable IDs and agreed changes. After every revision,
check every active item again, including already satisfied items, for regressions
across prose, algorithms, figures, tables, and appendices. Record current evidence,
the reviewed version, and unresolved items; do not delete completed feedback or
carry an unchecked item forward as newly verified. When opinions conflict, use
the user's latest explicit instruction or explicitly approved plan, preserving
the earlier instruction and its replacement in the register. Date precedence by
the original instruction or latest confirmation, not by a later re-paste of old
feedback. Unapproved agent suggestions do not supersede user requirements.
Keep proposed fixes separate from approved changes when the user asks to review
a plan first. Every manuscript delivery must update the register's review log.

## Writing

In prose source, keep each complete paragraph on one source line, with blank
lines between logical paragraphs. Do not hard-wrap prose at sentence boundaries
or a fixed width. Preserve structured line breaks in equations, algorithms,
tables, and code listings.

Keep the official ICLR style files byte-for-byte identical to the package
linked by the current Author Guidelines. Do not redefine the template's page
dimensions, body font sizes, or line spacing. Use local \small for algorithm
bodies and table contents, as explicitly requested by the user on 2026-09-25.
Do not treat absence from the official example TeX as a prohibition. Preserve
permitted URL wrapping, local hyphenation, pagination, and figure/table layout
controls. Follow explicit user preferences for optional hyperlink styling.

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

Never expose internal development names or operational bookkeeping in the
manuscript, including headings, captions, legends, table rows, and notes. Internal
version labels, run identifiers, experiment codes, configuration keys, branch
names, and archival labels belong in provenance documents. Use the method's paper
name and describe datasets and experimental variants by their scientific meaning.
Keep genuine methodological differences explicit without referring to development
history. This rule also applies to text generated by figure and table scripts.

## Results and figures

Use one frozen task collection and one acceptance protocol for the main method
comparison. All applicable methods must run on the same task identifiers, source
programs, evaluation inputs, initial states, seeds, and acceptance thresholds.
Define a common task and supply the inputs each native method requires before
launching the comparison. Keep its native algorithm, tools, prompts, and retry
policy intact; document necessary backend integration. Never fabricate source
programs from hidden healthy targets or supply fault labels or repair answers.
Separate methods that solve different tasks from the main ranking; do not pad the
main comparison with results from incompatible datasets or denominators.

Preserve each baseline's own implementation and settings. Do not repair its
algorithmic bugs, improve its prompts or parsers, add retries, or compensate for
its functional failures. Restore prior baseline-specific fixes to the pinned
upstream behavior and retain their historical results under the actual modified
configuration. Fix errors in our integration, task inputs, evaluation, and
dependency setup so the comparison does not handicap a baseline; document these
changes separately. Baseline failures remain in the declared denominator and
cost ledger. Use useful baseline ideas to improve our method, and check our own
implementation for problems observed in baselines. Pursue better results through
method improvements under the frozen protocol, retaining all valid outcomes.

Report the main comparison in a consolidated table and shared figures. State
attempt and model budgets, failures, applicability, and cost accounting once in
the experimental setup. Use the same declared denominator and include all failed
attempts in cost. Use additional tables only for distinct scientific questions,
not for internal batches or versions. Preserve historical evidence, but do not
combine outcomes across protocols or substitute favorable historical numbers.
The earlier guided 50/50, 84%, and 29-fold results are archival measurements,
not targets that a new autonomous comparison must reproduce.

Do not rerun or expand experiments unless requested. Keep fault-specific repair acceptance,
paired-threshold verification, localization accuracy, and detection latency
distinct. Missing measurements after execution failure are `n/a`, never zero
or a passing check. Do not alter numbers, denominators, or attempt budgets.

Each figure should support a distinct claim. Figure 3 compares total token use
and matched per-input token costs for LaDiM and MatchFixAgent. Keep acceptance
at the measured budgets of 1, 2, and 4 attempts in the experimental prose. Update
generation scripts, labels, captions, and included assets together. Check figures
at their actual manuscript size for readable text, overlap, and clipping.

In the training-signal detection figure (`fig:gradient-drift`, currently Figure 4),
panel (a) contains loss and gradient differences; panel (b) contains
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

## ICLR 2027 submission compliance

Treat this section as a hard submission gate. Re-check the official pages immediately before uploading because deadlines, form fields, and policies can change:

- [ICLR 2027 Author Guidelines](https://iclr.cc/Conferences/2027/AuthorGuidelines)
- [ICLR 2027 AI Policy for Authors](https://iclr.cc/Conferences/2027/AIPolicyForAuthors)
- [ICLR 2027 Call for Papers](https://iclr.cc/Conferences/2027/CallForPapers)
- [ICLR 2027 official style files](https://media.iclr.cc/Conferences/ICLR2027/iclr-2027-style-files.zip)

### Required paper and submission contents

- Submit the genuine, final abstract and paper through the ICLR 2027 OpenReview venue. Verify the current abstract and full-paper deadlines; the official page states that late submissions are not accommodated.
- Include a non-empty `AI use statement` in the submitted paper PDF. It must be visible in the anonymous review build, appear before the references, and be excluded from the page count. Complete the separate AI-use fields in the OpenReview form as well.
- The AI disclosure must cover every required-disclosure task that applies, including synthetic data, theoretical or conceptual development, mathematical claims or proofs, hypotheses, methodology or experiment design, method implementation, translation, dataset cleaning or reformatting, qualitative analysis, and result interpretation. Disclose recommended uses when applicable, including code editing, figures or images, paper drafting or editing, literature search, brainstorming, parameter suggestions, and artifact creation. State how the authors reviewed AI-assisted work and take responsibility for the final content.
- Add the recommended paragraph-long `Reproducibility Statement` at the end of the main text before the references. It should point to the paper, appendix, code, data-processing description, assumptions or proofs, and supplementary materials that support reproduction. ICLR does not require a separate reproducibility checklist file; do not treat one as a missing formal upload.
- Add an `Ethics Statement` when the work raises relevant issues such as human subjects, data release, harmful applications, sponsorship or conflicts, bias or fairness, privacy or security, legal compliance, or research integrity. This statement is optional otherwise and does not count toward the page limit (the guidelines recommend no more than one page).
- Use the official ICLR 2027 style files byte-for-byte. Keep the review submission in anonymous mode and do not change the official page dimensions, body font sizes, or line spacing.
- Keep the main text at nine pages or fewer at initial submission. References do not count, and appendices may follow the bibliography; the AI-use, reproducibility, and applicable ethics statements are excluded as specified by the guidelines. Reviewers are not required to read appendices or supplementary material.
- Assemble any supplementary text after the references and label it as an appendix. Code and other supplementary files are encouraged but optional; every submitted file, archive, link, source comment, generated artifact, and file metadata must preserve double-blind anonymity and be runnable or inspectable as described in the reproducibility statement.

### OpenReview and policy checks

- Confirm that every author has a current OpenReview profile and that the author names, order, affiliations, email addresses, conflicts, subject areas, keywords, title, and abstract are final and consistent. Do not add or remove authors after the abstract deadline, do not change the author set after the paper deadline, and observe the title-change restriction after the paper deadline.
- Check the ICLR author quotas and reciprocal-reviewing requirement for the current cycle, including the requirement that at least one eligible author registers as a reviewer when the guidelines require it.
- Confirm that the work is not previously published, accepted, or submitted in parallel in violation of the dual-submission policy. Cite related anonymous-review work in third person as required.
- Have every author read and explicitly acknowledge the ICLR Code of Ethics during submission. Decide and record whether an ethics statement is applicable before final PDF generation.
- Verify that the upload contains the intended PDF and anonymous supplementary bundle, and that the PDF page count is measured from the final rendered submission rather than from source files or an earlier build.

### Current repository audit (2026-09-25)

- **Resolved in the 2026-09-25 revision: AI use statement visible.** `conference_101719.tex` now contains a non-empty disclosure outside `\ificlrfinal`, so the anonymous review PDF includes it. Re-check the disclosure against the final AI-use form before upload.
- **Resolved in the 2026-09-25 compression: page limit met.** The latest rendered build ends the main text on page 9 near review line 479. Algorithms and tables use local small text per the user's explicit instruction; the official style files are unchanged. Re-check the final PDF after subsequent edits.
- **Recommended item missing: reproducibility statement.** No `Reproducibility Statement` is currently present in the manuscript. Add it before the references and link it to the existing code, data, provenance, seeds, budgets, and reproduction commands.
- **Template check satisfied, subject to a final re-check.** The repository audit records a byte-for-byte match between the four tracked style files and the ICLR 2027 archive. Re-verify the archive hash and compile with the official files immediately before submission.
- **Anonymous review mode is present but not fully cleared.** The source uses `Anonymous Authors` and final-only acknowledgments, but audit the final PDF, supplementary bundle, code archive, URLs, comments, and metadata for author or institutional identifiers.
- **OpenReview-only items are unverified in this checkout.** Before upload, record the final author/profile, abstract, conflict, quota, reviewer-registration, Code of Ethics, dual-submission, and AI-form checks in the submission log.
- **Ethics applicability is unresolved.** No ethics statement is currently present. Make an explicit applicability decision from the final data, software, sponsorship, privacy, safety, and research-integrity description; add the statement if any listed issue applies.
