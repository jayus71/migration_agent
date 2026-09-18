# JAX integration review

This is a parent review of the in-progress runner, before its API experiments.
It records checks to resolve during preparation; it is not a result report.

## Protocol and comparator identity

The frozen v4 reference is
`/media/main/whj/projects/torch4ms/ascend-torch4ms-autonomous-verifier-20260917/experiments/autonomous_verifier_20260917/progress_v4`.
The current four-attempt `direct_shared_tools` control is distinct from the
historical one-call `c_direct` implementation. Both may be evaluated, but their
names, budgets, prompts and provenance must remain distinct. Reusing the shared
control does not rerun the historical Direct algorithm. Historical converter
calls and healthy gates retain their original behavior.

## Initial state

The historical backend at `3352f71` returns `initial_vector` for reference and
target. Its `PairedTorchaxVerifier` does not check equality of those vectors.
The draft new runner likewise computes loss, gradient-norm and named-update
differences without inspecting initial-state agreement.

The raw vectors should be retained and their length, finiteness and differences
reported for every executable evaluation. Any new acceptance rule must be
declared before API execution, applied equally to all methods and reported
separately from the historical three-threshold criterion. Do not silently add
a criterion after observing accepted patches. A nonmatching initial state also
prevents describing a trajectory as a synchronized comparison.

The parent added `scripts/audit_maintext_jax_initial_states.py` as a separate
offline audit, with four numerical/availability tests passing. On the
`formal_v5` preflight snapshot, all six accepted TorchAX healthy checks have
exactly matching initial vectors. One accepted Ivy healthy check has no
recorded initial vector; it is marked unavailable. The thirteen-measurement
snapshot is stored in
`output/autonomous-verifier-20260917/jax_initial_states_preflight_v5.json`.
This snapshot includes intermediate setup checks and is not the final repair
audit. The existing acceptance rule was not changed.

## Runtime and missing values

The draft checks actual `is_jax_array` evidence from the fixed runtime, finite
measurements, update-name sets and per-parameter lengths. Retain these checks.
The backend uses `jax_value_and_grad` and Optax for the actual training step;
candidate changes remain confined to its declared public program.

Unexecuted or malformed measurements stay unavailable. Converter clean-gate
failures need their actual exception and environment status, as recorded by
the original implementation. Preserve their native failure, and distinguish
that failure from a defect introduced by the new sandbox or worker launcher.

## Resource allocation

After its offline tests and frozen-input preflight pass, this JAX study may use
two DeepSeek API workers. This allocation is independent of the four workers
assigned to the new component ablations. Existing repair and diagnosis
dispatchers remain unchanged.

The parent started the twelve-condition `formal_v5` repair grid at approximately
2026-09-17 18:30 UTC through `launch_maintext_jax_parent_review.sh` and the
separately saved `dispatch_parent_review.py`. The dispatcher also recognizes
HTTP 401/402/403 in the frozen client's error text; one regression test passed.
Five JAX integration tests passed before launch. This changes dispatch handling
only, not the frozen agent, acceptance, inputs or baseline algorithms. Its
`worker_logs` directory is created exclusively before launch to reject a second
dispatcher for the same conditions.
