# 2026-09-14T22:17:48Z — Repeated profiles select 64 requests for peak MTP throughput

Run ID: `RUN-0019`

- Status: resolved
- Phase: inference / runtime shutdown
- Related turns: [Refinement](2026-09-14T22-06-18Z-mtp-throughput-refinement.md),
  [matched comparison](2026-09-14T21-55-45Z-mtp-throughput-peak-bracket.md),
  [server configuration](2026-09-14T21-33-38Z-mtp-capacity96-startup.md)
- Repo revision: `17d39b06860ea7159a3d4a3443053b4d79bf867e`, dirty
- Host/GPU: one DGX Spark GB10, Linux aarch64, driver `580.173.02`
- Container: `inferpack-qwen38-fp8-mtp-capacity96`, image
  `dgxspark/qwen3.8-27b-fp8-sglang:0.1.0`, ID
  `sha256:3c11adf54d4a220f587f361f48eee66b50a8e2b8c068db7484c598beb3684b62`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, FlashInfer `0.6.17`,
  torch `2.13.0+cu130`, transformers `5.12.1`
- Model: `Qwen/Qwen3.8-27B-FP8`, revision
  `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`

## Command And Conditions

Continued on the unchanged RUN-0016 server: FP8 native MTP EAGLE three steps /
top-k one / four draft tokens, memory fraction 0.85, active cap 96, Mamba slots
384, graph maximum 96, context 32768, prefill chunk 2048, BF16 KV/GDN state.
AIPerf 0.12.0 ran through uv-managed Python 3.12.12 using the same offline
client environment as RUN-0017.

```bash
export QWEN_REQUEST_COUNT=384 QWEN_WARMUP_COUNT=96
pack=models/qwen3.8-27b-fp8/sglang/targets/dgx-spark
for concurrency in 56 64; do
  curl --fail --silent --show-error -X POST 'http://127.0.0.1:30000/flush_cache?timeout=30'
  export QWEN_SEED_BASE=$((5000 - concurrency))
  export QWEN_BENCHMARK_ROOT="$pack/artifacts/2026-09-14T22-06-18Z-capacity96-repeat-c$concurrency"
  "$pack/benchmark-aiperf.sh" "$concurrency"
done
```

Both idle-cache flushes succeeded. Workload: streaming chat, 512 target input
tokens / 128 forced output tokens, temperature zero, thinking disabled. Actual
input lengths were 523–526. The two seed-5000 input files were byte-identical,
SHA256 `5e7f6d734f3a13cd9e289816a469646aba31993938dd39052fab0ca59aa45fa3`,
and their measured conversation-ID multisets matched. These are fresh inputs
relative to the seed-3000 pair. Relative execution order was reversed.

## Results

| Concurrency | Seed 3000 output tokens/s | Seed 5000 output tokens/s | Mean output tokens/s | Pooled median / p95 latency (s) | Pooled median / p95 TTFT (s) |
| --- | --- | --- | --- | --- | --- |
| 56 | 204.78 | 203.26 | 204.02 | 34.68 / 45.40 | 2.15 / 12.18 |
| 64 | 207.79 | 206.91 | **207.35** | 39.07 / 50.93 | 2.37 / 14.35 |

Each seed/concurrency cell represents 384 measured requests after 96 warmups.
Means are arithmetic means of the reported aggregate throughputs. Pooled
latency quantiles use all 768 measured request records at that concurrency.
Aggregate throughput includes measured-phase ramp-up and drain; it is not a
decode-only or infinite-duration steady-state rate.

The larger matched sweep (seed 3000, same server) was:

| Concurrency | Output tokens/s |
| --- | --- |
| 48 | 199.10 |
| 56 | 204.78 |
| 64 | **207.79** |
| 72 | 200.75 |
| 80 | 195.90 |
| 96 | 172.49 |

## Verification And Decision

All 768 new measured requests and 192 warmups passed without errors or
cancellations, with exactly 128 reported and measured completion tokens.
Across the complete capacity search, 15 profiles covered concurrency
4, 8, 16, 24, 32, 48, 56, 64, 72, 80, and 96, including repeated settings:
**4,032 measured requests and 964 warmups passed**. The four startup smoke
checks on each of the two capacity servers are additional to those counts.

Repeated client median effective concurrency equalled 56 and 64. Sampled
server active medians were 56 and 63, with zero median queue depth. Monitor
collection had no errors; sampled cache-hit rates were zero and acceptance
length medians approximately 2.75 and 2.74. Minimum sampled available host
memory in the repeat measured phases was 12,793 MiB. Runtime log inspection
found no inference traceback, CUDA error, or OOM; the earlier startup readiness
503 is already recorded in RUN-0016.

Select **64 client requests in flight** when maximizing throughput for this
tested FP8 MTP workload: it won both paired seeds and averaged 207.35 output
tokens/s. Treat 56–64 as a broad practical top, with 56 giving about 1.6% less
throughput and 11% lower pooled median latency. This is the best tested setting,
not proof of a unique optimum among every integer concurrency. Larger tested
batches reduced throughput. Other prompt/output lengths, reasoning modes,
decoding methods, and full-context workloads require their own sweeps.

The exact reproduced server retained cap 96 / Mamba 384 / memory 0.85 / graph
maximum 96. The initial cap-64 / Mamba-256 / memory-0.80 / graph-64 server
separately achieved 204.16 tokens/s at concurrency 64 in RUN-0015; do not fold
that different configuration into the paired mean. Shared-host recipe defaults
remain unchanged. Model documentation now includes the observed curve and
dedicated-host reproduction settings.

## Shutdown And Artifacts

Stopped monitoring after all profiles completed, saved the runtime log, and ran:

```bash
docker stop -t 60 inferpack-qwen38-fp8-mtp-capacity96
docker inspect --format '{{.State.ExitCode}} {{.State.OOMKilled}}' inferpack-qwen38-fp8-mtp-capacity96
nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory --format=csv
docker ps --format '{{.Names}} {{.Status}}'
```

The shutdown-only `SystemExit: 0` / `asyncio.exceptions.CancelledError` recurred
as in RUN-0011. Docker reported `0 false`; the GPU query listed no compute
processes and Docker listed no running containers. The original idle service
state was restored. No shutdown fix was required for completed inference.

The ignored shared server artifact directory
`artifacts/2026-09-14T21-28-17Z-capacity96-server/` contains `coarse.json`,
`refined.json`, `repeat.json`, `final-comparison.json`, monitor samples,
startup/runtime/shutdown logs, cache-flush confirmations, and copies of the
smoke, sweep, refinement, repeat, audit, and collection scripts. Raw exports
and generated inputs remain in their separate profile directories.

## Lesson And Next Step

Search beyond the apparent maximum, refine around the turnover, then repeat
the strongest candidates with matched fresh inputs. Report total throughput
and latency separately, and preserve the exact serving configuration.

Next step: none for this short-workload concurrency search.
