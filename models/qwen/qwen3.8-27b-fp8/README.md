# Qwen3.8 27B FP8

This recipe serves
[`Qwen/Qwen3.8-27B-FP8`](https://huggingface.co/Qwen/Qwen3.8-27B-FP8)
on one DGX Spark GPU through SGLang's OpenAI-compatible API.

Status: experimental. On 2026-09-04, the image built and the model completed
health, model-listing, Responses API, and chat-completion validation on a DGX
Spark. The tested
runtime was SGLang `0.0.0.dev1+g5f55db35e` with model revision
`017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`.

## Deployment

```bash
# Optional for this public model: export HF_TOKEN=hf_example
scripts/deploy qwen/qwen3.8-27b-fp8 --engine sglang
scripts/logs qwen/qwen3.8-27b-fp8 --engine sglang
scripts/validate-responses qwen/qwen3.8-27b-fp8 --engine sglang --timeout 600
scripts/stop qwen/qwen3.8-27b-fp8 --engine sglang
```

`HF_TOKEN` is optional while the model remains public. Model weights persist
under `$HF_CACHE_DIR`; the default is `$HOME/.cache/huggingface`. The service
listens on `http://localhost:30000` by default.

The Responses API at `/v1/responses` is this recipe's primary validation and
application path. `scripts/validate` follows the endpoint selected by the model
manifest, while `scripts/validate-responses` explicitly tests Responses API
compatibility.

The observed first start with an empty cache took about 89 minutes from weight
download through CUDA graph capture. Warm-cache starts avoid that download. The
Compose health check allows 90 minutes before failed probes count against
service health.

## Configuration

Copy `sglang/.env.example` to `sglang/.env`, or export individual values before
running a script.

| Variable | Default | Purpose |
| --- | --- | --- |
| `SGLANG_BASE_IMAGE` | `lmsysorg/sglang:dev-qwen38-27b-dflash2` | Qwen3.8-capable official SGLang image |
| `SGLANG_PORT` | `30000` | Host API port |
| `CONTEXT_LENGTH` | `32768` | Initial qualification context limit |
| `MEM_FRACTION_STATIC` | `0.80` | Unified-memory fraction for model and runtime caches |
| `MAX_RUNNING_REQUESTS` | `4` | Scheduler concurrency cap |
| `MAX_MAMBA_CACHE_SIZE` | `16` | Four GDN state slots per request with `extra_buffer_lazy` |
| `CHUNKED_PREFILL_SIZE` | `2048` | Prefill chunk size chosen to avoid long decode stalls |
| `HF_CACHE_DIR` | `$HOME/.cache/huggingface` | Persistent model cache |
| `SGLANG_EXTRA_ARGS` | unset | Additional model-specific launch arguments |

DGX Spark's 128 GB is unified with the host. SGLang's Qwen3.8 cookbook reports
that `--mem-fraction-static 0.85` can cross the operating system's early-OOM
threshold, while `0.80` completed its DGX Spark boot-and-serve matrix. This
recipe therefore uses `0.80`; it is not a hard container memory limit.

Qwen3.8 is a hybrid Gated DeltaNet model, so the GDN state cache must be sized
alongside the paged attention KV cache. With the `extra_buffer_lazy` strategy,
four state slots are reserved per active request. The defaults pair four active
requests with 16 slots rather than relying on SGLang's generic memory-ratio
heuristic.

The model supports a native 262,144-token context. The 32K default is a
conservative first operating point for this repository and can be increased
after workload-specific concurrency and host-memory validation.

## Source Settings

The launch command follows the official model card and SGLang cookbook:

- one GPU (`--tp 1`)
- FlashInfer attention for SM121
- blockwise FP8 checkpoint weights and the checkpoint-declared KV-cache format
- BF16 GDN state
- `qwen3` reasoning and `qwen3_coder` tool-call parsers
- trusted repository code

The image is model-specific because Qwen3.8 support is newer than the SGLang
release pinned by the existing Nemotron recipe.

Sources:

- [Qwen model card](https://huggingface.co/Qwen/Qwen3.8-27B-FP8)
- [SGLang Qwen3.8 cookbook](https://docs.sglang.io/cookbook/autoregressive/Qwen/Qwen3.8-27B)

Observed deployment failures, diagnoses, and verified fixes are kept in the
[SGLang experiment journal](../../../docs/experiments/qwen/qwen3.8-27b-fp8/sglang/README.md).
