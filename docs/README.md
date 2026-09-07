# InferPack Design

This repository is a container-first catalog of hardware-targeted inference
packs for running AI models on a single node or single GPU. The current packs
target NVIDIA DGX Spark; other hardware is represented by additional explicit
targets when qualified recipes are implemented.

See [SPEC.md](SPEC.md) for the current architecture spec and
[experiments/README.md](experiments/README.md) for the failed-run journal guide
and deployment-pack journals.

The important rule:

> Each `model + engine + hardware target` pack owns its Docker environment.

That matters because CPU architecture, GPU memory topology, CUDA, PyTorch,
vLLM, SGLang, tokenizer, quantization, and launch settings can differ between
models and hardware. The host Python environment should only run lightweight
repository tooling.

## Documentation Approach

Keep documentation proportional to implemented behavior. Record architecture,
assumptions, and tradeoffs in the spec before implementing or changing a
significant design. Add model-, engine-, hardware-, and troubleshooting-specific
material when the corresponding recipe or observed behavior exists instead of
writing speculative documentation in advance.

When user feedback changes a requirement or architectural direction, update the
authoritative spec, guide, or model documentation directly. Do not maintain a
separate duplicate history or leave a pointer in its place.

## Scope

Only these inference engines are in scope for now:

- vLLM
- SGLang

## Layout

```text
DGXSpark-Small-LLMs/
|-- README.md
|-- pyproject.toml
|-- scripts/
|   |-- build
|   |-- serve
|   |-- stop
|   |-- logs
|   |-- services
|   |-- validate
|   `-- validate-responses
|-- src/
|   `-- inferpack/
|       |-- cli.py
|       |-- manifest.py
|       `-- docker.py
|-- models/
|   `-- <model>/
|       |-- manifest.yaml
|       |-- README.md
|       |-- vllm/
|       |   `-- targets/
|       |       `-- <hardware>/
|       |           |-- Dockerfile
|       |           |-- compose.yaml
|       |           |-- start.sh
|       |           |-- .env.example
|       |           `-- tests/
|       `-- sglang/
|           `-- targets/
|               `-- <hardware>/
|                   |-- Dockerfile
|                   |-- compose.yaml
|                   |-- start.sh
|                   |-- .env.example
|                   `-- tests/
`-- docs/
    |-- README.md
    `-- experiments/
        |-- README.md
        `-- <model>/<engine>/<hardware>/
            |-- README.md
            `-- <timestamp>-<slug>.md
```

Model directory names and manifest IDs are globally unique slugs. Provider
identity remains explicit manifest metadata and remains part of upstream source
repository IDs. Add a provider or brand to the model slug only when it is useful
for recognition or uniqueness.

Do not create empty target directories for unsupported combinations. A target
directory means that a concrete deployment pack exists, and its target-level
status communicates the current qualification state.

Do not add global vLLM or SGLang installs for serving. The shared Python package
should only find models, read manifests, resolve a deployment target, run Docker
commands, and perform basic validation.

## Command Shape

Top-level scripts are thin wrappers around the Python CLI:

```bash
scripts/models
scripts/services
scripts/build gemma-4-e4b-it --engine sglang --target dgx-spark
scripts/serve gemma-4-e4b-it --engine sglang --target dgx-spark
scripts/logs gemma-4-e4b-it --engine sglang --target dgx-spark
scripts/validate gemma-4-e4b-it --engine sglang --target dgx-spark
scripts/stop gemma-4-e4b-it --engine sglang --target dgx-spark
```

Each script calls:

```bash
uv run --python 3.12 infer <command> "$@"
```

The CLI runs Docker Compose from the selected target directory. Target
selection is explicit; InferPack does not silently choose a recipe from the
detected GPU.

## Manifest

Each model has one manifest at:

```text
models/<model>/manifest.yaml
```

Example:

```yaml
id: gemma-4-e4b-it
name: Gemma 4 E4B IT
provider: google

model:
  source: huggingface
  repo: google/gemma-4-E4B-it
  served_name: gemma-4-e4b-it

engines:
  sglang:
    targets:
      dgx-spark:
        status: experimental
        image: dgxspark/gemma-4-e4b-it-sglang:0.1.0
        base_image: lmsysorg/sglang:dev-qwen38-27b-dflash2
        base_image_env: SGLANG_BASE_IMAGE
        compose: sglang/targets/dgx-spark/compose.yaml
        port: 30000
        host:
          architectures: [aarch64, arm64]

validation:
  endpoint: /v1/chat/completions
  prompt: Reply with exactly this text and nothing else: ready
  max_tokens: 128
```

## Add A Model Or Target

1. Choose a globally unique model slug and create `models/<model>/` if needed.
2. Add or update the model-level `manifest.yaml` and `README.md`.
3. Add `<engine>/targets/<hardware>/` only for the engine and hardware being
   implemented.
4. Put the target's Dockerfile, Compose file, startup script, environment
   example, and service tests in that directory.
5. Pin runtime versions inside the target Dockerfile and keep model- and
   hardware-specific launch defaults inside the target pack.
6. Add the target under the matching manifest engine with its host constraints
   and qualification status.
7. Start its append-only journal at
   `docs/experiments/<model>/<engine>/<hardware>/` when experiments begin.

Hardware slugs should describe a reproducible class, such as `dgx-spark` or
`rtx-4080-16gb`, rather than an ambiguous marketing family.
