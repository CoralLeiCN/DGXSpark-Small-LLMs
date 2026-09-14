# 2026-09-14T21:55:45Z — Matched profiles bracket the MTP throughput peak near 64

Run ID: `RUN-0017`

- Status: resolved (four matched profiles completed; finer search follows)
- Phase: inference
- Related turns: [96-request server](2026-09-14T21-33-38Z-mtp-capacity96-startup.md),
  [initial sweep](2026-09-14T21-28-07Z-mtp-concurrency-sweep-through64.md)
- Repo revision: `17d39b06860ea7159a3d4a3443053b4d79bf867e`, dirty
- Host/GPU: one DGX Spark GB10, Linux aarch64, driver `580.173.02`
- Image: `dgxspark/qwen3.8-27b-fp8-sglang:0.1.0`,
  `sha256:3c11adf54d4a220f587f361f48eee66b50a8e2b8c068db7484c598beb3684b62`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, FlashInfer `0.6.17`,
  torch `2.13.0+cu130`, transformers `5.12.1`
- Model: `Qwen/Qwen3.8-27B-FP8`, revision
  `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`

## Configuration And Command

The RUN-0016 server stayed fixed: native FP8 MTP EAGLE three steps / top-k one /
four draft tokens, memory fraction 0.85, active cap 96, Mamba slots 384, graph
maximum 96, context 32768, prefill chunk 2048, BF16 KV/GDN state. AIPerf 0.12.0
ran through uv-managed Python 3.12.12. No other model service was started.

```bash
export UV_TOOL_DIR=/tmp/codex-aiperf-tools
export UV_CACHE_DIR=/tmp/codex-aiperf-uv-cache
export UV_PYTHON_INSTALL_DIR=/tmp/codex-aiperf-python
export UV_OFFLINE=1 HF_HUB_OFFLINE=1
export QWEN_REQUEST_COUNT=384 QWEN_WARMUP_COUNT=96
pack=models/qwen3.8-27b-fp8/sglang/targets/dgx-spark
for concurrency in 96 80 64 48; do
  curl --fail --silent --show-error -X POST 'http://127.0.0.1:30000/flush_cache?timeout=30'
  export QWEN_SEED_BASE=$((3000 - concurrency))
  export QWEN_BENCHMARK_ROOT="$pack/artifacts/2026-09-14T21-28-17Z-capacity96-c$concurrency"
  "$pack/benchmark-aiperf.sh" "$concurrency"
done
```

All four flushes succeeded before their profiles. Each profile had 96 warmups
and 384 measured streaming chat requests, 512 target input tokens / 128 forced
output tokens, temperature zero, thinking disabled, and seed 3000. Actual input
lengths were 523–526. Generated inputs were byte-identical across all four
profiles: SHA256 `6f6c35d182d422d5a72017dc2a199a5925bda7b6fadc8c179e240fd39a657392`.
The measured conversation-ID multisets also matched. Warmups are excluded.

## Results And Verification

| Concurrency | Output tokens/s | Median / p95 latency (s) | Median / p95 TTFT (s) | Mean per-user decode tokens/s |
| --- | --- | --- | --- | --- |
| 48 | 199.10 | 30.16 / 39.38 | 2.04 / 9.87 | 4.80 |
| 64 | 207.79 | 39.11 / 49.96 | 2.39 / 14.35 | 3.78 |
| 80 | 195.90 | 51.90 / 70.01 | 3.23 / 18.65 | 2.98 |
| 96 | 172.49 | 69.69 / 92.93 | 4.11 / 22.93 | 2.11 |

All 1,536 measured requests and 384 warmups passed without errors or
cancellations. Every response reported exactly 128 completion tokens, matching
the measured output length. Median client effective concurrency equalled the
requested value; five-second scheduler median active counts were 48, 63, 79,
and 94. The sampled queue median was zero except at 96, where it was one.
Scheduler gauges can temporarily exceed client counts because their updates
occur at different stages; do not interpret them as synchronized client traces.

Monitor collection had no errors. Sampled speculative acceptance length
medians were approximately 2.75 at every setting, and sampled cache-hit rates
were zero. The lowest sampled `MemAvailable` during the measured phases was
12,695 MiB. These are host-memory and scheduler samples, not continuous GPU
telemetry. No inference failures were observed.

## Diagnosis And Next Step

The best of these matched points is 64. Throughput falls 5.72% at 80 and 16.99%
at 96 relative to 64, while latency rises. This brackets a local practical peak;
it does not establish a unique optimum among every integer concurrency or
across other workloads/decoding configurations. The lower points agree closely
with RUN-0015 despite its different server allocation and shorter profiles.

Test 72 and 56 with these same inputs/settings, then repeat the strongest
candidates using a second seed. The server remains running for that follow-up.

## Artifacts And Lesson

Per-profile artifacts are in the command's four ignored output directories.
The shared `artifacts/2026-09-14T21-28-17Z-capacity96-server/` directory contains
the monitor stream, flush confirmations, driver scripts, and `coarse.json`
with input matching and per-profile monitor summaries.

Larger batches can reduce total throughput even when they fit in memory.
Use matched inputs, fixed server settings, and points on both sides of the
observed peak to select concurrency.
