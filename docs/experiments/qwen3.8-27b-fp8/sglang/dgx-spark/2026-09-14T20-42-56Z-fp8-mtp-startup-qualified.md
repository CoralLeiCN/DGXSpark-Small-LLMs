# 2026-09-14T20:42:56Z — Native FP8 MTP startup and API smoke checks qualified

Run ID: `RUN-0012`

- Status: workaround (existing capacity fallback; MTP text serving qualified)
- Phase: engine startup / model load / health check / inference
- Related turns: [plain FP8 baseline](2026-09-14T20-12-03Z-aiperf-concurrency-baseline.md),
  [prior startup warnings](2026-09-14T19-52-51Z-benchmark-startup-qualified.md)
- Repo revision: `17d39b06860ea7159a3d4a3443053b4d79bf867e`, dirty with benchmark files
- Host/GPU: DGX Spark, Linux aarch64, GB10, driver `580.173.02`
- Container: isolated `inferpack-qwen38-fp8-mtp-bench`, using
  `dgxspark/qwen3.8-27b-fp8-sglang:0.1.0`, image
  `sha256:3c11adf54d4a220f587f361f48eee66b50a8e2b8c068db7484c598beb3684b62`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, FlashInfer `0.6.17`,
  torch `2.13.0+cu130`, transformers `5.12.1`
- Target and MTP checkpoint: `Qwen/Qwen3.8-27B-FP8`, revision
  `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`, both loaded as FP8 e4m3
- Configuration: original TP 1, FlashInfer attention, BF16 GDN and KV,
  32768 context, memory fraction 0.45, max running requests 4, Mamba slots 16,
  prefill chunk 2048, `extra_buffer_lazy`, metrics enabled. Added native MTP
  through EAGLE with steps 3, top-k 1, and 4 draft tokens. ReplaySSM was not enabled.

## Command

```bash
docker run -d --name inferpack-qwen38-fp8-mtp-bench \
  --gpus all --ipc host --shm-size 32gb \
  --ulimit memlock=-1 --ulimit stack=67108864 \
  --volumes-from dgxspark-qwen3-8-27b-fp8-sglang-1 \
  -p 127.0.0.1:30000:30000 \
  -e HF_HUB_DISABLE_IMPLICIT_TOKEN=1 -e HF_HUB_OFFLINE=1 \
  -e MODEL_ID=Qwen/Qwen3.8-27B-FP8 \
  -e SERVED_MODEL_NAME=qwen3.8-27b-fp8 \
  -e CONTEXT_LENGTH=32768 -e MEM_FRACTION_STATIC=0.45 \
  -e MAX_RUNNING_REQUESTS=4 -e MAX_MAMBA_CACHE_SIZE=16 \
  -e CHUNKED_PREFILL_SIZE=2048 \
  -e 'SGLANG_EXTRA_ARGS=--enable-metrics --speculative-algorithm EAGLE --speculative-num-steps 3 --speculative-eagle-topk 1 --speculative-num-draft-tokens 4' \
  --health-cmd 'curl --fail --silent http://127.0.0.1:30000/health' \
  --health-interval 30s --health-timeout 10s \
  --health-start-period 10m --health-retries 5 \
  dgxspark/qwen3.8-27b-fp8-sglang:0.1.0
```

Started at 20:37:47 UTC on the idle GPU. Reused cached volumes from the stopped
baseline container. No additional checkpoint was downloaded or dependency
installed. The baseline container configuration was retained.

## Error Or Observation

The same nonfatal startup warnings as RUN-0008 recurred:

```text
Failed to get GPU memory capacity from nvidia-smi. Falling back to
torch.cuda.mem_get_info(). Reported total GPU memory per device (MiB): [124610]
torchcodec is not installed; audio inputs will fail at request time
Ignore import error when loading sglang.srt.multimodal.processors.mimo_v2:
No module named 'torchcodec'
```

Target loading took 181.47 seconds and 29.09 GB. The same snapshot supplied
`Qwen3_5ForCausalLMMTP`, loaded in 3.16 seconds using another 5.29 GB.
Both load records declared `quant=fp8, fmt=e4m3`.

The 16-slot Mamba cache allocated 0.05 GB convolution state, 1.20 GB SSM state,
1.41 GB intermediate SSM state, and 0.03 GB intermediate convolution windows.
Target KV capacity was 221044 tokens, with K/V at 6.75 GB each; draft K/V
added 0.42 GB each. This is below the plain baseline's 341648 KV slots, but
comfortably above this experiment's short-context requirement. Prefill, target
verify, draft decode, and draft extend graph capture all completed. Readiness
was announced at 20:41:53 UTC, approximately four minutes after start.

## Diagnosis And Configuration Choice

The installed image supports native MTP and its FlashInfer source includes
`uniform_q_len`, the interface required by the
[official SGLang MTP recipe](https://docs.sglang.io/cookbook/autoregressive/Qwen/Qwen3.8-27B).
No attention-backend fallback was needed. The capacity warning is handled by
the runtime's PyTorch fallback; the missing audio dependency does not block
the tested text path. No audio inference was attempted.

Using the existing FP8 MTP head keeps target weights unchanged. MTP still adds
draft-model allocations and verification state; it is not memory-free. The
existing 0.45 allocation and four-request limit fit without a cache-size change.

## Verification

Docker reported healthy. Three greedy, thinking-disabled chat requests passed:

- Exact text: `DGX Spark ready`.
- Arithmetic: `17 * 19` returned `323`.
- JSON sorting: `9, 2, 5` returned `[2, 5, 9]`.

The primary `/v1/responses` endpoint also returned status `completed` and the
expected `DGX Spark SGLang ready`, with temperature 0.6, top-p 0.95, thinking
disabled, and max output 512. The chat checks used max tokens 128.

The checks ran via uv-managed Python 3.12 using the standard-library HTTP
client. The script and full responses are retained as `qwen-mtp-smoke.py` and
`qwen-mtp-smoke.json` under the subsequent benchmark's local artifact directory
`models/qwen3.8-27b-fp8/sglang/targets/dgx-spark/artifacts/2026-09-14T20-37-47Z-mtp/`.
These are small correctness smoke checks, not a quality benchmark or proof of
token-for-token equivalence with ordinary decoding.

## Lesson

FP8 target weights do not preclude native speculative decoding. Check the
installed MTP and attention-backend interfaces, then budget draft and verify
state explicitly and validate actual responses before timing the configuration.

## Next Step

Run the same AIPerf workload and concurrency sweep as RUN-0010 and verify draft
acceptance in runtime evidence.
