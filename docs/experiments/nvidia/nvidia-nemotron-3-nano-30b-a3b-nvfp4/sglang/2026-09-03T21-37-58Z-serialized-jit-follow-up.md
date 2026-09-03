# 2026-09-03T21:37:58Z — Serialized JIT avoided OOM but was too slow

Run ID: `RUN-0005`

- Status: workaround
- Phase: engine startup
- Related turns:
  [Parallel FlashInfer compilation exhausted memory](2026-09-03T21-18-43Z-flashinfer-jit-oom.md)
- Repo revision: `c520931` (`dirty`)
- Host/GPU: DGX Spark, NVIDIA GB10, 121.69 GiB unified memory, driver
  `580.173.02`, ARM64
- Container: `dgxspark/nemotron-3-nano-30b-a3b-nvfp4-sglang:0.1.0`
- Engine: SGLang `0.5.15.post1`, FlashInfer `0.6.12`
- Model: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4`, revision
  `6efb4a2a1c1fa277ce7b3df7a1416255011b1c99`, NVFP4

## Command

```bash
scripts/serve nvidia/nvidia-nemotron-3-nano-30b-a3b-nvfp4 \
  --engine sglang
```

The Compose environment set `MAX_JOBS=1`.

## Error Or Observation

```text
ninja .../fp4_gemm_cutlass_sm120/build.ninja -j 1
```

The 17-object FP4 GEMM extension compiled and linked without OOM. The next
fused-MoE extension exposed 96 object targets, making full serialization
unnecessarily slow.

## Diagnosis

- Symptom: the one-worker limit prevented memory exhaustion but made the larger
  fused-MoE build impractical.
- Root cause: `MAX_JOBS=1` eliminated all safe parallelism as well as the unsafe
  unbounded parallelism from the failed turn.
- Evidence: the active fused-MoE compiler used about 2.1 GiB while approximately
  54 GiB remained available. The earlier failure had launched 18 workers.

## Fix Or Change

Raise the default to `MAX_JOBS=4`, still far below the unbounded 18-way compile.
Keep the named FlashInfer and SGLang volumes so completed objects survive the
container restart.

## Verification

The 17-object FP4 GEMM extension was present in the persistent cache, and the
next container started with `MAX_JOBS=4`. Full verification continues in
[the service-ready turn](2026-09-03T21-54-10Z-service-ready.md).

## Lesson

Concurrency limits should be based on measured per-worker memory and remaining
headroom. The safest possible value can impose excessive recovery time; bounded
parallelism is the useful production setting.

## Next Step

Compile the remaining fused-MoE extension with four workers, then verify Docker
health and the API.
