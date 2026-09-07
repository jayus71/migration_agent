# Section 6.6 Real-Data Training Consistency

This report compares PyTorch and torch4ms training trajectories on CIFAR-10 and AG News real-data batches.

Candidate provenance: `oracle_candidate`.

## Data Checks

- `cifar10_archive`: ok=True, path=`experiments/paper_section_65_66/data/cifar10/cifar-10-python.tar.gz`
- `cifar10_batches`: ok=True, path=`experiments/paper_section_65_66/data/cifar10/cifar-10-batches-py/data_batch_1`
- `ag_news_train.csv`: ok=True, path=`experiments/paper_section_65_66/data/ag_news_csv/train.csv`
- `ag_news_test.csv`: ok=True, path=`experiments/paper_section_65_66/data/ag_news_csv/test.csv`

| Model | Runs | Strict pass rate | Mean loss diff | Max loss diff | Mean grad diff | Mean param update rel L2 |
|---|---:|---:|---:|---:|---:|---:|
| `cnn` | 3 | 1.000 | 4.569689432779948e-07 | 2.9802322387695312e-06 | 1.509984334309896e-08 | 1.146376709859271e-06 |
| `nlp` | 3 | 1.000 | 6.167093912760416e-07 | 1.6689300537109375e-06 | 1.4413769046465556e-08 | 3.825308604689108e-06 |
| `tiny_causal_lm` | 3 | 1.000 | 1.7452239990234376e-06 | 3.814697265625e-06 | 3.83456548055013e-08 | 1.126530534752786e-06 |
| `transformer` | 3 | 1.000 | 5.642573038736979e-08 | 2.384185791015625e-07 | 1.7484029134114583e-08 | 7.912662454727441e-07 |

## Figures

- `experiments/paper_section_65_66/results_realdata_66/figures/loss_trend_steps50.png`
- `experiments/paper_section_65_66/results_realdata_66/figures/grad_norm_diff_steps50.png`
- `experiments/paper_section_65_66/results_realdata_66/figures/param_update_diff_steps50.png`
