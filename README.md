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
scripts/stop <provider>/<model> --engine sglang
```

`deploy` runs preflight checks, builds the model image, and starts it in the
background. Model downloads are stored in the host Hugging Face cache and are
not baked into the image.

Architecture details and design decisions are in
[docs/SPEC.md](docs/SPEC.md). Failed Docker and inference runs, their diagnoses,
and verified fixes are kept in the
[inference experiment journals](docs/experiments/README.md).
