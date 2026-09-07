# Tomoro ColQwen3 Embed 4B

SGLang pack for `TomoroAI/tomoro-colqwen3-embed-4b` on NVIDIA DGX Spark.
Status: **experimental; text/image qualified on DGX Spark on 2026-09-07**.
Docker build, health, live unequal-length batching, and comparison against the
original Transformers checkpoint passed. Text vectors had mean/minimum cosine
0.999651/0.999368; image vectors had 0.997614/0.967261 on a generated 256×256
fixture. Input tokens, image grid, and pixel tensors matched exactly. This is
smoke-test qualification, not a retrieval benchmark or video qualification.
The service was tested alongside Qwen3.8 at its reduced 0.45 allocation.

## Deployment

```bash
uv run --python 3.12 infer deploy tomoro-colqwen3-embed-4b --engine sglang --target dgx-spark
uv run --python 3.12 infer logs tomoro-colqwen3-embed-4b --engine sglang --target dgx-spark
# Run after the server reports ready:
uv run --python 3.12 infer validate tomoro-colqwen3-embed-4b --engine sglang --target dgx-spark
INFERPACK_LIVE_TESTS=1 uv run --python 3.12 pytest models/tomoro-colqwen3-embed-4b/sglang/targets/dgx-spark/tests/test_service.py -v
uv run --python 3.12 infer stop tomoro-colqwen3-embed-4b --engine sglang --target dgx-spark
```

Use a GPU with sufficient free unified memory. The host API uses port 30001
to coexist with Qwen3.8 on port 30000. Defaults reserve 25% of device
memory, limit context to 8,192 tokens, and permit two concurrent requests.
Export overrides from the target's [environment example](sglang/targets/dgx-spark/.env.example)
in the invoking shell. The image uses Python 3.12 and keeps all serving
dependencies in Docker.

## API and model behavior

This is a late-interaction retrieval model. `POST /encode` returns an
`embedding` matrix with one normalized 320-dimensional vector per input token.
Batched `text` inputs return one result per item. Preserve the token dimension
for MaxSim retrieval; pooling to a single vector changes this model's behavior.
The native endpoint accepts **already formatted** text and image prompts.

For a retrieval query, append ten `<|endoftext|>` tokens, matching the pinned
reference processor's query augmentation. The manifest's short raw-text input
checks vector structure only.

```python
import json
import urllib.request

body = {"text": "What is the capital of France?" + "<|endoftext|>" * 10}
request = urllib.request.Request(
    "http://localhost:30001/encode",
    data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(request, timeout=300) as response:
    vectors = json.load(response)["embedding"]
```

For an image, use this text together with `image_data` containing a PNG/JPEG
data URI:

```text
<|im_start|>user
<|vision_start|><|image_pad|><|vision_end|>Describe the image.<|im_end|><|endoftext|>
```

Start other GPU services first and wait for readiness before deploying this
pack; overlapping weight allocation can distort SGLang's memory profiling.

Images retain the checkpoint's pixel limits (up to 1,280 visual tokens).
PDFs must be rendered to images by the caller. Video is outside this pack's
qualification scope. Chat and Responses APIs are not validation paths for
this embedding pack.

## Runtime extension and qualification

The cached SGLang image `lmsysorg/sglang:dev-qwen38-27b-dflash2`
(version `0.0.0.dev1+g5f55db35e`) has Qwen3-VL support but no ColQwen3 model.
The pack's external model package replaces its Qwen3-VL registry entry inside
this container, adds Tomoro's learned projection including its bias, and returns
all token vectors. SGLang still executes the vision and language backbones.

`prepare_model.py` downloads checkpoint revision
`13517a29e8c5e408f7f2684337ed407df3acb212` and creates a container-local
configuration view compatible with the native Qwen3-VL processor. Weight files
are symlinked from the shared Hugging Face cache; cached files are never edited.
Prefix caching and chunked prefill are disabled so every input token retains an
output vector. Vision-position interpolation retains FP32 weights and accumulation to match
the reference implementation; the image's vectorized/graph vision paths are
disabled so they cannot bypass this correction. The launch uses BF16 model
weights, Triton language attention, and SDPA vision attention. This extension is tied to the selected image; changing SGLang requires
requalification.

The reference test loads the original checkpoint in Transformers alongside the
service and compares text and image token vectors. It requires additional GPU
memory and pytest in the container:

```bash
docker compose -f models/tomoro-colqwen3-embed-4b/sglang/targets/dgx-spark/compose.yaml exec \
  -e INFERPACK_REFERENCE_TESTS=1 sglang \
  uv run --no-project --python /opt/sglang/bin/python python -m pytest \
  /opt/inferpack/tests/test_reference.py -v -s
```

Observed failures and later qualification belong in the append-only
[experiment journal](../../docs/experiments/tomoro-colqwen3-embed-4b/sglang/dgx-spark/README.md).

Sources: [model and reference code](https://huggingface.co/TomoroAI/tomoro-colqwen3-embed-4b/tree/13517a29e8c5e408f7f2684337ed407df3acb212),
[SGLang source](https://github.com/sgl-project/sglang/tree/5f55db35e/python/sglang/srt).
