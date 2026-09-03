# 2026-09-03T21:55:31Z — Detokenizer heartbeat timed out on the first API request

Run ID: `RUN-0007`

- Status: resolved
- Phase: health check
- Related turns:
  [Service became healthy](2026-09-03T21-54-10Z-service-ready.md)
- Repo revision: `c520931` (`dirty`)
- Host/GPU: DGX Spark, NVIDIA GB10, driver `580.173.02`, ARM64
- Container: `dgxspark/nemotron-3-nano-30b-a3b-nvfp4-sglang:0.1.0`
- Engine: SGLang `0.5.15.post1`
- Model: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4`, NVFP4

## Command

```bash
scripts/validate nvidia/nvidia-nemotron-3-nano-30b-a3b-nvfp4 \
  --engine sglang --timeout 300
```

## Error Or Observation

```text
Health check failed. Server couldn't get a response from detokenizer for last
20 seconds. tic start time: 21:55:11. last_heartbeat time: 21:54:40
```

## Diagnosis

- Symptom: SGLang emitted an internal health warning during the first external
  OpenAI-compatible chat request after startup.
- Root cause: not conclusively isolated. The timing indicates that first-request
  work delayed the detokenizer heartbeat; neither the scheduler nor container
  crashed.
- Evidence: the request began prefill at `21:55:34Z` and returned HTTP 200 at
  `21:55:36Z`. `/health` returned 200 again at `21:55:52Z`, and Docker retained
  zero restarts with `OOMKilled=false`.

## Fix Or Change

No runtime change was needed. The Compose health check's retries tolerated the
transient first-request warning, and subsequent requests completed normally.

## Verification

```bash
curl --fail --silent --show-error http://127.0.0.1:30000/health
scripts/validate nvidia/nvidia-nemotron-3-nano-30b-a3b-nvfp4 \
  --engine sglang --timeout 300
```

Both commands succeeded, and the final validation completed in about eight
seconds with non-empty output.

## Lesson

A single engine-internal heartbeat warning during first-request warmup is not
equivalent to a dead service. Use retry thresholds plus container restart and
OOM evidence before declaring the deployment unhealthy.

## Next Step

Revisit only if the heartbeat warning repeats after warmup or causes Docker's
health state to become unhealthy.
