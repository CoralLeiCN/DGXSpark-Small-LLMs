# 2026-09-14T21:28:07Z — MTP throughput growth slows near 64 active requests

Run ID: `RUN-0015`

- Status: resolved (seven profiles completed; maximum not yet established)
- Phase: inference / runtime shutdown
- Related turns: [Expanded server startup](2026-09-14T21-08-33Z-mtp-capacity64-startup.md)
- Repo revision: `17d39b06860ea7159a3d4a3443053b4d79bf867e`, dirty
- Host/GPU: one DGX Spark GB10, Linux aarch64, driver `580.173.02`
- Container: `inferpack-qwen38-fp8-mtp-capacity64`, image
  `dgxspark/qwen3.8-27b-fp8-sglang:0.1.0`, image ID
  `sha256:3c11adf54d4a220f587f361f48eee66b50a8e2b8c068db7484c598beb3684b62`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, FlashInfer `0.6.17`,
  torch `2.13.0+cu130`, transformers `5.12.1`
- Model: `Qwen/Qwen3.8-27B-FP8`, revision
  `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`, FP8 target and native MTP

## Command And Workload

The fixed server used memory fraction 0.80, active limit 64, 256 Mamba slots,
CUDA graph maximum 64, context 32768, chunked prefill 2048, and native MTP
EAGLE with three steps / top-k one / four draft tokens. See RUN-0014 for the
complete launch command. No other model service was running.

```bash
UV_TOOL_DIR=/tmp/codex-aiperf-tools \
UV_CACHE_DIR=/tmp/codex-aiperf-uv-cache \
UV_PYTHON_INSTALL_DIR=/tmp/codex-aiperf-python \
UV_OFFLINE=1 HF_HUB_OFFLINE=1 \
QWEN_REQUEST_COUNT=auto QWEN_WARMUP_COUNT=auto QWEN_SEED_BASE=1000 \
QWEN_BENCHMARK_ROOT=models/qwen3.8-27b-fp8/sglang/targets/dgx-spark/artifacts/2026-09-14T21-02-25Z-capacity64-sweep \
models/qwen3.8-27b-fp8/sglang/targets/dgx-spark/benchmark-aiperf.sh 4 8 16 24 32 48 64
```

AIPerf 0.12.0, Python 3.12.12 through uv, streaming chat completions,
512 synthetic target input tokens, 128 forced output tokens, temperature zero,
thinking disabled, server token counts. Actual inputs were 523–527 tokens.
Measured count was `max(96, 4 * concurrency)`; warmup count equalled concurrency.
Seeds were `1000 + concurrency`. Prefix caching remained enabled and was not
flushed. Warmups are excluded from these aggregate metrics.

## Results

| Concurrency | Measured / warmup | Output tokens/s | Median / p95 latency (s) | Median / p95 TTFT (s) |
| --- | --- | --- | --- | --- |
| 4 | 96 / 4 | 52.74 | 9.49 / 11.07 | 0.52 / 1.11 |
| 8 | 96 / 8 | 87.70 | 11.47 / 13.78 | 0.79 / 2.27 |
| 16 | 96 / 16 | 129.92 | 14.99 / 18.31 | 0.87 / 4.46 |
| 24 | 96 / 24 | 156.36 | 19.46 / 23.92 | 1.75 / 6.78 |
| 32 | 128 / 32 | 176.55 | 22.42 / 29.98 | 1.78 / 8.92 |
| 48 | 192 / 48 | 198.27 | 29.90 / 42.00 | 2.46 / 12.19 |
| 64 | 256 / 64 | 204.16 | 38.53 / 53.16 | 2.16 / 15.68 |

All 960 measured requests and 196 warmups completed, without errors or
cancellations. Every response reported exactly 128 completion tokens, matching
the measured output length. Client effective concurrency reached each requested
level; its median equalled the requested level. Five-second scheduler samples
and decode logs confirmed active batches well above four and through 64.
These gauges are sampled at different scheduler stages and occasionally exceed
the instantaneous client count; they are not an exact simultaneous client trace.

The sampled queue median was zero for every profile, with temporary prefill
queues. Sampled speculative acceptance length medians were 2.70–2.76.
The server's sampled cache-hit gauge was zero; AIPerf still lacked per-request
cache-read token usage. The monitor had no collection errors. Minimum host
`MemAvailable` was 18,501 MiB; these are host memory samples, not continuous GPU
telemetry. No runtime OOM or inference traceback was observed.

## Diagnosis And Follow-Up

Increasing 48 to 64 improved aggregate throughput by only 2.97%, while median
latency increased by 28.85%. This suggests proximity to a plateau, but the
highest point is at the edge of the sweep. It is not evidence that 64 is the
maximum. Profile sizes and seeds differ, and one short run per setting does
not establish uncertainty or a production capacity guarantee.

The next experiment increases active capacity to 96 and compares 48, 64, 80,
and 96 with equal request counts under that fixed server. Common points must
be remeasured because a larger state pool and memory budget change the server.
Repeat/refine the strongest settings before selecting a workload-specific peak.

## Shutdown And Artifacts

Stopped the monitor after the completed sweep, saved the runtime log, then ran:

```bash
docker stop -t 60 inferpack-qwen38-fp8-mtp-capacity64
docker inspect --format '{{.State.ExitCode}} {{.State.OOMKilled}}' inferpack-qwen38-fp8-mtp-capacity64
```

Observed the same shutdown-only `SystemExit: 0` followed by
`asyncio.exceptions.CancelledError` as RUN-0011. Docker reported `0 false`;
this did not affect completed inference. No fix was needed for this benchmark.

The local ignored artifact directory in the command contains per-request and
aggregate exports, generated input files, logs, `summary.json`,
`monitored-summary.json`, `server-samples.jsonl`, `server.log`, `shutdown.log`,
and copies of the smoke, audit, and monitor scripts. Earlier startup warnings
and readiness 503 are recorded in RUN-0014.

## Lesson

Continue past a rising endpoint rather than calling it the maximum. Near a
plateau, use equal-sized, repeated measurements and report the latency cost
alongside aggregate throughput.
