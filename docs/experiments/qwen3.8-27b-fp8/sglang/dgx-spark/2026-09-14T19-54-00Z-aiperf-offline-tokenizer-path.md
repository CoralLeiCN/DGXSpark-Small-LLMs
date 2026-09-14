# 2026-09-14T19:54:00Z — AIPerf offline tokenizer rejects filesystem paths

Run ID: `RUN-0009`

- Status: open (diagnosed; retry follows separately)
- Phase: preflight / benchmark dataset configuration
- Related turns: [offline client setup](2026-09-14T19-49-45Z-aiperf-offline-client.md),
  [server qualification](2026-09-14T19-52-51Z-benchmark-startup-qualified.md)
- Repo revision: `17d39b06860ea7159a3d4a3443053b4d79bf867e`, dirty with benchmark files
- Host/GPU: DGX Spark, Linux aarch64, GB10; driver `580.173.02`
- Container: `dgxspark/qwen3.8-27b-fp8-sglang:0.1.0`, healthy
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, torch `2.13.0+cu130`, transformers `5.12.1`
- Model: `Qwen/Qwen3.8-27B-FP8`, revision
  `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`
- Client: AIPerf `0.12.0`, uv `0.9.7`, managed CPython `3.12.12`

## Command

```bash
UV_TOOL_DIR=/tmp/codex-aiperf-tools \
UV_CACHE_DIR=/tmp/codex-aiperf-uv-cache \
UV_PYTHON_INSTALL_DIR=/tmp/codex-aiperf-python \
UV_OFFLINE=1 HF_HUB_OFFLINE=1 \
QWEN_TOKENIZER="$HOME/.cache/huggingface/hub/models--Qwen--Qwen3.8-27B-FP8/snapshots/017b9c7af6b5689d5dd426a76e0bc077eb5ca20a" \
QWEN_BENCHMARK_ROOT="<pack>/artifacts/2026-09-14T19-52-40Z-baseline" \
  models/qwen3.8-27b-fp8/sglang/targets/dgx-spark/benchmark-aiperf.sh
```

This ran the initial runner version with concurrency 1, 2, 4, four warmups,
32 measured requests, 512 target input tokens, and 128 fixed output tokens.
It exited 1 during the first profile's dataset configuration, before inference.

## Error Or Observation

```text
Dataset configuration failed: TokenizerError
HFValidationError: Repo id must be in the form 'repo_name' or
'namespace/repo_name': '<local snapshot path>'
```

## Diagnosis

The installed AIPerf `common/tokenizer.py` routes offline mode through
`_from_pretrained_local` and `_resolve_local_snapshot`, which call
`snapshot_download(name, revision=revision, local_files_only=True)`. That API
requires a repository ID even though AIPerf's general CLI help advertises local
paths. The tokenizer files exist; this is argument routing, not missing weights
or a model-serving failure.

## Fix Or Change

Updated the runner to use `Qwen/Qwen3.8-27B-FP8` and an explicit
`--tokenizer-revision 017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`.
Offline loading can then resolve that snapshot from the existing HF cache.
No installed library or server configuration was modified.

## Verification

Source inspection confirmed the failing call chain. The failed profile contains
no performance result. A live retry with a fresh artifact directory is recorded
in the next turn; it must not overwrite this failed attempt's logs.

Artifacts: `<pack>/artifacts/2026-09-14T19-52-40Z-baseline/c1.log` and
`c1/logs/aiperf.log`.

## Lesson

For AIPerf 0.12.0 offline mode, select cached tokenizers by repository ID and
revision. Validate dataset configuration before interpreting a profile as an
inference attempt.

## Next Step

Retry with the corrected tokenizer arguments and check actual server token counts.
