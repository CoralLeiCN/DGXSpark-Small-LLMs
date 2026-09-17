# Qwen3.8 27B NVFP4

This recipe serves NVIDIA's official
[`nvidia/Qwen3.8-27B-NVFP4`](https://huggingface.co/nvidia/Qwen3.8-27B-NVFP4)
checkpoint on one DGX Spark GPU through SGLang's OpenAI-compatible API.

The checkpoint is a mixed-precision ModelOpt build: MLP layers and the language
model head use NVFP4, while attention layers use FP8. It is approximately 22 GB
on disk and targets NVIDIA Blackwell hardware.

Status: experimental. On 2026-09-16 UTC, the cached NVIDIA revision
`dbb8f445b3145f8a4c18ddc769f032d57d32867c` loaded on a DGX Spark with no
restarts or OOMs. Health, model discovery, exact-text Responses API generation,
and parsed tool calling passed. Image and video requests, long-context capacity,
quality, and throughput remain unqualified.

## Deployment

Download the public checkpoint if it is not already cached:

```bash
scripts/download-qwen3.8-27b-nvfp4
```

Then deploy, validate, and stop it:

```bash
scripts/deploy qwen3.8-27b-nvfp4 --engine sglang --target dgx-spark
scripts/validate-responses qwen3.8-27b-nvfp4 --engine sglang --target dgx-spark --timeout 600
scripts/stop qwen3.8-27b-nvfp4 --engine sglang --target dgx-spark
```

The API listens on `http://localhost:30000/v1`. The model is public, so
`HF_TOKEN` is optional. The host cache defaults to `$HOME/.cache/huggingface`
and can be changed with `HF_CACHE_DIR`.

## Configuration

Copy `sglang/targets/dgx-spark/.env.example` to
`sglang/targets/dgx-spark/.env`, or export individual values before deployment.

| Variable | Default | Purpose |
| --- | --- | --- |
| `SGLANG_BASE_IMAGE` | `lmsysorg/sglang:dev-qwen38-27b-dflash2` | Qwen3.8-capable ARM64 SGLang image |
| `SGLANG_PORT` | `30000` | Host API port |
| `CONTEXT_LENGTH` | `32768` | Maximum admitted context |
| `MEM_FRACTION_STATIC` | `0.45` | SGLang model and cache memory fraction |
| `MAX_RUNNING_REQUESTS` | `4` | Scheduler concurrency limit |
| `CHUNKED_PREFILL_SIZE` | `2048` | Chunked-prefill token count |
| `HF_CACHE_DIR` | `$HOME/.cache/huggingface` | Persistent model cache root |

The model card documents a 262K context limit. The initial 32K setting and 0.45
memory fraction are conservative DGX Spark defaults and can be raised after
workload-specific capacity testing.

At the qualified defaults, SGLang used 21.90 GB for weights, allocated 176,670
FP8 KV-cache tokens, and completed cold startup in 183.60 seconds. The Mamba
cache used 0.46 GB for convolution state and 23.62 GB for SSM state.

## Source Settings

The launch command follows NVIDIA's SGLang example with tensor parallelism 1,
FP8 E4M3 KV cache, FlashInfer attention, 2,048-token chunked prefill, Qwen3
reasoning, the Qwen3 Coder tool parser, float32 Mamba state, the `extra_buffer`
Mamba radix strategy, and a 4.59 full-memory ratio.

Sources:

- [NVIDIA model card](https://huggingface.co/nvidia/Qwen3.8-27B-NVFP4)
- [SGLang Qwen3.8 cookbook](https://docs.sglang.io/cookbook/autoregressive/Qwen/Qwen3.8-27B)

Deployment observations are kept in the
[DGX Spark SGLang experiment journal](../../docs/experiments/qwen3.8-27b-nvfp4/sglang/dgx-spark/README.md).
