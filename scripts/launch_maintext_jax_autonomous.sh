#!/usr/bin/env bash
set -euo pipefail
source /media/main/whj/.autofix_llm_env
exec /media/main/whj/miniconda3/envs/torchax311/bin/python -u \
  /media/main/whj/projects/torch4ms/experiments/maintext_jax_autonomous_20260918/dispatch.py \
  --run /media/main/whj/projects/torch4ms/experiments/maintext_jax_autonomous_20260918/formal_v5 \
  --workers "${1:-2}"
