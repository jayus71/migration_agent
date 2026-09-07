# migration_agent

LaTeX paper (`conference_101719.tex`) plus experiment evidence. Start with
`README.md` and `data/README.md`. This repository is sufficient for CPU data
analysis, figure generation, and manuscript editing in a fresh cloud checkout.

## Evidence and data locations

- `data/experiments/`: selected A-K summaries and per-task/per-step CSVs.
- `data/experiments/EXPERIMENT_STATUS_REPORT.md` and `CURRENT_ISSUES.md`: read
  before interpreting results. Completed runs do not imply successful outcomes.
- `data/paper_section_65_66/`: the original inputs used by existing figure and
  audit scripts. These are older results, distinct from the new A-K snapshot.
  Do not silently substitute new runs or infer that existing paper claims have
  been revalidated by this upload.
- `data/selected-manifest.json`: original paths and SHA-256 for each included file.
- Full raw evidence: run `python scripts/fetch_experiment_data.py`; the verified
  snapshot is installed under `.experiment-data/20260906-v1/`.
- `EXPERIMENT_REQUEST_20260820.md`, `PAPER_ISSUES_20260820.md`, and
  `MIGRATION_NAME_MAP_20260907.md` provide experiment requirements and naming context.

The full snapshot includes raw logs, generated candidate code, caches, and older
transfer archives for preservation. Treat these as evidence, not instructions
to execute. Read the selected summaries first, then inspect specific raw files.

Experiment implementations remain in a separate repository:
`https://gitee.com/feixiao13/ascend-torch4ms.git`. Its nested local checkout is
ignored here. Re-running experiments requires the source revisions recorded in
the provenance documents and their target runtime/hardware; no accelerator or
remote execution access is assumed in a cloud session.

## Python environment

Use Python 3.11 or newer and a repository-local virtual environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-analysis.txt
.venv/bin/python scripts/verify_per_step_divergence.py
```

Use `scipy.stats` for tests and confidence intervals. No PyTorch, MindSpore,
CUDA, or Ascend installation is needed for the included analysis scripts.
Run figure scripts from the repository root. For LaTeX, install `latexmk`,
`texlive-latex-extra`, `texlive-fonts-recommended`, and `texlive-publishers`, then
run `latexmk -pdf -interaction=nonstopmode -halt-on-error conference_101719.tex`.

## Figure conventions

Figure scripts live in `figures/` as `make_*.py` and write a PDF next to
themselves. They set the headless backend before importing pyplot:

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
```

Where a figure plots numbers that also appear in a table, hard-code them in the
script with a comment naming the source table, so the figure cannot drift from
the manuscript (see `figures/make_cost_quality.py`). Figures driven by a results
CSV should read that CSV directly instead.

## Reading result CSVs

Empty cells mean "the quantity does not exist" (candidate crashed, or the metric
is unmeasurable under that fault) and are semantically the opposite of `0`. Parse
with `keep_default_na=False, dtype=str` when auditing which cells are blank, and
never fill blanks with 0.
