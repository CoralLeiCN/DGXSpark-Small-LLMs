# 2026-09-27T15:40:46Z — Hardware pilot: replace intrusive kernel collection with calibrated application ranges

Run ID: `RUN-0043`

- Status: open (range calibration passed; inference collection restarting)
- Phase: detailed profiling overhead, mode qualification and lifecycle
- Related: [timelines and annotations](2026-09-27T15-25-54Z-hardware-pilot-timelines-and-forward-annotations.md)
- Environment: same model/engine/tool pins as RUN-0040; Nsight Compute2025.3.1, driver580.173.02
- Artifacts: [archive](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T13-56-21Z-mtp2-hardware-pilot/)

## Observed overhead and interrupted capture

The ncu-fp4-v4 session profiled a single c1 prefill iteration with kernel replay,
whole CUDA graphs, four metrics and one pass per entity. Collection advanced
through over1000 graph/kernel entities and stretched a normally subsecond step
into several minutes. Default clock/cache state could change between these
large profiler pauses, so these timings are poor evidence for ordinary inference.
The capture was deliberately stopped; its partial114MB report is preserved
and excluded from complete-step utilization claims.

The final ncu log contains `Failed to profile chunk_local_cumsum_scalar_ker...`
and `The application returned an error code (9)` after shutdown. The server
log records kill_process_tree at15:32:59UTC; no watchdog-timeout message was
found. A watchdog failure was a concern, not an observed diagnosis. Source
inspection confirmed that the scheduler's300-second watchdog is not automatically
suspended for profiling. The experiment was stopped intentionally instead.

An initial calibration guard refused to launch while the old container was
still running. An explicit docker stop --timeout30 completed shutdown before
any calibration GPU work started. This preserved serial GPU use.

## Supported alternative and calibration failures

The installed [NVIDIA profiling guide](https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html#application-range-replay)
describes application-range replay: counters cover an entire range, including
CUDA graphs, without per-kernel serialization or API capture. It differs from
range replay's API compatibility restrictions. We selected a metric set proven
to fit one pass, avoiding any inference-client replay requirement.

Two small CLI qualifications failed before GPU work:

```text
--replay-mode app-range --app-replay-buffer memory ...
Option '--app-replay-buffer' is not supported with range-based replay modes.

--replay-mode app-range --profile-from-start off ...
Option profile-from-start is not supported during range replay.
```

Both options were removed in calibrate-app-range-v3.sh. CUDA profiler start/stop
APIs delimit the range. Raw failed commands/logs and all script versions remain.

The third calibration succeeded and returned exactly137438953472 FP4 operations,
equal to2*4096^3, with profiler__replayer_passes=1. The numerical check also passed.
Its gpu__time_duration.sum was2517568ns: this includes the whole profiled range,
so the derived54.59TFLOPS is not the isolated GEMM's326TFLOPS calibration rate.
This establishes operation-count and scope correctness, not negligible boundary
overhead. Source report and extracted native-unit counters are retained.

## Diagnostic-only shape logging and restarted protocol

Application-range records need actual forward shapes separately. The qualified
NVTX bridge now appends detailed step names and epoch timestamps only while
profile annotations are active. The log-forward-shapes.py patch changes no
model arithmetic. Dockerfile.profiling-v6 built image
sha256:7c694cc214888ed37c1eba40e3be4d8e82c6516faeaf4ccb23d0833369169b92.
A no-GPU import and clearly named qualification-only marker verified JSONL
logging before model startup; that marker is not inference evidence.

profiles-v5.py records one range per prefill/decode capture, verifies one-pass
range log entries, saves actual shapes per capture, and checks for EXTEND or
TARGET_VERIFY as appropriate. It retains normal startup warmup and the declared
diagnostic request counts, with fresh prompt cache per capture. The final report
must have six single-pass ranges. Timing remains diagnostic and separate from
the completed960-request baseline.

orchestrate-v6.py runs only the remaining FP4/FP8 sessions under
nvfp4-hw-pilot-profiles-v6-20260927.service, with new profiles/<mode>-v5 paths,
30-minute records and automatic cleanup. At this entry its FP4 server is starting.

Lesson: single-pass kernel collection can still impose severe host overhead.
For whole-step utilization, qualify a supported range mode on known work, verify
its pass count and timing scope, and preserve shape/capture provenance.
