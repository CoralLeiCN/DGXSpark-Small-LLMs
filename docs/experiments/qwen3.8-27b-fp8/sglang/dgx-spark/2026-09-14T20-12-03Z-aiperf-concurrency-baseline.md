# 2026-09-14T20:12:03Z — Streaming concurrency baseline qualified

Run ID: `RUN-0010`

- Status: resolved
- Phase: inference / performance validation
- Related turns: [tokenizer path failure](2026-09-14T19-54-00Z-aiperf-offline-tokenizer-path.md),
  [startup and runtime configuration](2026-09-14T19-52-51Z-benchmark-startup-qualified.md)
- Repo revision: `17d39b06860ea7159a3d4a3443053b4d79bf867e`, dirty with benchmark
  runner, documentation, and journals
- Host/GPU: one DGX Spark, Linux aarch64, NVIDIA GB10, driver `580.173.02`,
  CUDA driver capability `13.0`; client on the same host over loopback
- Container: `dgxspark/qwen3.8-27b-fp8-sglang:0.1.0`, image
  `sha256:3c11adf54d4a220f587f361f48eee66b50a8e2b8c068db7484c598beb3684b62`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, torch `2.13.0+cu130`, transformers `5.12.1`
- Model and tokenizer: `Qwen/Qwen3.8-27B-FP8`, revision
  `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`, FP8 weights; BF16 KV cache and GDN state
- Launch: TP 1, FlashInfer attention, context 32768, memory fraction 0.45,
  max running requests 4, Mamba slots 16, prefill chunk 2048,
  `extra_buffer_lazy`, `--enable-metrics`, no speculative decoding
- Client: AIPerf `0.12.0`, uv `0.9.7`, uv-managed CPython `3.12.12`

## Command

Executed the checked-in [benchmark runner](../../../../../models/qwen3.8-27b-fp8/sglang/targets/dgx-spark/benchmark-aiperf.sh)
with these environment settings:

```bash
UV_TOOL_DIR=/tmp/codex-aiperf-tools \
UV_CACHE_DIR=/tmp/codex-aiperf-uv-cache \
UV_PYTHON_INSTALL_DIR=/tmp/codex-aiperf-python \
UV_OFFLINE=1 HF_HUB_OFFLINE=1 \
QWEN_BENCHMARK_ROOT="$PWD/models/qwen3.8-27b-fp8/sglang/targets/dgx-spark/artifacts/2026-09-14T19-54-35Z-baseline" \
  models/qwen3.8-27b-fp8/sglang/targets/dgx-spark/benchmark-aiperf.sh
```

The runner executed sequential concurrency profiles 1, 2, and 4 against
`http://127.0.0.1:30000/v1/chat/completions`, served name `qwen3.8-27b-fp8`.
Each profile used four warmups and 32 measured requests, target input length
512, fixed output length 128, streaming, server token counts, legacy
`max_tokens`, temperature 0, `ignore_eos=true`, and
`chat_template_kwargs={"enable_thinking":false}`. Seeds were 43, 44, and 46.
Client server-metric collection and GPU telemetry were disabled.

## Observation

All profiles exited 0. All 96 measured requests and 12 warmups succeeded with
exactly 128 server-reported completion tokens each. Measured input lengths were
524–526 tokens after chat formatting. Each measured profile produced 4096
output tokens. The prior tokenizer error was resolved by the cached repository
ID and exact revision; no model-serving changes were needed.

| Concurrency | TTFT p50 / p95 (ms) | Request latency p50 / p95 (s) | ITL mean (ms) | Aggregate output tokens/s | Per-user decode tokens/s (mean) | Requests/s | Measured duration (s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 413.88 / 424.14 | 15.833 / 16.130 | 121.71 | 8.06 | 8.22 | 0.0630 | 507.91 |
| 2 | 717.94 / 843.96 | 15.837 / 17.073 | 121.25 | 15.84 | 8.25 | 0.1237 | 258.63 |
| 4 | 1187.61 / 1307.28 | 16.595 / 16.612 | 121.09 | 30.85 | 8.26 | 0.2410 | 132.79 |

Measured UTC windows, derived from per-request epoch timestamps:

- Concurrency 1: 19:55:28.909–20:03:56.817.
- Concurrency 2: 20:04:38.625–20:08:57.253.
- Concurrency 4: 20:09:18.984–20:11:31.773.

AIPerf's displayed times and aggregate `start_time`/`end_time` strings use
Europe/London local time without an offset, one hour ahead of UTC on this date.
The artifact directory timestamp is a label, not the exact measurement start.

## Interpretation And Limits

Concurrency 4 delivered 3.82 times the concurrency-1 aggregate throughput.
Per-user decode speed remained around 8.2–8.3 tokens/s, while median TTFT grew
from 0.414 to 1.188 seconds. Median full-request latency rose by about 4.8%.
Batching increased total throughput without a material decode-speed penalty
within the tested four-request scheduler cap. This does not establish maximum
hardware throughput or justify increasing the cap without further validation.

This is a short synthetic, fixed-output, thinking-disabled text baseline, not
a natural-stopping, reasoning-quality, long-context, multimodal, or sustained
production benchmark. There was one profile per concurrency with only 32
measured requests; tail percentiles have limited statistical support. Profile
order was fixed, without repeated trials or confidence intervals.

Prefix caching remained enabled and was not flushed. Different seeds reduced
exact prompt reuse between profiles. Warmup and profile phases may still reuse
prefixes. AIPerf warned that `usage.prompt_tokens_details.cached_tokens` was
absent, so cache-hit rates cannot be quantified. No cache-disabled performance
claim is supported. The server had metrics enabled, but this benchmark did not
collect them or continuous GPU telemetry. Qwen was the only running Docker
container; host background activity was not independently quantified. Loopback
timings exclude remote network latency.

## Verification And Artifacts

Parsed all aggregate JSON exports and all 108 per-request records. Verified
32 measured requests and four warmups per profile, no errors or cancellations,
the intended thinking override, and zero output-length mismatches. Post-run
health returned HTTP 200. Docker reported healthy, zero restarts, and no OOM
kill. No error, exception, traceback, failed operation, or HTTP 4xx/5xx matched
the saved server logs from benchmark start through the post-run health check.

Local artifacts live under
`models/qwen3.8-27b-fp8/sglang/targets/dgx-spark/artifacts/2026-09-14T19-54-35Z-baseline/`:

- `c1/`, `c2/`, `c4/`: aggregate JSON/CSV, per-request JSONL, generated inputs,
  phase exports, and client logs.
- `c1.log`, `c2.log`, `c4.log`: console output and exact CLI settings.
- `summary.json`: audited metrics and UTC measurement windows.
- `server-runtime.log`: benchmark-interval server logs, ending before shutdown.

Artifacts are local and ignored by Git; this journal preserves the measured
summary and reproduction settings. The failed initial attempt remains separately
under `artifacts/2026-09-14T19-52-40Z-baseline/`. Runner syntax validation and
`git diff --check` passed. No tests were added.

## Lesson

Measure aggregate output throughput and per-user latency separately. For this
configuration, batching improves overall throughput while first-token latency
grows; it does not make an individual response decode substantially faster.

## Next Step

Restore the initially stopped container state after saving results. Further
benchmarking would require another workload or an explicit tuning experiment.
