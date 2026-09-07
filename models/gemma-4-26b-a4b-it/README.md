# Gemma 4 26B A4B IT

This recipe serves
[`google/gemma-4-26B-A4B-it`](https://huggingface.co/google/gemma-4-26B-A4B-it)
on one DGX Spark GPU through SGLang's OpenAI-compatible API.

Status: experimental. On 2026-09-05, the image built and the model completed
health, model-listing, and chat-completion validation on a DGX Spark. The tested
runtime was SGLang `0.0.0.dev1+g5f55db35e` with model revision
`4d7ae4984b7db7de8f8457170b3f1a419ee76d52`. Text inference was qualified;
image input, tool calling, and long-context capacity were not exercised.

## Deployment

```bash
# Optional for this public model: export HF_TOKEN=hf_example
scripts/deploy gemma-4-26b-a4b-it --engine sglang --target dgx-spark
scripts/logs gemma-4-26b-a4b-it --engine sglang --target dgx-spark
scripts/validate gemma-4-26b-a4b-it --engine sglang --target dgx-spark --timeout 600
scripts/stop gemma-4-26b-a4b-it --engine sglang --target dgx-spark
```

Model weights persist under `$HF_CACHE_DIR`; the default is
`$HOME/.cache/huggingface`. The service listens on
`http://localhost:30000` by default.

## Configuration

Copy `sglang/targets/dgx-spark/.env.example` to
`sglang/targets/dgx-spark/.env`, or export individual values before running a
script.

| Variable | Default | Purpose |
| --- | --- | --- |
| `SGLANG_BASE_IMAGE` | `lmsysorg/sglang:dev-qwen38-27b-dflash2` | CUDA 13 ARM64 SGLang image with Gemma 4 support |
| `SGLANG_PORT` | `30000` | Host API port |
| `CONTEXT_LENGTH` | `32768` | Initial qualification context limit |
| `MEM_FRACTION_STATIC` | `0.75` | Unified-memory fraction for model and runtime caches |
| `MAX_RUNNING_REQUESTS` | `4` | Scheduler concurrency cap |
| `HF_CACHE_DIR` | `$HOME/.cache/huggingface` | Persistent model cache |
| `SGLANG_EXTRA_ARGS` | unset | Additional model-specific launch arguments |

DGX Spark's 128 GB is unified with the host. The `0.75` default follows
SGLang's Gemma 4 guidance for the BF16 26B-A4B MoE variant and leaves workspace
headroom for Triton MoE kernels. It is not a hard container memory limit.

The model supports a native 262,144-token context. The 32K default is a
conservative initial operating point and should be increased only after
workload-specific concurrency and host-memory validation.

## Source Settings

The launch command follows the official model card and SGLang cookbook:

- one GPU (`--tp 1`)
- Triton attention for correct bidirectional image-token attention
- `gemma4` reasoning and tool-call parsers
- trusted repository code

The initial qualification does not enable the optional Gemma 4 assistant model
for NEXTN speculative decoding. That keeps startup memory and compatibility
variables isolated while the base service is established.

The tested SGLang image resolved to digest
`sha256:616a3e97f45191af975896cfa644279096cb31bd408a071c2e99ca7209c3cafe`
and commit `5f55db35e926d50676f75b812640ea2410b0fe0e`. Startup used the default
Triton MoE configuration because this build did not contain tuned kernel files
for NVIDIA GB10. That affects performance tuning, not the successful
correctness check recorded here.

Sources:

- [Google model card](https://huggingface.co/google/gemma-4-26B-A4B-it)
- [SGLang Gemma 4 cookbook](https://docs.sglang.io/cookbook/autoregressive/Google/Gemma4)

Observed deployment failures, diagnoses, and verified fixes are kept in the
[DGX Spark SGLang experiment journal](../../docs/experiments/gemma-4-26b-a4b-it/sglang/dgx-spark/README.md).
