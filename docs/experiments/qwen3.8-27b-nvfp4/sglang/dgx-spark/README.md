# Qwen3.8 27B NVFP4 — SGLang — DGX Spark Experiment Journal

Deployment recipe: [`models/qwen3.8-27b-nvfp4/sglang/targets/dgx-spark/`](../../../../../models/qwen3.8-27b-nvfp4/sglang/targets/dgx-spark/)

Runs recorded: 11

Next run ID: `RUN-0012`

Preserved benchmark data and report copies:
[`$HOME/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/`](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/README.md).
The external archive is independent of Git and worktree cleanup; see `RUN-0010`
for its file inventory and integrity verification.

| Run ID | Time (UTC) | Status | Outcome |
| --- | --- | --- | --- |
| `RUN-0001` | 2026-09-16T23:43:33Z | resolved | [Initial API qualification](2026-09-16T23-43-33Z-initial-api-qualification.md) |
| `RUN-0002` | 2026-09-20T11:27:41Z | workaround | [Full sweep stopped after the c1 profile proved impractical](2026-09-20T11-27-41Z-aiperf-full-sweep-aborted.md) |
| `RUN-0003` | 2026-09-20T11:29:56Z | resolved | [72-client AIPerf profile with NVML and SGLang metrics](2026-09-20T11-29-56Z-aiperf-c72-profile.md) |
| `RUN-0004` | 2026-09-20T12:15:57Z | workaround | [Increasing the Mamba ratio raised admission only to 38](2026-09-20T12-15-57Z-mamba-ratio-c38.md) |
| `RUN-0005` | 2026-09-20T12:20:27Z | resolved | [Explicit 360-slot cache exhausted the former static-memory budget](2026-09-20T12-20-27Z-mamba-cache-static-memory-failure.md) |
| `RUN-0006` | 2026-09-20T12:25:45Z | resolved | [72-request server admission startup validation](2026-09-20T12-25-45Z-mamba-cache-c72-startup.md) |
| `RUN-0007` | 2026-09-20T12:47:55Z | resolved | [Full c1–c72 AIPerf sweep at 72-request admission](2026-09-20T12-47-55Z-aiperf-full-c1-c72.md) |
| `RUN-0008` | 2026-09-20T16:28:58Z | resolved | [Full concurrency performance report: throughput, latency, streaming pauses, and c72 tail behavior](2026-09-20T16-28-58Z-concurrency-performance-report.md) |
| `RUN-0009` | 2026-09-20T16:33:51Z | resolved | [Concurrency assessment with SGLang estimated TFLOPS in the main comparison](2026-09-20T16-33-51Z-tflops-concurrency-assessment.md) |
| `RUN-0010` | 2026-09-20T16:47:13Z | resolved | [All benchmark metrics preserved outside Git, with checksums and future output defaults](2026-09-20T16-47-13Z-artifacts-preserved-outside-git.md) |
| `RUN-0011` | 2026-09-20T16:50:31Z | resolved | [Queueing below the admission cap: repeated prompt-processing waves](2026-09-20T16-50-31Z-queueing-below-admission-cap.md) |
