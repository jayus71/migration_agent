# MARS / migration_agent

Paper sources and experiment evidence for cross-framework training-code repair.
MARS stands for Multi-Agent Repair System, the method phrase in the current
paper title. Earlier drafts used LADDER for the same method.
This checkout supports cloud-based manuscript editing and CPU result analysis.
The repository and its experiment-data Release are public.

## Cloud setup

```bash
git clone https://github.com/jayus71/migration_agent.git
cd migration_agent
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-analysis.txt
.venv/bin/python scripts/verify_per_step_divergence.py
```

Python 3.11 or newer is required. In Claude Code's cloud environment, connect
this GitHub repository, use `main`, and run the installation commands above
from the checkout root. `CLAUDE.md` contains the project-specific instructions.
Dependency installation needs access to PyPI. No API key is required to download
the public data asset; allow access to `github.com` and GitHub's release-asset
download hosts if the cloud environment restricts networking.

## Evidence

- [A-K experiment status](data/experiments/EXPERIMENT_STATUS_REPORT.md)
- [Current issues and evidence limits](data/experiments/CURRENT_ISSUES.md)
- [Data layout and provenance](data/README.md)
- [Experiment requirements](EXPERIMENT_REQUEST_20260820.md)
- [Manuscript sources](conference_101719.tex)

Selected summaries and analysis tables are included in Git. To inspect all raw
logs, trajectories, and generated candidates, download the complete snapshot:

```bash
python3 scripts/fetch_experiment_data.py
python3 scripts/fetch_experiment_data.py --verify-only
```

The downloader verifies the archive and every extracted file against the
committed SHA-256 manifest. It writes to `.experiment-data/20260906-v1/` and
refuses to replace a modified snapshot. An existing verified snapshot is reused.
Reserve at least 750 MiB of free space for downloading and extracting the snapshot.

If the browser has downloaded the asset already:

```bash
python3 scripts/fetch_experiment_data.py --archive /path/to/experiment-data-20260906-v1.tar.gz
```

## Writing style reference

The [Zhekai Du writing DNA](literature/zhekai-du/Academic-Writing-DNA.md) describes
writing patterns in six English first-author papers, including LoCA and its TPAMI
extension. It covers paragraph structure, language, argumentation, and figures.
Read it before drafting or editing with this style, and base all technical claims
and results on this project's evidence.

[Analysis notes](literature/zhekai-du/STYLE-EVIDENCE.md) document the paper sources,
measurement methods, and limitations. The
[independent writing check](literature/zhekai-du/TRANSFER-CHECK.md) contains a
hypothetical example used to test the DNA; it is separate from the manuscript and
experiment results.

The DNA, supporting notes, bibliographic records, measurements, and corpus-specific
scripts are included in Git and available in cloud checkouts. Source PDFs,
extracted text, page images, and raw search responses stay local and are ignored by
Git. Reading the DNA requires no PDF downloads. Repeating the extraction requires
the local papers, `pypdf`, and Poppler; see the analysis notes for the procedure.

## Figures and PDF

The manuscript uses the official ICLR 2027 template in anonymous review mode.
The initial submission has a nine-page main-text limit; references and the AI
use statement are excluded. The AI use statement is intentionally blank for
the authors to complete. See [ICLR template notes](docs/iclr-2027-template.md)
for the template source, build instructions, and current page count.

```bash
.venv/bin/python figures/make_gradient_drift.py
.venv/bin/python figures/make_repair_comparison.py
.venv/bin/python figures/make_jax_table.py
.venv/bin/python figures/update_overview_labels.py
.venv/bin/python -m unittest discover -s tests
latexmk -pdf -interaction=nonstopmode -halt-on-error conference_101719.tex
```

LaTeX requires `latexmk`, `texlive-latex-extra`, and `texlive-fonts-recommended`
(Debian/Ubuntu package names). Figure scripts require NumPy,
pandas, and Matplotlib and export vector PDFs plus 300-dpi PNGs. The manuscript
uses the original 50-instance fault-check acceptance counts, including 50/50 for
MARS; these counts do not assert all-step paired-threshold compliance. The
12-task signal ablation and the diagnostic studies use separate measurements.
See [figure inputs and provenance](data/paper_figures/README.md) for source CSVs,
checksums, scoring definitions, and links to the archived diagnostic data.

The abstract states cross-framework effectiveness on MindSpore and JAX. The three
manuscript figures show gradient drift, the repair architecture, and cost with
cumulative repair acceptance at the recorded 1-, 2-, and 4-attempt budgets.
The main results table reports the original 50-instance MindSpore repair study.
A separate table reports JAX fault repair from the original Track C records.
The JAX discussion explains the diagnostic interpretation across runtimes.
The complete MindSpore translation comparison is excluded from the manuscript;
the separate translator documentation ablation remains in Table III(b).
Table headings use complete
terms with line breaks where needed.
Fault signatures,
localization, and the separate 12-task signal-composition results are described
in the text. Their plotting scripts and assets remain available in `figures/`
but are not included in the manuscript. Generated figure assets are tracked;
the compiled manuscript `conference_101719.pdf` remains local and is ignored by
Git. The overview retains its existing layout. `update_overview_labels.py`
updates agent roles, diagnostic labels, and target runtimes from the original
PNG in `figures_to_be_redrawed/`, using Pillow and Arial Narrow (or DejaVu Sans
Condensed). The editable PowerPoint and vector overview remain deferred to the
separate diagram revision.

## Re-running experiments

Experiment implementations live in the separate
[ascend-torch4ms repository](https://gitee.com/feixiao13/ascend-torch4ms).
Consult the [source index](data/experiments/SOURCE_INDEX.md) and each run's
provenance for its exact revision, dependencies, and hardware. The analysis
environment here does not install experiment runtimes or provide accelerator
access. A cloud code-editing session alone is not a replacement for that setup.
