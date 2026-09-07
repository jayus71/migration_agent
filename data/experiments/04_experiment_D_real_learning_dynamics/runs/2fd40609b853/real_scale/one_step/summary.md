# Experiment D real-scale spot-check

This is a fail-closed execution and drift spot-check on full-resolution real CIFAR-10 batches. A failed torch4ms run remains a measured coverage failure; it is not replaced with fake data.

| Model | Seed | PyTorch | torch4ms | Training valid | Train-loss abs. diff | Val-loss abs. diff | PyTorch time | torch4ms time |
|---|---:|:---:|:---:|:---:|---:|---:|---:|---:|
| resnet18 | 101 | complete | complete | True | 9.5367431640625e-07 | 3.4523010254083886e-05 | 1.422s | 5.963s |
| mobilenet_v2 | 101 | complete | complete | True | 1.6689300537109375e-06 | 2.7179718018466303e-06 | 0.946s | 7.510s |

Paired executions: 2/2; training-valid pairs: 2/2.

This spot-check reports observed aggregate drift and wall time; it does not relabel these aggregate metrics as the per-step strict verifier used by the controlled fault pool.
