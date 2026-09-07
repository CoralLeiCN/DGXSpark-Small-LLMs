# 2026-09-07T12:42:18Z — Reference loader fixed; image token parity below tolerance

Run ID: `RUN-0005`

- Status: open
- Phase: inference validation
- Related turns: RUN-0004 (reference import failure), RUN-0003 (live batching)
- Repo revision: f58941b plus reference loader fix
- Host/GPU: DGX Spark GB10, driver 580.173.02, CUDA 13.0
- Container: dgxspark/tomoro-colqwen3-embed-4b-sglang:0.1.0 with updated test copied into container
- Engine: SGLang 0.0.0.dev1+g5f55db35e, Python 3.12.3
- Model: TomoroAI/tomoro-colqwen3-embed-4b at 13517a29e8c5e408f7f2684337ed407df3acb212, BF16

## Command

```bash
docker exec -e INFERPACK_REFERENCE_TESTS=1 dgxspark-tomoro-colqwen3-embed-4b-sglang-1 uv run --no-project --python /opt/sglang/bin/python python -m pytest /opt/inferpack/tests/test_reference.py -v -s
```

## Error Or Observation

The temporary reference view fixes RUN-0004's import failure. Reference loading warns about an unused missing `vlm.lm_head.weight` (the retrieval forward calls the backbone, not the LM head) and an upstream missing docstring entry. Text: shape (17,320), mean cosine 0.999651, minimum 0.999368. Image: shape (75,320), mean cosine 0.996029, minimum 0.915526. The minimum-cosine assertion (>0.95) fails.

## Diagnosis

The numerical discrepancy is isolated to image inputs. Inspection shows the SGLang vision interpolation casts bilinear weights to BF16 before accumulation, while the installed Transformers reference accumulates in FP32. This is a hypothesis to verify, not yet a confirmed cause.

## Fix Or Change

Keep parity tolerances unchanged. Next attempt will preserve FP32 vision-position interpolation in the model-local extension and compare input preprocessing as well.

## Verification

Text parity passes; image parity fails. No merge is justified yet.

## Lesson

Validate token-level image outputs against a reference; a high mean cosine can conceal individual token discrepancies.

## Next Step

Implement and test reference-equivalent vision-position interpolation.
