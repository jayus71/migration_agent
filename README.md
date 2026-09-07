# LADDER / migration_agent

Paper sources and experiment evidence for cross-framework training-code repair.
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

## Figures and PDF

```bash
.venv/bin/python figures/make_verdict_collapse.py
.venv/bin/python figures/make_cost_quality.py
latexmk -pdf -interaction=nonstopmode -halt-on-error conference_101719.tex
```

LaTeX requires `latexmk`, `texlive-latex-extra`, `texlive-fonts-recommended`, and
`texlive-publishers` (Debian/Ubuntu package names). Figure scripts use the original
paper inputs under `data/paper_section_65_66/`. The newer A-K archive is separate:
the upload preserves results and does not reconcile the paper's claims with them.

## Re-running experiments

Experiment implementations live in the separate
[ascend-torch4ms repository](https://gitee.com/feixiao13/ascend-torch4ms).
Consult the [source index](data/experiments/SOURCE_INDEX.md) and each run's
provenance for its exact revision, dependencies, and hardware. The analysis
environment here does not install experiment runtimes or provide accelerator
access. A cloud code-editing session alone is not a replacement for that setup.
