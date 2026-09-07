# 2026-09-04T08:42:53Z — API connection reset during warm-cache startup

Run ID: `RUN-0003`

- Status: resolved
- Phase: model load and health check
- Related turns: [Host API passed after retry outside the network sandbox](2026-09-04T01-15-47Z-host-api-validation.md)
- Repo revision: `def11da` plus uncommitted Qwen recipe and journal changes
- Host/GPU: DGX Spark, NVIDIA GB10, 124610 MiB unified memory reported by PyTorch
- Container: `dgxspark/qwen3.8-27b-fp8-sglang:0.1.0` (`sha256:1fe48564cd63becc4d5f4246ac6cd96fe84ac711e1aae51c7290fcb4b9d83a98`)
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, PyTorch `2.13.0+cu130`, Transformers `5.12.1`
- Model: `Qwen/Qwen3.8-27B-FP8`, revision `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`, blockwise FP8

## Command

```bash
curl http://localhost:30000/v1/models
```

## Error Or Observation

```text
curl: (56) Recv failure: Connection reset by peer
```

## Diagnosis

- Symptom: a host request reached the published port before it returned an API
  response.
- Root cause: the request was made during SGLang's warm-cache initialization,
  before the API completed readiness. This start still had to deserialize 66
  cached weight shards, allocate caches, and capture CUDA graphs.
- Evidence: SGLang found the local Hugging Face snapshot and skipped download,
  began loading at 08:30:08 UTC, and reported `load_weight=194.27` seconds and
  `scheduler_e2e=236.77` seconds. Uvicorn started at 08:34:00, its first health
  request returned HTTP 503, and SGLang announced readiness at 08:34:03. Docker
  subsequently reported `healthy`, zero restarts, and `OOMKilled=false`.

## Fix Or Change

No recipe change was required. Wait for `/health` to return HTTP 200, or follow
the service logs until `The server is fired up and ready to roll!`, before
calling the OpenAI-compatible endpoints.

Use the raw URL in the shell; Markdown link syntax such as
`[http://localhost:30000/v1/models](http://localhost:30000/v1/models)` is not a
curl URL.

## Verification

```bash
curl --fail --silent --show-error http://127.0.0.1:30000/health
curl --fail --silent --show-error http://127.0.0.1:30000/v1/models
```

Both commands succeeded at 08:42:53 UTC. The model listing returned
`qwen3.8-27b-fp8` with a maximum model length of 32768.

## Lesson

A warm model cache removes the network download but not weight deserialization,
memory-pool allocation, or CUDA graph capture. Gate clients on the readiness
endpoint rather than container creation or port publication.

## Next Step

None. Leave the healthy service running for the user's API calls.
