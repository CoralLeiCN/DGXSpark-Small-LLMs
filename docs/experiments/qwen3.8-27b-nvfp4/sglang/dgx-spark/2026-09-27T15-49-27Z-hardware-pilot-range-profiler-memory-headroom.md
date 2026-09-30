# 2026-09-27T15:49:27Z — Hardware pilot: application-range profiler OOM and diagnostic memory headroom

Run ID: `RUN-0044`

- Status: open (reduced static-memory diagnostic retry starting)
- Phase: model startup, health validation, profiling memory overhead
- Related: [calibrated application-range mode](2026-09-27T15-40-46Z-hardware-pilot-application-range-calibration.md)
- Environment: [hardware-pilot environment](../../../../RESOLVED_ISSUES.md#hardware-pilot-runner-fixes); diagnostic image7c694cc21488 with NVTX/shape instrumentation
- Artifacts: [archive](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T13-56-21Z-mtp2-hardware-pilot/)

The first application-range inference server (ncu-fp4-v5) completed most startup
but reported only0.56–0.61GiB free when Triton kernels were device-loaded after
serving began. Health remained503 during qualification. Docker then confirmed:

```text
OOMKilled: true
ExitCode: 9
FinishedAt: 2026-09-27T15:44:25.859762271Z
```

The driver detected the stopped server at15:44:30UTC, halted the remaining
sequence and verified cleanup. No successful inference capture from this
attempt is claimed. Commands, server logs, profiler log and state remain in
profiles/ncu-fp4-v5/. This is an observed memory-exhaustion failure, unlike the
intentional interruption in RUN-0043.

## Recovery protocol

The diagnostic retry reduces MEM_FRACTION_STATIC from0.90 to0.75 to reserve
space for the range profiler and startup/kernel allocations on shared-memory
GB10. It preserves weights, revision, precision, MTP2/top-k1/three positions,
requested admission64, explicit256 Mamba slots and all workload settings.
Actual admission must still be64 before any client runs; actual cache capacity
and memory allocation must be reported as profiling-specific differences.
This is not a replacement normal benchmark or a matched client-performance run.
The normal960-request results remain unchanged at static fraction0.90.

profiles-v6.py and orchestrate-v7.py use new profiles/<mode>-v6 output paths and
new containers, while retaining the one-pass whole-range calibration and actual
shape checks. Unit nvfp4-hw-pilot-profiles-v7-20260927.service began after the
previous container's stopped state was verified. At this entry startup is still
underway; readiness and the intended64-request admission have not yet passed.

For context, saved baseline-v3 server-info reports391869 KV tokens,11.959GB
KV storage and9.307GB startup availability. The Systems diagnostic reported
343661 KV tokens. Identical static settings did not guarantee identical pool
capacity under instrumentation, so final analysis must use each saved readback.

Lesson: profile memory overhead is part of the experiment configuration. On
unified-memory hardware, qualify headroom and actual admission, retain the
unprofiled performance baseline, and disclose diagnostic cache-budget changes.
