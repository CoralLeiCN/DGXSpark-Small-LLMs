# 2026-09-05T21:22:36Z — Gemma text API qualified on DGX Spark

Run ID: `RUN-0002`

- Status: resolved
- Phase: model load and inference
- Related turns: [Official runtime image restored GPU preflight semantics](2026-09-05T21-22-01Z-official-runtime-preflight.md)
- Repo revision: `4fe8345` plus uncommitted Gemma recipe and journal changes
- Host/GPU: DGX Spark, NVIDIA GB10, ARM64, 124610 MiB unified memory reported by PyTorch, Linux `6.17.0-1031-nvidia`
- Container: `dgxspark/gemma-4-26b-a4b-it-sglang:0.1.0` (`sha256:1ea5c92343e3caba5f9c71face3c97845779052d6ebf564aeff516ea8e30fe02`), based on `lmsysorg/sglang:dev-qwen38-27b-dflash2` (`sha256:616a3e97f45191af975896cfa644279096cb31bd408a071c2e99ca7209c3cafe`)
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, PyTorch `2.13.0+cu130`, Transformers `5.12.1`, CUDA 13.0
- Model: `google/gemma-4-26B-A4B-it`, revision `4d7ae4984b7db7de8f8457170b3f1a419ee76d52`, BF16

## Command

```bash
scripts/deploy google/gemma-4-26b-a4b-it --engine sglang
curl --fail --silent --show-error http://127.0.0.1:30000/health
curl --fail --silent --show-error http://127.0.0.1:30000/v1/models
scripts/validate google/gemma-4-26b-a4b-it --engine sglang --timeout 600
```

## Error Or Observation

```text
Load weight end. elapsed=312.45 s, type=Gemma4ForConditionalGeneration,
avail mem=66.05 GB, mem usage=47.23 GB.
SWAKVPool mem usage: 36.69 GB, swa size: 171008, full size: 213761
Capture target decode CUDA graph end. elapsed=25.74 s, mem usage=2.66 GB,
avail mem=24.45 GB.
Engine startup timings (s): load_weight=312.45, scheduler_e2e=361.83,
tokenizer_e2e=366.77
The server is fired up and ready to roll!
```

The current Hugging Face `main` revision differed from the initially cached
snapshot. SGLang logged that the new snapshot did not yet contain weights and
would attempt a download, but the underlying blobs were unchanged: cache size
remained 49 GiB, container network traffic stayed below 310 KiB, and both
safetensor shard links appeared under the new revision.

SGLang also reported that tuned Triton MoE configuration files for NVIDIA GB10
were unavailable and used its default kernel configuration. This is a
performance qualification gap, not a correctness failure in this run.

## Diagnosis

- Symptom: the earlier deploy did not pass GPU preflight; this retry reached
  readiness and served a correct completion without a restart or OOM.
- Root cause: the earlier failure was isolated to using a completed model image
  as a preflight base. The official raw SGLang image and the cached Gemma weights
  were compatible with the GB10.
- Evidence: the model loaded as `Gemma4ForConditionalGeneration`; Docker showed
  zero restarts and `OOMKilled=false`; SGLang's warmup chat request returned HTTP
  200; and host health, model listing, and chat validation all returned HTTP 200.

## Fix Or Change

A dedicated model recipe was added with a 32,768-token initial context,
`--mem-fraction-static 0.75`, four maximum running requests, explicit Triton
attention, and the `gemma4` reasoning and tool-call parsers. The official
SGLang runtime image was restored and used as the build base.

## Verification

Observed host results:

```text
Model: gemma-4-26b-a4b-it
Maximum model length: 32768
Response: DGX Spark Gemma ready
Container before shutdown: running, zero restarts, OOMKilled=false
```

SGLang logged HTTP 200 for `/health`, `/v1/models`, and
`/v1/chat/completions`. This turn qualified text input only; image input,
tool-calling behavior, and long-context capacity were not exercised.

## Lesson

The BF16 Gemma 4 26B-A4B checkpoint fits on one DGX Spark at a 0.75 static
memory fraction with substantial hybrid-attention cache capacity. A complete
cached snapshot can absorb a metadata-only revision change without redownloading
unchanged weight blobs, but the exact resolved revision should still be recorded.

## Next Step

Stop the service as requested and confirm that the container and published port
are removed while the named compiler caches remain.
