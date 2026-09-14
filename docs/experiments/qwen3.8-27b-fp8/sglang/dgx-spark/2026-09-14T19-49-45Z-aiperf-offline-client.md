# 2026-09-14T19:49:45Z — Reuse cached AIPerf after sandbox DNS failure

Run ID: `RUN-0007`

- Status: resolved (benchmark client setup)
- Phase: preflight
- Related turns: [host preflight](2026-09-14T19-47-23Z-benchmark-host-preflight.md)
- Repo revision: `17d39b06860ea7159a3d4a3443053b4d79bf867e`, dirty with benchmark files
- Host/GPU: DGX Spark, Linux aarch64, GB10; driver `580.173.02`
- Container: `dgxspark/qwen3.8-27b-fp8-sglang:0.1.0`, starting independently
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, torch `2.13.0+cu130`, transformers `5.12.1`
- Model: `Qwen/Qwen3.8-27B-FP8`, cached revision
  `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`

## Command

```bash
export UV_TOOL_DIR=/tmp/codex-aiperf-tools
export UV_CACHE_DIR=/tmp/codex-aiperf-uv-cache
export UV_PYTHON_INSTALL_DIR=/tmp/codex-aiperf-python
uv tool run --managed-python --python 3.12 --from aiperf==0.12.0 aiperf --version
```

## Error Or Observation

The command exited 2 before any inference:

```text
Failed to fetch: https://pypi.org/simple/aiperf/
failed to lookup address information: Temporary failure in name resolution
```

## Diagnosis

The sandbox could not resolve PyPI. AIPerf and its Python environment were
already cached from prior work; this was not a missing client dependency.

## Fix Or Change

Use uv offline mode for the cached pinned client. Use the model's local snapshot
as the benchmark tokenizer to avoid a separate tokenizer download.

## Verification

```bash
uv tool run --offline --managed-python --python 3.12 \
  --from aiperf==0.12.0 aiperf --version
```

With the same exported cache directories, this exited 0 and reported `0.12.0`.
The server snapshot's `tokenizer.json` and `tokenizer_config.json` exist locally.
No benchmark requests were sent in this client-setup turn.

## Lesson

Reuse a cached, pinned benchmark client with uv offline mode when registry
access is unavailable. Keep the client environment separate from model-serving
dependencies.

## Next Step

Wait for Qwen readiness and run the streaming baseline.
