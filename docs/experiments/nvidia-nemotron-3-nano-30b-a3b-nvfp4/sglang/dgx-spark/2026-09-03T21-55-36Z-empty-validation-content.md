# 2026-09-03T21:55:36Z — Validation returned reasoning but no final answer

Run ID: `RUN-0008`

- Status: resolved
- Phase: inference
- Related turns:
  [First-request heartbeat warning](2026-09-03T21-55-31Z-detokenizer-heartbeat.md)
- Repo revision: `c520931` (`dirty`)
- Host/GPU: DGX Spark, NVIDIA GB10, driver `580.173.02`, ARM64
- Container: `dgxspark/nemotron-3-nano-30b-a3b-nvfp4-sglang:0.1.0`
- Engine: SGLang `0.5.15.post1`
- Model: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4`, revision
  `6efb4a2a1c1fa277ce7b3df7a1416255011b1c99`, NVFP4

## Command

```bash
scripts/validate nvidia/nvidia-nemotron-3-nano-30b-a3b-nvfp4 \
  --engine sglang --timeout 300
```

## Error Or Observation

```text
Reasoning:
...the model's analysis...

Response:

```

The endpoint returned HTTP 200, so the original validator exited successfully
despite the empty final content.

## Diagnosis

- Symptom: `reasoning_content` was present but final `content` was empty.
- Root cause: the hard-coded 128-token validation budget was consumed by this
  reasoning model before it produced the final answer.
- Evidence: repeating the same request with `max_tokens=512` returned a valid
  haiku using 337 completion tokens, of which 316 were reasoning tokens.

## Fix Or Change

Add model-specific `validation.max_tokens` support to the manifest loader and
set this recipe to 512. Make the validator fail when a successful HTTP response
contains no final text, preventing future false-positive checks.

## Verification

```bash
uv run --python 3.12 python -m unittest discover -s tests -v
scripts/validate nvidia/nvidia-nemotron-3-nano-30b-a3b-nvfp4 \
  --engine sglang --timeout 300
```

Both regression tests passed. The updated validator returned a non-empty haiku
in about eight seconds, and the final health check reported HTTP 200 with zero
container restarts and `OOMKilled=false`.

## Lesson

For reasoning models, budget output tokens for both hidden reasoning and final
content. A 200 response is not sufficient validation: assert that the expected
final response field is non-empty.

## Next Step

None.
