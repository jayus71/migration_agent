# Export and verification notes

This source supplement was assembled from the measured program implementation, its frozen baseline integration snapshots, and the final repository implementation. The program and repository variants are kept in separate directories. Source algorithms and recorded budgets are preserved within the export scope.

Packaging changes are limited to:

1. Replacing identifying library/workspace names with neutral placeholders and replacing private runtime locations with environment variables or neutral paths.
2. Removing author-owned bridge execution branches from the native measurement worker. Native PyTorch, native MindSpore, and the external MSAdapter measurement paths remain.
3. Excluding benchmark construction, embedded source-task collections, fault injection, healthy targets, saved candidates, reference traces, model responses, and Git history.
4. Exporting generic evaluator lifecycle helpers while disabling the inherited bridge-specific default evaluator. The native runner injects the provided native evaluator explicitly.
5. Exporting the measured repository scheduling function with external input roots and evaluator/adapter factories in place of private launch locations. External frozen-input validation is the caller's responsibility; shared translation, source and task checks remain in the schedule.
6. Adding documentation, a command-line wrapper, file integrity verification, and an offline check entry point. One test's expected file ordering is adjusted for the neutral workspace directory name.

The `configs/intertrans_adapter.py` file is supplied as a configuration/request-construction reference. It shows the actual graph-search parameters and method transport, but depends on a dataset-specific external evaluation service that is not included. It is not an executable standalone baseline installation.

Offline verification checks Python syntax, file hashes, agent budget accounting, evidence/history handling, edit guards, numerical acceptance, and repository context. It does not install or execute third-party baselines, call an LLM, access accelerators, or rerun paper experiments. Synthetic unit-test fixtures are small temporary programs; they are not benchmark datasets.

All ZIP members use a common normalized timestamp and regular-file permissions. No original filesystem ownership, ZIP comment, source-control metadata, manuscript metadata, or private source map is included. File hashes in `MANIFEST.sha256` identify the anonymous distributed bytes.
