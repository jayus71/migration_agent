# September 18 code and evidence checkpoint

This checkpoint preserves the current manuscript, editable figure sources,
analysis and experiment orchestration scripts, frozen task manifests, and
September 17-18 provenance notes on `codex/iclr-2027-template`.

The selected files under `output/` contain the current paper tables, their
source summaries, component and training-signal results, JAX analysis, diagnostic
provenance, and paired-repair and translation summaries. The explicit allowlist
in `.gitignore` records the selection. Existing evidence paths remain unchanged.
The full raw archives and intermediate runtime files remain local; they are not
included in the older September 6 Release. Recomputing analyses that read raw
trajectories still requires those local archives or the recorded remote runs.
`tmp/` is ignored for new files; its two previously tracked audit files remain
versioned.

The two maintained experiment status documents retain their original snapshot
checksums in `data/selected-manifest.json` alongside the updated Git-copy hashes.
No experiment was launched or rerun while preparing this commit.

Validation:

- `python -m unittest discover -s tests`: 94 passed, one module skipped because
  the separate `autofix` experiment runtime is unavailable on `PYTHONPATH`.
- `python -m unittest discover -s scripts -p 'test_*.py'`: 31 passed.
- `python -m pytest -q experiments/unified_migration50_20260918/test_score.py`:
  five passed, including seven subtests.
- `python scripts/verify_per_step_divergence.py`: 27 checks passed.
- `latexmk -pdf -interaction=nonstopmode -halt-on-error conference_101719.tex`:
  the PDF is up to date; all 14 rendered pages were inspected. The main text
  ends on page 8. No overfull-box warning appears in the build log.

The native integration tests in
`experiments/unified_migration50_20260918/test_preparation.py` require the
separate experiment runtime and were not run in the analysis environment.
To run the component tests with that runtime available, add its repository root
to `PYTHONPATH`. These checks use synthetic responses and do not require model
calls. The manuscript is preserved as a working draft in this checkpoint.
