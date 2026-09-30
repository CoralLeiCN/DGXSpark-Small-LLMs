# 2026-09-27T15:00:27Z — MTP=2 fresh-cache normal baseline completed and stopped

Run ID: `RUN-0039`

- Status: resolved (normal baseline only; hardware diagnostics continue separately)
- Related: [Hardware-pilot runner fixes](../../../../RESOLVED_ISSUES.md#hardware-pilot-runner-fixes)
- Environment: same pinned model/image/SGLang/AIPerf as RUN-0035; repo f3f1d2e plus local scripts and documentation
- Artifacts: [complete archive](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T13-56-21Z-mtp2-hardware-pilot/)

All nine normal trials passed: concurrency 1, 8 and 64, three trials each,
64/64/192 requests per trial, 960 total. Every request completed with 128 output
tokens, and all measured prompt-cache fractions were zero. Both prompt histogram
count deltas matched the completed request counts. Seeds and input hashes match
across each concurrency's repeats. Separate warmup was excluded.

| Concurrency | SGLang estimated TFLOPS/GPU | Total output tokens/s | Mean response time (s) |
| ---: | ---: | ---: | ---: |
| 1 | 4.909 ± 0.015 | 21.808 ± 0.063 | 5.866 ± 0.017 |
| 8 | 24.043 ± 0.220 | 106.644 ± 1.071 | 9.377 ± 0.089 |
| 64 | 45.533 ± 0.060 | 202.545 ± 0.394 | 38.507 ± 0.075 |

Mean ± sample standard deviation over three trials.


SGLang TFLOPS are model-operation estimates, not measured hardware arithmetic.
Mean TTFT was 0.254/0.781/4.328 seconds at c1/c8/c64; mean queue wait was
0.00019/0.03959/2.47219 seconds. GPU activity sample means were about 95% at all
three concurrencies, which does not establish compute or memory saturation.

The original c1 trial1 was retained from baseline-v2 after its checker failed;
remaining trials followed a same-configuration restart and rewarm. Treat the
three-trial variability as descriptive, with this restart/thermal caveat.
The baseline container exited at 14:57:54 UTC, exit code0, OOMKilled=false.
The saved shutdown verification confirms stopped=true.

## Independent validation and retained scripts

`analyze-baseline.py ROOT ROOT/analysis/baseline` rechecked all nine exports,
per-request output lengths, cache histogram sums/counts, identical input hashes,
GPU samples in the client measurement windows and monotonic FLOPs counters.
It reproduced the table, saved per-trial CSV and aggregate/source-hash JSON,
and returned validation=passed. AIPerf text timestamps use host-local time;
analysis windows use epoch-nanosecond timestamps.

At the user's request, execution, failed-attempt, recovery, calibration and
analysis scripts are retained under
[hardware-utilization](../../../../../models/qwen3.8-27b-nvfp4/sglang/targets/dgx-spark/experiments/hardware-utilization/README.md).
Raw artifacts remain outside Git. The source manifest links snapshots to their
archived originals. A read-only inspection attempted a nonexistent top-level
`server_args` field in get_server_info and raised KeyError after printing the
validated results; this did not affect inference or saved analysis.

## Next step

Separate Nsight diagnostics started after baseline shutdown. Their startup
reported a missing NVTX Python package; that attempt was stopped before capture,
and dependency qualification/recovery will be recorded separately. Normal
performance results above do not include profiler overhead.
