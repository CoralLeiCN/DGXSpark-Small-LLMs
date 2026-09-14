# 2026-09-14T21:08:33Z — Expanded MTP server qualifies for a concurrency sweep

Run ID: `RUN-0014`

- Status: resolved (startup and text smoke checks; capacity sweep follows)
- Phase: engine startup / model load / health check / inference
- Related turns: [MTP baseline](2026-09-14T20-53-32Z-fp8-mtp-concurrency-benchmark.md)
- Repo revision: `17d39b06860ea7159a3d4a3443053b4d79bf867e`, dirty with benchmark files
- Host/GPU: one DGX Spark, Linux aarch64, GB10, driver `580.173.02`
- Container: `inferpack-qwen38-fp8-mtp-capacity64`, image
  `dgxspark/qwen3.8-27b-fp8-sglang:0.1.0`,
  `sha256:3c11adf54d4a220f587f361f48eee66b50a8e2b8c068db7484c598beb3684b62`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, FlashInfer `0.6.17`,
  torch `2.13.0+cu130`, transformers `5.12.1`
- Model: `Qwen/Qwen3.8-27B-FP8`, revision
  `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`, FP8 target and native MTP head

## Command And Change

The user requested increasing active concurrency until throughput reaches its
maximum. A four-request scheduler cap would measure queuing above four, not
larger GPU batches. The temporary server therefore raises the cap to 64, Mamba
slots to 256 (four per request), static memory fraction to 0.80, and CUDA graph
maximum batch size to 64. All other model and MTP settings remain as in RUN-0013.
The GPU was idle; no other service was stopped to make room.

```bash
docker run -d --name inferpack-qwen38-fp8-mtp-capacity64 \
  --gpus all --ipc host --shm-size 32gb \
  --ulimit memlock=-1 --ulimit stack=67108864 \
  --volumes-from dgxspark-qwen3-8-27b-fp8-sglang-1 \
  -p 127.0.0.1:30000:30000 \
  -e HF_HUB_DISABLE_IMPLICIT_TOKEN=1 -e HF_HUB_OFFLINE=1 \
  -e MODEL_ID=Qwen/Qwen3.8-27B-FP8 \
  -e SERVED_MODEL_NAME=qwen3.8-27b-fp8 \
  -e CONTEXT_LENGTH=32768 -e MEM_FRACTION_STATIC=0.80 \
  -e MAX_RUNNING_REQUESTS=64 -e MAX_MAMBA_CACHE_SIZE=256 \
  -e CHUNKED_PREFILL_SIZE=2048 \
  -e 'SGLANG_EXTRA_ARGS=--enable-metrics --speculative-algorithm EAGLE --speculative-num-steps 3 --speculative-eagle-topk 1 --speculative-num-draft-tokens 4 --cuda-graph-max-bs 64' \
  --health-cmd 'curl --fail --silent http://127.0.0.1:30000/health' \
  --health-interval 30s --health-timeout 10s \
  --health-start-period 10m --health-retries 5 \
  dgxspark/qwen3.8-27b-fp8-sglang:0.1.0
```

## Error Or Observation

Started at 21:02:25 UTC. The recurring nonfatal capacity-query fallback and
missing optional torchcodec import were observed, as in RUN-0012. The model
loaded from cache: target 198.64 seconds / 29.11 GB, MTP 3.36 seconds / 5.41 GB.

Allocated Mamba state: 256 slots, 0.71 GB convolution, 18.07 GB SSM,
18.28 GB intermediate SSM, 0.36 GB intermediate convolution windows. Target
BF16 KV capacity: 294176 slots, K/V 8.98 GB each; draft K/V 0.56 GB each.
Available memory after draft KV allocation was 22.21 GB. Prefill graph capture
completed in 26.90 seconds. Target verify graphs explicitly covered batch sizes
through 64, followed by draft graph preparation.

A Docker health probe reached HTTP before readiness:

```text
[21:07:07] GET /health HTTP/1.1 503 Service Unavailable
[21:07:17] The server is fired up and ready to roll!
[21:07:18] GET /health HTTP/1.1 200 OK
```

## Diagnosis And Fix

The 503 was transient startup readiness, not a loaded-server inference failure;
it occurred within the configured health-check grace period. Waiting for graph
capture and the server warmup resolved it. The GPU memory query fallback is
expected on this unified-memory target, and missing torchcodec did not block
text. No driver, package, or attention-backend change was required.

## Verification

Docker reported healthy. The same four smoke checks as RUN-0012 passed via
uv-managed Python 3.12: exact text, arithmetic `17 * 19 = 323`, JSON sorting,
and the primary Responses API's expected ready message. The script is
`/tmp/qwen-capacity64-smoke.py`; responses are `/tmp/qwen-capacity64-smoke.json`.
These are small-fixture checks, not a quality or full-context capacity study.

The reusable benchmark runner now supports explicit request/warmup counts,
`auto` sizing (at least 96 measured requests and four batches per concurrency,
one full warmup batch), and a seed base. It rejects measured request counts
below the requested concurrency. Existing baseline defaults remain 32/4.

## Lesson

To locate a throughput plateau, raise the active scheduler limit and associated
state pool together, verify graph coverage, and sustain several batches per
profile. A high client concurrency alone can merely increase queue length.

## Next Step

Sweep 4, 8, 16, 24, 32, 48, and 64 under the fixed expanded server, then refine
and repeat around the strongest settings. Interpret any maximum as specific
to the tested workload, runtime, and memory budget.
