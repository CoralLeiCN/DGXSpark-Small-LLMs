# 2026-09-27T14:24:57Z — Hardware pilot qualified; isolated graph profiles scheduled

Run ID: `RUN-0037`

- Status: open (normal baseline in progress)
- Related: [CLI retry](2026-09-27T14-11-53Z-hardware-pilot-warmup-cli-retry.md), [calibration](2026-09-27T14-07-18Z-hardware-counter-calibration.md)
- Artifacts: [2026-09-27T13-56-21Z-mtp2-hardware-pilot](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T13-56-21Z-mtp2-hardware-pilot/)
- Environment: same pinned image/model/SGLang/AIPerf as RUN-0035; profiler versions from RUN-0034

## Qualification verification

The v2 server passed the five API checks and its four-request c1 telemetry
preflight. Validation confirmed expected MTP steps2/verification positions3,
per-request AIPerf data, GPU utilization/temperature/power samples, and an
increasing estimated-FLOPs counter over the request window. Separate c1 warmup
completed. The first64-request measured c1 trial is in progress. No final
performance or nine-trial completion is claimed yet.

AIPerf warns that its per-request cached-token usage field is absent; the pilot
uses persisted SGLang Prometheus prompt/cached token deltas for cache verification.
This warning is not evidence of zero reuse and does not replace that check.

## Declared profiling detail and lifecycle

The durable profiler orchestrator waits for successful completion and verified
shutdown of the normal baseline. It then runs separate Nsight Systems, Nsight
Compute FP4 and Nsight Compute FP8 sessions, serially on the GPU. All use
concurrency1,8,64 only, the same pinned serving settings and independently
flushed prompt caches. They retain diagnostic AIPerf client/engine/GPU exports,
NVTX markers, clock/power samples and raw profiler reports.

Nsight Systems uses up to25seconds after load detection per capture, CUDA
profiler API boundaries, CUDA/NVTX tracing and1kHz GPU sampling. Nsight Compute
selects one scheduler iteration for prefill and one under a full running decode
batch at each concurrency, with the current CUDA graph execution retained.
The installed2025.3.1 range-replay documentation explicitly excludes graph APIs;
use kernel replay with graph-profiling=graph instead. Hardware cache flushing
and clock overrides are disabled. Each detailed session requests one precision's
Tensor Core operation count, GPU duration and the calibrated L2/system-memory
traffic proxy. FP4/FP8 are separately measured; scalar and other-precision work
must not be silently included in a claimed total.

Each diagnostic load uses max(8,3C) requests and separate max(8,C) warmup; these
short captures are declared profiling exceptions, excluded from the960-request
normal performance baseline. Full graphs reduce serialization within captured
graphs, but profiler timing/selection effects remain separate from client results.

The master records status at least every30minutes and at completion. Each driver
stops its owned container on success/error; the master has independent cleanup
and a systemd ExecStopPost fallback. Unit: nvfp4-hw-pilot-profiles-20260927.service.
Exact commands, prepared scripts and plan.json are saved outside Git.

## Additional capability and data-quality observations

The read-only SoC metric-set query lists only t234 (Tegra Orin), not a GB10 set.
The Linux PMU listing has CPU/SMMU event sources, not an identified memory-controller
source. No SoC collection or additional GPU load ran during baseline measurements.
This does not establish that future tools cannot expose GB10 DRAM counters.

The calibration Nsight Systems SQLite export has negative clock-frequency values
under MHz labels, inconsistent with meaningful clock readings. Preserve the raw
export and treat these clock fields as unusable without verified decoding; do
not assume a correction. Profiler sessions separately record nvidia-smi clocks.
Activity percentages have plausible0–100 ranges, but remain activity metrics.

## Lesson

Keep the measured normal workload stable while choosing profiling mechanisms
supported by the installed tool and the actual CUDA graph execution. Report
counter coverage and export anomalies explicitly.
