# 2026-09-04T00:19:32Z — Cold download exceeded the health-check grace period

Run ID: `RUN-0001`

- Status: open
- Phase: health check
- Related turns: `none`
- Repo revision: `def11da` plus uncommitted Qwen recipe changes
- Host/GPU: DGX Spark, NVIDIA GB10, 124610 MiB unified memory reported by PyTorch
- Container: `dgxspark/qwen3.8-27b-fp8-sglang:0.1.0` (`sha256:1fe48564cd63becc4d5f4246ac6cd96fe84ac711e1aae51c7290fcb4b9d83a98`), based on `lmsysorg/sglang:dev-qwen38-27b-dflash2` (`sha256:616a3e97f45191af975896cfa644279096cb31bd408a071c2e99ca7209c3cafe`)
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, PyTorch `2.13.0+cu130`, Transformers `5.12.1`
- Model: `Qwen/Qwen3.8-27B-FP8`, revision `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`, blockwise FP8

## Command

```bash
scripts/deploy qwen/qwen3.8-27b-fp8 --engine sglang
docker inspect --format '{{json .State.Health}}' dgxspark-qwen3-8-27b-fp8-sglang-1
```

No Hugging Face token was supplied because the model is public.

## Error Or Observation

```text
Status: unhealthy
FailingStreak: 11
Health command exit code: 7
Container state: running
Restart count: 0
OOM killed: false
```

The health transition occurred while the Hugging Face Xet download was still
making progress. At the transition, the cache held about 12 GiB and the Xet log
reported 12,356,685,191 transferred bytes across 248 completed transmissions
with a 1.000 success ratio.

## Diagnosis

- Symptom: Docker marked the service unhealthy before SGLang opened port 30000.
- Root cause: the 30-minute `start_period` was shorter than the first-run image
  and model cold-start path on this host. The health probe itself was correct,
  but Docker began counting its expected connection failures too early.
- Evidence: the SGLang scheduler remained alive, Docker reported zero restarts
  and no OOM kill, Xet shard timestamps and network/block I/O continued to
  advance, and no engine traceback or download error appeared.

## Fix Or Change

Increase the Compose health-check `start_period` from 30 minutes to 90 minutes.
This preserves the same readiness endpoint, interval, timeout, and retry budget
while accommodating a public-cache cold start for the roughly 28.5 GB model.

The running container was not recreated, so its in-flight download remained
uninterrupted. The updated grace period will apply to subsequent deployments.

## Verification

```bash
docker compose -f models/qwen/qwen3.8-27b-fp8/sglang/compose.yaml config
curl --fail --silent http://127.0.0.1:30000/health
scripts/validate qwen/qwen3.8-27b-fp8 --engine sglang --timeout 600
```

Compose configuration validation and live API verification are pending. Record
the later verification as a new turn and link it to this observation.

## Lesson

Size the health-check grace period for an empty-cache deployment, not only for
weight loading from a warm cache. Monitor transfer and process evidence before
restarting a service that has not yet opened its readiness port.

## Next Step

Allow the current download and model initialization to complete, then verify the
health endpoint, model listing, and chat completion. Confirm the rendered
Compose configuration contains the 90-minute startup grace period.
