# Experiment D 50-step seed-101 diagnostic

This is an explicitly labelled exploratory diagnostic on the current D-R2 configuration. It does not bypass the failed 10-step gate and is not counted as the formal six-condition real-scale result.

Configuration: real CIFAR-10, ResNet18 and MobileNetV2, seed 101, PyNative, 50 training steps, five validation batches, batch size 64, SGD learning rate 0.001.

| Model | Execution / training valid | Minibatch residual max abs / p2p | Fixed-probe residual max abs / p2p | Validation loss abs diff | Parameter-update norm rel diff | First minibatch / probe exceedance |
|---|---|---:|---:|---:|---:|---|
| ResNet18 | yes / yes | 0.172889 / 0.329296 | 0.124093 / 0.196730 | 0.019814 | 0.011713 | step 6 / step 14 |
| MobileNetV2 | yes / yes | 0.092366 / 0.157575 | 8.352048 / 8.354403 | 0.016758 | 0.031519 | step 4 / step 39 |

Both pairs had identical initial parameters, non-empty gradients, non-zero updates, and identical updated-parameter sets. They are valid training executions but fail the current drift gate.

For MobileNetV2, the step-50 Torch4MS-dispatched fixed-probe loss was 10.7042, while native validation on the same candidate state after leaving the dispatch environment was 2.3177. Training minibatch loss was also finite and near 2.29. This isolates the largest observed discrepancy to the dispatched eval path rather than demonstrating a general weight explosion. BatchNorm inference state conversion and wrapper refresh are the next diagnostic targets.

The cached dataset is the complete CIFAR-10 source split (50,000 train / 10,000 test), but this protocol is a 50-batch spot-check: 3,200 shuffled training examples and 320 validation examples per condition. It is not a full epoch.

Raw per-model outputs, parameter audits, buffer audits, step metrics, and logs are preserved in the sibling `resnet18/`, `mobilenet_v2/`, and `logs/` directories.
