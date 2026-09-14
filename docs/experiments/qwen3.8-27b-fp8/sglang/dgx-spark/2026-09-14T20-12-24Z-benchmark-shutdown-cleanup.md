# 2026-09-14T20:12:24Z — Benchmark shutdown emits cancellation traceback

Run ID: `RUN-0011`

- Status: resolved (container stopped; shutdown log noise remains)
- Phase: container shutdown
- Related turns: [completed benchmark](2026-09-14T20-12-03Z-aiperf-concurrency-baseline.md)
- Repo revision: `17d39b06860ea7159a3d4a3443053b4d79bf867e`, dirty with benchmark files
- Host/GPU: DGX Spark, Linux aarch64, GB10; driver `580.173.02`
- Container: `dgxspark/qwen3.8-27b-fp8-sglang:0.1.0`, image
  `sha256:3c11adf54d4a220f587f361f48eee66b50a8e2b8c068db7484c598beb3684b62`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, torch `2.13.0+cu130`, transformers `5.12.1`
- Model: `Qwen/Qwen3.8-27B-FP8`, revision
  `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`

## Command

```bash
docker stop --timeout 120 dgxspark-qwen3-8-27b-fp8-sglang-1
docker logs --since 2026-09-14T20:12:03Z --tail 20 dgxspark-qwen3-8-27b-fp8-sglang-1
```

## Error Or Observation

Shutdown emitted a traceback after SIGTERM:

```text
tokenizer_manager.py, in sigterm_watchdog
    kill_process_tree(os.getpid(), include_parent=True)
common.py, in kill_process_tree
    sys.exit(0)
SystemExit: 0
During handling of the above exception, another exception occurred:
starlette/routing.py, in lifespan
    await receive()
asyncio.exceptions.CancelledError
```

## Diagnosis

The traceback belongs to intentional process and ASGI lifespan cancellation
during shutdown. Docker stop succeeded, the container exited 0, no OOM kill or
restart occurred, and no GPU compute process remained. The completed benchmark
had no runtime error matches before shutdown. This is shutdown cleanup log
noise, not failed inference or failed container termination.

## Fix Or Change

No runtime patch was applied. Stopped the container started for this benchmark,
restoring the original idle state. Retained the container, image, model weights,
caches, and benchmark artifacts.

## Verification

```bash
docker inspect --format 'status={{.State.Status}} exit={{.State.ExitCode}} oom={{.State.OOMKilled}} restarts={{.RestartCount}}' dgxspark-qwen3-8-27b-fp8-sglang-1
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
```

Observed `status=exited exit=0 oom=false restarts=0`. The GPU compute-process
query returned only its header.

## Lesson

Correlate shutdown tracebacks with exit status, OOM/restart state, and remaining
processes before classifying them as inference failures. Keep post-benchmark
shutdown diagnostics separate from measured runtime logs.

## Next Step

None for the benchmark; shutdown traceback suppression remains an upstream
runtime behavior rather than a recipe fix.
