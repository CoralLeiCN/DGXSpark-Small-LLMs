# 2026-09-09T22:08:47Z — Monitoring host preflight requires host access

Run ID: `RUN-0004`

- Status: resolved
- Phase: preflight
- Related turns: none
- Repo revision: `75d9507`, dirty; branch `codex/shared-inference-monitoring`
- Host/GPU: DGX Spark, aarch64, NVIDIA GB10; host reports 127600748 kB total RAM
- Container: existing `dgxspark/gemma-4-26b-a4b-it-sglang:0.1.0`
- Engine: SGLang; running version not queried in this preflight
- Model: `google/gemma-4-26B-A4B-it`; current revision not queried

## Command

```bash
docker ps --format '{{.Names}}'
docker image ls --format '{{.Repository}}:{{.Tag}}'
nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader
```

## Error Or Observation

```text
permission denied while trying to connect to the docker API at unix:///var/run/docker.sock
NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver.
```

Git branch creation also initially failed because sandboxed Git metadata was
read-only. No model build, launch, or inference was attempted in that sandbox.

## Diagnosis

The restricted execution environment could not access the Docker socket or
GPU driver. Repeating the read-only checks with approved host access succeeded:
Docker listed the healthy Gemma 4 26B A4B container and NVIDIA-SMI reported GB10.
This distinguishes an execution-permission boundary from a broken GPU runtime.

## Fix Or Change

Use approved host execution for Docker/GPU operations. Branch creation then
succeeded. The user selected the existing 26B A4B service for monitoring validation.

## Verification

The same Docker and NVIDIA-SMI checks succeeded outside the sandbox. The running
model uses `MEM_FRACTION_STATIC=0.75`, `CONTEXT_LENGTH=32768`, and no extra flags.
Its host ports and network attachments were empty in Docker inspection, despite
successful internal health checks. This is an observation, not a diagnosed cause.
A subsequent container recreation will apply `--enable-metrics` and the declared
Compose networking.

## Lesson

Verify runtime failures against host access before diagnosing a driver or model
incompatibility. Inspect existing workload settings before recreating services.

## Next Step

Deploy shared monitoring and validate token counts and throughput with Gemma.
