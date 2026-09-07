#!/usr/bin/env bash
set -euo pipefail

model_id="${MODEL_ID:-Qwen/Qwen3.8-27B-FP8}"
served_name="${SERVED_MODEL_NAME:-qwen3.8-27b-fp8}"
port="${SGLANG_CONTAINER_PORT:-30000}"
context_length="${CONTEXT_LENGTH:-32768}"
mem_fraction="${MEM_FRACTION_STATIC:-0.80}"
max_running_requests="${MAX_RUNNING_REQUESTS:-4}"
max_mamba_cache_size="${MAX_MAMBA_CACHE_SIZE:-16}"
chunked_prefill_size="${CHUNKED_PREFILL_SIZE:-2048}"

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
  --attention-backend flashinfer
  --chunked-prefill-size "${chunked_prefill_size}"
  --mamba-radix-cache-strategy extra_buffer_lazy
  --mamba-ssm-dtype bfloat16
  --max-mamba-cache-size "${max_mamba_cache_size}"
  --max-running-requests "${max_running_requests}"
  --reasoning-parser qwen3
  --tool-call-parser qwen3_coder
)

if [[ -n "${SGLANG_EXTRA_ARGS:-}" ]]; then
  read -r -a extra_args <<<"${SGLANG_EXTRA_ARGS}"
  args+=("${extra_args[@]}")
fi

exec "${args[@]}"
