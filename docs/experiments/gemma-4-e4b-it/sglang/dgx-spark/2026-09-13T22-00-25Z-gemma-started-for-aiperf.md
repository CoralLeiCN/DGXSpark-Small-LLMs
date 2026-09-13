# 2026-09-13T22:00:25Z — Gemma started and validated for AIPerf

Run ID: `RUN-0004`

- Status: workaround (text serving qualified; GPU-capacity fallback and missing
  audio dependency remain)
- Phase: engine startup / health check / inference
- Related turns: [AIPerf client preflight](2026-09-13T21-46-37Z-aiperf-client-preflight.md),
  [initial text qualification](2026-09-05T23-07-59Z-text-api-qualified.md)
- Repo revision: `0d0acca2289c8d0475ba3c8dab76b366e4f150da`, dirty with benchmark
  documentation changes
- Host/GPU: DGX Spark, Linux aarch64, one GPU; PyTorch reported 124610 MiB total
- Container: `dgxspark/gemma-4-e4b-it-sglang:0.1.0`, image
  `sha256:326c8aa85e4ac705f9e7ed17ea19ac079851a56c97cfc87bb9a9715a968baf41`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, torch `2.13.0+cu130`,
  transformers `5.12.1`
- Model: `google/gemma-4-E4B-it`, cached revision
  `ee0ef6023621cff504d758262d4e04895a5af4a2`, BF16 with no quantization override
- Launch: context 32768, memory fraction 0.85, max running requests 4,
  Triton attention, TP 1, Gemma 4 reasoning/tool parsers, no extra launch flags

## Command

The user explicitly authorized stopping the current service and running Gemma.

```bash
docker stop --timeout 120 dgxspark-qwen3-8-27b-fp8-sglang-1
scripts/serve gemma-4-e4b-it --engine sglang --target dgx-spark
docker logs --tail 18 dgxspark-gemma-4-e4b-it-sglang-1
```

## Error Or Observation

```text
Failed to get GPU memory capacity from nvidia-smi. Falling back to torch.cuda.mem_get_info().
Reported total GPU memory per device (MiB): [124610]
torchcodec is not installed; audio inputs will fail at request time
Ignore import error when loading sglang.srt.multimodal.processors.mimo_v2: No module named 'torchcodec'
2026-09-13 21:59:36 GET /health HTTP/1.1 503 Service Unavailable
2026-09-13 21:59:42 The server is fired up and ready to roll!
2026-09-13 21:59:43 GET /health HTTP/1.1 200 OK
```

## Diagnosis

The runtime could not obtain GPU memory capacity through nvidia-smi and used its
built-in PyTorch fallback successfully. No driver fault was established. Missing
torchcodec is the previously observed optional audio limitation; it did not
prevent text startup. The transient health 503 occurred after Uvicorn started
but before SGLang finished its own warmup and GC freezing. Subsequent readiness
and inference checks passed without a restart.

## Fix Or Change

Stopped Qwen without removing its container, then started the existing Gemma
image through the repository recipe. Waited for the engine's readiness message
before external validation. Kept the known working text recipe unchanged.

Weights loaded from the existing snapshot in 95.45 seconds, using 15.73 GB of
memory. SGLang allocated 80.05 GB of BF16 full/sliding-window KV pools. Template
detection reported `enable_thinking` with `default_enabled=False`.

## Verification

```bash
curl --fail --silent --show-error --max-time 10 http://127.0.0.1:30000/health
curl --fail --silent --show-error --max-time 10 http://127.0.0.1:30000/v1/models
scripts/validate gemma-4-e4b-it --engine sglang --target dgx-spark --timeout 120
```

Health returned success, model listing identified `gemma-4-e4b-it` with a 32768
context, and chat validation returned `DGX Spark Gemma E4B ready`. Docker
reported Gemma running and healthy. Qwen was stopped. No image rebuild or
weight download was needed. AIPerf was launched after this validation; this
startup turn contains no benchmark measurements.

## Lesson

An HTTP listener can be available before the engine finishes startup. Wait for
readiness and validate the served model and a chat response before measuring
latency. Keep startup, warmup, and timed benchmark phases distinct.

## Next Step

Complete the AIPerf concurrency comparison and record results in a new turn.
