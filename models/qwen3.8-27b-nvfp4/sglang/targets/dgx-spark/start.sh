#!/usr/bin/env bash
set -euo pipefail

model_id="${MODEL_ID:-nvidia/Qwen3.8-27B-NVFP4}"
served_name="${SERVED_MODEL_NAME:-qwen3.8-27b-nvfp4}"
port="${SGLANG_CONTAINER_PORT:-30000}"
context_length="${CONTEXT_LENGTH:-32768}"
mem_fraction="${MEM_FRACTION_STATIC:-0.45}"
max_running_requests="${MAX_RUNNING_REQUESTS:-4}"
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
  --kv-cache-dtype fp8_e4m3
  --attention-backend flashinfer
  --chunked-prefill-size "${chunked_prefill_size}"
  --mamba-full-memory-ratio 4.59
  --mamba-radix-cache-strategy extra_buffer
  --mamba-ssm-dtype float32
  --max-running-requests "${max_running_requests}"
  --reasoning-parser qwen3
  --tool-call-parser qwen3_coder
)

if [[ -n "${SGLANG_EXTRA_ARGS:-}" ]]; then
  read -r -a extra_args <<<"${SGLANG_EXTRA_ARGS}"
  args+=("${extra_args[@]}")
fi

if [[ "${INFERPACK_ENABLE_METRICS:-0}" == 1 && " ${args[*]} " != *" --enable-metrics "* ]]; then
  args+=(--enable-metrics)
fi
exec "${args[@]}"
