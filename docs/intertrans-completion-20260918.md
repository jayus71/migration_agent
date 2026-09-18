# N18 InterTrans completion, 2026-09-18

Status: all 18 conditions are complete and have valid outcomes. One is accepted.
The authorized completion uses the existing DeepSeek endpoint and the frozen
18-source N18 pool. No manuscript or autonomous-framework implementation is edited.

## Evidence and remaining work

The historical N18 InterTrans batch contains 18 records marked search_exhausted.
Inspection of its native responses finds FAILED_NO_EXTRACTED target edges, with
no extracted code. All 36 provider usage records are distinct; they total 574,304
tokens, including 294,912 completion tokens. Each response spent all 8,192
completion tokens on reasoning. These are preserved incomplete generation records.
There are zero reusable functional outcomes and 18 conditions to complete under
the already authorized 131,072 output-token limit. Functional failures produced
by a completed current search will be retained without another model attempt.

Historical evidence root:
`/media/main/whj/projects/torch4ms/ascend-torch4ms-n18-348e8cd/artifacts/n18_training/intertrans`.
The newer paused preparation contains no completed InterTrans phase.

## Frozen method

The dedicated checkout is
`/media/main/whj/projects/torch4ms/ascend-torch4ms-intertrans-completion-20260918`,
at `c21dadcf6e5e82665fa163b90c9dccb1ea15c4ef`.
InterTrans upstream is `84d2d4337dc82d848772cf834440ba17497b7683`.
Its graph algorithm has SHA-256
`8fb54f8b43cca90b6ec3ce484db6c6dd33e3705bfc2b7866ad9e0b98b1e5ae42`.
The build copies the pinned source and applies the existing Docker transport
and raw-response/usage logging adapters. Native algorithm and common Go files
are compared byte-for-byte before generation.

The existing adapter retains its prompt template, fenced-code parser, compute
efficient search, expansionIntermediaryNodes 3, earlyStop false, and languages
JavaScript/Python. This executes a direct Java-to-Python path and an indirect
Java-to-JavaScript-to-Python path. Intermediate execution validation remains
disabled, as in the frozen configuration. Final Python candidates undergo actual
two-step training verification using visible seed 101; accepted selected outputs
are additionally checked at held-out seeds 202 and 303.

The input is the complete hash-verified upstream source, including all notebook
cells when applicable, plus the common interface and public shape/asset metadata.
No healthy target implementation or expected numerical trace is placed in the
model prompt. Candidates execute without network access or host-home mounts.
The visible verification service holds the reference privately and returns the
existing ordinary test feedback. Acceptance covers two post-preprocessing
training steps; it does not certify the whole program.

## Preparation

The current checkout's isolation smoke passed healthy, forward, backward, and
optimizer controls. Native InterTrans fake-transport graph and verification
smoke passed. An initial smoke invocation used a nonexistent Python 3.11 client
site path; it stopped before inference. The corrected Python 3.9 environment is
recorded in the next smoke directory. All directories are retained.

Independent 108-case measurement calibration passed in
`/media/main/whj/projects/torch4ms/intertrans-completion-20260918/calibration`.
All 54 healthy, 18 forward, 18 backward, and 18 optimizer controls passed.
The runner checks this calibration, isolation, native graph smoke, clean checkout,
and frozen source/algorithm hashes before any real model call.

The N18-only launcher is `scripts/run_intertrans_completion_20260918.py` in the
paper repository and `run_completion.py` under the remote output root. It calls
the existing native adapter directly after concrete InterTrans-only gates; the
six-method batch finalizer would additionally require unrelated SWE and MatchFix
smokes. It does not change baseline prompts, parsing, or search settings.

## Results

The completed run has 15 search-exhausted outcomes, one evaluated outcome,
and two generation/extraction failures. All 18 remain in the denominator;
the acceptance result is 1/18. The 53 current provider calls used 1,711,730
tokens. Including the historical output-budget failures gives 89 calls and
2,286,034 tokens. No model calls were added during the final environment replay.

Raw provider responses and usage, native search responses,
visible tests, final evaluations, and status records remain under
`/media/main/whj/projects/torch4ms/intertrans-completion-20260918`.

The first two tasks exposed a missing torchvision dependency in the existing
runtime. A derivative image adds torchvision 0.22.1+cpu and Pillow 11.2.1 while
retaining torch 2.7.1+cpu. Saved native inference outputs are replayed through
the upstream verification RPC with the same parser and tests, without model
calls or candidate edits. The first three affected target edges then fail on
candidate interface usage or target label types. Their original errors and
replays are both retained. Search generation remains unchanged; completed
functional failures are not regenerated.

The final unresolved item, `d2l_mlp_scratch`, required matplotlib. The separate
`intertrans-n/python:n18-matplotlib-20260918` image adds matplotlib 3.10.6.
Replaying its two existing Python outputs produced candidate execution failures,
with no remaining dependency failure and no additional model requests. The
upstream parser, search, and generated programs were preserved.

The final local summary is
`output/intertrans-completion-final-20260918/intertrans-completion-20260918/paper_results.json`.
The earlier local directory is a historical progress snapshot.
The complete archive is `output/intertrans-completion-20260918-evidence.tar.gz`,
3,810,610 bytes, containing 1,215 evidence files. Its SHA-256 is
`5f9c2e227c1a6bb72000043ba3e49eca2be094def335b686d0b56ea29bcd1489`.
All member hashes were checked, and credentials were excluded. The manifest
SHA-256 is `7533b7396a0b7c789dd31803ad7746a14eedf8e3cd6940d031a2f9f931bf121c`.
