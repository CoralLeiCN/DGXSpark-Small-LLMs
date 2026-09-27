# 2026-09-27T15:09:09Z — Hardware pilot: offline client cache path recovery

Run ID: `RUN-0041`

- Status: open (client preflight recovered; annotated profiler restarting)
- Phase: diagnostic warmup CLI environment and container cleanup
- Related: [NVTX-qualified retry](2026-09-27T15-04-30Z-hardware-pilot-nvtx-profiling-retry.md)
- Environment: same model/engine/profiler pins as RUN-0040; diagnostic image3081c11204b7; AIPerf0.12.0
- Artifacts: [archive](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T13-56-21Z-mtp2-hardware-pilot/)

The annotated server reached readiness and effective admission64. Its first
warmup failed before sending requests:

```text
uv tool run --managed-python --python3.12 --from aiperf==0.12.0 aiperf profile ...
Because aiperf was not found in the cache and you require aiperf==0.12.0 ...
Packages were unavailable because the network was disabled.
```

The diagnostic systemd launch introduced UV_CACHE_DIR=/tmp/codex-mtp2-uv-cache,
which contains the host stdlib runner environment but not the cached AIPerf tool.
The successful baseline used the existing /home/coral/.cache/uv cache.
The normal960-request results were not affected. The failed profiler container
stopped at15:07:08UTC with exit137, OOMKilled=false, after cleanup sent the server
SIGTERM; this is a shutdown result, not an observed memory-exhaustion event.
No captures were made. Original outputs remain in profiles/nsys-v2/.

Verification with UV_CACHE_DIR=/home/coral/.cache/uv and UV_OFFLINE=1 returned
AIPerf version0.12.0. profiles-v3.py now pins that client cache explicitly and
checks the exact offline client before launching the model. orchestrate-v4.py
uses fresh profiles/<mode>-v3 paths, new container names and the corrected
service environment. The NVTX-qualified image and workload remain unchanged.
The new service is nvfp4-hw-pilot-profiles-v4-20260927.service; the prior container
was verified stopped before it started. Full hardware capture validation remains
pending at this entry.

Lesson: inherited environment overrides are part of experiment reproducibility.
Qualify the client in the same environment as the durable service before paying
the cost of model startup, even when the package exists elsewhere on the host.
