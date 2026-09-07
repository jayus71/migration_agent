# Experiment K: layer-localization accuracy

The formal Fixed50 `R-HIER` rerun completed on commit `0d71f58` with real LLM repair, blind prompts, temperature 0.1, and four attempts per instance.

## Main result

- diagnosis complete: 50/50
- correct layer: 48/50 (96.0%)
- strict repair success: 46/50 (92.0%)
- valid model bindings: 50/50
- LLM calls: 65
- prompt/completion/total tokens: 145,132 / 91,933 / 237,065
- summed per-instance wall time: 2,952.70 s

The confusion-matrix row totals are exactly 20 execution, 14 numerical, and 16 gradient/update instances. Both localization errors are `NU-07` instances, which were predicted as execution rather than numerical. This is interpretable: the injected non-finite numerical fault first manifests as a failed executable/finite-value contract, so the first-failing-stage diagnosis differs from the registry's injected-fault label.

Four repairs did not pass the strict verifier: `EX-06-A`, `EX-07-A`, `EX-08-B`, and `NU-03-B`. Localization accuracy and repair success are therefore distinct outcomes, as intended.

See `results/section65_real_fault_repair_summary.md` for per-instance details and `results/section65_fault_pool_localization_confusion_matrix.csv` for the complete matrix.
