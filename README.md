# DGX Spark Small LLMs

Container-first deployment recipes for serving language models on NVIDIA DGX
Spark. Each `model + engine` pair owns its Docker environment so CUDA, PyTorch,
SGLang, vLLM, and model-specific flags can be pinned independently.

Supported inference engines are limited to SGLang and vLLM.

## NVIDIA Nemotron 3 Nano NVFP4

The first recipe serves
[`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4`](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4)
with SGLang:

```bash
export HF_TOKEN=hf_example
scripts/preflight nvidia/nvidia-nemotron-3-nano-30b-a3b-nvfp4
scripts/deploy-nemotron-nano
scripts/logs nvidia/nvidia-nemotron-3-nano-30b-a3b-nvfp4
```

When the server is healthy:

```bash
scripts/validate nvidia/nvidia-nemotron-3-nano-30b-a3b-nvfp4
```

The API is available at `http://localhost:30000/v1`. See the
[model recipe](models/nvidia/nvidia-nemotron-3-nano-30b-a3b-nvfp4/README.md)
for configuration and source documentation.

## Gemma 4 26B A4B IT

The Gemma recipe serves
[`google/gemma-4-26B-A4B-it`](https://huggingface.co/google/gemma-4-26B-A4B-it)
with a Gemma 4-capable SGLang image:

```bash
scripts/deploy google/gemma-4-26b-a4b-it --engine sglang
scripts/validate google/gemma-4-26b-a4b-it --engine sglang --timeout 600
scripts/stop google/gemma-4-26b-a4b-it --engine sglang
```

See the [model recipe](models/google/gemma-4-26b-a4b-it/README.md) for the DGX
Spark memory assumptions and configuration controls.

## Gemma 4 E4B IT

The dense E4B recipe serves
[`google/gemma-4-E4B-it`](https://huggingface.co/google/gemma-4-E4B-it)
with a Gemma 4-capable SGLang image:

```bash
scripts/deploy google/gemma-4-e4b-it --engine sglang
scripts/validate google/gemma-4-e4b-it --engine sglang --timeout 600
scripts/stop google/gemma-4-e4b-it --engine sglang
```

See the [model recipe](models/google/gemma-4-e4b-it/README.md) for its initial
DGX Spark qualification settings and configuration controls.

## Qwen3.8 27B FP8

The Qwen recipe serves
[`Qwen/Qwen3.8-27B-FP8`](https://huggingface.co/Qwen/Qwen3.8-27B-FP8)
with a Qwen3.8-capable SGLang image:

```bash
scripts/deploy qwen/qwen3.8-27b-fp8 --engine sglang
scripts/validate-responses qwen/qwen3.8-27b-fp8 --engine sglang --timeout 600
scripts/stop qwen/qwen3.8-27b-fp8 --engine sglang
```

See the [model recipe](models/qwen/qwen3.8-27b-fp8/README.md) for the DGX
Spark memory assumptions and configuration controls.

## Commands

All top-level scripts are thin wrappers around the Python 3.12 CLI and run
through `uv`:

```bash
scripts/build <provider>/<model> --engine sglang
scripts/serve <provider>/<model> --engine sglang
scripts/deploy <provider>/<model> --engine sglang
scripts/status <provider>/<model> --engine sglang
scripts/logs <provider>/<model> --engine sglang
scripts/validate <provider>/<model> --engine sglang
scripts/validate-responses <provider>/<model> --engine sglang
scripts/stop <provider>/<model> --engine sglang
```

`deploy` runs preflight checks, builds the model image, and starts it in the
background. Model downloads are stored in the host Hugging Face cache and are
not baked into the image.

`validate` uses the endpoint selected by the model manifest.
`validate-responses` explicitly tests the OpenAI-compatible `/v1/responses`
endpoint. Responses API is the primary application path for recipes whose
engine supports it, including Qwen3.8.

Architecture details and design decisions are in
[docs/SPEC.md](docs/SPEC.md). Failed Docker and inference runs, their diagnoses,
and verified fixes are kept in the
[inference experiment journals](docs/experiments/README.md).
