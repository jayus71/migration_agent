# LaDiM / migration_agent

Paper sources and experiment evidence for cross-framework training-code repair.
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
.venv/bin/python scripts/build_maintext_results_bundle.py --recovery output/maintext-ablations-20260918/recovery_final.json
.venv/bin/python figures/make_repair_comparison.py
.venv/bin/python figures/make_slim_v4_overview.py
.venv/bin/python figures/update_overview_labels.py
.venv/bin/python -m unittest discover -s tests
latexmk -pdf -interaction=nonstopmode -halt-on-error conference_101719.tex
```

LaTeX requires `latexmk`, `texlive-latex-extra`, and `texlive-fonts-recommended`
(Debian/Ubuntu package names). The overview exporter also requires Inkscape.
Figure scripts require NumPy,
pandas, and Matplotlib and export vector PDFs plus 300-dpi PNGs. The manuscript
uses the autonomous slim-v4 results: 45/50 fault-specific acceptance on Fixed50
and four repairs among five faulty Natural10 translations. Five initially healthy
translations remain accepted. The component, 16-instance training-signal, JAX,
and diagnostic studies retain their respective protocols and scoring definitions.
See [figure inputs and provenance](data/paper_figures/README.md) for source CSVs,
checksums, scoring definitions, and links to the archived diagnostic data.

The abstract states cross-framework effectiveness on MindSpore and JAX. The three
manuscript figures show gradient drift, the repair architecture, and cost with
cumulative repair acceptance at the recorded 1-, 2-, and 4-attempt budgets.
The experiment section contains Main Experiments, Analysis Experiments, and
Ablation Studies. Analyses cover task overlap, retry recovery, cost, unresolved
faults, signal detection latency, and generalization across frameworks. The
component reference and the completed JAX and training-signal studies use
original v4; their identity is preserved after selecting slim v4. Historical
guided experiments remain separately labeled in the appendix. Current evidence
and implementation provenance are indexed in
`docs/maintext-results-20260918.md` and `docs/frozen-method-v4-20260918.md`.
Generated figure assets are tracked;
the compiled manuscript `conference_101719.pdf` remains local and is ignored by
Git. `figures/make_slim_v4_overview.py` generates the current diagram as editable
PowerPoint shapes and connectors in `hierarchical_feedback_architecture.pptx`
and as `slim_v4_overview.svg` from one layout. `update_overview_labels.py` exports
the matching vector PDF and PNG through Inkscape. The earlier overview SVG is
preserved as a historical asset.

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
