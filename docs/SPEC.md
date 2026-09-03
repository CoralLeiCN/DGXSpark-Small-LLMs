# DGX Spark Model Hub Spec

Status: draft

This spec describes the architecture for this DGX Spark model-serving hub.

## Goal

Build and maintain multiple model-serving recipes for DGX Spark, with each model able to define its own runtime environment for vLLM or SGLang.

The repository should make it easy to:

- add a new model
- choose vLLM or SGLang when supported
- build the model-specific container
- start, stop, inspect, and validate the service
- keep incompatible model runtimes isolated from each other

## Technical Decision: Supported Inference Engines

The initial technical research and architecture evaluation selected two
inference engines for model-serving recipes:

- vLLM
- SGLang

Only these engines are supported. Other inference engines require a new
technical evaluation and an explicit project-scope decision; an individual
model recipe must not introduce one on its own.

## Non-goals

The repository does not try to support every inference engine or deployment platform.

Out of scope:

- TensorRT-LLM
- NVIDIA NIM
- Ollama
- llama.cpp
- Kubernetes
- multi-node orchestration
- a web UI
- a global Python environment that serves all models directly

## Core Architecture

Model serving on DGX Spark is container-first. The repository does not provide
one universal serving environment: CUDA, PyTorch, inference-engine, tokenizer,
and quantization compatibility can differ by model, and an environment that
works for one model may break another.

The main deployment unit is:

```text
model + engine
```

Examples:

```text
nvidia/nemotron-3-super-120b-a12b + vllm
google/gemma + sglang
```

Each deployment unit owns its own Dockerfile, Compose file, startup script, and runtime configuration. This avoids forcing all models to share one CUDA, PyTorch, vLLM, or SGLang version.

The repository has two layers:

1. Shared repo tooling
2. Model-specific serving environments

Shared repo tooling should be small. It should locate manifests, validate required files, and call Docker Compose. It should not import vLLM or SGLang directly.

Model-specific serving environments should contain the real inference dependencies and launch commands.

## Repository Layout

Target layout:

```text
DGXSpark-Small-LLMs/
|-- README.md
|-- pyproject.toml
|-- uv.lock
|-- docs/
|   |-- README.md
|   |-- SPEC.md
|   `-- experiments/
|       |-- README.md
|       `-- <provider>/<model>/<engine>/
|           |-- README.md
|           `-- <timestamp>-<slug>.md
|-- scripts/
|   |-- build
|   |-- serve
|   |-- stop
|   |-- logs
|   `-- validate
|-- src/
|   `-- dgxspark_hub/
|       |-- __init__.py
|       |-- cli.py
|       |-- manifest.py
|       |-- docker.py
|       `-- validation.py
`-- models/
    `-- <provider>/
        `-- <model>/
            |-- manifest.yaml
            |-- README.md
            |-- vllm/
            |   |-- Dockerfile
            |   |-- compose.yaml
            |   |-- start.sh
            |   |-- .env.example
            |   `-- tests/
            `-- sglang/
                |-- Dockerfile
                |-- compose.yaml
                |-- start.sh
                |-- .env.example
                `-- tests/
```

## Component Responsibilities

### `scripts/`

Top-level scripts are user-facing wrappers. They should stay thin and call the Python CLI through `uv`.

Example shape:

```bash
uv run --python 3.12 dgxspark build "$@"
```

### `src/dgxspark_hub/`

This package owns shared repository behavior:

- parse command-line arguments
- find model manifests
- check whether an engine is enabled
- resolve the model engine directory
- run Docker Compose commands
- perform basic validation requests

It should not own model-specific vLLM or SGLang flags.

### `models/`

This is the model catalog. Each model has one folder under its provider.

A model folder owns:

- identity and metadata in `manifest.yaml`
- human notes in `README.md`
- one optional `vllm/` folder
- one optional `sglang/` folder

### `models/<provider>/<model>/<engine>/`

This is the actual deployable serving environment.

It owns:

- base image choice
- pinned runtime versions
- model-specific launch flags
- exposed port
- environment defaults
- Docker Compose service definition
- service-specific tests

### `docs/experiments/`

This is the operational learning record. Each `model + engine` deployment unit
has an indexed journal directory at
`docs/experiments/<provider>/<model>/<engine>/`. Each experiment turn has one
immutable UTC-timestamped Markdown file and a stable engine-local sequential ID
such as `RUN-0001`; later diagnosis or verification goes in a new linked turn
file with the next ID. The engine index records the run count and next ID. Every
observed Docker, engine-startup, model-loading, health-check, or inference
failure is recorded with its environment, error, diagnosis, fix, verification,
and reusable lesson. The journals complement the stable recipe documentation:
model READMEs explain how the service should work, while turn files preserve how
failures were actually investigated and resolved.

## Model Manifest

Each model should include a manifest at:

```text
models/<provider>/<model>/manifest.yaml
```

Minimal example:

```yaml
id: nvidia/nemotron-3-super-120b-a12b
name: Nemotron 3 Super 120B A12B
provider: nvidia
status: experimental

model:
  source: huggingface
  repo: nvidia/REPLACE_WITH_REAL_REPO
  local_path: /models/nemotron-3-super-120b-a12b
  served_name: nemotron-3-super-120b-a12b

engines:
  vllm:
    enabled: true
    image: dgxspark/nemotron-3-super-120b-a12b-vllm:0.1.0
    compose: vllm/compose.yaml
    port: 8000

  sglang:
    enabled: false
    image: dgxspark/nemotron-3-super-120b-a12b-sglang:0.1.0
    compose: sglang/compose.yaml
    port: 30000

validation:
  endpoint: /v1/chat/completions
  prompt: Explain tensor parallelism in one paragraph.
  max_tokens: 128
```

## Command Model

The intended user interface is:

```bash
scripts/build <provider>/<model> --engine vllm
scripts/serve <provider>/<model> --engine vllm
scripts/logs <provider>/<model> --engine vllm
scripts/validate <provider>/<model> --engine vllm
scripts/stop <provider>/<model> --engine vllm
```

The CLI should translate those commands into Docker Compose operations in the selected engine folder.

For example:

```bash
scripts/build nvidia/nemotron-3-super-120b-a12b --engine vllm
```

should resolve to something like:

```bash
cd models/nvidia/nemotron-3-super-120b-a12b/vllm
docker compose -f compose.yaml build
```

## Assumptions

- DGX Spark deployments should run model servers in containers.
- The host has Docker and NVIDIA container runtime support.
- The host uses `uv` and Python 3.12 for repository tooling.
- The model server API should prefer OpenAI-compatible endpoints where the engine supports them.
- Models may be gated or require credentials, so `.env` files are local and not committed.
- vLLM and SGLang versions may differ per model.
- Some models may only support one of the two engines.
- Official SGLang images or NVIDIA framework images are preferred over
  unrelated third-party serving images to reduce provenance and compatibility
  ambiguity.
- Exact cached base-image tags should be reused when compatible, rather than
  downloading a different large framework image. Cache reuse saves deployment
  time and bandwidth but must not override model-specific compatibility.

## First Implemented Model

The first real deployment unit is:

```text
nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4 + SGLang
```

Its Dockerfile defaults to the locally cached
`nvcr.io/nvidia/pytorch:26.02-py3` ARM64 image. SGLang is pinned inside the
model-specific image and is not installed into the host Python environment.
The launch flags follow NVIDIA's model card and cookbook.

## Tradeoffs

### Per-model containers over one shared environment

This increases duplication across model folders, but it makes deployments more reproducible and avoids dependency conflicts between models.

### Docker Compose over raw Docker commands

Compose adds a small amount of file structure, but it makes ports, volumes, environment variables, GPU settings, and service names easier to inspect and reproduce.

### Thin top-level scripts over large shell scripts

Thin scripts keep the user interface simple while allowing validation and manifest parsing to live in Python. The tradeoff is that the Python CLI must exist before the scripts are useful.

### Minimal manifest over full schema upfront

A small manifest is easier to maintain early. The tradeoff is that fields may need to evolve as real models expose more requirements.

### vLLM and SGLang only

The technical evaluation limits the supported engines to vLLM and SGLang to
keep the repository focused and implementable while bounding its design and
maintenance burden. The tradeoff is that some models may work better on other
runtimes, but adopting one requires fresh research and an explicit project-scope
decision.

## Open Questions

- Should model images be built locally only, or eventually pushed to a registry?
- Should downloaded model weights be shared through one host cache path, such as `/data/models`?
- Should validation use only `/v1/chat/completions`, or support `/v1/completions` too?
- Should `serve` run containers in attached mode or detached mode by default?
