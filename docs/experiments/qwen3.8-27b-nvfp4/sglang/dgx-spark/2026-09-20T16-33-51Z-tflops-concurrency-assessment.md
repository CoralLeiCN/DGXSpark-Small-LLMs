# 2026-09-20T16:33:51Z — Concurrency assessment including SGLang estimated TFLOPS

Run ID: `RUN-0009`

- Status: resolved.
- Phase: offline analysis of existing inference artifacts; no new inference run.
- Related turn: [Full performance report, RUN-0008](2026-09-20T16-28-58Z-concurrency-performance-report.md).
- Model/engine/hardware: Qwen3.8 27B NVFP4, SGLang `0.0.0.dev1+g5f55db35e`, one DGX Spark NVIDIA GB10.
- Source sweep: `nvfp4-admission72-full-20260920-21dGW0`, 2026-09-20 12:47:55–16:12:08 UTC.
- Workload: 512 target input tokens (about 524 server-reported), 128 output tokens; 384 measured requests per concurrency, after 96 warmups.

**My assessment is that c48 offers most of the measured capacity with shorter waits, while c64 is the strongest measured choice when maximizing completed work. SGLang's estimated operation rate supports the same plateau: 45.61 TFLOPS/GPU at c48, 49.84 at c64, and 49.59 at c72. For responsive interaction, c4–c8 remains the more useful range.**

| Concurrency | SGLang est. TFLOPS/GPU | Total output tok/s | Mean decode tok/s/user | Mean first-token wait (s) | Mean completion (s) |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 2.70 | 12.03 | 12.28 | 0.30 | 10.64 |
| 2 | 5.09 | 22.63 | 11.79 | 0.53 | 11.31 |
| 4 | 9.44 | 41.97 | 11.27 | 0.92 | 12.20 |
| 8 | 16.62 | 73.90 | 10.27 | 1.48 | 13.85 |
| 16 | 26.85 | 119.37 | 8.63 | 2.39 | 17.15 |
| 32 | 38.59 | 171.96 | 6.49 | 4.08 | 23.81 |
| 48 | 45.61 | 202.79 | 5.24 | 5.72 | 30.29 |
| 56 | 47.50 | 211.19 | 4.81 | 6.49 | 33.30 |
| 64 | 49.84 | 221.74 | 4.37 | 7.39 | 36.94 |
| 72 | 49.59 | 220.49 | 4.26 | 8.31 | 39.25 |

Decode speed describes the stream after the first token and excludes the initial wait. The first-token and completion columns are means. All 3,840 measured requests succeeded; the full report separately examines slow-request percentiles and streaming pauses.

## What TFLOPS adds to the assessment

At c1–c8, estimated model-operation throughput rises from **2.70 to 16.62 TFLOPS/GPU** as batching serves more requests together. Users still average 10.27–12.28 decode tokens/s, with mean first-token waits of 0.30–1.48 seconds. Choosing lower concurrency accepts lower aggregate work in exchange for shorter waits.

At c16–c32, the rate rises to **26.85–38.59 TFLOPS/GPU**, but mean completion time reaches 17.15–23.81 seconds. This range makes sense when more completed work is worth visibly slower interaction.

At c48, **45.61 TFLOPS/GPU is about 91.5% of the c64 estimate**, alongside 91.5% of peak output throughput. Mean completion is 30.29 seconds, compared with 36.94 seconds at c64. That makes c48 a useful throughput-oriented compromise.

At c56, the estimate is **47.50 TFLOPS/GPU**, about 95.3% of c64. Output throughput is 95.2% of the measured peak. Moving from c56 to c64 gains roughly 5% throughput while increasing mean completion time by about 11%.

At c64, **49.84 TFLOPS/GPU and 221.74 output tokens/s** are the highest values observed in this sweep. At c72, both stay essentially flat—**49.59 TFLOPS/GPU and 220.49 output tokens/s**—while mean completion increases and five requests take 62.69–80.07 seconds. There is no measured throughput justification for preferring c72 here.

Because request lengths are nearly fixed, the estimated operation rate naturally tracks completed-work throughput. It provides a server-side measure consistent with the client result, rather than an independent hardware profiling diagnosis. Neither metric proves a particular compute, memory, or thermal bottleneck, and one sweep cannot establish a universal optimum.

## Metric definition and verification

The values are the profiling-window rates exported under:

```text
cN/phases/profiling/server_metrics.json
data.endpoint_summaries["127.0.0.1:30000"]
    .metrics["sglang:estimated_flops_per_gpu"].series[0].stats.rate / 1e12
```

The underlying Prometheus counter is `sglang:estimated_flops_per_gpu_total`; taking its rate and dividing by `1e12` expresses the estimated operation rate in TFLOPS/GPU. Warmup is excluded from the table.

**These are SGLang estimates of model operations per second.** They include the measured workload's prompt-processing and generation work. They are not a direct hardware FLOPS measurement, a decode-only rate, or an MFU percentage, and should not be divided by an advertised peak specification to claim hardware utilization.

All ten values were reread from the original profiling-phase server exports and matched against the [extracted CSV](2026-09-20T16-28-58Z-concurrency-performance-report/concurrency-metrics.csv). The original full report remains the source for runtime settings, methodology, latency distributions, GPU telemetry and limitations. This follow-up adds TFLOPS to the primary comparison while preserving journal chronology.

