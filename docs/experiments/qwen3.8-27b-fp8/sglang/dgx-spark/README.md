# Qwen3.8 27B FP8 — SGLang — DGX Spark Experiment Journal

Deployment recipe:
[`models/qwen3.8-27b-fp8/sglang/targets/dgx-spark/`](../../../../../models/qwen3.8-27b-fp8/sglang/targets/dgx-spark/)

Follow the [journal guide](../../../README.md). Each row links to one immutable
experiment turn; later turns link back to the observations they continue.

Runs recorded: 21

Next run ID: `RUN-0022`

| Run ID | Time (UTC) | Status | Outcome |
| --- | --- | --- | --- |
| `RUN-0001` | 2026-09-04T00:19:32Z | open | [Cold download exceeded the health-check grace period](2026-09-04T00-19-32Z-cold-download-health-timeout.md) |
| `RUN-0002` | 2026-09-04T01:15:47Z | resolved | [Host API passed after retry outside the network sandbox](2026-09-04T01-15-47Z-host-api-validation.md) |
| `RUN-0003` | 2026-09-04T08:42:53Z | resolved | [API connection reset during warm-cache startup](2026-09-04T08-42-53Z-api-reset-during-startup.md) |
| `RUN-0004` | 2026-09-07T12:40:39Z | open | [Concurrent model startup distorts available cache budget](2026-09-07T12-40-39Z-concurrent-start-memory-profiling.md) |
| `RUN-0005` | 2026-09-07T12:47:42Z | resolved | [Sequential startup qualifies 45 percent allocation](2026-09-07T12-47-42Z-reduced-memory-qualified.md) |
| `RUN-0006` | 2026-09-14T19:47:23Z | resolved | [Benchmark GPU inspection requires host access](2026-09-14T19-47-23Z-benchmark-host-preflight.md) |
| `RUN-0007` | 2026-09-14T19:49:45Z | resolved | [Reuse cached AIPerf after sandbox DNS failure](2026-09-14T19-49-45Z-aiperf-offline-client.md) |
| `RUN-0008` | 2026-09-14T19:52:51Z | workaround | [Warm-cache startup qualified for benchmarking](2026-09-14T19-52-51Z-benchmark-startup-qualified.md) |
| `RUN-0009` | 2026-09-14T19:54:00Z | open | [AIPerf offline tokenizer rejects filesystem paths](2026-09-14T19-54-00Z-aiperf-offline-tokenizer-path.md) |
| `RUN-0010` | 2026-09-14T20:12:03Z | resolved | [Streaming concurrency baseline qualified](2026-09-14T20-12-03Z-aiperf-concurrency-baseline.md) |
| `RUN-0011` | 2026-09-14T20:12:24Z | resolved | [Benchmark shutdown emits cancellation traceback](2026-09-14T20-12-24Z-benchmark-shutdown-cleanup.md) |
| `RUN-0012` | 2026-09-14T20:42:56Z | workaround | [Native FP8 MTP startup and API smoke checks qualified](2026-09-14T20-42-56Z-fp8-mtp-startup-qualified.md) |
| `RUN-0013` | 2026-09-14T20:53:32Z | resolved | [Native FP8 MTP improves the matched concurrency baseline](2026-09-14T20-53-32Z-fp8-mtp-concurrency-benchmark.md) |
| `RUN-0014` | 2026-09-14T21:08:33Z | resolved | [Expanded MTP server qualifies for a concurrency sweep](2026-09-14T21-08-33Z-mtp-capacity64-startup.md) |
| `RUN-0015` | 2026-09-14T21:28:07Z | resolved | [MTP throughput growth slows near 64 active requests](2026-09-14T21-28-07Z-mtp-concurrency-sweep-through64.md) |
| `RUN-0016` | 2026-09-14T21:33:38Z | resolved | [MTP server qualifies for 96-request capacity comparisons](2026-09-14T21-33-38Z-mtp-capacity96-startup.md) |
| `RUN-0017` | 2026-09-14T21:55:45Z | resolved | [Matched profiles bracket the MTP throughput peak near 64](2026-09-14T21-55-45Z-mtp-throughput-peak-bracket.md) |
| `RUN-0018` | 2026-09-14T22:06:18Z | resolved | [Intermediate concurrency checks retain the peak at 64](2026-09-14T22-06-18Z-mtp-throughput-refinement.md) |
| `RUN-0019` | 2026-09-14T22:17:48Z | resolved | [Repeated profiles select 64 requests for peak MTP throughput](2026-09-14T22-17-48Z-mtp-throughput-peak-confirmed.md) |
| `RUN-0020` | 2026-09-14T22:30:07Z | resolved | [Input throughput and API-equivalent value of the measured peak](2026-09-14T22-30-07Z-token-rates-api-value.md) |
| `RUN-0021` | 2026-09-14T22:33:51Z | resolved | [DGX Spark hosted API and rental price references](2026-09-14T22-33-51Z-spark-hosted-api-pricing.md) |
