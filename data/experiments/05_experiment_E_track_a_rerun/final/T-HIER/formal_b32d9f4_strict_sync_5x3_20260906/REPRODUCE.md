# Reproduce Experiment E T-HIER synchronized rerun

Check out run commit `b32d9f4a27ed90646943b671d43f8616b4ad73fe` in an isolated worktree. Use Python 3.9 with the versions recorded in `environment.json`, place the repository root on `PYTHONPATH`, and configure the LLM provider through environment variables without writing credentials to the result directory.

From the repository root run:

```bash
export PYTHONPATH=.
export AUTOFIX_LLM_MODEL=deepseek-v4-flash
python experiments/baselines/track_a/T-HIER/run_t_hier.py \
  --llm \
  --repeats 3 \
  --seeds 642 643 644 \
  --max-repair-rounds 4 \
  --timeout-sec 300 \
  --output-dir <OUTPUT_DIR>
```

The output is valid only if it contains exactly 5 tasks × 3 seeds, all final verifier JSON files are present, and compile, execution, training, and strict status are reported separately. The unchanged strict thresholds are loss ≤ 0.02, gradient norm difference ≤ 0.05, and parameter-update relative L2 ≤ 0.03.

The Markdown row-alignment display fix is in commit `18bbf43a70611bf82f930590a7172d0e19b9523e`. It can regenerate `summary.md` from the immutable `summary.json`; it does not alter experimental measurements.
