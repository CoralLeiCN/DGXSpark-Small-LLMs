# 2026-09-04T01:15:47Z — Host API passed after retry outside the network sandbox

Run ID: `RUN-0002`

- Status: resolved
- Phase: health check and inference
- Related turns: [Cold download exceeded the health-check grace period](2026-09-04T00-19-32Z-cold-download-health-timeout.md)
- Repo revision: `def11da` plus uncommitted Qwen recipe and journal changes
- Host/GPU: DGX Spark, NVIDIA GB10, 124610 MiB unified memory reported by PyTorch
- Container: `dgxspark/qwen3.8-27b-fp8-sglang:0.1.0` (`sha256:1fe48564cd63becc4d5f4246ac6cd96fe84ac711e1aae51c7290fcb4b9d83a98`), based on `lmsysorg/sglang:dev-qwen38-27b-dflash2` (`sha256:616a3e97f45191af975896cfa644279096cb31bd408a071c2e99ca7209c3cafe`)
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, PyTorch `2.13.0+cu130`, Transformers `5.12.1`
- Model: `Qwen/Qwen3.8-27B-FP8`, revision `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`, blockwise FP8

## Command

The first host API check ran inside the workspace sandbox:

```bash
curl --fail --silent --show-error http://127.0.0.1:30000/health
curl --fail --silent --show-error http://127.0.0.1:30000/v1/models
```

## Error Or Observation

```text
curl: (7) Failed to connect to 127.0.0.1 port 30000 after 0 ms: Couldn't connect to server
```

At the same time, Docker's in-container probe reported `healthy`. The identical
host checks succeeded when run outside the network-isolated workspace sandbox.

## Diagnosis

- Symptom: host loopback requests from the sandbox failed immediately, despite
  Docker reporting that the service was healthy.
- Root cause: the workspace command sandbox could not access the host-published
  loopback port. The model service was not at fault.
- Evidence: the same curls outside the sandbox succeeded; `/v1/models` returned
  `qwen3.8-27b-fp8` with `max_model_len` 32768; the repository validator received
  a successful chat completion; and container inspection showed `running`,
  `healthy`, zero restarts, and `OOMKilled=false`.

## Fix Or Change

Run host-published API qualification outside the network sandbox. No service
configuration change was needed for this connectivity boundary.

The earlier health-grace fix also rendered correctly as `start_period: 1h30m0s`.
The original live container eventually recovered from `unhealthy` to `healthy`
after its uninterrupted cold download, FP8 load, and CUDA graph capture finished.

## Verification

```bash
docker compose -f models/qwen/qwen3.8-27b-fp8/sglang/compose.yaml config
curl --fail --silent --show-error http://127.0.0.1:30000/health
curl --fail --silent --show-error http://127.0.0.1:30000/v1/models
scripts/validate qwen/qwen3.8-27b-fp8 --engine sglang --timeout 600
docker inspect --format 'status={{.State.Status}} health={{.State.Health.Status}} restarts={{.RestartCount}} oom={{.State.OOMKilled}}' dgxspark-qwen3-8-27b-fp8-sglang-1
```

Observed results:

```text
Rendered start_period: 1h30m0s
Model: qwen3.8-27b-fp8
Maximum model length: 32768
Reasoning: We need answer exactly text. Need final only exact.
Response: DGX Spark SGLang ready
Container: status=running health=healthy restarts=0 oom=false
```

SGLang logged HTTP 200 responses for `/health`, `/v1/models`, and
`/v1/chat/completions`. The final audit contained no engine traceback or OOM.

## Lesson

When an in-container health probe passes but a sandboxed host curl fails
immediately, repeat the host-port check in a context that shares the host network
before diagnosing the model service. Preserve container health and request-log
evidence so the isolation boundary is explicit.

## Next Step

Stop the Qwen Compose service as requested, retain the named caches, and verify
that its container and published port are gone.
