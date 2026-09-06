# InferPack

Hardware-targeted, ready-to-run inference packs for serving AI models on a
single node or single GPU. The current recipes target NVIDIA DGX Spark. Each
`model + engine` pair owns its Docker environment so CUDA, PyTorch, SGLang,
vLLM, and model-specific flags can be pinned independently.

The initial catalog contains language models. The package format is intended to
also support vision-language, embedding, OCR, parser, and other inference
workloads as qualified recipes are implemented.

Supported inference engines are limited to SGLang and vLLM.

Set up the repository CLI with Python 3.12:

```bash
uv sync --python 3.12
source .venv/bin/activate
infer models
```

The Codex app local environment is defined in
`.codex/environments/environment.toml`. New worktrees install the host-side
development dependencies with `uv` automatically.

## NVIDIA Nemotron 3 Nano NVFP4

The first recipe serves
[`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4`](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4)
with SGLang:

```bash
export HF_TOKEN=hf_example
infer preflight nvidia/nvidia-nemotron-3-nano-30b-a3b-nvfp4
infer deploy nvidia/nvidia-nemotron-3-nano-30b-a3b-nvfp4
infer logs nvidia/nvidia-nemotron-3-nano-30b-a3b-nvfp4
```

When the server is healthy:

```bash
infer validate nvidia/nvidia-nemotron-3-nano-30b-a3b-nvfp4
```

The API is available at `http://localhost:30000/v1`. See the
[model recipe](models/nvidia/nvidia-nemotron-3-nano-30b-a3b-nvfp4/README.md)
for configuration and source documentation.

## Gemma 4 26B A4B IT

The Gemma recipe serves
[`google/gemma-4-26B-A4B-it`](https://huggingface.co/google/gemma-4-26B-A4B-it)
with a Gemma 4-capable SGLang image:

```bash
infer deploy google/gemma-4-26b-a4b-it --engine sglang
infer validate google/gemma-4-26b-a4b-it --engine sglang --timeout 600
infer stop google/gemma-4-26b-a4b-it --engine sglang
```

See the [model recipe](models/google/gemma-4-26b-a4b-it/README.md) for the DGX
Spark memory assumptions and configuration controls.

## Gemma 4 E4B IT

The dense E4B recipe serves
[`google/gemma-4-E4B-it`](https://huggingface.co/google/gemma-4-E4B-it)
with a Gemma 4-capable SGLang image:

```bash
infer deploy google/gemma-4-e4b-it --engine sglang
infer validate google/gemma-4-e4b-it --engine sglang --timeout 600
infer stop google/gemma-4-e4b-it --engine sglang
```

See the [model recipe](models/google/gemma-4-e4b-it/README.md) for its initial
DGX Spark qualification settings and configuration controls.

## Qwen3.8 27B FP8

The Qwen recipe serves
[`Qwen/Qwen3.8-27B-FP8`](https://huggingface.co/Qwen/Qwen3.8-27B-FP8)
with a Qwen3.8-capable SGLang image:

```bash
infer deploy qwen/qwen3.8-27b-fp8 --engine sglang
infer validate-responses qwen/qwen3.8-27b-fp8 --engine sglang --timeout 600
infer stop qwen/qwen3.8-27b-fp8 --engine sglang
```

See the [model recipe](models/qwen/qwen3.8-27b-fp8/README.md) for the DGX
Spark memory assumptions and configuration controls.

## Commands

The Python 3.12 CLI runs through `uv`:

```bash
infer models
infer build <provider>/<model> --engine sglang
infer serve <provider>/<model> --engine sglang
infer deploy <provider>/<model> --engine sglang
infer status <provider>/<model> --engine sglang
infer logs <provider>/<model> --engine sglang
infer validate <provider>/<model> --engine sglang
infer validate-responses <provider>/<model> --engine sglang
infer stop <provider>/<model> --engine sglang
```

`models` discovers the inference pack manifests in the repository and prints
each model's identifier, enabled inference engines, and API-facing served name.
The matching top-level scripts remain available as thin convenience wrappers.

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
