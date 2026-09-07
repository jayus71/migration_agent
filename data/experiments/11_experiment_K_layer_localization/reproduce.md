# Reproduction

Configure the standard real-LLM environment without embedding any machine-specific home directory, then run from the repository root:

```bash
export AUTOFIX_LLM_ENABLED=1
export AUTOFIX_FIXER_LLM_ENABLED=1
export AUTOFIX_LLM_MODEL=deepseek-v4-flash

PYTHONPATH=. python experiments/paper_section_65_66/run_section65_real_fault_repair.py \
  --instance-suite fixed50 --real-llm --blind --repair-attempts 4 \
  --timeout-sec 300 --baseline r_hier \
  --reports-dir experiments/experiment_request_20260820/11_experiment_K_layer_localization/reports \
  --output-dir experiments/experiment_request_20260820/11_experiment_K_layer_localization/results
```

The API key and base URL must be supplied through `AUTOFIX_LLM_API_KEY` and `AUTOFIX_LLM_BASE_URL`; they are not stored in result artifacts.
