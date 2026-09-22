# Writer checks — 2026-09-22

This revision changes `sections/methods.tex`, `sections/experiments.tex`, `figures/make_cumulative_components.py`, and its generated table. The parent agent reviews the combined manuscript and owns PDF compilation and visual checks after its figure, bibliography, and appendix changes.

- All three algorithm interfaces now explicitly receive the LLM `M`. Investigation and repair invoke `Query(M, A, H, b, B)`, the nested calls propagate `M`, and repository translation uses `Translate(M, A_T, T)`. The Preliminary section distinguishes the LLM from role instructions and identifies translation as a call to the same model. Existing nested control flow and budget accounting remain intact.
- Section 4.3 uses bold paragraph labels, including the full `Generalization Across Frameworks` wording. Concrete seed values and repeated seed statements were removed from the experimental main text; the 69 and 145 repository denominators remain explained.
- The merged ablation table has separate panel titles and headers for 16 faulty candidates and one time series repository. The caption distinguishes investigation-and-repair costs from totals including the shared initial translation.
- The time series panel contains four rows: 69/69 in every condition; calls 26, 18, 26, 22; total tokens 6.128, 3.896, 6.047, 1.937 million. The prose correctly distinguishes the fewest calls from the lowest token cost.
- `make_cumulative_components.py` parses successfully and regenerated the table. Its assertions checked all eight completed runs, both fixed denominators, and token reconciliation before presenting only the four time series rows.
- The complete eight-run evidence remains unchanged. SHA-256 of `output/cumulative-component-ablation-20260922/summary.json`: `3e7f0b2f2c36fd431694888e7e02d372932dc40dd92dfd6785b6e783ba87cf43`.
- Direct source checks passed for model-call signatures, nested model propagation, paragraph heading structure, concrete-seed removal, one reference to each merged panel asset, absence of recommendation component results, and the four generated time series rows.
- Figure 4's caption identifies LaDiM detection at step 1 and loss-based detection on the mean loss-difference curves at steps 31 and 18, retaining the individual-run crossing counts. These values describe the measured curves.

No new experiments were run. No method-overview assets, bibliography, appendix, or parent-owned figure files were changed by this subagent. No page-count compression was performed.
