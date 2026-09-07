# 2026-09-07T12:40:39Z — Concurrent model startup distorts available cache budget

Run ID: `RUN-0004`

- Status: open
- Phase: engine startup / memory pool allocation
- Related turns: RUN-0003 (previous startup readiness)
- Repo revision: c7fe299 plus memory-default changes
- Host/GPU: DGX Spark GB10, driver 580.173.02, CUDA 13.0
- Container: dgxspark/qwen3.8-27b-fp8-sglang:0.1.0; base lmsysorg/sglang:dev-qwen38-27b-dflash2
- Engine: SGLang 0.0.0.dev1+g5f55db35e, Python 3.12.3
- Model: Qwen/Qwen3.8-27B-FP8, revision 017b9c7af6b5689d5dd426a76e0bc077eb5ca20a

## Command

```bash
docker compose -f /tmp/inferpack-qwen38-memory/models/qwen3.8-27b-fp8/sglang/targets/dgx-spark/compose.yaml up -d --no-build
# Tomoro startup overlapped this weight-loading interval.
```

## Error Or Observation

`ValueError: Loaded weights leave no GPU memory for the KV cache under --mem-fraction-static=0.45. Raise --mem-fraction-static above 0.473 (minimum viable = 1 - available/pre = 0.4726).` The first load measured free memory falling from 114.02 to 60.41 GB while Tomoro also allocated its weights and cache. Qwen's scheduler itself was later observed using about 29 GB during the automatic retry.

## Diagnosis

The runtime profiles a before/after free-memory delta. Simultaneous model allocation was charged against Qwen's own budget, so this failed attempt does not establish that 0.45 is insufficient when started sequentially. The service entered its Compose automatic restart path. Startup also logged the known successful torch fallback for GB10 memory capacity and an unused torchcodec processor import warning.

## Fix Or Change

Stopped Qwen's retry while Tomoro reference validation runs. Next attempt will start Qwen alone, then start an embedding service only after Qwen is ready.

## Verification

The initial reduced-memory attempt failed before API readiness; no inference validation was attempted against that startup.

## Lesson

Serialize model startup on shared unified-memory devices. A free-memory delta cannot distinguish another process's allocations from the loading model's own allocations.

## Next Step

Retry 0.45 with no simultaneous model allocation and validate the API.
