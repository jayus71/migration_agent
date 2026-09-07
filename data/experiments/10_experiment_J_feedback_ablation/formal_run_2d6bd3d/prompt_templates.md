# Experiment J prompt contracts

All arms use the same Fixed50 pool, blind candidate input, model, temperature, and four-attempt budget.
The arms distinguish detection coverage, feedback granularity, and evidence order. In particular, `r_exec` checks only execution while `r_binary` checks all E/N/G signals before compressing them into one strict bit.

| Condition | Exact meaning | Hierarchical route | Presentation order |
|---|---|---:|---|
| `r_exec` | Execution-only feedback: the Fixer sees runtime success/failure, exception type, and traceback. Numerical and gradient/update defects that execute normally do not trigger repair. | 0 | execution -> numerical -> gradient_update |
| `r_binary` | Strict aggregate binary feedback: the verifier checks execution, numerical, and gradient/update signals, then exposes only one overall pass/fail bit to the Fixer. It exposes no failing stage, metric, step, tensor, parameter, or repair route. | 0 | execution -> numerical -> gradient_update |
| `r_stage` | Stage-label feedback: the verifier checks all three layers and exposes only the first failing stage label, without numerical or tensor/parameter details. | 1 | execution -> numerical -> gradient_update |
| `r_flat` | Flat full feedback: execution, numerical, and gradient/update evidence is exposed as an unordered metric collection, without first-failure localization or routing. | 0 | execution -> numerical -> gradient_update |
| `r_hier` | Hierarchical LADDER feedback: full evidence is ordered execution -> numerical -> gradient/update with first-failure localization and repair routing. | 1 | execution -> numerical -> gradient_update |
| `r_reverse` | Reverse hierarchical feedback: the same full evidence and routing as r_hier is presented gradient/update -> numerical -> execution. | 1 | gradient_update -> numerical -> execution |
