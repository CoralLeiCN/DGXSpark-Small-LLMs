# 2026-09-05T23:07:59Z — Gemma E4B text API qualified after cold download

Run ID: `RUN-0001`

- Status: resolved
- Phase: model load and inference
- Related turns: `none`
- Repo revision: `ac2df44` plus uncommitted E4B recipe and journal changes
- Host/GPU: DGX Spark, NVIDIA GB10, ARM64, 124610 MiB unified memory reported by PyTorch, Linux `6.17.0-1031-nvidia`
- Container: `dgxspark/gemma-4-e4b-it-sglang:0.1.0` (`sha256:326c8aa85e4ac705f9e7ed17ea19ac079851a56c97cfc87bb9a9715a968baf41`), based on `lmsysorg/sglang:dev-qwen38-27b-dflash2` (`sha256:616a3e97f45191af975896cfa644279096cb31bd408a071c2e99ca7209c3cafe`)
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, PyTorch `2.13.0+cu130`, Transformers `5.12.1`, CUDA 13.0
- Model: `google/gemma-4-E4B-it`, revision `ee0ef6023621cff504d758262d4e04895a5af4a2`, BF16

## Command

```bash
scripts/preflight google/gemma-4-e4b-it --engine sglang
scripts/deploy google/gemma-4-e4b-it --engine sglang
curl --fail --silent --show-error http://127.0.0.1:30000/health
curl --fail --silent --show-error http://127.0.0.1:30000/v1/models
scripts/validate google/gemma-4-e4b-it --engine sglang --timeout 600
```

## Error Or Observation

```text
Load weight end. elapsed=2415.46 s, type=Gemma4ForConditionalGeneration,
avail mem=97.30 GB, mem usage=15.56 GB.
SWAKVPool mem usage: 79.94 GB, swa size: 798276, full size: 997846
Capture target decode CUDA graph end. elapsed=22.18 s, mem usage=1.91 GB,
avail mem=14.18 GB.
Engine startup timings (s): load_weight=2415.46, scheduler_e2e=2456.47,
tokenizer_e2e=2461.44
The server is fired up and ready to roll!
```

The cold-cache run downloaded one 15,992,595,884-byte safetensors file. The
container also warned that `torchcodec` was not installed and audio inputs
would fail at request time. Audio was not invoked in this text qualification.

## Diagnosis

- Symptom: the first deployment spent about 40 minutes in the weight-loading
  phase before reaching readiness, then returned the expected text completion.
- Root cause: most of the startup time was an anonymous, uncached Hugging Face
  download and Xet reconstruction of the single 15.99 GB weight object; this
  was not an engine hang or compatibility failure.
- Evidence: cache and container network usage advanced throughout the quiet
  period; the completed snapshot linked the expected blob; SGLang loaded the
  model as `Gemma4ForConditionalGeneration`; and Docker reported zero restarts
  with `OOMKilled=false`.

## Fix Or Change

A dedicated E4B recipe was added with a 32,768-token qualification context,
`--mem-fraction-static 0.85`, four maximum running requests, explicit Triton
attention, and the `gemma4` reasoning and tool-call parsers. No runtime retry or
workaround was required; preserving the original process allowed the cold
download to complete.

## Verification

Observed host results:

```text
Model: gemma-4-e4b-it
Maximum model length: 32768
Response: DGX Spark Gemma E4B ready
Container before shutdown: healthy, zero restarts, OOMKilled=false
```

SGLang logged HTTP 200 for its warmup chat request and the independent host
health, model-listing, and chat validation all succeeded. This turn qualified
text input only; multimodal input, tool calling, and long-context capacity were
not exercised.

## Lesson

Gemma 4 E4B BF16 fits on one DGX Spark with substantial hybrid-attention cache
capacity at a 0.85 static-memory fraction. During an uncached Xet download, the
single output file may advance in large flushes while inbound traffic and
process activity provide the more reliable liveness signals.

## Next Step

Stop the service as requested and confirm container removal and port closure.
