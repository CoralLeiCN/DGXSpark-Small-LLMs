# 2026-09-07T12:38:24Z — Startup warmup and live token batches pass

Run ID: `RUN-0003`

- Status: resolved
- Phase: engine startup / health check / inference
- Related turns: RUN-0002 (processor-only qualification)
- Repo revision: f58941b plus memory/port review changes
- Host/GPU: DGX Spark, GB10, driver 580.173.02, CUDA 13.0
- Container: dgxspark/tomoro-colqwen3-embed-4b-sglang:0.1.0 (sha256:baad2432f5a792b9d0cae3602833dd25956b30475ebb5e6b4760fcdb59a0853f)
- Engine: SGLang 0.0.0.dev1+g5f55db35e, Python 3.12.3
- Model: TomoroAI/tomoro-colqwen3-embed-4b at 13517a29e8c5e408f7f2684337ed407df3acb212, BF16

## Command

```bash
docker compose -f models/tomoro-colqwen3-embed-4b/sglang/targets/dgx-spark/compose.yaml build
docker compose -f models/tomoro-colqwen3-embed-4b/sglang/targets/dgx-spark/compose.yaml up -d --no-build
INFERPACK_LIVE_TESTS=1 uv run --python 3.12 pytest models/tomoro-colqwen3-embed-4b/sglang/targets/dgx-spark/tests/test_service.py -v
```

## Error Or Observation

Startup logged `Failed to get GPU memory capacity from nvidia-smi` followed by a successful torch.cuda.mem_get_info fallback (124610 MiB). It also skipped an unrelated optional MiMo processor because torchcodec is absent. Health probes returned HTTP 503 at 12:37:22, 12:37:27, and 12:37:32 UTC during warmup. `/encode` warmup returned HTTP 200 at 12:37:34, followed by the server-ready message.

## Diagnosis

GB10 does not expose the usual discrete-GPU memory capacity through nvidia-smi; SGLang's fallback works. The missing torchcodec module belongs to an unused audio processor. The health failures reflect warmup before readiness, not failed model loading.

## Fix Or Change

Review changed the host port to 30001 and static allocation fraction to 0.25 so Tomoro can coexist with the user's Qwen3.8 service after its allocation was reduced to 0.45. Waited for the explicit ready message before validation.

## Verification

Weight loading took 49.26 seconds. Live tests passed: 8 tests, including finite normalized 320-dimensional token vectors and unequal-length batch isolation (per-token cosine > 0.99 against standalone calls). Text/image Transformers parity is a separate next step.

## Lesson

Reserve host capacity and distinct ports for coexisting packs, and separate warmup health responses from steady-state failures.

## Next Step

Run reference parity and stop Tomoro before merging.
