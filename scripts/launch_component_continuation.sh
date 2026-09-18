#!/usr/bin/env bash
set -euo pipefail
source /media/main/whj/.autofix_llm_env
root=/media/main/whj/projects/torch4ms/maintext-ablations-20260918
exec /media/main/whj/miniconda3/envs/mstorch/bin/python \
  "$root/continue_component_dispatch.py" "$root/fixed50_v3" \
  --dispatcher-pid 2619458 --workers 16
