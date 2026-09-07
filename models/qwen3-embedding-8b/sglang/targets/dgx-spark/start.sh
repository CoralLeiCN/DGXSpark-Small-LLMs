#!/usr/bin/env bash
set -euo pipefail
args=(
  uv run --no-project --python /opt/sglang/bin/python --no-python-downloads -m sglang.launch_server
  --model-path "${MODEL_ID:-Qwen/Qwen3-Embedding-8B}"
  --revision "${MODEL_REVISION:-1d8ad4ca9b3dd8059ad90a75d4983776a23d44af}"
  --served-model-name "${SERVED_MODEL_NAME:-qwen3-embedding-8b}"
  --host 0.0.0.0 --port "${SGLANG_CONTAINER_PORT:-30000}"
  --is-embedding --dtype bfloat16 --tp 1
  --context-length "${CONTEXT_LENGTH:-8192}"
  --mem-fraction-static "${MEM_FRACTION_STATIC:-0.40}"
  --max-running-requests "${MAX_RUNNING_REQUESTS:-2}"
  --attention-backend triton
  --json-model-override-args '{"is_matryoshka":true}'
  --disable-radix-cache --chunked-prefill-size -1
  --cuda-graph-backend-decode disabled --cuda-graph-backend-prefill disabled
)
if [[ -n "${SGLANG_EXTRA_ARGS:-}" ]]; then
  read -r -a extra_args <<<"${SGLANG_EXTRA_ARGS}"
  args+=("${extra_args[@]}")
fi
exec "${args[@]}"
