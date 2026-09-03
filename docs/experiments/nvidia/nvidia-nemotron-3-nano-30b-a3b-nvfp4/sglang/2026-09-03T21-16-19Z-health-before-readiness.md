# 2026-09-03T21:16:19Z — Health probe reset while JIT compilation was running

Run ID: `RUN-0003`

- Status: open
- Phase: health check
- Related turns: none
- Repo revision: `c520931` (`dirty`)
- Host/GPU: DGX Spark, NVIDIA GB10, driver `580.173.02`, ARM64
- Container: `dgxspark/nemotron-3-nano-30b-a3b-nvfp4-sglang:0.1.0`
- Engine: SGLang `0.5.15.post1`
- Model: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4`, NVFP4

## Command

```bash
curl --silent --show-error --max-time 5 \
  http://127.0.0.1:30000/health
```

## Error Or Observation

```text
curl: (56) Recv failure: Connection reset by peer
```

## Diagnosis

- Symptom: the published port accepted and then reset the request while Docker
  still reported `health=starting`.
- Root cause: the API was not ready because the scheduler was compiling the
  initial FlashInfer FP4 kernels.
- Evidence: the container was running with zero restarts, and its process tree
  showed active Ninja, `nvcc`, and `cicc` workers under the SGLang scheduler.

## Fix Or Change

Do not send validation traffic until Docker reports the service healthy. The
Compose health check already allows a 30-minute first-start period for model
loading and kernel compilation.

## Verification

Pending successful engine startup after the compilation-memory fix.

## Lesson

An exposed TCP port does not mean a model server is ready. Gate inference
validation on the engine health endpoint, especially on first startup when JIT
compilation can take several minutes.

## Next Step

Verify readiness in
[the service-ready turn](2026-09-03T21-54-10Z-service-ready.md).
