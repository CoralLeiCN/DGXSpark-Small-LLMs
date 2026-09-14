# 2026-09-14T19:52:51Z — Warm-cache startup qualified for benchmarking

Run ID: `RUN-0008`

- Status: workaround (GPU capacity fallback; text inference qualified)
- Phase: engine startup / model load / health check / inference
- Related turns: [host preflight](2026-09-14T19-47-23Z-benchmark-host-preflight.md),
  [45 percent allocation qualification](2026-09-07T12-47-42Z-reduced-memory-qualified.md)
- Repo revision: `17d39b06860ea7159a3d4a3443053b4d79bf867e`, dirty with benchmark files
- Host/GPU: DGX Spark, Linux aarch64, GB10; driver `580.173.02`, CUDA capability `13.0`
- Container: `dgxspark/qwen3.8-27b-fp8-sglang:0.1.0`, image
  `sha256:3c11adf54d4a220f587f361f48eee66b50a8e2b8c068db7484c598beb3684b62`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, torch `2.13.0+cu130`, transformers `5.12.1`
- Model: `Qwen/Qwen3.8-27B-FP8`, revision
  `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`, FP8 e4m3 weights
- Launch: TP 1, FlashInfer attention, context 32768, static memory fraction 0.45,
  max running requests 4, Mamba slots 16, BF16 GDN state, prefill chunk 2048,
  `extra_buffer_lazy`, `qwen3` reasoning and `qwen3_coder` tool parsers,
  `--enable-metrics`, no speculative decoding

## Command

```bash
docker start dgxspark-qwen3-8-27b-fp8-sglang-1
docker logs --since 10m dgxspark-qwen3-8-27b-fp8-sglang-1
```

The existing stopped container was started on an idle GPU. No other model
container was running; no service was stopped to make room.

## Error Or Observation

Startup logged these nonfatal limitations:

```text
Failed to get GPU memory capacity from nvidia-smi. Falling back to
torch.cuda.mem_get_info(). Reported total GPU memory per device (MiB): [124610]
torchcodec is not installed; audio inputs will fail at request time
Ignore import error when loading sglang.srt.multimodal.processors.mimo_v2:
No module named 'torchcodec'
```

The cached snapshot was used without downloading weights. Weight loading
finished at 19:51:05 UTC in 181.95 seconds, using 29.03 GB. SGLang allocated
16 Mamba slots (0.05 GB convolution state, 1.20 GB SSM state) and 341648 KV
token slots in BF16 (10.43 GB each for K and V). Available memory after pool
allocation was 62.67 GB. The service announced readiness at 19:51:40 UTC,
about four minutes after container start.

## Diagnosis

The engine's nvidia-smi capacity query cannot supply capacity on this unified
memory GPU, but its PyTorch fallback successfully sizes memory. This differs
from the sandbox inspection failure recorded in RUN-0006. Missing torchcodec
affects the optional audio path; the text benchmark does not exercise it.

## Fix Or Change

Retained the existing recipe and accepted the runtime's capacity fallback.
No packages were added. Explicitly disabled thinking in the text smoke request
because the server detects `enable_thinking=True` as the model default.

## Verification

```bash
curl --fail http://127.0.0.1:30000/health
curl --fail http://127.0.0.1:30000/v1/models
curl --fail http://127.0.0.1:30000/v1/chat/completions \
  -H 'Content-Type: application/json' --data-binary \
  '{"model":"qwen3.8-27b-fp8","messages":[{"role":"user","content":"Reply with exactly: DGX Spark ready"}],"max_tokens":64,"temperature":0,"chat_template_kwargs":{"enable_thinking":false}}'
```

Health and model listing succeeded. The smoke request returned `DGX Spark ready`,
five completion tokens, zero reasoning tokens, and stop termination. Docker
reported healthy, zero restarts, and no OOM kill. Audio remains unverified.

## Lesson

Wait for readiness after warm-cache loading and graph capture. Check the actual
thinking default and verify an explicit override before comparing fixed-output
text performance. Treat optional audio dependency failures separately from
validated text inference.

## Next Step

Run the streaming benchmark using the local tokenizer snapshot.
