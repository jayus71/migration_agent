# LaDiM / migration_agent

Paper sources and experiment evidence for training-code migration across
frameworks and programming languages.
LaDiM stands for Layered Diagnosis for Multi-Agent Code Migration, the current
paper title. Earlier drafts used MARS and LADDER for the same method.
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
- [Result metrics and component ablations](docs/metrics-and-ablation-revision.md)

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
.venv/bin/python figures/make_migration_motivation.py
.venv/bin/python figures/make_unified_results.py
.venv/bin/python figures/make_cumulative_components.py
.venv/bin/python figures/update_overview_labels.py
.venv/bin/python -m unittest discover -s tests -p 'test_paper_figure*.py'
.venv/bin/python -m unittest discover -s tests -p 'test_unified_paper_results.py'
latexmk -pdf -interaction=nonstopmode -halt-on-error conference_101719.tex
```

LaTeX requires `latexmk`, `texlive-latex-extra`, and `texlive-fonts-recommended`.
The successful build hook also refreshes the word-level comparison in
`output/manuscript-comparison/index.html`, using `detex` from
`texlive-extra-utils`. Its fixed baseline is the September 21 manuscript saved
before the 6 Pro revision, under `data/manuscript_baselines/pre-6pro-20260921/`.
Run `python3 scripts/update_manuscript_diff.py` to refresh it independently.
The page compares prose and expanded LaTeX, highlights added and removed words,
and links to both PDFs. To keep the page open with automatic refresh after builds:

```bash
python3 -m http.server 8766 --bind 127.0.0.1 --directory output/manuscript-comparison
```

Open `http://localhost:8766`. Opening the HTML file directly also supports
comparison, search, and section navigation; reload it after subsequent builds.

Figure export uses NumPy, pandas, Matplotlib, and Inkscape. The manuscript's main
MindSpore comparison reports 50 task identifiers: LaDiM and MatchFixAgent both
accept 50/50, with 57.4% fewer end-to-end tokens for LaDiM. The 50 identifiers
correspond to 29 distinct source-and-contract pairs. Identical conditions were
executed once; token totals count actual calls. The total and per-input token
comparison uses this same collection. The second main-table panel compares
all six methods on 18 Java/DJL-to-Python/PyTorch tasks.

The experimental section is organized into Experimental Setup, Main Experiments,
Analysis Experiments, and Ablation Studies, in `sections/experiments.tex`.
Main tables report source collections, migration outcomes, natural fault repairs,
JAX repairs, cumulative training signals, and cumulative agent components.
The consolidated migration table covers framework and language migration and
both repository tasks.
Analyses explain repair and preservation, per-task cost, retries, detection
latency, and repair in another target framework. The
complete component matrices, repository check details, and additional repair protocols are in
`sections/supplementary_experiments.tex`. Answer-guided historical experiments
remain in the repository archives.

The four figures show complete migration costs in the introduction, the
investigation and repair procedure, total model use with signed per-input
token savings, and training-signal detection beside its analysis. The savings bars show all 29 distinct inputs, sorted
within initially accepted and initially faulty groups.
The measured acceptance at one, two, and four submissions remains in the text.
The overview is a simple placeholder for the author's replacement. Its editable
PowerPoint and SVG share the same labels and layout; `update_overview_labels.py`
exports the SVG as a vector PDF and PNG. The compiled manuscript PDF remains
local and ignored by Git.

See [figure inputs and provenance](data/paper_figures/README.md),
[revision record](docs/paper-revision-20260920.md), and
[evidence and claims](docs/paper-evidence-and-claims-plan-20260920.md).

## Re-running experiments

The September 17-18 code and evidence checkpoint includes the selected
`output/maintext-results-20260918/` tables and their source summaries. The explicit
allowlist in `.gitignore` keeps these small evidence files in Git while raw
archives, runtime snapshots, rendered review pages, and `tmp/` stay local.
See [checkpoint contents and checks](docs/checkpoint-20260918.md).

Experiment implementations live in the separate
[ascend-torch4ms repository](https://gitee.com/feixiao13/ascend-torch4ms).
Consult the [source index](data/experiments/SOURCE_INDEX.md) and each run's
provenance for its exact revision, dependencies, and hardware. The analysis
environment here does not install experiment runtimes or provide accelerator
access. A cloud code-editing session alone is not a replacement for that setup.
