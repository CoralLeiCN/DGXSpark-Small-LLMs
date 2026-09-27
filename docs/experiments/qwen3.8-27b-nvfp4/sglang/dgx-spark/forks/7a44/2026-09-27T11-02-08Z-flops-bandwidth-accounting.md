# 2026-09-27T11:02:08Z — NVFP4: estimated FLOPs and memory-bandwidth measurement limits

Run ID: `RUN-0027`

- Status: resolved
- Phase: inference / benchmark / lifecycle
- Repo revision: `89611e1`, dirty with experiment documentation
- Host/GPU: DGX Spark, NVIDIA GB10, driver `580.173.02`, aarch64
- Image: `sha256:110ad45e7872397f337ea5714e6c97c400852938a9b8f258bcc27cab07182b0c`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`; AIPerf `0.12.0`, Python 3.12
- Model: `nvidia/Qwen3.8-27B-NVFP4`, revision `482ca0f3832238542f8f5295dde86b5f22711d80`
- Artifacts: [2026-09-27T11-00-03Z-mtp2-aligned](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T11-00-03Z-mtp2-aligned/)
- Related turns: [MTP=2 launch](../../2026-09-25T20-24-59Z-mtp2-c72-round.md); see this target index for the MTP=1/3 launch and subsequent events.

## Scope and evidence

Offline inspection of all 80 completed trial exports and the pinned SGLang source.
No inference was run for this audit. Reproducible script, source copy, per-trial
metric inventories, counter endpoints, and source SHA256 values are preserved in
[metric-accounting-audit](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T11-00-03Z-mtp2-aligned/metric-accounting-audit/). This follows RUN-0026 without modifying historical files.

## Findings

The decode reporting path calls its estimate with `batch_size + num_correct_drafts`.
The formula applies model-shape constants to these tokens and context lengths.
It does not explicitly account for every separate draft forward or rejected target
verification position. Prefill charges newly processed token lengths. This is a
model-work estimate, not measured GPU arithmetic or complete speculative cost;
its bias is not established as a uniform undercount for this hybrid architecture.

Physical DRAM bytes/s is not present in these exports. The NVML memory-activity
series is identically zero in 80 of 80 trials.
That is an inconclusive telemetry observation, not proof of no memory traffic.
NVIDIA defines this field as activity time, not the fraction of peak byte bandwidth.

SGLang estimated read/write-byte counters are present. Their implementation uses
server dtype sizes and a per-token weight-read charge. It does not model packed
NVFP4 weights or shared weight reads across tokens. For the disabled c64 trial,
estimated reads/time is 49,351.14 GB/s; for MTP=3 c48 trial3 it is 15,296.54 GB/s.
These are clearly not physical traffic through a 273 GB/s memory interface.
Do not normalize them against Spark bandwidth or infer bandwidth headroom from
estimated TFLOPS, output tokens/s, resident model size, or GPU-busy percentage.

## Interpretation and follow-up

The measured throughput plateau means increased concurrency stopped improving
this serving workload. It does not establish that DRAM bandwidth was saturated.
Actual bandwidth/headroom remains unknown. A separate supported hardware-counter
profile, distinguishing prefill and decode and reporting profiler overhead, would
be needed. No intrusive profiler or extra benchmark was started for this audit.
The shared benchmarking guide now explicitly records this metric distinction.

Sources checked September 27, 2026:
- [NVIDIA NVML utilization](https://docs.nvidia.com/deploy/nvml-api/api/structnvmlUtilization__t.html)
- [NVIDIA Spark hardware](https://docs.nvidia.com/dgx/dgx-spark/hardware.html)
- [NVIDIA Nsight Compute profiling](https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html)

Lesson: preserve raw software estimates, but verify their accounting before
using them to claim physical compute or memory utilization.
