#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Usage: benchmark-aiperf.sh [CONCURRENCY ...]

Benchmark the running Qwen3.8 27B NVFP4 endpoint with AIPerf 0.12.0.
Defaults: a capacity sweep through the configured maximum of 72 concurrent
requests: 1 2 4 8 16 32 48 56 64 72. Each setting uses 96 warmups and 384
measured requests, with 512 target input tokens and 128 output tokens.

BENCHMARK_URL                 Server origin (default: http://127.0.0.1:30000)
QWEN_NVFP4_BENCHMARK_ROOT     New output directory (default: <tag>-<suffix> under
                              $HOME/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/).
                              Existing directories are not overwritten.
QWEN_NVFP4_TOKENIZER          Hugging Face ID (default: nvidia/Qwen3.8-27B-NVFP4).
QWEN_NVFP4_TOKENIZER_REVISION Validated model snapshot (default:
                              dbb8f445b3145f8a4c18ddc769f032d57d32867c).
QWEN_NVFP4_REQUEST_COUNT      Measured requests per setting (default: 384).
QWEN_NVFP4_WARMUP_COUNT       Warmups per setting (default: 96).
QWEN_NVFP4_MAX_CONCURRENCY    Largest allowed client concurrency (default: 72).
QWEN_NVFP4_SEED_BASE          Random seed is this integer plus concurrency (default: 42).
QWEN_NVFP4_EXPERIMENT_TAG     Safe tag linking all profiles and telemetry in one
                              run (default: UTC timestamp plus model name).

Requires uv and a running Qwen service configured with MAX_RUNNING_REQUESTS=72.
The service must expose SGLang metrics and its estimated-FLOPS counter at
/metrics; start it with make start MODEL=qwen3.8-27b-nvfp4.
Uses an isolated uv tool environment with managed Python 3.12. Does not start,
stop, or reconfigure the model server. Set UV_OFFLINE=1 to use an already
cached AIPerf installation.
EOF
  exit 0
fi

if [[ $# -eq 0 ]]; then
  set -- 1 2 4 8 16 32 48 56 64 72
fi

max_concurrency="${QWEN_NVFP4_MAX_CONCURRENCY:-72}"
if [[ ! "$max_concurrency" =~ ^[1-9][0-9]{0,8}$ ]]; then
  printf 'QWEN_NVFP4_MAX_CONCURRENCY must be a positive integer without leading zeros.\n' >&2
  exit 2
fi

seen=" "
for concurrency in "$@"; do
  if [[ ! "$concurrency" =~ ^[1-9][0-9]{0,8}$ || "$seen" == *" $concurrency "* ]]; then
    printf 'Provide distinct positive concurrency integers without leading zeros: %s\n' "$concurrency" >&2
    exit 2
  fi
  if (( concurrency > max_concurrency )); then
    printf 'Concurrency %s exceeds QWEN_NVFP4_MAX_CONCURRENCY=%s.\n' "$concurrency" "$max_concurrency" >&2
    exit 2
  fi
  seen+="$concurrency "
done

for count in "${QWEN_NVFP4_REQUEST_COUNT:-384}" "${QWEN_NVFP4_WARMUP_COUNT:-96}"; do
  if [[ ! "$count" =~ ^[1-9][0-9]{0,8}$ ]]; then
    printf 'Request and warmup counts must be positive integers.\n' >&2
    exit 2
  fi
done
for concurrency in "$@"; do
  if (( ${QWEN_NVFP4_REQUEST_COUNT:-384} < concurrency )); then
    printf 'Measured request count must reach concurrency %s.\n' "$concurrency" >&2
    exit 2
  fi
done
seed_base="${QWEN_NVFP4_SEED_BASE:-42}"
if [[ ! "$seed_base" =~ ^(0|[1-9][0-9]{0,8})$ ]]; then
  printf 'QWEN_NVFP4_SEED_BASE must be a nonnegative integer without leading zeros.\n' >&2
  exit 2
fi
experiment_tag="${QWEN_NVFP4_EXPERIMENT_TAG:-$(date -u +%Y-%m-%dT%H-%M-%SZ)-qwen3.8-27b-nvfp4}"
if [[ ! "$experiment_tag" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$ ]]; then
  printf 'QWEN_NVFP4_EXPERIMENT_TAG must be 1-64 letters, digits, dots, underscores, or hyphens.\n' >&2
  exit 2
fi
command -v uv >/dev/null || { printf 'uv is required.\n' >&2; exit 1; }

if [[ -n "${QWEN_NVFP4_BENCHMARK_ROOT:-}" ]]; then
  benchmark_root="$QWEN_NVFP4_BENCHMARK_ROOT"
  mkdir -p -- "$(dirname -- "$benchmark_root")"
  mkdir -- "$benchmark_root"
else
  artifact_parent="${HOME:?HOME must be set}/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark"
  mkdir -p -- "$artifact_parent"
  benchmark_root="$(mktemp -d "$artifact_parent/${experiment_tag}-XXXXXX")"
fi
export HF_HUB_DISABLE_IMPLICIT_TOKEN="${HF_HUB_DISABLE_IMPLICIT_TOKEN:-1}"
benchmark_url="${BENCHMARK_URL:-http://127.0.0.1:30000}"
benchmark_url="${benchmark_url%/}"
metrics_url="$benchmark_url/metrics"
if ! curl --fail --silent --show-error "$metrics_url" | grep -q '^sglang:estimated_flops_per_gpu_total'; then
  printf 'SGLang estimated-FLOPS metric is unavailable at %s. Start the service with metrics enabled.\n' "$metrics_url" >&2
  exit 1
fi
run_started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf '{"experiment_tag":"%s","model":"qwen3.8-27b-nvfp4","started_at_utc":"%s","benchmark_url":"%s","metrics_url":"%s","max_concurrency":%s,"request_count":%s,"warmup_count":%s}\n' \
  "$experiment_tag" "$run_started_at" "$benchmark_url" "$metrics_url" "$max_concurrency" \
  "${QWEN_NVFP4_REQUEST_COUNT:-384}" "${QWEN_NVFP4_WARMUP_COUNT:-96}" > "$benchmark_root/experiment.json"
printf 'Experiment tag: %s\nArtifacts: %s\n' "$experiment_tag" "$benchmark_root"

for concurrency in "$@"; do
  profile_started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf '{"experiment_tag":"%s","concurrency":%s,"phase":"profile","event":"started","at_utc":"%s"}\n' \
    "$experiment_tag" "$concurrency" "$profile_started_at" >> "$benchmark_root/experiment-events.jsonl"
  printf 'Starting concurrency %s (%s measured, %s warmups) at %s\n' \
    "$concurrency" "${QWEN_NVFP4_REQUEST_COUNT:-384}" "${QWEN_NVFP4_WARMUP_COUNT:-96}" "$profile_started_at"
  if uv tool run --managed-python --python 3.12 --from aiperf==0.12.0 aiperf profile \
    --url "$benchmark_url" \
    --model qwen3.8-27b-nvfp4 --tokenizer "${QWEN_NVFP4_TOKENIZER:-nvidia/Qwen3.8-27B-NVFP4}" \
    --tokenizer-revision "${QWEN_NVFP4_TOKENIZER_REVISION:-dbb8f445b3145f8a4c18ddc769f032d57d32867c}" \
    --endpoint-type chat --endpoint /v1/chat/completions \
    --streaming --use-legacy-max-tokens --use-server-token-count \
    --synthetic-input-tokens-mean 512 --synthetic-input-tokens-stddev 0 \
    --output-tokens-mean 128 --output-tokens-stddev 0 \
    --extra-inputs '{"temperature":0,"ignore_eos":true,"chat_template_kwargs":{"enable_thinking":false}}' \
    --header "X-Inferpack-Experiment-Tag:${experiment_tag}" \
    --concurrency "$concurrency" --warmup-request-count "${QWEN_NVFP4_WARMUP_COUNT:-96}" --request-count "${QWEN_NVFP4_REQUEST_COUNT:-384}" \
    --random-seed "$((seed_base + concurrency))" \
    --server-metrics "$metrics_url" --server-metrics-formats json csv jsonl \
    --gpu-telemetry pynvml --ui-type none \
    --artifact-dir "$benchmark_root/c$concurrency" \
    > "$benchmark_root/c$concurrency.log" 2>&1; then
    printf '{"experiment_tag":"%s","concurrency":%s,"phase":"profile","event":"completed","at_utc":"%s"}\n' \
      "$experiment_tag" "$concurrency" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$benchmark_root/experiment-events.jsonl"
    tail -40 "$benchmark_root/c$concurrency.log"
  else
    status=$?
    printf '{"experiment_tag":"%s","concurrency":%s,"phase":"profile","event":"failed","at_utc":"%s","exit_status":%s}\n' \
      "$experiment_tag" "$concurrency" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$status" >> "$benchmark_root/experiment-events.jsonl"
    printf 'AIPerf failed at concurrency %s. Log: %s\n' "$concurrency" "$benchmark_root/c$concurrency.log" >&2
    tail -80 "$benchmark_root/c$concurrency.log" >&2
    exit "$status"
  fi
done
printf 'Artifacts: %s\n' "$benchmark_root"
