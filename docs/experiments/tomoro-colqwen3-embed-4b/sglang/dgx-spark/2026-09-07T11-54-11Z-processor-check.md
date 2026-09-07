# 2026-09-07T11:54:11Z — Container processor check and corrected uv invocation

Run ID: `RUN-0002`

- Status: resolved
- Phase: model load (configuration/processor only)
- Related turns: [Host access](2026-09-07T11-44-25Z-restricted-host-access.md)
- Repo revision: c7fe299 plus uncommitted Tomoro pack
- Host/GPU: aarch64 DGX Spark, GB10; no model GPU allocation in this check
- Container: dgxspark/tomoro-colqwen3-embed-4b-sglang:0.1.0, based on lmsysorg/sglang:dev-qwen38-27b-dflash2
- Engine: SGLang 0.0.0.dev1+g5f55db35e, Python 3.12.3
- Model: TomoroAI/tomoro-colqwen3-embed-4b, revision 13517a29e8c5e408f7f2684337ed407df3acb212, BF16

## Command

Inside a disposable container with the shared Hugging Face cache:

```bash
uv run --no-project --python /opt/sglang/bin/python prepare_model.py
uv run --no-project --python /opt/sglang/bin/python -c '<configuration check>'
```

## Error Or Observation

```text
error: unexpected argument '-c' found
```

## Diagnosis

The diagnostic omitted the Python command after `uv run`. The interpreter
selection option does not make Python's `-c` flag a uv option. Model preparation
had already succeeded; this was not a checkpoint or engine failure.

## Fix Or Change

Use `uv run --no-project --python /opt/sglang/bin/python python -c ...`.

## Verification

The corrected command loaded `AutoConfig` and `AutoProcessor` from the prepared
view and reported `Qwen3VLConfig Qwen3VLProcessor`. Text tokenization returned
`[[3838, 374, 279, 6722, 315, 9625, 30]]`. Both container builds succeeded.
The original checkpoint files remain unchanged in the shared cache.
GPU weight loading, API readiness, and reference parity remain untested.

## Lesson

Separate interpreter selection from the command passed to `uv run`, and
qualify configuration loading separately from GPU inference.

## Next Step

Run live text/image qualification once GPU capacity is available.
