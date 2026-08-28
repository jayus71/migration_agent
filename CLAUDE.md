# migration_agent

LaTeX paper (`conference_101719.tex`) plus the experiment data it cites. Experiment
code and result CSVs live in the nested `ascend-torch4ms/` checkout (separate git
repo, remote `gitee.com/feixiao13/ascend-torch4ms`).

## Python environment

**Use the `lzf` conda env for all data analysis and figure generation.**

```bash
/opt/miniconda3/envs/lzf/bin/python script.py
```

It is the only env on this host with the full analysis stack. The default
`python3` on PATH is conda `base`, which has **no pandas** — scripts will fail
with `ModuleNotFoundError: No module named 'pandas'`.

| Package | `lzf` (use this) | `base` (default PATH) | `rec` |
|---|---|---|---|
| python | 3.12.2 | 3.12.4 | 3.7.16 |
| pandas | 2.3.3 | **missing** | 1.3.5 |
| numpy | 2.4.1 | 1.26.4 | 1.21.6 |
| matplotlib | 3.10.8 | 3.10.8 | 3.5.3 |
| scipy | 1.17.0 | 1.17.0 | 1.7.3 |
| seaborn | 0.13.2 | **missing** | **missing** |
| scikit-learn | 1.8.0 | **missing** | **missing** |
| torch | 2.9.1+cu128 | 2.7.1+cu126 | 1.13.1+cu117 |

`statsmodels` is absent everywhere; use `scipy.stats` for tests and CIs.
`rec` is Python 3.7 with old pins — avoid unless something needs legacy torch.

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
