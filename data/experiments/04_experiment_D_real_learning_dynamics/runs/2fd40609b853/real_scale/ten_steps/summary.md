# Experiment D real-scale spot-check

This is a fail-closed execution and drift spot-check on full-resolution real CIFAR-10 batches. A failed torch4ms run remains a measured coverage failure; it is not replaced with fake data.

| Model | Seed | PyTorch | torch4ms | Training valid | Train-loss abs. diff | Val-loss abs. diff | PyTorch time | torch4ms time |
|---|---:|:---:|:---:|:---:|---:|---:|---:|---:|
| resnet18 | 101 | complete | complete | True | 0.010141825675964444 | 0.007310914993285955 | 6.900s | 37.663s |
| mobilenet_v2 | 101 | complete | complete | True | 0.010341644287109375 | 9.655952453613281e-05 | 6.031s | 65.532s |

Paired executions: 2/2; training-valid pairs: 2/2.

This spot-check reports observed aggregate drift and wall time; it does not relabel these aggregate metrics as the per-step strict verifier used by the controlled fault pool.
