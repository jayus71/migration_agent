# Reproduce Experiment C

Run from the repository root in the `mstorch` environment. Set `DATA_DIR` to a
local directory containing the checksum-validated CIFAR-10 and AG News files;
the command intentionally contains no machine-specific home path.

```bash
export PYTHONPATH=.
export DATA_DIR=/path/to/section66/data

python experiments/paper_section_65_66/run_section66_realdata_training_consistency.py \
  --per-step-divergence \
  --models cnn,mlp,transformer,tiny_causal_lm \
  --steps 50 \
  --seeds 3 \
  --couplings teacher-forced,free-running \
  --faults none,grad_wrong,param_wrong \
  --grad-wrong-scale 1.5 \
  --data-dir "$DATA_DIR" \
  --output-dir experiments/experiment_request_20260820/03_experiment_C_gradient_and_parameter_faults/results_per_step
```

Expected commit ancestry: `0d71f58` or later on
`codex/llm-fixer-capability`.
