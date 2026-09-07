# Experiment D real-scale spot-check

This is a fail-closed execution and drift spot-check on full-resolution real CIFAR-10 batches. A failed torch4ms run remains a measured coverage failure; it is not replaced with fake data.

| Model | Seed | PyTorch | torch4ms | Training valid | Train-loss abs. diff | Val-loss abs. diff | PyTorch time | torch4ms time |
|---|---:|:---:|:---:|:---:|---:|---:|---:|---:|
| mobilenet_v2 | 101 | complete | complete | True | 0.01616278648376479 | 0.016757774353027166 | 26.526s | 308.090s |

Paired executions: 1/1; training-valid pairs: 1/1.

This spot-check reports observed aggregate drift and wall time; it does not relabel these aggregate metrics as the per-step strict verifier used by the controlled fault pool.
