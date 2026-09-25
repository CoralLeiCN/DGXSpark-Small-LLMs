# 2026-09-20T12:20:27Z — Explicit 360-slot cache exhausted the former static-memory budget

Run ID: `RUN-0005`

- Status: resolved
- Phase: engine startup
- Related turns: [Ratio-based c38 startup](2026-09-20T12-15-57Z-mamba-ratio-c38.md)
- Repo revision: `03fef1fa2114c30d915d6d8d40244e18e435d0b5`, dirty
- Host/GPU: DGX Spark, one NVIDIA GB10
- Container: `dgxspark/qwen3.8-27b-nvfp4-sglang:0.1.0`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, Torch `2.13.0+cu130`
- Model: `nvidia/Qwen3.8-27B-NVFP4`, snapshot `482ca0f3832238542f8f5295dde86b5f22711d80`, NVFP4

## Command

```bash
INFERPACK_ENABLE_METRICS=1 MAX_RUNNING_REQUESTS=72 \
MEM_FRACTION_STATIC=0.45 MAMBA_FULL_MEMORY_RATIO=10.0 \
SGLANG_EXTRA_ARGS='--max-mamba-cache-size 360' \
scripts/deploy qwen3.8-27b-nvfp4 --engine sglang --target dgx-spark
```

## Error Or Observation

```text
ValueError: Loaded weights leave no GPU memory for the KV cache under
--mem-fraction-static=0.45.
```

The service's restart policy restarted the container after this scheduler startup failure.

## Diagnosis

- Symptom: the explicit Mamba cache was accepted as 360 slots but KV-cache allocation was rejected.
- Root cause: `MEM_FRACTION_STATIC=0.45` reserved 55% of pre-load GPU memory as runtime slack. After weights and the fixed 360-slot Mamba cache, the remaining static budget for the KV cache was non-positive.
- Evidence: the installed SGLang allocator subtracts `pre_model_load_memory * (1 - mem_fraction_static)` and the fixed Mamba allocation before allocating KV cache. The parsed process arguments confirmed `mem_fraction_static=0.45` and `max_mamba_cache_size=360`.

## Fix Or Change

Raised `MEM_FRACTION_STATIC` to 0.70 while retaining the explicit 360-slot cache. This reduces the reserved non-static slack and gives the KV allocator a positive budget.

## Verification

```bash
INFERPACK_ENABLE_METRICS=1 MAX_RUNNING_REQUESTS=72 \
MEM_FRACTION_STATIC=0.70 SGLANG_EXTRA_ARGS='--max-mamba-cache-size 360' \
scripts/deploy qwen3.8-27b-nvfp4 --engine sglang --target dgx-spark
```

The next startup completed and reported `max_running_requests=72`; see `RUN-0006`.

## Lesson

When increasing a fixed Mamba cache, raise the static-memory fraction as well. The allocator's generic minimum-fraction error is calculated before the fixed Mamba allocation, so inspect its final allocation logs rather than treating that minimum as sufficient.

## Next Step

Benchmark the successful c72 admission configuration before treating it as a throughput recommendation.
