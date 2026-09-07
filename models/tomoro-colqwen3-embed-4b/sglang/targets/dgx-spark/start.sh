#!/usr/bin/env bash
set -euo pipefail
uv run --no-project --python /opt/sglang/bin/python --no-python-downloads /opt/inferpack/prepare_model.py
args=(
  uv run --no-project --python /opt/sglang/bin/python --no-python-downloads -m sglang.launch_server
  --model-path /opt/inferpack/model
  --served-model-name "${SERVED_MODEL_NAME:-tomoro-colqwen3-embed-4b}"
  --host 0.0.0.0 --port "${SGLANG_CONTAINER_PORT:-30000}"
  --is-embedding --dtype bfloat16 --tp 1
  --context-length "${CONTEXT_LENGTH:-8192}"
  --mem-fraction-static "${MEM_FRACTION_STATIC:-0.35}"
  --max-running-requests "${MAX_RUNNING_REQUESTS:-2}"
  --attention-backend triton --mm-attention-backend sdpa
  --disable-radix-cache --chunked-prefill-size -1 --disable-cuda-graph
)
if [[ -n "${SGLANG_EXTRA_ARGS:-}" ]]; then
  read -r -a extra_args <<<"${SGLANG_EXTRA_ARGS}"
  args+=("${extra_args[@]}")
fi
exec "${args[@]}"
