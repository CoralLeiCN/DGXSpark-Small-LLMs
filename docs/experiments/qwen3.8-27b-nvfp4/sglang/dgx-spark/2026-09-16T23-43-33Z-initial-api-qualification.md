# 2026-09-16T23:43:33Z — Initial API qualification

Run ID: `RUN-0001`

- Status: resolved
- Phase: model load, health check, and inference
- Related turns: `none`
- Repo revision: `7de7cfe89bc196ed2e2921096edba7c0b0b8bc79`, dirty with the new pack
- Host/GPU: DGX Spark, `aarch64`, NVIDIA GB10, driver 580.173.02, CUDA 13.0
- Container: `dgxspark/qwen3.8-27b-nvfp4-sglang:0.1.0`, image `sha256:8484f3a848cea131bce8f31d41c94afddafdef6dda5b9cd1c5d6da40a5c632be`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, Torch `2.13.0+cu130`
- Model: `nvidia/Qwen3.8-27B-NVFP4`, revision `dbb8f445b3145f8a4c18ddc769f032d57d32867c`, ModelOpt mixed NVFP4/FP8

## Command

```bash
uv run --python 3.12 infer preflight qwen3.8-27b-nvfp4 --engine sglang --target dgx-spark
uv run --python 3.12 infer deploy qwen3.8-27b-nvfp4 --engine sglang --target dgx-spark
uv run --python 3.12 infer validate-responses qwen3.8-27b-nvfp4 --engine sglang --target dgx-spark --timeout 600
```

The service used a 32,768-token context, `0.45` static memory fraction, four
maximum running requests, FP8 E4M3 KV cache, 2,048-token chunked prefill,
float32 Mamba state, `extra_buffer` Mamba radix cache, and the NVIDIA-recommended
4.59 Mamba full-memory ratio.

## Error Or Observation

```text
Found local HF snapshot .../dbb8f445b3145f8a4c18ddc769f032d57d32867c; skipping download.
Load weight end. elapsed=116.26 s, quant=modelopt_mixed,
quant_algo=MIXED_PRECISION, mem usage=21.90 GB.
GET /health HTTP/1.1 503 Service Unavailable
The server is fired up and ready to roll!
GET /health HTTP/1.1 200 OK
```

The transient 503 was returned by the health probe after the HTTP process had
started but before SGLang completed its internal warmup request and readiness
transition. The next probe returned 200. The container remained running with
zero restarts and `OOMKilled=false`.

SGLang allocated a 23.62 GB SSM state, 0.46 GB convolution state, and a 5.40 GB
FP8 KV cache supporting 176,670 tokens. Cold startup completed in 183.60 seconds.
The runtime warned that FP8 KV scaling factors were absent and therefore
defaulted to 1.0; this matches the model card's FP8 KV-cache launch example but
leaves accuracy impact outside this smoke qualification.

## Diagnosis

- Symptom: one health request returned 503 during warmup.
- Root cause: the HTTP server was reachable before the engine's warmup request
  and GC freeze completed; SGLang intentionally reported not-ready during that
  interval.
- Evidence: startup logs show the 503 at 23:42:06Z, a successful internal chat
  completion at 23:42:10Z, the ready message at 23:42:10Z, and health 200 at
  23:42:12Z. There were no restarts or OOM events.

## Fix Or Change

No runtime workaround was required. The Compose health check already tolerates
the warmup interval with a 90-minute start period and repeated probes. The new
pack keeps NVIDIA's documented mixed-precision, KV-cache, Mamba, parser, and
chunked-prefill settings while using conservative DGX Spark context and memory
defaults.

## Verification

```bash
uv run --python 3.12 infer validate-responses qwen3.8-27b-nvfp4 --engine sglang --target dgx-spark --timeout 600
curl --fail --silent http://127.0.0.1:30000/v1/models
curl --fail --silent http://127.0.0.1:30000/v1/chat/completions # required get_weather tool call
uv run --python 3.12 pytest -q tests
uv run --python 3.12 infer stop qwen3.8-27b-nvfp4 --engine sglang --target dgx-spark
```

The Responses API completed and returned exactly `DGX Spark NVFP4 ready`.
Model discovery reported `qwen3.8-27b-nvfp4` with a 32,768-token limit. A
required-tool request produced a parsed `get_weather` call with
`{"location":"London"}` and `finish_reason: tool_calls`. The host suite passed:
53 tests. Compose then stopped and removed the container and network; a final
check found no matching container and confirmed that port 30000 was closed.

An unrestricted `pytest -q` invocation did not run because pytest's default
import mode collided on duplicate `test_service.py` and `test_reference.py`
module names in unrelated model directories. This is a repository-wide test
collection issue, not an NVFP4 runtime failure; the scoped host suite above was
used for verification.

## Lesson

For Qwen3.8 ModelOpt mixed checkpoints, confirm that startup logs identify both
FP8 and NVFP4 layers and wait for SGLang's explicit ready transition rather than
treating the first reachable HTTP health endpoint as readiness. The cached
Qwen3.8 development image supports the required Blackwell kernels and parser
flags on DGX Spark.

## Next Step

Qualify image/video inputs, long-context capacity, output quality, and sustained
concurrency before changing the pack from experimental status.
