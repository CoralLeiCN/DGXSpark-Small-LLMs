# Gemma 4 E4B IT

This recipe serves
[`google/gemma-4-E4B-it`](https://huggingface.co/google/gemma-4-E4B-it)
on one DGX Spark GPU through SGLang's OpenAI-compatible API.

Status: experimental. On 2026-09-05, the image built and the model completed
health, model-listing, and chat-completion validation on a DGX Spark. The tested
runtime was SGLang `0.0.0.dev1+g5f55db35e` with model revision
`ee0ef6023621cff504d758262d4e04895a5af4a2`. Text inference was qualified;
image, audio, video, tool calling, speculative decoding, and long-context
capacity were not exercised. This runtime logs that `torchcodec` is absent, so
audio requests are expected to fail until that dependency is added and tested.

## Deployment

```bash
# Optional for this public model: export HF_TOKEN=hf_example
scripts/deploy gemma-4-e4b-it --engine sglang --target dgx-spark
scripts/logs gemma-4-e4b-it --engine sglang --target dgx-spark
scripts/validate gemma-4-e4b-it --engine sglang --target dgx-spark --timeout 600
scripts/stop gemma-4-e4b-it --engine sglang --target dgx-spark
```

Model weights persist under `$HF_CACHE_DIR`; the default is
`$HOME/.cache/huggingface`. The service listens on
`http://localhost:30000` by default.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `SGLANG_BASE_IMAGE` | `lmsysorg/sglang:dev-qwen38-27b-dflash2` | CUDA 13 ARM64 SGLang image with Gemma 4 support |
| `SGLANG_PORT` | `30000` | Host API port |
| `CONTEXT_LENGTH` | `32768` | Initial qualification context limit |
| `MEM_FRACTION_STATIC` | `0.85` | Unified-memory fraction for model and runtime caches |
| `MAX_RUNNING_REQUESTS` | `4` | Scheduler concurrency cap |
| `HF_CACHE_DIR` | `$HOME/.cache/huggingface` | Persistent model cache |
| `SGLANG_EXTRA_ARGS` | unset | Additional model-specific launch arguments |

DGX Spark's 128 GB is unified with the host. The model has approximately 8B
total parameters including per-layer embeddings. The 32K context and `0.85`
static-memory defaults are conservative qualification settings rather than the
model's native 128K limit or a hard container memory limit.

## Source Settings

The launch command follows the official model card and SGLang cookbook:

- one GPU (`--tp 1`)
- Triton attention for correct bidirectional image-token attention
- `gemma4` reasoning and tool-call parsers
- trusted repository code

The initial qualification does not enable the optional Gemma 4 assistant model
for NEXTN speculative decoding. That keeps startup and compatibility variables
isolated while the base service is established.

The tested image resolved to
`sha256:326c8aa85e4ac705f9e7ed17ea19ac079851a56c97cfc87bb9a9715a968baf41`
and its SGLang base to digest
`sha256:616a3e97f45191af975896cfa644279096cb31bd408a071c2e99ca7209c3cafe`.
The cold start downloaded one 15.99 GB safetensors file. SGLang reported 15.56
GB of weight memory, allocated BF16 hybrid-attention KV pools, and retained
14.18 GB after decode CUDA-graph capture.

On shutdown, this SGLang development build drains requests and Compose removes
the service, but the engine logs an NCCL process-group warning followed by a
`SystemExit: 0` and Starlette cancellation traceback. Verify container removal
and port closure rather than interpreting that cleanup traceback as a running
service; the observation is preserved in the experiment journal.

Sources:

- [Google model card](https://huggingface.co/google/gemma-4-E4B-it)
- [SGLang Gemma 4 cookbook](https://docs.sglang.io/cookbook/autoregressive/Google/Gemma4)

Observed deployment experiments are kept in the
[DGX Spark SGLang experiment journal](../../docs/experiments/gemma-4-e4b-it/sglang/dgx-spark/README.md).
