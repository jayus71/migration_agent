# Reproduce Experiment D

From the repository root, with the `mstorch` environment active and datasets already cached:

```bash
python experiments/experiment_request_20260820/04_experiment_D_real_learning_dynamics/run_experiment_d.py \
  --phase all --resume --data-dir <SECTION66_DATA_DIR> --real-data-dir <CIFAR10_DATA_DIR>
```

Run one stage only by replacing `all` with `minimal`, `sweep`, `controlled`, or `real`.
The default output is `experiments/experiment_request_20260820/04_experiment_D_real_learning_dynamics/runs/<commit>`.
No personal absolute path is required.

To reassemble already validated immutable stages without repeating training:

```bash
python experiments/experiment_request_20260820/04_experiment_D_real_learning_dynamics/run_experiment_d.py   --phase all --resume --data-dir <SECTION66_DATA_DIR> --real-data-dir <CIFAR10_DATA_DIR>   --reuse-sweep-from experiments/experiment_request_20260820/04_experiment_D_real_learning_dynamics/runs/<SWEEP_RUN>   --reuse-controlled-from experiments/experiment_request_20260820/04_experiment_D_real_learning_dynamics/runs/<CONTROLLED_RUN>   --reuse-real-from experiments/experiment_request_20260820/04_experiment_D_real_learning_dynamics/runs/<REAL_RUN>
```

`manifest.json` records the exact executed command and the source commit for every reused stage.
