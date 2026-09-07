# 2026-09-07T12:47:42Z — Sequential startup qualifies 45 percent allocation

Run ID: `RUN-0005`

- Status: resolved
- Phase: engine startup / inference
- Related turns: [Concurrent startup failure](2026-09-07T12-40-39Z-concurrent-start-memory-profiling.md) (RUN-0004)
- Repo revision: c7fe299 plus memory-default changes
- Host/GPU: DGX Spark GB10, driver 580.173.02, CUDA 13.0
- Container: dgxspark/qwen3.8-27b-fp8-sglang:0.1.0, image sha256:3c11adf54d4a220f587f361f48eee66b50a8e2b8c068db7484c598beb3684b62
- Engine: SGLang 0.0.0.dev1+g5f55db35e, Python 3.12.3
- Model: Qwen/Qwen3.8-27B-FP8 at 017b9c7af6b5689d5dd426a76e0bc077eb5ca20a

## Command

```bash
# Started with no other model allocating GPU memory.
docker start dgxspark-qwen3-8-27b-fp8-sglang-1
uv run --python 3.12 infer validate-responses qwen3.8-27b-fp8 --target dgx-spark --timeout 600
nvidia-smi --query-compute-apps=process_name,used_memory --format=csv,noheader
```

## Observation And Diagnosis

Sequential startup measures weight usage of 29.11 GB (114.09 to 84.98 GB free), unlike the 53.61 GB delta observed when Tomoro allocated concurrently. At `MEM_FRACTION_STATIC=0.45`, 16 Mamba slots and 337292 KV token slots allocate successfully (10.29 GB each for K/V). Prefill graph capture completes in 25.82 seconds. The retained 32768 context and four-request limit fit.

## Fix Or Change

Keep the reduced 0.45 default and serialize startup. The earlier failure was caused by another model's allocation entering Qwen's profiling interval.

## Verification

Health passed. Responses API returned status `completed` and `DGX Spark SGLang ready`. Scheduler GPU allocation is 53639 MiB, down from the observed 95325 MiB at 0.80 (41686 MiB freed). Tokenizer process uses 218 MiB. This is a measured allocation, not a hard process RAM cap or a concurrency throughput benchmark.

## Lesson

Validate a lower allocation with stable co-tenant memory, then confirm actual process usage and inference before publishing new defaults.

## Next Step

Leave Qwen3.8 running and qualify each embedding service sequentially.
