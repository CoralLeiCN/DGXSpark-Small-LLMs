# Qwen3.8 27B FP8

This recipe serves
[`Qwen/Qwen3.8-27B-FP8`](https://huggingface.co/Qwen/Qwen3.8-27B-FP8)
on one DGX Spark GPU through SGLang's OpenAI-compatible API.

Status: experimental. On 2026-09-04, the image built and the model completed
health, model-listing, Responses API, and chat-completion validation on a DGX
Spark. The tested
runtime was SGLang `0.0.0.dev1+g5f55db35e` with model revision
`017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`.

## Deployment

```bash
# Optional for this public model: export HF_TOKEN=hf_example
scripts/deploy qwen3.8-27b-fp8 --engine sglang --target dgx-spark
scripts/logs qwen3.8-27b-fp8 --engine sglang --target dgx-spark
scripts/validate-responses qwen3.8-27b-fp8 --engine sglang --target dgx-spark --timeout 600
scripts/stop qwen3.8-27b-fp8 --engine sglang --target dgx-spark
```

`HF_TOKEN` is optional while the model remains public. Model weights persist
under `$HF_CACHE_DIR`; the default is `$HOME/.cache/huggingface`. The service
listens on `http://localhost:30000` by default.

The Responses API at `/v1/responses` is this recipe's primary validation and
application path. `scripts/validate` follows the endpoint selected by the model
manifest, while `scripts/validate-responses` explicitly tests Responses API
compatibility.

The observed first start with an empty cache took about 89 minutes from weight
download through CUDA graph capture. Warm-cache starts avoid that download. The
Compose health check allows 90 minutes before failed probes count against
service health.

## Configuration

Export values from `sglang/targets/dgx-spark/.env.example` in the invoking
shell before running a script.

| Variable | Default | Purpose |
| --- | --- | --- |
| `SGLANG_BASE_IMAGE` | `lmsysorg/sglang:dev-qwen38-27b-dflash2` | Qwen3.8-capable official SGLang image |
| `SGLANG_PORT` | `30000` | Host API port |
| `CONTEXT_LENGTH` | `32768` | Initial qualification context limit |
| `MEM_FRACTION_STATIC` | `0.45` | Unified-memory fraction for model and runtime caches |
| `MAX_RUNNING_REQUESTS` | `4` | Scheduler concurrency cap |
| `MAX_MAMBA_CACHE_SIZE` | `16` | Four GDN state slots per request with `extra_buffer_lazy` |
| `CHUNKED_PREFILL_SIZE` | `2048` | Prefill chunk size chosen to avoid long decode stalls |
| `HF_CACHE_DIR` | `$HOME/.cache/huggingface` | Persistent model cache |
| `SGLANG_EXTRA_ARGS` | unset | Additional model-specific launch arguments |

DGX Spark's 128 GB is unified with the host. The default static allocation
fraction is `0.45` to leave room for a separate embedding service and the host.
This reduces cache capacity compared with the earlier `0.80` standalone
configuration. It is an SGLang allocation target, not a hard container RAM
limit; activations and other services also consume unified memory. Keep the
32K context and four-request limits unless workload validation justifies
changing them. Export `MEM_FRACTION_STATIC=0.80` only when dedicating the host
to this service and after checking available memory.

Start Qwen3.8 first and wait for readiness before starting another GPU service.
SGLang profiles free memory around weight loading, so concurrent startup can
charge another service's allocations against this model's cache budget.

Qwen3.8 is a hybrid Gated DeltaNet model, so the GDN state cache must be sized
alongside the paged attention KV cache. With the `extra_buffer_lazy` strategy,
four state slots are reserved per active request. The defaults pair four active
requests with 16 slots rather than relying on SGLang's generic memory-ratio
heuristic.

The model supports a native 262,144-token context. The 32K default is a
conservative first operating point for this repository and can be increased
after workload-specific concurrency and host-memory validation.

## Performance Benchmark

On 2026-09-14, the existing FP8 recipe on one DGX Spark produced these AIPerf
results with thinking disabled and 128 output tokens per request:

| Concurrent requests | Aggregate output tokens/s | Per-user decode tokens/s | Median TTFT | Median request latency |
| --- | --- | --- | --- | --- |
| 1 | 8.06 | 8.22 | 0.414 s | 15.83 s |
| 2 | 15.84 | 8.25 | 0.718 s | 15.84 s |
| 4 | 30.85 | 8.26 | 1.188 s | 16.60 s |

All 96 measured requests succeeded. Actual input lengths were 524–526 tokens.
Concurrency 4 increased aggregate throughput 3.82 times while per-user decode
speed stayed near 8.3 tokens/s. These results use the 0.45 memory fraction and
four-request limit, with no speculative decoding. See the
[full benchmark record](../../docs/experiments/qwen3.8-27b-fp8/sglang/dgx-spark/2026-09-14T20-12-03Z-aiperf-concurrency-baseline.md)
for p95 latency, exact versions, methodology, and limitations.

Reference comparison checked on 2026-09-14: treat this as a plausible plain-FP8
baseline, not an optimized single-user performance result. NVIDIA specifies
[273 GB/s memory bandwidth](https://www.nvidia.com/en-us/products/workstations/dgx-spark/),
and the [SGLang cookbook](https://docs.sglang.io/cookbook/autoregressive/Qwen/Qwen3.8-27B)
estimates FP8 weights at about 28.5 GB. Assuming roughly one weight read per
ordinary decode step gives a simplified bandwidth estimate of
`273 / 28.5 = 9.6 tokens/s` before other costs. This is a sanity check, not a
measured bottleneck diagnosis, exact roofline, or limit for speculative decoding.

[SGLang's official announcement](https://www.linkedin.com/posts/sgl-project_the-king-of-small-models-is-back-qwen38-activity-7494117214267273216-Pw-c)
promotes NVFP4 plus DSpark and reports 38.28 decode tokens/s on DGX Spark.
Its short post omits the complete workload and measurement protocol; it is not
a matched plain-FP8 baseline. The current cookbook documents MTP, DSpark, and
DFlash2 options and validates configurations on v0.5.19, but explicitly says
throughput was not remeasured in that validation sweep. Our older pinned
development runtime and no-speculation result must not be compared as though
these settings were identical.

For an additional independent, non-official reference,
[0xBakeer's measured vLLM FP8 baseline](https://github.com/0xBakeer/Qwen3.8-27B-FP8-on-a-single-DGX-Spark/blob/main/RESULTS.md)
reports 7.88 tokens/s with speculation off, and 17.70 with MTP on a fresh-code
workload. These use different prompts, output lengths, and device allocations;
they provide context, not a reproduction or guaranteed tuning target. The native
MTP comparison below uses the same FP8 checkpoint and pinned runtime with
matched input fixtures; its small correctness checks do not establish general
quality equivalence.

With this model healthy on port 30000, run the pack's AIPerf baseline:

```bash
models/qwen3.8-27b-fp8/sglang/targets/dgx-spark/benchmark-aiperf.sh
```

The runner uses AIPerf `0.12.0` in an isolated uv-managed Python 3.12
environment. It measures streaming `/v1/chat/completions` at concurrency
1, 2, and 4, with four warmups and 32 measured requests per setting. Requests
target 512 input tokens and force 128 output tokens with `ignore_eos=true`,
temperature zero, and thinking explicitly disabled. The server's default
thinking mode is enabled; this benchmark overrides it per request. Actual
input counts include chat formatting and can exceed 512. Metrics use the
server's token counts.

The tokenizer defaults to `Qwen/Qwen3.8-27B-FP8` revision
`017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`. Use
`QWEN_TOKENIZER_REVISION` to match another deployed checkpoint. With AIPerf
and the tokenizer already cached, `UV_OFFLINE=1 HF_HUB_OFFLINE=1` avoids
registry and tokenizer network access. AIPerf 0.12.0 offline mode requires a
Hugging Face repository ID, even for a locally cached tokenizer; passing a
snapshot filesystem path fails during dataset configuration.

Pass concurrency levels as arguments or set `BENCHMARK_URL` to change the
server origin. Verify `/v1/models` identifies this model before running.
`QWEN_REQUEST_COUNT` and `QWEN_WARMUP_COUNT` override profile sizes; setting
both to `auto` uses at least 96 measured requests and four batches per
concurrency, plus one full warmup batch. The runner rejects a measured count
below concurrency. `QWEN_SEED_BASE` sets the seed to that value plus concurrency.
Raise the server's active-request limit, Mamba pool, and graph coverage before
testing larger active batches; extra client requests otherwise measure queuing
behind the existing scheduler cap.
`QWEN_BENCHMARK_ROOT` selects a new artifact directory; by default, JSON/CSV
summaries, per-request records, generated inputs, and logs go under the pack's
ignored `artifacts/` directory. Existing output directories are not overwritten.

This is a short synthetic text baseline. It does not measure natural stopping,
reasoning, multimodal inputs, long contexts, or sustained production capacity.
Prefix caching remains enabled and is not flushed; different seeds are used
for each concurrency. The current server does not report cache-read tokens,
so AIPerf cannot quantify prefix-cache hits. Warmups are excluded, and client
GPU telemetry and server-metric collection are disabled. The runner does not
start, stop, or reconfigure services.

A [host telemetry check](../../docs/experiments/qwen3.8-27b-fp8/sglang/dgx-spark/2026-09-14T22-48-06Z-gpu-telemetry-support.md)
verified GPU temperature, utilisation, and power draw on GB10 with driver
`580.173.02`. GPU memory used/total returned `N/A` on the shared-memory device.
Collection through AIPerf itself remains unverified.

### Estimated model TFLOPS

When `--enable-metrics` is present (including through `make start`), this pack
also adds `--enable-mfu-metrics`. Rebuild the image and recreate the service to
apply the updated launch script; `make start MODEL=qwen3.8-27b-fp8` does both.
The shared Grafana dashboard plots
`rate(sglang:estimated_flops_per_gpu_total[1m]) / 1e12`, with its selected
filters and adaptive rate interval. The counter measures estimated operations;
its rate includes idle time. It does not need DCGM or GPU hardware counters.

Treat this as an approximate SGLang model-operation rate. The pinned image's
estimator uses attention and MLP dimensions rather than complete kernel
accounting for Qwen's hybrid GDN layers or MTP draft/verification work. It is
not measured FP8 throughput or a reliable hardware MFU percentage. AIPerf's
benchmark runner still disables server-metric collection; Prometheus collects
the counter independently when monitoring is running.

[Live verification with ordinary decoding](../../docs/experiments/qwen3.8-27b-fp8/sglang/dgx-spark/2026-09-14T23-46-12Z-mfu-live-validation.md)
passed Responses and Chat Completions inference, counter increments, and the
TFLOPS query through Prometheus and Grafana. An
[earlier check with native MTP](../../docs/experiments/qwen3.8-27b-fp8/sglang/dgx-spark/2026-09-14T22-54-51Z-sglang-estimated-tflops.md)
also passed inference and the Prometheus rate query.

## Native MTP Speculative Decoding

On 2026-09-14, native MTP improved the same synthetic benchmark with identical
generated inputs, 128 output tokens, and thinking disabled:

| Concurrent requests | Plain FP8 total output tokens/s | FP8 MTP total output tokens/s | Plain / MTP median latency |
| --- | --- | --- | --- |
| 1 | 8.06 | 15.20 | 15.83 / 8.50 s |
| 2 | 15.84 | 29.83 | 15.84 / 8.53 s |
| 4 | 30.85 | 52.26 | 16.60 / 9.58 s |

Single-user decode averaged 15.85 tokens/s with MTP, versus 8.22 without it.
All 96 measured MTP requests and 12 warmups passed. Aggregate gains were about
1.9x at concurrency 1–2 and 1.7x at concurrency 4. This is one short profile
per setting, with content-dependent acceptance; it does not establish general
quality equivalence or long-context capacity. See the
[full MTP comparison](../../docs/experiments/qwen3.8-27b-fp8/sglang/dgx-spark/2026-09-14T20-53-32Z-fp8-mtp-concurrency-benchmark.md)
for versions, p95 latency, acceptance evidence, memory costs, and limitations.

The FP8 checkpoint includes its own MTP head. Enable it with the model-specific
extra arguments, then recreate the service:

```bash
export SGLANG_EXTRA_ARGS="--enable-metrics --speculative-algorithm EAGLE --speculative-num-steps 3 --speculative-eagle-topk 1 --speculative-num-draft-tokens 4"
scripts/serve qwen3.8-27b-fp8 --engine sglang --target dgx-spark
scripts/validate-responses qwen3.8-27b-fp8 --engine sglang --target dgx-spark --timeout 600
```

The tested runtime was SGLang `0.0.0.dev1+g5f55db35e` with FlashInfer `0.6.17`.
Both the target and `Qwen3_5ForCausalLMMTP` loaded from the same FP8 snapshot;
no separate draft checkpoint was downloaded. Target, draft, and verification
buffers fit the existing 0.45 memory fraction, 32768 context, four-request
limit, and 16 Mamba slots. Target KV capacity fell from 341648 to 221044 slots.
Full-context concurrency remains unqualified. ReplaySSM was not enabled.

The [startup record](../../docs/experiments/qwen3.8-27b-fp8/sglang/dgx-spark/2026-09-14T20-42-56Z-fp8-mtp-startup-qualified.md)
records the exact isolated-container command, memory observations, and API
smoke checks. Those checks covered exact text, arithmetic, JSON, and Responses
API output; they do not prove token-for-token equivalence with ordinary decoding.

To return to ordinary decoding, set `SGLANG_EXTRA_ARGS="--enable-metrics"` and
rerun the same `scripts/serve` command. The default configuration keeps MTP off.

## Throughput Capacity

On 2026-09-14, a dedicated DGX Spark concurrency sweep selected **64 requests
in flight** as the best tested setting for this FP8 native-MTP workload.
Two matched runs averaged **207.35 aggregate output tokens/s** at concurrency
64, versus 204.02 at 56. The practical top is around 56–64; 56 gave about
1.6% less throughput with 11% lower median latency. Higher tested concurrency
reduced throughput.

The refined comparison used one fixed server configuration and identical
generated inputs (seed 3000), with 384 measured requests and 96 warmups per row:

| Concurrent requests | Aggregate output tokens/s | Median request latency |
| --- | --- | --- |
| 48 | 199.10 | 30.16 s |
| 56 | 204.78 | 34.48 s |
| 64 | **207.79** | 39.11 s |
| 72 | 200.75 | 44.74 s |
| 80 | 195.90 | 51.90 s |
| 96 | 172.49 | 69.69 s |

Repeating 56 and 64 with seed 5000 produced 203.26 and 206.91 tokens/s,
respectively. Concurrency 64 won both paired seeds; its pooled median latency
was 39.07 seconds, p95 latency 50.93 seconds, and median TTFT 2.37 seconds.
This identifies the best sampled concurrency, with a broad peak rather than
a proven unique optimum among every integer value.

Across all 15 capacity profiles, **4,032 measured requests and 964 warmups
passed**, each with exactly 128 output tokens. The initial sweep also measured
4, 8, 16, 24, and 32 before extending through 96 and refining around the peak.
See the [confirmed peak and full experiment chain](../../docs/experiments/qwen3.8-27b-fp8/sglang/dgx-spark/2026-09-14T22-17-48Z-mtp-throughput-peak-confirmed.md)
for repeated measurements, exact versions, memory observations, and artifacts.

Reproduce the comparison server on a host dedicated to this model:

```bash
export MEM_FRACTION_STATIC=0.85
export MAX_RUNNING_REQUESTS=96
export MAX_MAMBA_CACHE_SIZE=384
export CONTEXT_LENGTH=32768
export CHUNKED_PREFILL_SIZE=2048
export SGLANG_EXTRA_ARGS="--enable-metrics --speculative-algorithm EAGLE --speculative-num-steps 3 --speculative-eagle-topk 1 --speculative-num-draft-tokens 4 --cuda-graph-max-bs 96"
scripts/serve qwen3.8-27b-fp8 --engine sglang --target dgx-spark
scripts/validate-responses qwen3.8-27b-fp8 --engine sglang --target dgx-spark --timeout 600

# With the server idle and healthy, clear prior prompt-cache contents.
curl --fail --silent --show-error -X POST 'http://localhost:30000/flush_cache?timeout=30'
QWEN_REQUEST_COUNT=384 QWEN_WARMUP_COUNT=96 QWEN_SEED_BASE=2936 \
  models/qwen3.8-27b-fp8/sglang/targets/dgx-spark/benchmark-aiperf.sh 64
```

The server cap remains 96 to reproduce the tested configuration; the recommended
client concurrency is 64. The earlier server with cap 64, Mamba slots 256,
memory fraction 0.80, and graph maximum 64 separately achieved 204.16 tokens/s
at concurrency 64. Those different server settings are excluded from the paired
mean above. Shared-host defaults remain at memory fraction 0.45 and cap four.

This qualification uses approximately 525 input tokens and 128 forced output
tokens, temperature zero, and thinking disabled. Each matched profile starts
with a successful idle-cache flush; warmups are excluded. Throughput includes
measured-phase ramp-up and drain. The expanded server allocated 92,478 BF16 KV
slots and retained at least approximately 12.4 GiB of sampled available host
memory during the measured profiles. Its configured 32K context limit does
not establish capacity for 96 simultaneous 32K requests. Rerun the sweep for
longer prompts/outputs, reasoning, or other decoding settings.

At concurrency 64, the two-run mean also includes **849.06 input tokens/s**,
for **1,056.42 total tokens/s** and 1.620 requests/s. Input throughput is averaged
over the full mixed prefill/decode workload, rather than an isolated prefill test.
At Alibaba's international list prices checked on 2026-09-14 ($0.50/M input,
$3.00/M output), both token streams represent approximately **$3.77/hour** in
API-equivalent gross value. Continuous full-load extrapolation gives $90.43/day
or $2,712.76 per 30 days; sustained operation and paying demand are unverified,
and costs are excluded. The [token-rate and pricing analysis](../../docs/experiments/qwen3.8-27b-fp8/sglang/dgx-spark/2026-09-14T22-30-07Z-token-rates-api-value.md)
contains primary price sources, a cheaper-provider comparison, formulas, and
utilization assumptions.

A direct Spark-hosted comparison checked the same day is AxForge's Qwen3.8
27B NVFP4 API at €0.29/M input and €1.77/M output, before VAT. Applied to our
FP8 token rates, that represents €2.21/hour in gross API-equivalent value.
The [Spark API and rental price reference](../../docs/experiments/qwen3.8-27b-fp8/sglang/dgx-spark/2026-09-14T22-33-51Z-spark-hosted-api-pricing.md)
records the primary sources, quantization difference, and separate rental rates.

## Source Settings

The launch command follows the official model card and SGLang cookbook:

- one GPU (`--tp 1`)
- FlashInfer attention for SM121
- blockwise FP8 checkpoint weights and the checkpoint-declared KV-cache format
- BF16 GDN state
- `qwen3` reasoning and `qwen3_coder` tool-call parsers
- trusted repository code

The image is model-specific because Qwen3.8 support is newer than the SGLang
release pinned by the existing Nemotron recipe.

Sources:

- [Qwen model card](https://huggingface.co/Qwen/Qwen3.8-27B-FP8)
- [SGLang Qwen3.8 cookbook](https://docs.sglang.io/cookbook/autoregressive/Qwen/Qwen3.8-27B)

Observed deployment failures, diagnoses, and verified fixes are kept in the
[DGX Spark SGLang experiment journal](../../docs/experiments/qwen3.8-27b-fp8/sglang/dgx-spark/README.md).
