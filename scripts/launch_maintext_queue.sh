#!/usr/bin/env bash
set -euo pipefail
queue_root="$1"
source /media/main/whj/.autofix_llm_env
nohup /media/main/whj/miniconda3/envs/mstorch/bin/python \
  "$queue_root/preparation/continue_maintext_queue.py" --root "$queue_root" \
  > "$queue_root/continuation.log" 2>&1 < /dev/null &
printf '%s\n' "$!"
