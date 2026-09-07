# Qwen3 Embedding 8B

SGLang pack for `Qwen/Qwen3-Embedding-8B` on NVIDIA DGX Spark.
Status: experimental; qualified on DGX Spark on 2026-09-07. Build, health,
CLI validation, batched retrieval, 1024-dimensional outputs, and independent
Transformers comparison passed alongside Qwen3.8 at its reduced allocation.
The three reference cosines were 0.999766, 0.999812, and 0.999892. The retrieval
fixture scored its relevant document 0.625806 and its unrelated document
0.135013. These are smoke tests, not a retrieval benchmark. The embedding
service was stopped after qualification.

## Deployment

```bash
uv run --python 3.12 infer deploy qwen3-embedding-8b --target dgx-spark
uv run --python 3.12 infer logs qwen3-embedding-8b --target dgx-spark
# After the server reports ready:
uv run --python 3.12 infer validate qwen3-embedding-8b --target dgx-spark
INFERPACK_LIVE_TESTS=1 uv run --python 3.12 pytest models/qwen3-embedding-8b/sglang/targets/dgx-spark/tests/test_service.py -v -s
uv run --python 3.12 infer stop qwen3-embedding-8b --target dgx-spark
```

Start Qwen3.8 first and wait for readiness before starting this pack. Concurrent
weight loading distorts SGLang's free-memory profiling. Port 30002 avoids the
Qwen3.8 API on 30000 and the Tomoro API on 30001. Export overrides from the
[environment example](sglang/targets/dgx-spark/.env.example) in the invoking
shell; HF credentials are optional for this public checkpoint.

## API

`POST /v1/embeddings` returns one L2-normalized 4096-dimensional vector per
input. The server uses causal attention and last-token pooling. Supply query
instructions explicitly; document passages can be sent without instructions.
There is no chat-template or automatic query-prefix application.

```python
import json
import urllib.request

body = {
    "model": "qwen3-embedding-8b",
    "input": [
        "Instruct: Retrieve a passage that answers the question.\nQuery: What is the capital of France?",
        "Paris is the capital of France.",
    ],
    "encoding_format": "float",
    # "dimensions": 1024,  # Optional normalized Matryoshka prefix.
}
request = urllib.request.Request(
    "http://localhost:30002/v1/embeddings",
    data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(request, timeout=300) as response:
    embeddings = json.load(response)["data"]
```

This pack is text-only. `infer validate` selects the embeddings endpoint;
Responses and Chat Completions are not its validation paths.

## Runtime and limits

| Setting | Default |
| --- | --- |
| Base image | `lmsysorg/sglang:dev-qwen38-27b-dflash2` |
| Model revision | `1d8ad4ca9b3dd8059ad90a75d4983776a23d44af` |
| Precision / attention | BF16 / Triton |
| Host port | 30002 |
| Context length | 8192 |
| Concurrent requests | 2 |
| Static allocation fraction | 0.40 |

The qualified image contains SGLang `0.0.0.dev1+g5f55db35e`, PyTorch
`2.13.0+cu130`, Transformers `5.12.1`, and Python `3.12.3`.

The runtime uses SGLang's native Qwen3 embedding path with `--is-embedding`.
`is_matryoshka=true` enables dimension requests for this model, whose upstream
configuration omits that metadata. Prefix caching, chunked prefill, and CUDA
graphs are disabled for the initial qualification configuration. No model
extension or host-side serving dependencies are installed.

The context default is below the model card's 32K window to limit prefill
activation memory. The static fraction is an engine allocation target, not a
hard container RAM limit. All services, reference tests, and the host share
DGX Spark's unified memory. Larger contexts or additional co-tenants require
workload-specific validation.

The container reference test requires extra GPU memory for a second copy of
the backbone. It checks last-token pooling against Transformers:

```bash
docker compose -f models/qwen3-embedding-8b/sglang/targets/dgx-spark/compose.yaml exec \
  -e INFERPACK_REFERENCE_TESTS=1 sglang \
  uv run --no-project --python /opt/sglang/bin/python python -m pytest \
  /opt/inferpack/tests/test_reference.py -v -s
```

Sources: [model card and checkpoint](https://huggingface.co/Qwen/Qwen3-Embedding-8B/tree/1d8ad4ca9b3dd8059ad90a75d4983776a23d44af),
[native SGLang implementation](https://github.com/sgl-project/sglang/blob/5f55db35e/python/sglang/srt/models/qwen3.py).
Observed qualification and failures are recorded in the
[experiment journal](../../docs/experiments/qwen3-embedding-8b/sglang/dgx-spark/README.md).
