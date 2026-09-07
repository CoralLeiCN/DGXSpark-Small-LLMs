# 2026-09-07T12:51:32Z — FP32 interpolation passes image parity; service stopped

Run ID: `RUN-0006`

- Status: resolved
- Phase: inference validation / shutdown
- Related turns: [Image parity failure](2026-09-07T12-42-18Z-image-reference-parity.md) (RUN-0005), [Reference loader failure](2026-09-07T12-39-09Z-reference-local-module-path.md) (RUN-0004)
- Repo revision: f58941b plus reviewed interpolation, reference-loader, memory and port fixes
- Host/GPU: DGX Spark GB10; driver 580.173.02, CUDA 13.0; Qwen3.8 healthy at 0.45 allocation
- Container: dgxspark/tomoro-colqwen3-embed-4b-sglang:0.1.0, image sha256:ec60e67cb5c556ea42de579634d284e11ee0337cb06f3d5f9bfe1531e786eccf
- Engine: SGLang 0.0.0.dev1+g5f55db35e, Python 3.12.3
- Model: TomoroAI/tomoro-colqwen3-embed-4b at 13517a29e8c5e408f7f2684337ed407df3acb212, BF16

## Command

```bash
docker compose -f models/tomoro-colqwen3-embed-4b/sglang/targets/dgx-spark/compose.yaml build
docker compose -f models/tomoro-colqwen3-embed-4b/sglang/targets/dgx-spark/compose.yaml up -d --no-build
docker exec -e INFERPACK_REFERENCE_TESTS=1 dgxspark-tomoro-colqwen3-embed-4b-sglang-1 uv run --no-project --python /opt/sglang/bin/python python -m pytest /opt/inferpack/tests/test_reference.py -v -s
INFERPACK_LIVE_TESTS=1 uv run --python 3.12 pytest --import-mode=importlib -q
uv run --python 3.12 infer validate tomoro-colqwen3-embed-4b --target dgx-spark
docker compose -f models/tomoro-colqwen3-embed-4b/sglang/targets/dgx-spark/compose.yaml stop
docker compose -f models/tomoro-colqwen3-embed-4b/sglang/targets/dgx-spark/compose.yaml down
```

## Fix And Diagnosis

The model-local vision hook uses the installed Transformers bilinear-index helper and FP32 weights/accumulation, casting the final positional embeddings to BF16. Vectorized and graph vision paths are disabled so they cannot bypass the hook. Cached checkpoint files are unchanged.

## Verification

The rebuilt image passes the unchanged tolerances: text (17,320), mean/minimum cosine 0.999651/0.999368; image (75,320), 0.997614/0.967261. Native and reference input IDs, image grid, and pixel tensors match exactly. This confirms interpolation precision contributed to the image discrepancy. Residual differences remain within the declared smoke-test tolerance; this is not bitwise parity or a retrieval benchmark.

Host suite: 10 passed, one reference test skipped on the host; container reference test: one passed. CLI validation reports seven normalized 320-dimensional vectors. Qwen3.8 Responses API remains successful while Tomoro is running.

## Startup And Shutdown Observations

One startup health probe returned HTTP 503 during warmup, followed by readiness and HTTP 200. The same known memory-capacity fallback and optional torchcodec warning remained non-blocking. Both the earlier diagnostic stop and this final stop drained zero outstanding requests and emitted the upstream NCCL warning `destroy_process_group() was not called before program exit`. Compose stop/down succeeded; the Tomoro container and network were removed. Only Qwen3.8 and Qdrant remain running. No shutdown workaround was required.

## Lesson

Validate vision-position arithmetic as well as checkpoint loading when adapting a token-embedding model. Preserve strict comparisons and record residual numerical tolerance. Start co-tenants sequentially and confirm shutdown separately from successful inference.

## Next Step

Merge the reviewed Tomoro PR, then implement Qwen3-Embedding-8B.
