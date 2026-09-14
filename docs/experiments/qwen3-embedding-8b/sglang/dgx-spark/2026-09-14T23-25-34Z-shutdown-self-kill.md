# 2026-09-14T23:25:34Z — Exit 137 follows upstream self-kill after draining

Run ID: `RUN-0004`

- Status: resolved (diagnosed upstream shutdown behaviour)
- Phase: container shutdown / source inspection
- Related turns: [live MFU validation](2026-09-14T23-20-51Z-mfu-live-validation.md)
- Host/GPU: DGX Spark GB10, driver `580.173.02`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, uv-launched Python 3.12
- Model image: `sha256:b60cc4d552b3a5555880e9699f68ae38a769f0c7c56475bdfeafdd23d501b6e1`
- Model: Qwen/Qwen3-Embedding-8B revision `1d8ad4ca9b3dd8059ad90a75d4983776a23d44af`, BF16

## Observation

RUN-0003 passed API, retrieval, dimensions, reference-vector parity, FLOP-counter,
and Prometheus/Grafana checks. The requested `docker stop --timeout 45
inferpack-mfu-model-check` completed after approximately six seconds and Docker
reported exit 137, `OOMKilled=false`. The log showed:

```text
SIGTERM received. Draining requests and shutting down...
Gracefully exiting... Remaining number of requests 0.
WARNING: destroy_process_group() was not called before program exit
kill_process_tree called: parent_pid=59, include_parent=True, pid=59
```

## Diagnosis And Verification

Inspected the same SGLang build in the next temporary model container:

```bash
docker exec inferpack-mfu-model-check sed -n '3135,3160p' /sgl-workspace/sglang/python/sglang/srt/managers/tokenizer_manager.py
docker exec inferpack-mfu-model-check sed -n '2240,2275p' /sgl-workspace/sglang/python/sglang/srt/utils/common.py
```

The drain path waits for zero requests, asks scheduler processes to exit, then
calls `kill_process_tree(os.getpid(), include_parent=True)`. That helper calls
`psutil.Process(...).kill()` on itself before `sys.exit(0)`. The uv parent
therefore observes SIGKILL and exits 137. This explains the observed exit code;
there was no Docker stop timeout or OOM. The NCCL cleanup warning also occurred
during the earlier model qualification (RUN-0001).

No serving fix was applied: this is existing engine shutdown behaviour, not a
failure of inference or estimated metrics. The model container was removed
before Tomoro started. Its completed requests and reference checks remain valid.

## Lesson

Interpret exit 137 together with OOMKilled, signal timing, request-drain logs,
and the engine shutdown path. It does not by itself establish an OOM or failure
during serving.
