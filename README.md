# DGXSpark_Nemotron-3-Super-120B-A12B

Deploy NVIDIA Nemotron 3 NVFP4 checkpoints on NVIDIA DGX Spark with vLLM.

## Dependency management

This repository uses `uv` for Python dependency management. Keep Python dependencies in `pyproject.toml` and commit `uv.lock` when it changes. Do not use `requirements.txt` as a second dependency source.

Install or update the local environment with:

```sh
uv sync
```

Run Python tools through `uv` so they use the locked environment:

```sh
uv run python validate_vllm.py
```

The Makefile follows the same convention; validation targets run through `uv run python`.

## vLLM

### Docker Compose

DGX Spark should use the NVIDIA vLLM container configured in `docker-compose.yml`.
The local Python environment is only used for endpoint validation.

Optionally copy the example environment file to set local overrides:

```sh
cp .env.example .env
```

If the Hugging Face model requires gated or private access, set `HF_TOKEN` in `.env` or export it in your shell. Otherwise, leave it unset and vLLM will download public models anonymously.

Download the Nano v3 reasoning parser before starting the Nano checkpoint:

```sh
wget https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4/resolve/main/nano_v3_reasoning_parser.py
```

Start the Nano checkpoint:

```sh
docker compose --profile nano up
```

Start the Super checkpoint:

```sh
docker compose --profile super up
```

Run in the background by adding `-d`:

```sh
docker compose --profile nano up -d
```

Stop the service:

```sh
docker compose down
```

Validate the local OpenAI-compatible vLLM endpoint:

```sh
uv run python validate_vllm.py
```

The validator waits up to 10 minutes by default because vLLM can take several minutes to load the checkpoint before the API is ready. Override this with `VLLM_VALIDATE_TIMEOUT_SECONDS` or adjust polling with `VLLM_VALIDATE_INTERVAL_SECONDS`.

For the Super profile, validate with its served model name:

```sh
VLLM_MODEL=nemotron-3-super uv run python validate_vllm.py
```

### Makefile

Start the Nano checkpoint:

```sh
make vllm-run-nano
```

Start the Super checkpoint:

```sh
make vllm-run-super
```

Validate the local OpenAI-compatible vLLM endpoint:

```sh
make vllm-validate
```
