# Formal Experiment A result

This directory is the accepted 6 x 50 Table I paired-threshold revalidation.
`paired_revalidation_summary.json` is the machine-readable entry point.

- 300/300 method-instances have formal Torch4MS bridge/core conclusions.
- 210 normal executions contain loss, gradient-norm and parameter-update metrics.
- 90 repaired candidates genuinely failed execution and contain failure reasons.
- 188/300 pass the unchanged Section 6.6 `_strict_pass()` contract.
- 66/300 decisions differ from the old `strict_success` value.

See `provenance.json` for exact source SHAs, commands, runtime versions and
thresholds. No LLM was used in this experiment.
