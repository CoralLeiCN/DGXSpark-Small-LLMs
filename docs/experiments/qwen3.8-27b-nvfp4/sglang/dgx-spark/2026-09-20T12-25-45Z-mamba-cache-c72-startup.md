# 2026-09-20T12:25:45Z — 72-request server admission startup validation

Run ID: `RUN-0006`

- Status: resolved
- Phase: engine startup
- Related turns: [Static-memory allocation failure](2026-09-20T12-20-27Z-mamba-cache-static-memory-failure.md)
- Repo revision: `03fef1fa2114c30d915d6d8d40244e18e435d0b5`, dirty
- Host/GPU: DGX Spark, one NVIDIA GB10
- Container: `dgxspark/qwen3.8-27b-nvfp4-sglang:0.1.0`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, Torch `2.13.0+cu130`
- Model: `nvidia/Qwen3.8-27B-NVFP4`, snapshot `482ca0f3832238542f8f5295dde86b5f22711d80`, NVFP4

## Command

```bash
INFERPACK_ENABLE_METRICS=1 MAX_RUNNING_REQUESTS=72 \
MEM_FRACTION_STATIC=0.70 SGLANG_EXTRA_ARGS='--max-mamba-cache-size 360' \
scripts/deploy qwen3.8-27b-nvfp4 --engine sglang --target dgx-spark
```

## Error Or Observation

```text
Mamba Cache is allocated. max_mamba_cache_size: 360,
conv_state size: 0.99GB, ssm_state size: 50.77GB
KV Cache is allocated. #tokens: 228520, K size: 3.49 GB, V size: 3.49 GB
max_total_num_tokens=228520, max_running_requests=72, available_gpu_mem=29.76 GB
The server is fired up and ready to roll!
```

## Diagnosis

- Symptom: none; SGLang completed model load, cache allocation, CUDA-graph capture through batch size 72, and health startup.
- Root cause: the 0.70 static-memory fraction provided enough budget for the explicit 360-slot Mamba cache and the FP8 KV cache.
- Evidence: the quoted startup records and successful service health check.

## Fix Or Change

Persisted `MEM_FRACTION_STATIC=0.70` and `MAX_MAMBA_CACHE_SIZE=360` as target defaults in the SGLang start script, Compose file, environment example, and recipe README.

## Verification

```bash
curl --fail http://127.0.0.1:30000/health
```

The service is healthy. This validates server admission configuration only; a new c72 AIPerf run is required to measure its latency and throughput.

## Lesson

For this DGX Spark target, c72 admission is feasible with 360 Mamba slots and 70% static GPU memory. Preserve roughly 30 GB after graph capture as observed headroom, and do not assume the older c72 benchmark describes this new configuration.

## Next Step

Run the tagged AIPerf c72 benchmark against this configuration and compare its client, GPU, and SGLang metrics with `RUN-0003`.
