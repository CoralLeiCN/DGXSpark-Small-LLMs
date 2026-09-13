#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Usage: benchmark-aiperf.sh [CONCURRENCY ...]

Benchmark the running Gemma E4B endpoint with AIPerf 0.12.0.
Defaults: concurrency 4 6 8 12; 12 warmups and 96 measured requests per setting;
512 target input tokens and 128 output tokens, streaming, temperature 0.

BENCHMARK_URL        Server origin (default: http://127.0.0.1:30000)
GEMMA_BENCHMARK_ROOT New output directory (default: artifacts/<UTC timestamp>-<suffix>
                    beside this script). Existing directories are not overwritten.

Requires uv and a running Gemma E4B service. Uses an isolated uv tool environment
with managed Python 3.12. Does not start, stop, or reconfigure the model server.
EOF
  exit 0
fi

if [[ $# -eq 0 ]]; then
  set -- 4 6 8 12
fi
seen=" "
for concurrency in "$@"; do
  if [[ ! "$concurrency" =~ ^[1-9][0-9]{0,8}$ || "$seen" == *" $concurrency "* ]]; then
    printf 'Provide distinct positive concurrency integers without leading zeros: %s\n' "$concurrency" >&2
    exit 2
  fi
  seen+="$concurrency "
done
command -v uv >/dev/null || { printf 'uv is required.\n' >&2; exit 1; }

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ -n "${GEMMA_BENCHMARK_ROOT:-}" ]]; then
  benchmark_root="$GEMMA_BENCHMARK_ROOT"
  mkdir -p -- "$(dirname -- "$benchmark_root")"
  mkdir -- "$benchmark_root"
else
  mkdir -p -- "$script_dir/artifacts"
  benchmark_root="$(mktemp -d "$script_dir/artifacts/$(date -u +%Y-%m-%dT%H-%M-%SZ)-XXXXXX")"
fi
export HF_HUB_DISABLE_IMPLICIT_TOKEN="${HF_HUB_DISABLE_IMPLICIT_TOKEN:-1}"
printf 'Artifacts: %s\n' "$benchmark_root"

for concurrency in "$@"; do
  printf 'Starting concurrency %s at %s\n' "$concurrency" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  if uv tool run --managed-python --python 3.12 --from aiperf==0.12.0 aiperf profile \
    --url "${BENCHMARK_URL:-http://127.0.0.1:30000}" \
    --model gemma-4-e4b-it --tokenizer google/gemma-4-E4B-it \
    --endpoint-type chat --endpoint /v1/chat/completions \
    --streaming --use-legacy-max-tokens --use-server-token-count \
    --synthetic-input-tokens-mean 512 --synthetic-input-tokens-stddev 0 \
    --output-tokens-mean 128 --output-tokens-stddev 0 \
    --extra-inputs '{"temperature":0,"ignore_eos":true}' \
    --concurrency "$concurrency" --warmup-request-count 12 --request-count 96 \
    --random-seed "$((1000 + concurrency))" \
    --no-server-metrics --no-gpu-telemetry --ui-type none \
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
