# 2026-09-03T21:18:43Z — Parallel FlashInfer FP4 compilation exhausted memory

Run ID: `RUN-0004`

- Status: open
- Phase: engine startup
- Related turns: none
- Repo revision: `c520931` (`dirty`)
- Host/GPU: DGX Spark, NVIDIA GB10, 121.69 GiB unified memory, driver
  `580.173.02`, ARM64
- Container: `dgxspark/nemotron-3-nano-30b-a3b-nvfp4-sglang:0.1.0`
- Engine: SGLang `0.5.15.post1`, FlashInfer `0.6.12`
- Model: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4`, revision
  `6efb4a2a1c1fa277ce7b3df7a1416255011b1c99`, NVFP4

## Command

```bash
scripts/deploy-nemotron-nano
```

## Error Or Observation

```text
subprocess.CalledProcessError: Command ['ninja', '-v', '-C',
'/root/.cache/flashinfer/0.6.12/121a/cached_ops/fp4_gemm_cutlass_sm120',
'-f', '.../build.ninja'] returned non-zero exit status 137.
...
FAILED: [code=137] ...fp4_gemm_cutlass...cuda.o
Killed
ninja: build stopped: subcommand failed.
```

## Diagnosis

- Symptom: the scheduler died during first-run FlashInfer FP4 GEMM compilation,
  after weights and runtime caches had initialized successfully.
- Root cause: Ninja launched many memory-heavy CUDA compiler processes in
  parallel. Their aggregate use exhausted the GB10's unified memory while the
  60 GiB SGLang allocation was resident, so the kernel killed compiler workers.
- Evidence: Docker recorded `OOMKilled=true`; the container process tree showed
  Ninja compiling 18 targets concurrently and several `cicc` workers each using
  roughly 3–4.5 percent of 121.69 GiB. The installed FlashInfer source reads
  `MAX_JOBS` and passes it to Ninja as `-j`.

## Fix Or Change

Set the recipe default to `MAX_JOBS=1` so FlashInfer JIT compilation is serial.
Add named Docker volumes for `/root/.cache/flashinfer` and
`/root/.cache/sglang` so compiled kernels and autotuning results survive
container recreation.

## Verification

Pending a rebuilt container, healthy endpoint, and successful inference request.

## Lesson

On unified-memory inference systems, the model allocation and build-time
compiler processes compete for the same capacity. Limit JIT build concurrency
explicitly; CPU count is not a safe default for CUDA template compilation.

## Next Step

Continue with
[the serialized JIT turn](2026-09-03T21-37-58Z-serialized-jit-follow-up.md).
