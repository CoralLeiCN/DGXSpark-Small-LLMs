# 2026-09-14T20:53:32Z — Native FP8 MTP improves the matched concurrency baseline

Run ID: `RUN-0013`

- Status: resolved (benchmark complete; clean exit with known shutdown log noise)
- Phase: inference / performance validation / container shutdown
- Related turns: [MTP startup](2026-09-14T20-42-56Z-fp8-mtp-startup-qualified.md),
  [plain FP8 benchmark](2026-09-14T20-12-03Z-aiperf-concurrency-baseline.md),
  [previous shutdown traceback](2026-09-14T20-12-24Z-benchmark-shutdown-cleanup.md)
- Repo revision: `17d39b06860ea7159a3d4a3443053b4d79bf867e`, dirty with benchmark
  runner, documentation, and journals
- Host/GPU: one DGX Spark, Linux aarch64, NVIDIA GB10, driver `580.173.02`;
  benchmark client on the same host over loopback
- Container: `inferpack-qwen38-fp8-mtp-bench`, image
  `dgxspark/qwen3.8-27b-fp8-sglang:0.1.0`,
  `sha256:3c11adf54d4a220f587f361f48eee66b50a8e2b8c068db7484c598beb3684b62`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, FlashInfer `0.6.17`,
  torch `2.13.0+cu130`, transformers `5.12.1`
- Target, draft head, and tokenizer: `Qwen/Qwen3.8-27B-FP8`, revision
  `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`; target and MTP FP8 e4m3,
  KV and GDN state BF16
- Launch: same target settings as RUN-0010: TP 1, FlashInfer attention,
  context 32768, memory fraction 0.45, max running requests 4, Mamba slots 16,
  prefill chunk 2048, `extra_buffer_lazy`, metrics enabled. Added native MTP:
  `EAGLE`, steps 3, top-k 1, draft tokens 4. ReplaySSM was not enabled.
- Client: AIPerf `0.12.0`, uv `0.9.7`, managed CPython `3.12.12`

## Command

The complete isolated server command is in RUN-0012. Against that ready server:

```bash
UV_TOOL_DIR=/tmp/codex-aiperf-tools \
UV_CACHE_DIR=/tmp/codex-aiperf-uv-cache \
UV_PYTHON_INSTALL_DIR=/tmp/codex-aiperf-python \
UV_OFFLINE=1 HF_HUB_OFFLINE=1 \
QWEN_BENCHMARK_ROOT="$PWD/models/qwen3.8-27b-fp8/sglang/targets/dgx-spark/artifacts/2026-09-14T20-37-47Z-mtp" \
  models/qwen3.8-27b-fp8/sglang/targets/dgx-spark/benchmark-aiperf.sh
```

The unchanged runner issued sequential concurrency profiles 1, 2, and 4 to
`/v1/chat/completions`, with four warmups and 32 measured requests each.
Each used target input 512, fixed output 128, temperature 0, `ignore_eos=true`,
thinking disabled, streaming, server token counts, and seeds 43, 44, and 46.
The generated `inputs.json` content was compared with RUN-0010 and was identical
for each matching concurrency, not merely the same requested token lengths.

## Results

All three profiles exited 0. All 96 measured requests and 12 warmups returned
128 server-reported output tokens, without errors, cancellations, or output
length mismatches. Actual measured inputs were 524–526 tokens; output totaled
4096 tokens per measured profile.

| Concurrency | Plain FP8 aggregate tokens/s | FP8 MTP aggregate tokens/s | Speedup | Plain median latency (s) | MTP median latency (s) |
| --- | --- | --- | --- | --- | --- |
| 1 | 8.06 | 15.20 | 1.89x | 15.833 | 8.497 |
| 2 | 15.84 | 29.83 | 1.88x | 15.837 | 8.535 |
| 4 | 30.85 | 52.26 | 1.69x | 16.595 | 9.583 |

Speedup ratios use unrounded measurements. Concurrency 2 is 1.88366x (about
1.9x); concurrency 1 is 1.88531x. Aggregate throughput includes prefill and all
requests over the measured window. It is distinct from per-user decode speed.

| Concurrency | MTP TTFT p50 / p95 (ms) | MTP request latency p50 / p95 (s) | ITL mean (ms) | Per-user decode tokens/s (mean) | Requests/s | Measured duration (s) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 359.11 / 362.89 | 8.497 / 9.262 | 63.44 | 15.85 | 0.1188 | 269.40 |
| 2 | 514.35 / 660.51 | 8.535 / 9.836 | 62.94 | 15.99 | 0.2331 | 137.30 |
| 4 | 514.46 / 1244.13 | 9.583 / 10.942 | 70.58 | 14.28 | 0.4083 | 78.37 |

Measured UTC windows, from per-request epoch timestamps:

- Concurrency 1: 20:43:32.023–20:48:01.424.
- Concurrency 2: 20:48:24.577–20:50:41.876.
- Concurrency 4: 20:50:56.727–20:52:15.099.

AIPerf's display/aggregate time strings are local Europe/London without offsets;
the above values are UTC. The artifact directory timestamp denotes server start.

## Speculative Decoding Evidence

Startup loaded `Qwen3_5ForCausalLMMTP` from the same FP8 snapshot. Runtime decode
logs contain draft acceptance lengths and rates. A post-run `/metrics` snapshot
reported steps 3, draft tokens 4, `spec_verify_calls_total=5100`,
`spec_accept_length=2.816993`, and `spec_accept_rate=0.605664`.
The acceptance gauges are snapshots, not averages for all measured profiles;
the verify counter also includes startup, smoke requests, and warmups. They
confirm active MTP but do not isolate a benchmark-wide acceptance rate.

## Interpretation And Limits

Native MTP improved single-request aggregate throughput by about 89%, with
median 128-token response latency falling from 15.83 to 8.50 seconds. The gain
persisted at two and four simultaneous requests, though four-request per-user
decode fell to 14.28 tokens/s compared with 15.85–15.99 at lower concurrency.

This is a matched synthetic-workload comparison, not a comprehensive quality
or production capacity result. Only one profile was run per concurrency in
each mode. The baseline and MTP runs used separate server boots at different
times, without randomized order or repeated-run confidence intervals. Prefix
caching was enabled and not flushed; the runs reused kernel cache volumes.
Identical input fixtures do not guarantee identical cache behavior or output
text. AIPerf again warned that prompt-cache read token fields were absent.

Thinking was disabled and output length forced to 128. MTP acceptance and speed
depend on generated content. Long-context, multimodal, reasoning-enabled,
natural-stopping, and quality-equivalence evaluations were not performed.
RUN-0012's four smoke checks establish only small-fixture correctness; no
token-for-token comparison with ordinary decoding was performed.

MTP consumed extra draft and intermediate state memory, reducing target KV
capacity from 341648 to 221044 slots under the unchanged 0.45 allocation. That
tradeoff was harmless for this short workload; full-context concurrency remains
unqualified. Qwen was the only running model container. Continuous GPU
telemetry was not collected; the sparse metric queries were diagnostic only.

## Verification, Shutdown Observation, And Artifacts

Audited all three aggregate exports and all 108 per-request records. Verified
request counts, output counts, no cancellations/errors, the thinking override,
and identical generated inputs versus RUN-0010. The final health probe passed;
Docker reported healthy, no OOM kill, and zero restarts. No errors, exceptions,
tracebacks, failed operations, or HTTP 4xx/5xx matched the benchmark runtime log.

Restored the initially idle GPU after saving the benchmark:

```bash
docker stop --timeout 120 inferpack-qwen38-fp8-mtp-bench
docker inspect --format 'status={{.State.Status}} exit={{.State.ExitCode}} oom={{.State.OOMKilled}} restarts={{.RestartCount}}' inferpack-qwen38-fp8-mtp-bench
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
```

The intentional stop emitted the same shutdown exception chain as RUN-0011:

```text
tokenizer_manager.py: sigterm_watchdog -> kill_process_tree
common.py: sys.exit(0)
SystemExit: 0
During handling of the above exception, another exception occurred:
starlette/routing.py: lifespan -> await receive()
asyncio.exceptions.CancelledError
```

Diagnosis: shutdown cancellation noise, not a benchmark failure. Verification
showed `status=exited exit=0 oom=false restarts=0`, with no GPU compute processes
remaining. No runtime patch was applied. Both the original container and the
isolated MTP container are stopped; weights and caches remain available.

Local, Git-ignored artifacts are under
`models/qwen3.8-27b-fp8/sglang/targets/dgx-spark/artifacts/2026-09-14T20-37-47Z-mtp/`:

- `c1/`, `c2/`, `c4/`: aggregate JSON/CSV, per-request JSONL, generated inputs,
  phase exports, and client logs; `c1.log`, `c2.log`, `c4.log` retain CLI settings.
- `summary.json` and `qwen-mtp-audit.py`: selected verified metrics and audit code.
- `qwen-mtp-smoke.py`, `qwen-mtp-smoke.json`: the startup smoke checks and responses.
- `server-runtime.log`: benchmark interval, ending before shutdown.
- `spec-metrics.prom`: post-run speculative metrics snapshot.
- `shutdown.log`: the separate intentional-stop log, including cancellation.

The model README and environment example document the optional flags; the
default stays non-speculative. No new tests were added. Shell syntax and
documentation consistency checks cover the documentation change; the live
benchmark and smoke checks provide the runtime evidence.

## Lesson

FP8 native MTP can substantially improve single-user latency without a new
target checkpoint. Confirm actual acceptance, compare identical inputs, and
report aggregate throughput, per-user decode, and memory cost separately.

## Next Step

None for this benchmark. Keep MTP opt-in until validated against the intended
quality, reasoning, context-length, and concurrency requirements.
