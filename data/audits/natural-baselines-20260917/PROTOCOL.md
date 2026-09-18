# Natural translation baseline follow-up, 2026-09-17

This follow-up runs only frozen Experiment I tasks I-08 and I-09 with SWE-agent
and MatchFixAgent. It is separate from the original Fixed50 table and does not
change its results. No fault is injected, no translation is regenerated, and no
LaDiM repair is rerun.

The source, initial translation, and private torch4ms implementation come from
commit `8c5c635b0c5c718fab052b885966be8980eea6ad` and its archived
`runs_real_core_v3` artifacts. Each condition starts with identical inputs.
The remote working branch is `codex/natural-baselines-20260917` at
`/media/main/whj/projects/torch4ms/ascend-torch4ms-natural-baselines-20260917`.

Both methods receive the full model and training source, translated candidate,
private adapter implementation, and an ordinary one-step execution test that
outputs a loss. They may create and run their own tests, inspect all workspace
code, and change `candidate.py` and `torch4ms/**/*.py`. The original source,
ordinary test, and task configuration are immutable. They are told to preserve
training behavior and the target framework. No gradient failure, faulty operator,
layer localization, or paired diagnostic is supplied.

Paired verification remains outside the agent workspace. It uses the original
seed, input, synchronization, and thresholds (loss 0.02, gradient norm 0.05,
relative parameter update 0.03). Its result does not trigger another repair.
Actual target backend execution is independently checked with the new observer;
native-PyTorch fallback is a failed migration even if the numeric checks pass.

The model is deepseek-v4-flash at temperature 0.1. Up to four checkpoints are
available. SWE-agent 1.1.0 retains the existing 12-call checkpoint configuration.
An `exit_cost` stop can continue with its own recorded observations; a normal
submission cannot be resumed merely because the hidden test failed. The library
may report 13 API calls when the extra call triggers the 12-call limit. The
original exit string is retained (including `submitted (exit_cost)`).

The MatchFix condition is **MatchFixAgent + DeepSeek tool execution adapter**.
It preserves the upstream six semantic analysis roles, role prompts, parser,
test/repair role, and verdict. Its coding role receives a shell function tool,
with at most 12 model calls per checkpoint. This restores actual test execution
that the historical wrapper replaced with an ordinary chat completion. It is
not the identical historical wrapper or upstream Codex/Claude Code backend.
Only successfully parsed structured repair code is eligible for application.
Raw responses, parsed responses, tool edits, structured application, and actual
test subprocess outputs remain separate. An asserted execution result in an LLM
JSON field is not treated as an observed test run.

The first MatchFix launch lacked its conda bin directory on PATH, so Graphviz
could not find `dot`. These infrastructure-failed startup records are preserved
under `r_matchfix_infrastructure_error_missing_dot_path`; they do not establish
detection or repair failures. The fixed launch restores the same PATH behavior as
the original wrapper and restarts from the frozen candidate.

SWE's local deployment uses shared `/tmp` files, so its two conditions serialize
through a lock. MatchFix conditions can run concurrently. All raw trajectories,
ordinary outputs, frozen hashes, patches, hidden evaluations, backend evidence,
token usage, and wall times are retained in each condition's evidence directory.
The final report derives detection from actual analysis and test evidence,
separately from repair, parsing, scope adherence, budget termination, and numeric
or backend acceptance. A process return code of zero is not a success verdict.

Continuation supplies only the previous checkpoint's trailing 24,000 characters
of observations. Long file reads displaced some earlier localization findings,
so continuation repair results are exploratory and do not support a repair
ranking. The first checkpoint's independent detection evidence is complete.

These are local shell tools with workspace instructions, not an OS sandbox.
Agents also wrote temporary test scripts under `/tmp`; the recorded names did
not collide across conditions. The hidden evaluator and its outputs were not
read in the recorded trajectories.
