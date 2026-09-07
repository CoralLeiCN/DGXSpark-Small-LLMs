# 2026-09-07T13:01:56Z — Dense embedding, reduced dimensions, and reference parity qualified

Run ID: `RUN-0001`

- Status: resolved
- Phase: preflight / build / health check / inference / shutdown
- Related turns: none (first qualification of this target)
- Repo revision: 32583d0 plus new Qwen3-Embedding-8B pack
- Host/GPU: DGX Spark GB10, aarch64, driver 580.173.02, CUDA 13.0; Qwen3.8 running at 0.45 static allocation
- Container: dgxspark/qwen3-embedding-8b-sglang:0.1.0, image sha256:d0eef67819ec248adc31646f7195473cc018f63e3fa9a5a390b17b90301e9f65; base lmsysorg/sglang:dev-qwen38-27b-dflash2
- Engine: SGLang 0.0.0.dev1+g5f55db35e; Python 3.12.3; PyTorch 2.13.0+cu130; Transformers 5.12.1
- Model: Qwen/Qwen3-Embedding-8B at 1d8ad4ca9b3dd8059ad90a75d4983776a23d44af, BF16

## Command

```bash
uv run --python 3.12 infer deploy qwen3-embedding-8b --target dgx-spark
INFERPACK_LIVE_TESTS=1 uv run --python 3.12 pytest models/qwen3-embedding-8b/sglang/targets/dgx-spark/tests/test_service.py -v -s
docker exec -e INFERPACK_REFERENCE_TESTS=1 dgxspark-qwen3-embedding-8b-sglang-1 uv run --no-project --python /opt/sglang/bin/python python -m pytest /opt/inferpack/tests/test_reference.py -v -s
uv run --python 3.12 infer validate qwen3-embedding-8b --target dgx-spark
uv run --python 3.12 infer validate-responses qwen3.8-27b-fp8 --target dgx-spark --timeout 600
docker compose -f models/qwen3-embedding-8b/sglang/targets/dgx-spark/compose.yaml stop
docker compose -f models/qwen3-embedding-8b/sglang/targets/dgx-spark/compose.yaml down
```

## Error Or Observation

GPU preflight and Docker build passed. The engine logged `Failed to get GPU memory capacity from nvidia-smi` and successfully fell back to torch.cuda.mem_get_info (124610 MiB). Health probes returned HTTP 503 during kernel warmup from 12:57:02 through 12:57:32 UTC, then passed. Shutdown emitted `destroy_process_group() was not called before program exit` after draining zero requests. These did not prevent inference or container removal.

## Diagnosis And Configuration

The capacity fallback is expected on GB10; readiness follows completed warmup. The upstream NCCL cleanup warning appears during engine exit, while Compose successfully stops and removes the service. No driver or kernel repair was necessary.

The native Qwen3 implementation uses causal attention, last-token pooling, and normalized vectors. `--json-model-override-args '{"is_matryoshka":true}'` enables dimension selection omitted from the upstream config. Port 30002, static allocation 0.40, context 8192, two requests, Triton attention, no prefix cache/chunked prefill/CUDA graphs. Qwen3.8 reached readiness before this startup to keep memory profiling stable.

## Verification

Weight loading took 80.40 seconds and consumed 14.91 GB. The engine allocated 47466 KV token slots with 3.26 GB each for K and V. Live tests passed: ordered batches, finite normalized 4096-dimensional vectors, standalone/batch cosine >0.99, and normalized 1024-dimensional prefixes matching truncated full vectors. Relevant/unrelated retrieval scores were 0.625806/0.135013.

Independent Transformers last-token reference comparison passed in 86.92 seconds with cosines [0.9997662306, 0.9998120666, 0.9998920560]. CLI embedding validation passed, and Qwen3.8's Responses API completed successfully during coexistence. Repository host suite: 10 passed, four opt-in live/reference tests skipped; live model suite: two passed; container reference suite: one passed. This is small-fixture qualification, not a retrieval benchmark or full-context concurrency stress test.

Stop/down succeeded and removed the embedding container/network. Final process inspection shows only Qwen3.8's tokenizer/scheduler (218/54485 MiB); Docker lists Qwen3.8 healthy and Qdrant running. Tomoro remains stopped.

## Lesson

Embedding qualification must test pooling semantics, vector dimensions/normalization, batch consistency, reduced dimensions, and numerical reference agreement. Serialize startup when sharing unified memory, and distinguish warmup health responses from steady-state failure.

## Next Step

Create, review, and merge the Qwen3-Embedding-8B PR.
