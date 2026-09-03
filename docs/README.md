# DGX Spark Model Hub Design

This repo should be a small, container-first hub for running different LLMs on DGX Spark.

See [SPEC.md](SPEC.md) for the current architecture spec and
[experiments/README.md](experiments/README.md) for the failed-run journal guide
and model-engine journals.

The important rule:

> Each `model + engine` pair owns its own Docker environment.

That matters because different models may need different CUDA, PyTorch, vLLM, SGLang, tokenizer, and quantization versions. The host Python environment should only run lightweight repo tooling.

## Documentation Approach

Keep documentation proportional to implemented behavior. Record architecture,
assumptions, and tradeoffs in the spec before implementing or changing a
significant design. Add model-, engine-, and troubleshooting-specific material
when the corresponding recipe or observed behavior exists instead of writing
speculative documentation in advance.

When user feedback changes a requirement or architectural direction, update the
authoritative spec, guide, or model documentation directly. Do not maintain a
separate duplicate history or leave a pointer in its place.

## Scope

Only these inference engines are in scope for now:

- vLLM
- SGLang

## Minimal Layout

```text
DGXSpark-Small-LLMs/
|-- README.md
|-- pyproject.toml
|-- scripts/
|   |-- build
|   |-- serve
|   |-- stop
|   |-- logs
|   `-- validate
|-- src/
|   `-- dgxspark_hub/
|       |-- cli.py
|       |-- manifest.py
|       `-- docker.py
|-- models/
|   `-- <provider>/
|       `-- <model>/
|           |-- manifest.yaml
|           |-- README.md
|           |-- vllm/
|           |   |-- Dockerfile
|           |   |-- compose.yaml
|           |   |-- start.sh
|           |   |-- .env.example
|           |   `-- tests/
|           `-- sglang/
|               |-- Dockerfile
|               |-- compose.yaml
|               |-- start.sh
|               |-- .env.example
|               `-- tests/
`-- docs/
    |-- README.md
    `-- experiments/
        |-- README.md
        `-- <provider>/<model>/<engine>/
            |-- README.md
            `-- <timestamp>-<slug>.md
```

Do not add global vLLM or SGLang installs for serving. The shared Python package should only find models, read manifests, and run Docker commands.

## Command Shape

Top-level scripts should be thin wrappers around the Python CLI:

```bash
scripts/build nvidia/nemotron-3-super-120b-a12b --engine vllm
scripts/serve nvidia/nemotron-3-super-120b-a12b --engine vllm
scripts/logs nvidia/nemotron-3-super-120b-a12b --engine vllm
scripts/validate nvidia/nemotron-3-super-120b-a12b --engine vllm
scripts/stop nvidia/nemotron-3-super-120b-a12b --engine vllm
```

Each script can simply call:

```bash
uv run --python 3.12 dgxspark <command> "$@"
```

The CLI should then run Docker Compose from the selected model engine directory.

## Minimal Manifest

Each model should have:

```text
models/<provider>/<model>/manifest.yaml
```

Example:

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

## Add A Model

For each new model:

1. Create `models/<provider>/<model>/`.
2. Add `manifest.yaml`.
3. Add a short model `README.md`.
4. Add `vllm/` and/or `sglang/` only when that engine is being tried.
5. Pin runtime versions inside that engine Dockerfile.
6. Keep model-specific launch flags inside that engine `start.sh` or `.env.example`.
7. Mark untested entries as `experimental`.
