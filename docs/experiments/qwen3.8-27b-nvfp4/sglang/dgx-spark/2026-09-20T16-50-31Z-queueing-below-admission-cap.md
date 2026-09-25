# 2026-09-20T16:50:31Z — Queueing below the configured admission cap

Run ID: `RUN-0011`

- Status: resolved for the interpretation of transient queueing; the precise c72 admission constraint remains unconfirmed.
- Phase: offline analysis of preserved metrics; no service change or new benchmark.
- Related turns: [Performance report, RUN-0008](2026-09-20T16-28-58Z-concurrency-performance-report.md), [archive, RUN-0010](2026-09-20T16-47-13Z-artifacts-preserved-outside-git.md).
- Runtime: SGLang `0.0.0.dev1+g5f55db35e`, one DGX Spark GB10, Qwen3.8 27B NVFP4.
- Question: why do c32 and c64 have queue wait when the configured maximum is 72 running requests?

The running-request limit is a capacity ceiling. A new request must still wait
for scheduling and prompt processing. A profile's maximum running count is the
highest sampled value at any point, whereas mean queue time measures the wait
experienced by requests before they are scheduled. These are different measures
over time, not simultaneous counts to add together.

## Direct evidence

Read `server_metrics_export.jsonl` within the profiling boundaries from
`phase_manifest.json` under the preserved full-sweep directory:

```text
/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/nvfp4-admission72-full-20260920-21dGW0/
```

Selected c64 samples relative to profiling start:

| Elapsed time | Queued requests |
| ---: | ---: |
| 1.10 s | 56 |
| 5.11 s | 40 |
| 10.12 s | 13 |
| 14.12 s | 0 |

Large queues recur through the profile. For c32, the queue reaches 24 near
1.26, 24.95 and 48.63 seconds, continuing approximately every 24 seconds. For
c64, it reaches 56 near 1.10, 38.48 and 75.18 seconds, continuing approximately
every 37 seconds. The benchmark sends a fixed-concurrency workload with nearly
equal prompt lengths and exactly 128 output tokens, producing repeated waves
of new requests as earlier responses finish. Queueing is not confined to the
initial wave or to warmup.

| Profiling metric | c32 | c64 | c72 |
| --- | ---: | ---: | ---: |
| Mean queue wait | 2.25 s | 5.46 s | 6.37 s |
| Mean prefill-forward latency | 1.70 s | 1.74 s | 1.75 s |
| Maximum sampled running requests | 32 | 64 | 71 |
| Median sampled queued requests | 0 | 0 | 1 |

The zero median queue at c32 and c64 coexists with positive mean queue waits
because the queues fill and drain. Every profile has 384 queue-time observations;
the quoted means include all those recorded requests.

## Interpretation and limits

This run used a 2,048-token chunked-prefill setting and roughly 524 input tokens
per request. Scheduling a 32-request wave entails roughly 16,768 prompt tokens;
a 64-request wave entails roughly 33,536. A prompt-processing token budget and
the running-request ceiling constrain different parts of execution. The observed
gradual admission is consistent with multiple prefill scheduling steps, even
when the server has capacity to hold all requests after prompt processing.

The [SGLang argument reference](https://docs.sglang.io/docs/advanced_features/server_arguments)
documents separate running-request, chunked-prefill and prefill-batch controls.
Those definitions support the distinction; current documentation is not proof
of every scheduler detail in the recorded development build. The artifacts do
not establish an exact requests-per-prefill-step rule or isolate the effect of
the chunk setting from other scheduling constraints. Do not assume the recorded
stage means are disjoint durations that can all be added together.

The c72 result also has a persistent component: median queue length is one and
running requests peak at 71, with the previously documented long waits. The
reason for that one-request boundary remains unconfirmed and should not be
attributed to the running cap or a specific Mamba allocation rule without a
scheduler trace or controlled experiment.

## Lesson

Interpret queue latency alongside time-series queue depth and running counts.
Capacity below the configured ceiling does not imply immediate prompt
processing. A capacity peak in a summary table cannot establish that every
request began running immediately or that the server stayed at that peak.
