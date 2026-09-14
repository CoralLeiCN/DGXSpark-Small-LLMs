# 2026-09-14T19:47:23Z — Benchmark GPU inspection requires host access

Run ID: `RUN-0006`

- Status: resolved (inspection only; benchmark follows separately)
- Phase: preflight / GPU discovery
- Related turns: [host API access](2026-09-04T01-15-47Z-host-api-validation.md)
- Repo revision: `17d39b06860ea7159a3d4a3443053b4d79bf867e`, clean
- Host/GPU: DGX Spark, Linux aarch64, NVIDIA GB10; driver `580.173.02`,
  CUDA driver capability `13.0`
- Container: existing `dgxspark/qwen3.8-27b-fp8-sglang:0.1.0`, image
  `sha256:3c11adf54d4a220f587f361f48eee66b50a8e2b8c068db7484c598beb3684b62`, stopped
- Engine: SGLang; installed version not inspected in this preflight
- Model: `Qwen/Qwen3.8-27B-FP8`; cached revision not inspected in this preflight

## Command

```bash
nvidia-smi
```

## Error Or Observation

The sandboxed command exited 9:

```text
NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver.
Make sure that the latest NVIDIA driver is installed and running.
```

## Diagnosis

This was an inspection-access limitation: the identical command with approved
host access succeeded, showing the GB10 at 0% utilization and only desktop GPU
processes. It does not establish a broken host driver. Docker inspection showed
Qwen and all other model containers stopped.

## Fix Or Change

Retried read-only GPU and Docker inspection with approved host access. No driver,
container, or model configuration was changed during this preflight.

## Verification

```bash
nvidia-smi
docker ps -a --format '{{.Names}}\t{{.Status}}\t{{.Ports}}'
```

Both succeeded outside the sandbox. Qwen was `Exited (0)` and port 30000 was
not published by a running model container.

## Lesson

Distinguish sandbox GPU visibility from host driver failure before changing the
runtime. Inspect active services before benchmarking a shared GPU or port.

## Next Step

Start the existing Qwen container and measure streaming performance.
