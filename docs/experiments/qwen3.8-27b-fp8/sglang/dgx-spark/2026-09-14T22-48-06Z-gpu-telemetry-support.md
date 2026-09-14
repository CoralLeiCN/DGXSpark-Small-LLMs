# 2026-09-14T22:48:06Z — DGX Spark basic GPU telemetry verified

Run ID: `RUN-0022`

- Status: resolved
- Phase: preflight
- Related turns: [host GPU inspection](2026-09-14T19-47-23Z-benchmark-host-preflight.md)
- Repo revision: `7de7cfe89bc196ed2e2921096edba7c0b0b8bc79` (clean before this record)
- Host/GPU: NVIDIA GB10 / DGX Spark, driver `580.173.02`
- Container/engine/model: none started; host-only telemetry check for this pack
- Benchmark client: recipe pins AIPerf `0.12.0`; no AIPerf profile run this turn

## Command

```bash
nvidia-smi --query-gpu=name,driver_version,temperature.gpu,utilization.gpu,utilization.memory,power.draw,power.limit,memory.used,memory.total --format=csv
```

## Error Or Observation

The sandbox attempt exited 9:

```text
NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver.
```

The identical read-only command with approved host access exited 0:

```text
name, driver_version, temperature.gpu, utilization.gpu [%], utilization.memory [%], power.draw [W], power.limit [W], memory.used [MiB], memory.total [MiB]
NVIDIA GB10, 580.173.02, 39, 0 %, 0 %, 5.04 W, [N/A], [N/A], [N/A]
```

## Diagnosis And Fix

The successful host retry identifies sandbox driver access as the initial
failure boundary; no driver or service change was needed. Temperature,
GPU utilisation, memory utilisation, and power draw are readable. This is one
idle sample, not a measurement under inference load. Memory utilisation is
an activity percentage, not allocated memory capacity.

NVIDIA documents unavailable framebuffer memory usage as expected on Spark's
integrated GPU with shared system memory:
[Spark known issues](https://docs.nvidia.com/dgx/dgx-spark/known-issues.html).

## Verification And Limits

The repeated command above verifies basic host telemetry only. NVIDIA documents
`--gpu-telemetry pynvml` for local AIPerf collection through the GPU driver:
[AIPerf telemetry guide](https://docs.nvidia.com/aiperf/tutorials/metrics-analysis/gpu-telemetry-with-ai-perf).
The checked-in runner still disables GPU telemetry and server metrics. AIPerf
collection and handling of unsupported memory fields were not exercised.
DCGM compatibility and TFLOPS measurement were not tested. TFLOPS is not one of
the basic telemetry readings; a separate model FLOP estimate or kernel profiling
is needed. No inference or health-check operation was performed.

## Lesson And Next Step

Check individual metric availability with host access before interpreting a
sandbox driver error or an unsupported memory field as absent GPU telemetry.
Before enabling telemetry in benchmark recipes, verify the pinned AIPerf NVML
collector on GB10, including its handling of unsupported memory queries.
