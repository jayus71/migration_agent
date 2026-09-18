#!/usr/bin/env bash
set -euo pipefail
source /media/main/whj/.autofix_llm_env
run=/media/main/whj/projects/torch4ms/maintext-ablations-20260918/recovery_round1
exec /media/main/whj/miniconda3/envs/mstorch/bin/python \
  "$run/recover_maintext_ablations.py" execute --output "$run" --workers 6
