# Experiment Tracker

| Run ID | Track | Baseline | 任务 | 次数/预算 | Priority | Status | Owner/Notes |
|---|---|---|---|---|---|---|---|
| `M001` | Migration | Direct LLM | 5 models | 3 outputs/task | MUST | TODO | Runner B |
| `M002` | Migration | CodeTransEngine Direct | 5 models | 3 outputs/task | MUST | TODO | Runner B |
| `M003` | Migration | X2MindSpore | 5 models | 1 output/task | MUST | TODO | Runner A |
| `M004` | Migration | MSAdapter v0.6.0 | 5 models | 1 output, 3 seeds/task | MUST | TODO | Runner A |
| `M005` | Migration | Full Translator + Fixer | 5 models | 3 runs, max 4 repairs | MUST | TODO | Runner C |
| `R001` | Repair pilot | Direct LLM Repair | 12 tasks | max 4 rounds | MUST | TODO | Runner B/D |
| `R002` | Repair pilot | Execution-only | 12 tasks | max 4 rounds | MUST | TODO | Runner C |
| `R003` | Repair pilot | Flat Semantic Feedback | 12 tasks | max 4 rounds | MUST | TODO | Runner C; first implement flat prompt |
| `R004` | Repair pilot | MatchFixAgent | 12 tasks | max 4 checkpoints | MUST | TODO | Runner D |
| `R005` | Repair pilot | SWE-agent v1.1.0 | 12 tasks | max 4 checkpoints | MUST | TODO | Runner D |
| `R006` | Repair pilot | Full Hierarchical | 12 tasks | max 4 rounds | MUST | TODO | Runner C |
| `R101` | Fixed50 | Direct LLM Repair | 50 instances | max 4 rounds | MUST | TODO | Start only after R001 |
| `R102` | Fixed50 | Flat Semantic Feedback | 50 instances | max 4 rounds | MUST | TODO | Start only after R003 |
| `R103` | Fixed50 | MatchFixAgent | 50 instances | max 4 checkpoints | MUST | TODO | Start only after R004 |
| `R104` | Fixed50 | SWE-agent | 50 instances | max 4 checkpoints | MUST | TODO | Start only after R005 |
| `R105` | Fixed50 | Full Hierarchical | 50 instances | max 4 rounds | MUST | TODO | Start only after R006 |
| `X001` | JAX optional | Ivy | MLP/CNN, 6 faults | 1 candidate/task | NICE | TODO | Runner E |
| `X002` | JAX optional | torch2jax | MLP/CNN, 6 faults | 1 candidate/task | NICE | TODO | Runner E |
| `X003` | JAX optional | Full TorchAX | MLP/CNN, 6 faults | max 3 rounds | NICE | TODO | Runner E |
