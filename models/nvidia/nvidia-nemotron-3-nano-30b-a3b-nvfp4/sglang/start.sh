#!/usr/bin/env bash
set -euo pipefail

model_id="${MODEL_ID:-nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4}"
served_name="${SERVED_MODEL_NAME:-nemotron-3-nano}"
port="${SGLANG_CONTAINER_PORT:-30000}"
context_length="${CONTEXT_LENGTH:-32768}"
memory_budget_gib="${GPU_MEMORY_BUDGET_GIB:-60}"
mem_fraction="${MEM_FRACTION_STATIC:-}"

if [[ -z "${mem_fraction}" ]]; then
  read -r mem_fraction total_memory_gib < <(
    python3 - "${memory_budget_gib}" <<'PY'
import sys

import torch

budget_gib = float(sys.argv[1])
total_bytes = torch.cuda.mem_get_info()[1]
fraction = budget_gib * 1024**3 / total_bytes
if not 0 < fraction < 1:
    total_gib = total_bytes / 1024**3
    raise SystemExit(
        f"GPU_MEMORY_BUDGET_GIB must be greater than 0 and less than "
        f"{total_gib:.2f} GiB"
    )
print(f"{fraction:.6f} {total_bytes / 1024**3:.2f}")
PY
  )
  echo "SGLang static memory budget: ${memory_budget_gib} GiB of ${total_memory_gib} GiB (fraction ${mem_fraction})"
else
  echo "SGLang static memory fraction override: ${mem_fraction}"
fi

args=(
  python3 -m sglang.launch_server
  --model-path "${model_id}"
  --served-model-name "${served_name}"
  --host 0.0.0.0
  --port "${port}"
  --trust-remote-code
  --tp 1
  --attention-backend flashinfer
  --tool-call-parser qwen3_coder
  --reasoning-parser nemotron_3
  --context-length "${context_length}"
  --mem-fraction-static "${mem_fraction}"
)

if [[ -n "${SGLANG_EXTRA_ARGS:-}" ]]; then
  read -r -a extra_args <<<"${SGLANG_EXTRA_ARGS}"
  args+=("${extra_args[@]}")
fi

exec "${args[@]}"
