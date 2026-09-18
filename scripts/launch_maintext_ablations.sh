#!/usr/bin/env bash
set -euo pipefail
run_path="$1"
slots="$2"
source /media/main/whj/.autofix_llm_env
cd "$run_path"
nohup /media/main/whj/miniconda3/envs/mstorch/bin/python \
  "$run_path/run_maintext_ablations.py" dispatch --output "$run_path" \
  --workers "$slots" > "$run_path/dispatch.log" 2>&1 < /dev/null &
printf '%s\n' "$!"
