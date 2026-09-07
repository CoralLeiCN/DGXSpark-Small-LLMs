# InferPack

Hardware-targeted, ready-to-run inference packs for serving AI models on a
single node or single GPU. The current recipes target NVIDIA DGX Spark. Each
`model + engine + hardware target` pack owns its Docker environment so CPU
architecture, CUDA, PyTorch, SGLang, vLLM, and launch flags can be pinned
independently.

The catalog includes language-generation packs, multimodal token embeddings,
and dense text embeddings. Each pack selects validation appropriate to its
task and declares its supported input modalities.

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
infer preflight nvidia-nemotron-3-nano-30b-a3b-nvfp4 --target dgx-spark
infer deploy nvidia-nemotron-3-nano-30b-a3b-nvfp4 --target dgx-spark
infer logs nvidia-nemotron-3-nano-30b-a3b-nvfp4 --target dgx-spark
```

When the server is healthy:

```bash
infer validate nvidia-nemotron-3-nano-30b-a3b-nvfp4 --target dgx-spark
```

The API is available at `http://localhost:30000/v1`. See the
[model recipe](models/nvidia-nemotron-3-nano-30b-a3b-nvfp4/README.md)
for configuration and source documentation.

## Gemma 4 26B A4B IT

The Gemma recipe serves
[`google/gemma-4-26B-A4B-it`](https://huggingface.co/google/gemma-4-26B-A4B-it)
with a Gemma 4-capable SGLang image:

```bash
infer deploy gemma-4-26b-a4b-it --engine sglang --target dgx-spark
infer validate gemma-4-26b-a4b-it --engine sglang --target dgx-spark --timeout 600
infer stop gemma-4-26b-a4b-it --engine sglang --target dgx-spark
```

See the [model recipe](models/gemma-4-26b-a4b-it/README.md) for the DGX
Spark memory assumptions and configuration controls.

## Gemma 4 E4B IT

The dense E4B recipe serves
[`google/gemma-4-E4B-it`](https://huggingface.co/google/gemma-4-E4B-it)
with a Gemma 4-capable SGLang image:

```bash
infer deploy gemma-4-e4b-it --engine sglang --target dgx-spark
infer validate gemma-4-e4b-it --engine sglang --target dgx-spark --timeout 600
infer stop gemma-4-e4b-it --engine sglang --target dgx-spark
```

See the [model recipe](models/gemma-4-e4b-it/README.md) for its initial
DGX Spark qualification settings and configuration controls.

## Qwen3.8 27B FP8

The Qwen recipe serves
[`Qwen/Qwen3.8-27B-FP8`](https://huggingface.co/Qwen/Qwen3.8-27B-FP8)
with a Qwen3.8-capable SGLang image:

```bash
infer deploy qwen3.8-27b-fp8 --engine sglang --target dgx-spark
infer validate-responses qwen3.8-27b-fp8 --engine sglang --target dgx-spark --timeout 600
infer stop qwen3.8-27b-fp8 --engine sglang --target dgx-spark
```

See the [model recipe](models/qwen3.8-27b-fp8/README.md) for the DGX
Spark memory assumptions and configuration controls.

## Tomoro ColQwen3 Embed 4B

An experimental SGLang pack for
[`TomoroAI/tomoro-colqwen3-embed-4b`](https://huggingface.co/TomoroAI/tomoro-colqwen3-embed-4b)
adds text/image token embeddings on DGX Spark. Live batching and text/image
reference comparisons passed; see the [model recipe](models/tomoro-colqwen3-embed-4b/README.md).

## Qwen3 Embedding 8B

The SGLang pack for
[`Qwen/Qwen3-Embedding-8B`](https://huggingface.co/Qwen/Qwen3-Embedding-8B)
serves text embeddings on port 30002 with task-specific validation:

```bash
infer deploy qwen3-embedding-8b --target dgx-spark
infer validate qwen3-embedding-8b --target dgx-spark
infer stop qwen3-embedding-8b --target dgx-spark
```

See the [model recipe](models/qwen3-embedding-8b/README.md) for query formatting,
Matryoshka dimensions, memory settings, and qualification results.

## Commands

The Python 3.12 CLI runs through `uv`:

```bash
infer models
infer services
infer build <model> --engine sglang --target <hardware>
infer serve <model> --engine sglang --target <hardware>
infer deploy <model> --engine sglang --target <hardware>
infer status <model> --engine sglang --target <hardware>
infer logs <model> --engine sglang --target <hardware>
infer validate <model> --engine sglang --target <hardware>
infer validate-responses <model> --engine sglang --target <hardware>
infer stop <model> --engine sglang --target <hardware>
```

`models` discovers the inference pack manifests in the repository and prints
one row for every model, engine, and hardware-target combination, including
provider metadata, qualification status, and the API-facing served name. Model
identifiers are globally unique slugs; provider names remain manifest metadata
and part of upstream repository identifiers. The matching top-level scripts
remain available as thin convenience wrappers.

`services` lists running containers across all inference packs in the repository,
showing the model, engine, target, service, container name, state, health, and
actual port bindings. No model or target selection is needed:

```bash
uv run --python 3.12 infer services
uv run --python 3.12 infer services --all  # Include stopped containers.
```

`scripts/services` is the equivalent convenience wrapper. The command queries
the current Docker daemon using each pack's Compose configuration; unrelated
Docker projects are not included. A running container may still be loading its
model, so check the health column and use `infer validate` to verify the API.
Containers must have Compose ownership labels matching a current pack's paths;
containers created from old recipe paths are omitted. A project-name override
does not make the same container appear under multiple models.
Containers removed by `infer stop` are no longer listed, even with `--all`.

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
