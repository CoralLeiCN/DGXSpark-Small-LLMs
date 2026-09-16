# 2026-09-07T22:33:33Z — Readiness probes reset until warm-cache startup completed

Run ID: `RUN-0025`

- Status: resolved
- Phase: model load / health check / inference
- Related turns: [API connection reset during warm-cache startup](2026-09-04T08-42-53Z-api-reset-during-startup.md) (`RUN-0003`), [Sequential startup qualifies 45 percent allocation](2026-09-07T12-47-42Z-reduced-memory-qualified.md) (`RUN-0005`)
- Repo revision: `75d9507`
- Host/GPU: DGX Spark GB10, CUDA 13.0.3; PyTorch memory fallback reported 124610 MiB
- Container: `dgxspark/qwen3.8-27b-fp8-sglang:0.1.0` (`sha256:3c11adf54d4a220f587f361f48eee66b50a8e2b8c068db7484c598beb3684b62`)
- Engine: SGLang `0.0.0.dev1+g5f55db35e`
- Model: `Qwen/Qwen3.8-27B-FP8` at `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`, FP8

## Command

```bash
docker stop qdrant-op-qdrant
uv run --python 3.12 infer deploy qwen3.8-27b-fp8 --engine sglang --target dgx-spark
uv run --python 3.12 infer validate-responses qwen3.8-27b-fp8 --engine sglang --target dgx-spark --timeout 600
curl --fail --silent --show-error http://127.0.0.1:30000/health
```

## Error Or Observation

```text
error: [Errno 104] Connection reset by peer
curl: (56) Recv failure: Connection reset by peer
```

The reset occurred while the published port was available but the API had not
finished startup. The scheduler stayed running with no restarts. It loaded the
cached local model snapshot, used 176.20 seconds for weight loading, allocated
339310 KV-cache tokens, captured CUDA graphs, and announced readiness at
22:37:36 UTC.

## Diagnosis

- Symptom: responses validation and repeated local health probes reset before readiness.
- Root cause: the probes ran before SGLang completed weight deserialization, cache allocation, CUDA graph capture, and its warmup request.
- Evidence: container inspection reported `healthy`, zero restarts, and `OOMKilled=false` after startup. The scheduler consumed 53759 MiB after cache allocation; logs recorded `scheduler_e2e=214.49` seconds followed by `The server is fired up and ready to roll!`.

## Fix Or Change

No recipe change was needed. Stopped the sole existing Docker service before
deployment so Qwen's memory profiling was uncontended, then gated validation on
`/health` instead of container creation or its published port.

## Verification

```bash
curl --fail --silent --show-error http://127.0.0.1:30000/health
uv run --python 3.12 infer validate-responses qwen3.8-27b-fp8 --engine sglang --target dgx-spark --timeout 600
```

The health endpoint succeeded. Responses validation returned status `completed`
with `DGX Spark SGLang ready`. Docker reported the Qwen container healthy on
host port 30000; it was the only active Docker service.

## Lesson

On DGX Spark, Qwen warm-cache startup still takes several minutes. Do not use a
published port or a running container as an API readiness signal; wait for
`/health` and the server-ready log line before sending validation traffic.

## Next Step

None. Leave Qwen3.8 running for user requests.
