# Baseline configuration index

All settings below describe the recorded comparisons. Public upstream implementations are external dependencies and are not bundled. The author-owned bridges and all benchmark datasets are omitted. No author repository or data-download location is provided.

| Method | Supplied settings and implementation interface |
| --- | --- |
| Direct LLM | `configs/program_comparison.json`, `configs/translation_prompt.txt`, and `program/translation.py`; one shared initial generation per distinct source-and-contract input |
| SWE-agent | Recorded revision in `configs/baseline_versions.json`; integration in each implementation's `autofix/autonomous/swe_upstream.py`; native shell, editor, parser, and history retained |
| MatchFixAgent | Recorded revision in `configs/baseline_versions.json`; `autofix/autonomous/baselines.py` contains the full native orchestration integration and shared provider/tool transport |
| CodeTransEngine | `configs/codetransengine.yaml`; direct translation configuration, separate from full InterTrans graph search |
| MSAdapter | Revision and import-conversion configuration in `configs/`; upstream adapter implementation is not included |
| InterTrans | `configs/intertrans.json` and `configs/intertrans_adapter.py`; native graph-search settings and request construction, with externally supplied evaluation services |
| Ordinary test repair | `configs/language_comparison.json`; four repair calls, 131072 output tokens per call, temperature 0.1, native visible-test stopping rule |
| Direct repair with shared tools | `configs/jax_comparison.json`; controller method `direct_shared_tools` and the corresponding `AgentConfig` policies |
| Ivy | `configs/jax_comparison.json`; conversion with `ivy.transpile`, native Flax differentiation and Optax SGD |
| torch2jax | `configs/jax_comparison.json`; conversion with `torch2jax.t2j`, native JAX differentiation and Optax SGD |

Program repair uses at most 40 calls, 120000 output tokens, 1800 seconds, and four external submissions. Initial generation is accounted for separately. Repository repair uses at most 80 calls, 480000 output tokens, 3600 seconds, and four submissions, with the shared initial-translation budget recorded separately. Consult the JSON for per-call limits and exact method policies.

The native CTE YAML retains its temperature 0.1 and top-p 0.95. Do not replace those settings with the program controller's nominal temperature. Provider/model names are the requested identifiers in the archived configurations; availability must be established independently when executing a new run. Failed calls and interrupted attempts remain in the cost ledger. Shared initial-generation cost is counted once per applicable end-to-end method/input, and aliases do not multiply actual calls.

The main native-framework runtime records are in `configs/recorded_native_packages.json`. SWE-agent, MatchFixAgent, InterTrans, Ivy, and torch2jax use separate upstream environments; this archive does not present the lightweight review requirements as a lockfile for those environments. Where an exact third-party package version was not available in the selected local evidence, no version has been invented.

To use the program controller's native baseline integrations, set `LADIM_SWE_ROOT`, `LADIM_SWE_PYTHON`, `LADIM_SWE_VENDOR`, `LADIM_MATCHFIX_ROOT`, and `LADIM_MATCHFIX_PYTHON` to independently installed runtimes as appropriate. The SWE vendor directory must contain the pinned unmodified upstream archive expected by the integration. The integrations validate upstream revisions and keep native failures observable.
