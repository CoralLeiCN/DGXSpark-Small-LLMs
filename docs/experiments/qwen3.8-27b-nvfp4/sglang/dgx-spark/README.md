# Qwen3.8 27B NVFP4 — SGLang — DGX Spark Experiment Journal

Deployment recipe: [`models/qwen3.8-27b-nvfp4/sglang/targets/dgx-spark/`](../../../../../models/qwen3.8-27b-nvfp4/sglang/targets/dgx-spark/)

**2026-09-20 NVFP4 benchmark baseline: MTP disabled (non-speculative decoding).**
All completed 2026-09-20 profiles, including the c1–c72 sweep, recorded
`sglang:spec_num_steps=0`. FP8 MTP results belong to the separate FP8 journal.
The separate 2026-09-25 MTP=2 round uses two drafting steps and three verification
positions; all ten profiles completed successfully, and its service was stopped
in `RUN-0015`. The MTP=3 then MTP=1 suite is documented in `RUN-0016`, with
three trials per concurrency, common admission64, and automatic service shutdown.
Consult its [external status file](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-26T00-12-44Z-mtp1-mtp3/status.json)
and subsequent entries for progress and final outcomes.

All four configurations completed, and the experiment services and monitor
stopped. The [September 26 comparison, RUN-0026](2026-09-26T08-06-38Z-mtp-disabled-1-2-3-final-report.md)
covers the original 80 measured trials, including cache effects and configuration differences.

An additional [MTP=2 round, RUN-0027](2026-09-27T11-01-08Z-mtp2-aligned-launch.md)
aligns its sampling, admission64, and repeated-prompt procedure with the completed
MTP=1/3 rounds. Its [external status](</home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T10-59-11Z-mtp2-aligned/status.json>)
and subsequent entries track qualification, measured trials, and automatic shutdown.
First/repeat passes retain separate cache measurements; pooled means are descriptive.

The aligned MTP=2 round completed all 30 measured trials and stopped its service
and monitor. The [updated final summary, RUN-0033](2026-09-27T13-24-43Z-final-aligned-mtp-summary.md)
uses the new MTP=2 results in a 100-trial comparison. MTP=3 had the fastest observed
means at c1–c8, MTP=2 at c16–c48, and the historical disabled baseline at c64–c72.
The close MTP peaks and different cache conditions do not establish a universal winner.

Runs recorded: 33

Next run ID: `RUN-0034`

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
| `RUN-0012` | 2026-09-25T20:16:53Z | resolved | [MTP=2 preflight: native head, host access, and memory budget](2026-09-25T20-16-53Z-mtp2-preflight.md) |
| `RUN-0013` | 2026-09-25T20:18:18Z | workaround | [Native MTP=2 text checks passed; older launcher limited admission to 69](2026-09-25T20-18-18Z-mtp2-startup.md) |
| `RUN-0014` | 2026-09-25T20:24:59Z | open | [MTP=2: admission 72 and metric exports qualified; full sweep started](2026-09-25T20-24-59Z-mtp2-c72-round.md) |
| `RUN-0015` | 2026-09-26T00:25:10Z | resolved | [NVFP4 MTP=2: all ten profiles completed and service stopped](2026-09-26T00-25-10Z-mtp2-sweep-completed.md) |
| `RUN-0016` | 2026-09-26T00:25:10Z | open | [NVFP4 MTP=1/3: matched protocol and unattended shutdown](2026-09-26T00-25-10Z-mtp13-suite-launch.md) |
| `RUN-0017` | 2026-09-26T00:25:34Z | resolved | [NVFP4 MTP=3: API and three-trial telemetry qualified](2026-09-26T00-25-34Z-mtp3-qualified.md) |
| `RUN-0018` | 2026-09-26T00:35:32Z | resolved | [NVFP4 MTP=1/3: 30-minute status monitor configured](2026-09-26T00-35-32Z-mtp13-30min-monitor.md) |
| `RUN-0019` | 2026-09-26T01:36:19Z | resolved | [NVFP4 MTP=3: full three-trial concurrency sweep completed](2026-09-26T01-36-19Z-mtp3-sweep-complete.md) |
| `RUN-0020` | 2026-09-26T01:43:10Z | resolved | [NVFP4 MTP=1: API and three-trial telemetry qualified](2026-09-26T01-43-10Z-mtp1-qualified.md) |
| `RUN-0021` | 2026-09-26T03:02:55Z | resolved | [NVFP4 MTP=1: full three-trial concurrency sweep completed](2026-09-26T03-02-55Z-mtp1-sweep-complete.md) |
| `RUN-0022` | 2026-09-26T03:03:11Z | resolved | [NVFP4 MTP=1/3 suite ended and shutdown was checked](2026-09-26T03-03-11Z-mtp13-suite-ended.md) |
| `RUN-0023` | 2026-09-26T03:04:44Z | resolved | [NVFP4 MTP=1/3: final monitor and shutdown check](2026-09-26T03-04-44Z-mtp13-monitor-finished.md) |
| `RUN-0024` | 2026-09-26T06:54:00Z | resolved | [NVFP4 MTP=1 results and repeated-trial cache effects](2026-09-26T06-54-00Z-mtp1-results-cache-assessment.md) |
| `RUN-0025` | 2026-09-26T08:06:38Z | resolved | [Offline MTP comparison: source layout and missing-counter handling](2026-09-26T08-06-38Z-mtp-comparison-analysis-preflight.md) |
| `RUN-0026` | 2026-09-26T08:06:38Z | resolved | [Final NVFP4 performance report: MTP disabled, MTP=1, MTP=2, MTP=3](2026-09-26T08-06-38Z-mtp-disabled-1-2-3-final-report.md) |
| `RUN-0027` | 2026-09-27T11:01:08Z | open | [NVFP4 MTP=2: align exploratory sampling with MTP=1/3](2026-09-27T11-01-08Z-mtp2-aligned-launch.md) |
| `RUN-0028` | 2026-09-27T11:05:54Z | resolved | [NVFP4 MTP=2: API and three-trial telemetry qualified](2026-09-27T11-05-54Z-mtp2-qualified.md) |
| `RUN-0029` | 2026-09-27T11:07:37Z | resolved | [NVFP4 aligned MTP=2: startup, telemetry and initial inputs verified](2026-09-27T11-07-37Z-mtp2-aligned-startup-verification.md) |
| `RUN-0030` | 2026-09-27T12:18:09Z | resolved | [NVFP4 MTP=2: full three-trial concurrency sweep completed](2026-09-27T12-18-09Z-mtp2-sweep-complete.md) |
| `RUN-0031` | 2026-09-27T12:18:25Z | resolved | [NVFP4 aligned MTP=2 sweep ended and shutdown was checked](2026-09-27T12-18-25Z-mtp2-aligned-suite-ended.md) |
| `RUN-0032` | 2026-09-27T12:18:25Z | resolved | [NVFP4 aligned MTP=2: final monitor and shutdown check](2026-09-27T12-18-25Z-mtp2-aligned-monitor-finished.md) |
| `RUN-0033` | 2026-09-27T13:24:43Z | resolved | [Final NVFP4 summary with aligned MTP=2](2026-09-27T13-24-43Z-final-aligned-mtp-summary.md) |
