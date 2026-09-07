# 2026-09-07T12:39:09Z — Reference loader resolves relative import beside a cache blob

Run ID: `RUN-0004`

- Status: open
- Phase: reference model load / inference validation
- Related turns: RUN-0003
- Repo revision: f58941b plus review changes
- Host/GPU: DGX Spark GB10; driver 580.173.02; CUDA 13.0
- Container: dgxspark/tomoro-colqwen3-embed-4b-sglang:0.1.0, base lmsysorg/sglang:dev-qwen38-27b-dflash2
- Engine: SGLang 0.0.0.dev1+g5f55db35e, Python 3.12.3
- Model: TomoroAI/tomoro-colqwen3-embed-4b revision 13517a29e8c5e408f7f2684337ed407df3acb212, BF16

## Command

```bash
docker exec -e INFERPACK_REFERENCE_TESTS=1 dgxspark-tomoro-colqwen3-embed-4b-sglang-1 uv run --no-project --python /opt/sglang/bin/python python -m pytest /opt/inferpack/tests/test_reference.py -v -s
```

## Error Or Observation

`FileNotFoundError: .../models--TomoroAI--tomoro-colqwen3-embed-4b/blobs/configuration_colqwen3.py` in Transformers `_compute_local_source_files_hash` / `get_relative_import_files`. The service's native SGLang inference had passed; the independent reference model failed before loading weights.

## Diagnosis

Passing a symlink-backed local HF snapshot to this Transformers dynamic-module loader resolves the modeling file into the blobs directory, then looks for its relative configuration import beside that blob. The snapshot contains the configuration file but the blobs directory uses content-hash filenames.

## Fix Or Change

Next attempt will create a temporary reference view with real Python source files and symlinked weights, keeping cached files immutable.

## Verification

Reference parity test failed before inference; no numerical comparison was produced.

## Lesson

A reference validation harness must preserve relative Python module paths when loading remote-code models from local symlink caches.

## Next Step

Rerun the reference test using the temporary source view.
