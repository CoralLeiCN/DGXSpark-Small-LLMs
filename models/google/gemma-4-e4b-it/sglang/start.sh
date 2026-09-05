#!/usr/bin/env bash
set -euo pipefail

model_id="${MODEL_ID:-google/gemma-4-E4B-it}"
served_name="${SERVED_MODEL_NAME:-gemma-4-e4b-it}"
port="${SGLANG_CONTAINER_PORT:-30000}"
context_length="${CONTEXT_LENGTH:-32768}"
mem_fraction="${MEM_FRACTION_STATIC:-0.85}"
max_running_requests="${MAX_RUNNING_REQUESTS:-4}"

args=(
  python3 -m sglang.launch_server
  --model-path "${model_id}"
  --served-model-name "${served_name}"
  --host 0.0.0.0
  --port "${port}"
  --trust-remote-code
  --tp 1
  --context-length "${context_length}"
  --mem-fraction-static "${mem_fraction}"
  --max-running-requests "${max_running_requests}"
  --attention-backend triton
  --reasoning-parser gemma4
  --tool-call-parser gemma4
)

if [[ -n "${SGLANG_EXTRA_ARGS:-}" ]]; then
  read -r -a extra_args <<<"${SGLANG_EXTRA_ARGS}"
  args+=("${extra_args[@]}")
fi

exec "${args[@]}"
