#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Usage: benchmark-aiperf.sh [CONCURRENCY ...]

Benchmark the running Qwen3.8 27B FP8 endpoint with AIPerf 0.12.0.
Defaults: concurrency 1 2 4; 4 warmups and 32 measured requests per setting;
512 target input tokens and 128 output tokens, streaming, thinking disabled.

BENCHMARK_URL        Server origin (default: http://127.0.0.1:30000)
QWEN_BENCHMARK_ROOT  New output directory (default: artifacts/<UTC>-<suffix>
                     beside this script). Existing directories are not overwritten.
QWEN_TOKENIZER       Hugging Face ID (default: Qwen/Qwen3.8-27B-FP8).
QWEN_TOKENIZER_REVISION  Revision (default: validated snapshot
                     017b9c7af6b5689d5dd426a76e0bc077eb5ca20a).
QWEN_REQUEST_COUNT   Measured requests per setting (default: 32).
                     'auto' uses max(96, 4 * concurrency) for capacity sweeps.
QWEN_WARMUP_COUNT    Warmups per setting (default: 4); 'auto' uses concurrency.
QWEN_SEED_BASE       Random seed is this integer plus concurrency (default: 42).

Requires uv and a running Qwen service. Uses an isolated uv tool environment
with managed Python 3.12. Does not start, stop, or reconfigure the model server.
Set UV_OFFLINE=1 to use an already cached AIPerf installation.
EOF
  exit 0
fi

if [[ $# -eq 0 ]]; then
  set -- 1 2 4
fi
seen=" "
for concurrency in "$@"; do
  if [[ ! "$concurrency" =~ ^[1-9][0-9]{0,8}$ || "$seen" == *" $concurrency "* ]]; then
    printf 'Provide distinct positive concurrency integers without leading zeros: %s\n' "$concurrency" >&2
    exit 2
  fi
  seen+="$concurrency "
done
for count in "${QWEN_REQUEST_COUNT:-32}" "${QWEN_WARMUP_COUNT:-4}"; do
  if [[ "$count" != auto && ! "$count" =~ ^[1-9][0-9]{0,8}$ ]]; then
    printf 'Request and warmup counts must be positive integers or auto.\n' >&2
    exit 2
  fi
done
seed_base="${QWEN_SEED_BASE:-42}"
if [[ ! "$seed_base" =~ ^(0|[1-9][0-9]{0,8})$ ]]; then
  printf 'QWEN_SEED_BASE must be a nonnegative integer without leading zeros.\n' >&2
  exit 2
fi
for concurrency in "$@"; do
  if [[ "${QWEN_REQUEST_COUNT:-32}" != auto ]] && (( ${QWEN_REQUEST_COUNT:-32} < concurrency )); then
    printf 'Measured request count must reach concurrency %s; use QWEN_REQUEST_COUNT=auto or a larger count.\n' "$concurrency" >&2
    exit 2
  fi
done
command -v uv >/dev/null || { printf 'uv is required.\n' >&2; exit 1; }

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ -n "${QWEN_BENCHMARK_ROOT:-}" ]]; then
  benchmark_root="$QWEN_BENCHMARK_ROOT"
  mkdir -p -- "$(dirname -- "$benchmark_root")"
  mkdir -- "$benchmark_root"
else
  mkdir -p -- "$script_dir/artifacts"
  benchmark_root="$(mktemp -d "$script_dir/artifacts/$(date -u +%Y-%m-%dT%H-%M-%SZ)-XXXXXX")"
fi
export HF_HUB_DISABLE_IMPLICIT_TOKEN="${HF_HUB_DISABLE_IMPLICIT_TOKEN:-1}"
printf 'Artifacts: %s\n' "$benchmark_root"

for concurrency in "$@"; do
  request_count="${QWEN_REQUEST_COUNT:-32}"
  warmup_count="${QWEN_WARMUP_COUNT:-4}"
  if [[ "$request_count" == auto ]]; then
    request_count=$((4 * concurrency))
    if (( request_count < 96 )); then request_count=96; fi
  fi
  if [[ "$warmup_count" == auto ]]; then warmup_count="$concurrency"; fi
  printf 'Starting concurrency %s (%s measured, %s warmups) at %s\n' "$concurrency" "$request_count" "$warmup_count" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  if uv tool run --managed-python --python 3.12 --from aiperf==0.12.0 aiperf profile \
    --url "${BENCHMARK_URL:-http://127.0.0.1:30000}" \
    --model qwen3.8-27b-fp8 --tokenizer "${QWEN_TOKENIZER:-Qwen/Qwen3.8-27B-FP8}" \
    --tokenizer-revision "${QWEN_TOKENIZER_REVISION:-017b9c7af6b5689d5dd426a76e0bc077eb5ca20a}" \
    --endpoint-type chat --endpoint /v1/chat/completions \
    --streaming --use-legacy-max-tokens --use-server-token-count \
    --synthetic-input-tokens-mean 512 --synthetic-input-tokens-stddev 0 \
    --output-tokens-mean 128 --output-tokens-stddev 0 \
    --extra-inputs '{"temperature":0,"ignore_eos":true,"chat_template_kwargs":{"enable_thinking":false}}' \
    --concurrency "$concurrency" --warmup-request-count "$warmup_count" --request-count "$request_count" \
    --random-seed "$((seed_base + concurrency))" \
    --no-server-metrics --gpu-telemetry pynvml --ui-type none \
    --artifact-dir "$benchmark_root/c$concurrency" \
    > "$benchmark_root/c$concurrency.log" 2>&1; then
    tail -40 "$benchmark_root/c$concurrency.log"
  else
    status=$?
    printf 'AIPerf failed at concurrency %s. Log: %s\n' "$concurrency" "$benchmark_root/c$concurrency.log" >&2
    tail -80 "$benchmark_root/c$concurrency.log" >&2
    exit "$status"
  fi
done
printf 'Artifacts: %s\n' "$benchmark_root"
