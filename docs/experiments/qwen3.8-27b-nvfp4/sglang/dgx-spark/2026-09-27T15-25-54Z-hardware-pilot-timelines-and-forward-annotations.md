# 2026-09-27T15:25:54Z — Hardware pilot: timelines captured; qualify detailed forward annotations

Run ID: `RUN-0042`

- Status: open (Nsight Systems complete; detailed counter collection continuing)
- Phase: hardware capture validation and profiling-only instrumentation
- Related: [offline-client recovery](2026-09-27T15-09-09Z-hardware-pilot-offline-client-cache-retry.md)
- Environment: same model/engine/profiler pins as RUN-0040; repo f3f1d2e plus local experiment files
- Artifacts: [archive](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T13-56-21Z-mtp2-hardware-pilot/)

## Completed timeline capture

profiles/nsys-v3 completed c1,c8,c64 captures and diagnostic clients (8,24,192
requests, excluded from normal performance results). Its service stopped and
all three inference.1/2/3.nsys-rep files exported successfully to SQLite.
The export validator confirmed GPU_METRICS and NVTX_EVENTS in every report.
The data includes CUDA graph activities as well as eager kernels and copies.
Union-of-intervals analysis avoids double counting overlapping activities.

| Client concurrency | Captured GPU activity span | GPU busy fraction | Tensor Active sample mean |
| --- | ---: | ---: | ---: |
| 1 | 29.670s | 98.94% | 9.65% |
| 8 | 27.138s | 99.13% | 13.88% |
| 64 | 27.837s | 99.45% | 22.26% |

These are diagnostic windows, not the full normal trials. Tensor Active is a
pipeline/activity metric, not arithmetic FLOP utilization. GPU clocks exported
under MHz labels include impossible negative values; they are excluded, while
independent nvidia-smi clock samples remain saved. No physical DRAM counter was
exposed in these captures. Do not interpret GPU busy as memory saturation.

## Annotation coverage gap and fix

Inspection found scheduler.run_batch ranges but no forward-mode/batch labels.
Pinned ModelRunner.forward calls profile_range(build_step_span_name(...))
without opting into nvtx_enabled. That helper defaults to false, so its detailed
span appears only with an active Torch profiler even when operation-NVTX is
requested. Source evidence is saved in preflight/model_runner.py and nvtx_utils.py.
This is a diagnostic coverage failure, not a failed inference request.

The already-starting ncu-fp4-v3 session was deliberately stopped before capture;
its container exited15 at15:20:55UTC, OOMKilled=false. It was verified stopped
before the replacement. Completed Nsight Systems captures are retained as valid
whole-window activity evidence; no detailed phase labels are fabricated.

The diagnostic-only enable-forward-nvtx.py patch makes profile_range's default
honor the existing NVTX_OPERATIONS_ENABLED flag. It asserts the exact pinned
source pattern and changes no model arithmetic. Dockerfile.profiling-v5 built
sha256:c53f031f6a2e3f09d633a695f19770bdd8cd282427157a803650e79293e85032
on the verified NVTX image3081c11204b7. A no-GPU container import/inspection
confirmed the default is true with the operation flag enabled. The build log
records before/after source hashes. Normal baseline and completed Systems
captures used their previously recorded images; this bridge is specific to
the remaining detailed Compute sessions.

profiles-v4.py and orchestrate-v5.py now run only ncu-fp4 and ncu-fp8, after
checking completed nsys-v3 status. The durable unit is
nvfp4-hw-pilot-profiles-v5-20260927.service; new outputs are profiles/<mode>-v4/.
At this entry ncu-fp4 is starting. Actual forward labels and counter coverage
still require verification after capture.

## Lesson

Verify the exported annotation content, not just package import and environment
flags. Record instrumentation changes separately from normal serving behavior;
retain useful partial coverage without presenting it as complete phase attribution.
