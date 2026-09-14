# 2026-09-14T21:33:38Z — MTP server qualifies for 96-request capacity comparisons

Run ID: `RUN-0016`

- Status: resolved (startup and four API smoke checks)
- Phase: engine startup / model load / health check / inference
- Related turns: [Sweep through 64](2026-09-14T21-28-07Z-mtp-concurrency-sweep-through64.md)
- Repo revision: `17d39b06860ea7159a3d4a3443053b4d79bf867e`, dirty
- Host/GPU: one otherwise idle DGX Spark GB10, Linux aarch64, driver `580.173.02`
- Container: `inferpack-qwen38-fp8-mtp-capacity96`,
  `dgxspark/qwen3.8-27b-fp8-sglang:0.1.0`, image ID
  `sha256:3c11adf54d4a220f587f361f48eee66b50a8e2b8c068db7484c598beb3684b62`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, FlashInfer `0.6.17`,
  torch `2.13.0+cu130`, transformers `5.12.1`
- Model: `Qwen/Qwen3.8-27B-FP8`, revision
  `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`, FP8 target and native MTP

## Command And Change

The first sweep was still rising at its upper endpoint. Increased active
capacity and graph coverage to 96, Mamba slots to 384, and memory fraction to
0.85. The extra memory allows the larger BF16 state pool while retaining
enough KV capacity for this short workload. This is a dedicated-host experiment,
not a change to the recipe's shared-host defaults or a long-context qualification.

```bash
docker run -d --name inferpack-qwen38-fp8-mtp-capacity96 \
  --gpus all --ipc host --shm-size 32gb \
  --ulimit memlock=-1 --ulimit stack=67108864 \
  --volumes-from dgxspark-qwen3-8-27b-fp8-sglang-1 \
  -p 127.0.0.1:30000:30000 \
  -e HF_HUB_DISABLE_IMPLICIT_TOKEN=1 -e HF_HUB_OFFLINE=1 \
  -e MODEL_ID=Qwen/Qwen3.8-27B-FP8 -e SERVED_MODEL_NAME=qwen3.8-27b-fp8 \
  -e CONTEXT_LENGTH=32768 -e MEM_FRACTION_STATIC=0.85 \
  -e MAX_RUNNING_REQUESTS=96 -e MAX_MAMBA_CACHE_SIZE=384 \
  -e CHUNKED_PREFILL_SIZE=2048 \
  -e 'SGLANG_EXTRA_ARGS=--enable-metrics --speculative-algorithm EAGLE --speculative-num-steps 3 --speculative-eagle-topk 1 --speculative-num-draft-tokens 4 --cuda-graph-max-bs 96' \
  --health-cmd 'curl --fail --silent http://127.0.0.1:30000/health' \
  --health-interval 30s --health-timeout 10s \
  --health-start-period 10m --health-retries 5 \
  dgxspark/qwen3.8-27b-fp8-sglang:0.1.0
```

## Observations, Diagnosis, And Verification

The recurring nonfatal GPU capacity-query fallback and optional torchcodec
import warning appeared, as in RUN-0014. Target loading took 182.88 seconds /
29.09 GB; MTP loading took 3.08 seconds / 5.28 GB. Mamba allocation was 1.06 GB
convolution, 27.07 GB SSM, 27.28 GB intermediate SSM, and 0.53 GB intermediate
convolution windows. BF16 KV capacity was 92,478 tokens, target K/V 2.82 GB
each and draft K/V 0.18 GB each.

Target verify and draft graphs included batch sizes through 96. Available
memory after all graph captures was 15.07 GB. One early Docker readiness probe
returned HTTP 503 at 21:32:55 UTC, within the startup grace period. The server
announced readiness at 21:32:58 and subsequently became healthy. Waiting for
startup resolved the readiness failure; no engine change was required.

Uv-managed Python 3.12 ran `/tmp/qwen-capacity96-smoke.py`. Exact text,
arithmetic `323`, JSON `[2, 5, 9]`, and the Responses API ready message all
passed. This is small-fixture API validation, not general quality equivalence.

Startup logs, smoke script/results, sweep driver, audit script, and monitor
are saved under the local ignored pack artifact directory
`artifacts/2026-09-14T21-28-17Z-capacity96-server/`.

## Next Step And Lesson

Run concurrency 96, 80, 64, and 48 under this fixed server with 384 measured
requests, 96 warmups, and seed 3000 at each setting. Clear the idle server's
radix cache before each profile using `POST /flush_cache?timeout=30`, verified
against the installed HTTP route. Remeasuring common points and using the same
inputs avoids treating a configuration change or prompt reuse as a concurrency
gain. Record actual active batches and available memory during inference.
