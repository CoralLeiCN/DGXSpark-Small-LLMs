# 2026-09-05T21:23:15Z — Service removed despite shutdown cleanup traceback

Run ID: `RUN-0003`

- Status: workaround
- Phase: container shutdown
- Related turns: [Gemma text API qualified on DGX Spark](2026-09-05T21-22-36Z-text-api-qualified.md)
- Repo revision: `4fe8345` plus uncommitted Gemma recipe and journal changes
- Host/GPU: DGX Spark, NVIDIA GB10, ARM64, 124610 MiB unified memory reported by PyTorch, Linux `6.17.0-1031-nvidia`
- Container: `dgxspark/gemma-4-26b-a4b-it-sglang:0.1.0` (`sha256:1ea5c92343e3caba5f9c71face3c97845779052d6ebf564aeff516ea8e30fe02`)
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, PyTorch `2.13.0+cu130`, Transformers `5.12.1`, CUDA 13.0
- Model: `google/gemma-4-26B-A4B-it`, revision `4d7ae4984b7db7de8f8457170b3f1a419ee76d52`, BF16

## Command

```bash
scripts/stop google/gemma-4-26b-a4b-it --engine sglang
scripts/status google/gemma-4-26b-a4b-it --engine sglang
curl --max-time 2 http://127.0.0.1:30000/health
```

## Error Or Observation

```text
SIGTERM received. Draining requests and shutting down...
Gracefully exiting... Remaining number of requests 0.
Warning: destroy_process_group() was not called before program exit
ERROR: ... sigterm_watchdog ... kill_process_tree ... sys.exit(0)
SystemExit: 0
... starlette/routing.py ... asyncio.exceptions.CancelledError
```

Compose nevertheless stopped and removed the container and its network. The
service list was empty, port 30000 no longer responded, and the SGLang and
Triton named volumes remained available for a future warm start.

## Diagnosis

- Symptom: normal Compose shutdown produced an NCCL cleanup warning and an
  application-level error traceback after requests had drained.
- Root cause: current hypothesis is cleanup ordering in this SGLang development
  build. Its SIGTERM watchdog calls `kill_process_tree`, which raises the shown
  successful `SystemExit: 0` while Starlette's lifespan task is being cancelled;
  the process exits before PyTorch observes an explicit process-group destroy.
- Evidence: the traceback originates in `sigterm_watchdog`; the log reported
  zero remaining requests before the stack; Compose completed removal; the
  container was absent afterward; and the host endpoint was closed.

## Fix Or Change

No runtime patch was attempted because shutdown achieved the requested external
state and changing SGLang signal handling is outside this model recipe's scope.
The operational workaround is to verify container removal and port closure
rather than treating this development build's cleanup traceback as proof that
the service is still running.

## Verification

```text
Compose status: no services listed
Gemma container: stopped and removed
Gemma endpoint: unavailable as expected
Retained volumes:
  dgxspark-gemma-4-26b-a4b-it_sglang-cache
  dgxspark-gemma-4-26b-a4b-it_triton-cache
```

## Lesson

Audit shutdown at both layers: preserve engine cleanup warnings for upstream
compatibility work, but separately verify the container, port, and GPU-serving
state. `SystemExit: 0` inside a cancelled lifespan task can be logged as an
error even when Compose removal succeeds.

## Next Step

None for the requested deployment qualification. Recheck SGLang shutdown
cleanup behavior when moving to a newer pinned runtime image.
