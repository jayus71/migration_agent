# Experiment D: real learning dynamics

This commit-scoped directory preserves the historical 4,800-row dataset and contains only new runs.
Every training condition distinguishes process execution from scientifically valid training. Backward
warnings, missing gradients, zero parameter updates, non-finite values, or incomplete telemetry fail closed.

The original requirement combined reference loss displacement above 0.05 with candidate absolute loss
peak-to-peak below 0.005. Those conditions conflict for a clean candidate that follows the reference.
The implemented gate uses deterministic fixed-probe reference loss displacement above 0.05 and paired
residual (`loss_torch4ms - loss_torch`) peak-to-peak below 0.005, as required by the optimization plan.

Version note: Experiment D core fixes are isolated by commit and worktree. Do not silently mix them with
other experiments frozen on older commits. torchvision real-scale models dispatch
`aten.native_batch_norm.default`; its output tuple and unbiased running-variance update must be tested,
and the 1-step real-scale gate must pass before 10-step or formal conditions are launched.
MindSpore gradient recomputation replays model forward; those internal replays must restore live module
buffers so a Torch4MS optimizer step advances BatchNorm running statistics exactly once.
Stochastic operators must use a paired PyTorch RNG mask and replay it during backward; independently
seeding PyTorch and MindSpore does not make per-step dropout loss comparable.
D-R1 (learning rate 0.01) remains a preserved failed 10-step stability result. D-R2 uses learning rate
0.001 uniformly for both real models; it is the only pre-registered real-scale stability extension.


## Current result status

- Commit: `2fd40609b85314400d951a7d6897bfb66a5af558`
- Minimal regression: `complete`
- Parameter sweep: `complete`
- Controlled experiment: `complete`;
  `24/24` training-valid conditions and
  `9600` recorded step rows.
- Real-scale 1-step: `complete`.
- Real-scale 10-step: `failed_gate`; maxima
  `{"paired_fixed_probe_residual_max_abs": 0.01698899269104004, "paired_loss_residual_max_abs": 0.08973050117492676, "parameter_update_norm_rel_diff": 0.01906902967441245, "val_loss_abs_diff": 0.007310914993285955}`.
- Real-scale formal 6 conditions: `blocked_by_ten_step_gate`.
- Paper positive claim supported: `false`.

The controlled claim is positive, but the overall Experiment D paper claim remains negative while the
real-scale 10-step loss gate fails. Execution success and training validity are not relabeled as threshold
success. The source commits for reused immutable outputs are recorded in `manifest.json`.

## Exploratory 50-step diagnostic

At the user's request, the current D-R2 configuration was also run for 50 steps on seed 101 for both
real-scale models. Both pairs were execution-successful and training-valid, but both exceeded the drift
gate. ResNet18 first exceeded the minibatch/probe loss limit at steps 6/14. MobileNetV2 first exceeded it
at steps 4/39; its dispatched fixed-probe loss reached 10.7042 while native validation on the same final
candidate state was 2.3177, pointing to a dispatched eval/BatchNorm-path defect rather than a general
weight explosion. See `real_scale/fifty_steps_seed101_diagnostic/summary.md` for the full diagnostic table.

This exploratory result is not counted as the formal `2 models × 3 seeds × 50 steps` stage. That stage
remains blocked by the failed 10-step gate.
