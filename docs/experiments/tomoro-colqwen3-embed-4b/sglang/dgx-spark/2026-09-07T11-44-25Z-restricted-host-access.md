# 2026-09-07T11:44:25Z — Restricted shell cannot inspect GPU or Docker

Run ID: `RUN-0001`

- Status: resolved
- Phase: preflight
- Related turns: none
- Repo revision: c7fe299
- Host/GPU: aarch64 DGX Spark, NVIDIA GB10; host driver 580.173.02, CUDA 13.0
- Container: lmsysorg/sglang:dev-qwen38-27b-dflash2 (not launched in this attempt)
- Engine: SGLang 0.0.0.dev1+g5f55db35e in cached runtime
- Model: TomoroAI/tomoro-colqwen3-embed-4b, BF16; weights not loaded

## Command

```bash
nvidia-smi
docker ps --format '{{.Names}} {{.Status}}'
```

## Error Or Observation

```text
NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver.
permission denied while trying to connect to the docker API at unix:///var/run/docker.sock
```

## Diagnosis

The restricted shell cannot reach the host GPU devices or Docker socket.
The same read-only diagnostics in the approved host execution context succeed.
This is an execution-permission boundary, not evidence of a broken driver.

## Fix Or Change

Run GPU and Docker operations in the approved host context.

## Verification

`nvidia-smi` identified NVIDIA GB10 and driver 580.173.02. `docker ps`
identified a healthy existing Qwen3.8 service occupying approximately 95 GB.
No Tomoro service was launched. Permission to stop the existing workload was
requested separately.

## Lesson

Confirm host execution permissions before diagnosing GPU or Docker failures.

## Next Step

Implement the model-local ColQwen3 extension and qualify it after capacity is available.
