# Gemma 4 E4B IT

This recipe serves
[`google/gemma-4-E4B-it`](https://huggingface.co/google/gemma-4-E4B-it)
on one DGX Spark GPU through SGLang's OpenAI-compatible API.

Status: experimental. On 2026-09-05, the image built and the model completed
health, model-listing, and chat-completion validation on a DGX Spark. The tested
runtime was SGLang `0.0.0.dev1+g5f55db35e` with model revision
`ee0ef6023621cff504d758262d4e04895a5af4a2`. Text inference was qualified;
image, audio, video, tool calling, speculative decoding, and long-context
capacity were not exercised. This runtime logs that `torchcodec` is absent, so
audio requests are expected to fail until that dependency is added and tested.

## Deployment

```bash
# Optional for this public model: export HF_TOKEN=hf_example
scripts/deploy gemma-4-e4b-it --engine sglang --target dgx-spark
scripts/logs gemma-4-e4b-it --engine sglang --target dgx-spark
scripts/validate gemma-4-e4b-it --engine sglang --target dgx-spark --timeout 600
scripts/stop gemma-4-e4b-it --engine sglang --target dgx-spark
```

Model weights persist under `$HF_CACHE_DIR`; the default is
`$HOME/.cache/huggingface`. The service listens on
`http://localhost:30000` by default.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `SGLANG_BASE_IMAGE` | `lmsysorg/sglang:dev-qwen38-27b-dflash2` | CUDA 13 ARM64 SGLang image with Gemma 4 support |
| `SGLANG_PORT` | `30000` | Host API port |
| `CONTEXT_LENGTH` | `32768` | Initial qualification context limit |
| `MEM_FRACTION_STATIC` | `0.85` | Unified-memory fraction for model and runtime caches |
| `MAX_RUNNING_REQUESTS` | `4` | Scheduler concurrency cap |
| `HF_CACHE_DIR` | `$HOME/.cache/huggingface` | Persistent model cache |
| `SGLANG_EXTRA_ARGS` | unset | Additional model-specific launch arguments |

DGX Spark's 128 GB is unified with the host. The model has approximately 8B
total parameters including per-layer embeddings. The 32K context and `0.85`
static-memory defaults are conservative qualification settings rather than the
model's native 128K limit or a hard container memory limit.

## Benchmark With AIPerf

Use AIPerf as an isolated HTTP benchmark client; the model continues running in
its SGLang container. The example below targets **Gemma 4 E4B**, using API model
name `gemma-4-e4b-it` and tokenizer `google/gemma-4-E4B-it`. The saved
[runner](sglang/targets/dgx-spark/benchmark-aiperf.sh) reproduces the plateau
sweep with 12 warmups and 96 measured requests per concurrency setting.

On the Spark, first start and validate this recipe using the deployment commands
above. Check for an existing service before deploying: recipes share port 30000
by default and GPU memory must also be available. When benchmarking remotely,
replace `127.0.0.1` with the Spark's address. AIPerf's URL is the server origin;
the chat endpoint supplies `/v1/chat/completions`.

```bash
export BENCHMARK_URL=http://127.0.0.1:30000
curl --fail --silent --show-error "$BENCHMARK_URL/v1/models"
# Confirm the returned model ID is gemma-4-e4b-it before sending benchmark load.

# Run from the repository root. Omitting the numbers also uses 4 6 8 12.
models/gemma-4-e4b-it/sglang/targets/dgx-spark/benchmark-aiperf.sh 4 6 8 12

# Choose other concurrency values or inspect the available settings.
models/gemma-4-e4b-it/sglang/targets/dgx-spark/benchmark-aiperf.sh --help
```

The runner pins AIPerf `0.12.0` in an isolated uv tool environment with managed
Python 3.12, using normal uv cache locations or any `UV_*` overrides you set.
It does not change the server's configuration or automatically search for a
plateau; it runs the supplied concurrency values in order and stops on an
AIPerf failure. It retains each profile's console log and prints its summary.

Each invocation prints a new UTC-timestamped output directory under
`sglang/targets/dgx-spark/artifacts/`, which Git ignores. Set
`GEMMA_BENCHMARK_ROOT` to use a different new directory; existing directories
are rejected to preserve previous results. Reports persist until you remove
them. The runner has no dependency on the original `/tmp` script or caches.

This synthetic workload targets 512 prompt tokens and requests 128 generated
tokens. SGLang's `ignore_eos` makes output length more consistent by suppressing
early end-of-sequence termination; remove it for a test of natural stopping.
The chat template can change the actual input length. Inspect the reported
input/output counts, successful requests, and errors before comparing results.
Reasoning follows the recipe's chat-template default; keep that mode consistent
between comparisons and count any reasoning as part of generation work.

Streaming enables time-to-first-token (TTFT) and inter-token latency (ITL).
Compare their median and tail values with end-to-end request latency, aggregate
output tokens/second, and requests/second. Aggregate output throughput measures
the whole service; it is different from the generation speed of one request.
The recipe defaults to four running requests, so concurrency above four mainly
adds queueing unless that server setting changes.

This command collects client-observed endpoint performance. It disables server
metrics and GPU telemetry collection; neither is required to measure the API.

AIPerf writes `profile_export_aiperf.json` and CSV reports into each artifact
directory. The saved runner uses 96 requests per setting; the initial comparison
below used 32. These are short baselines with limited support for tail-latency
estimates. For a capacity study, increase the request count,
repeat each setting, and use representative prompt/output lengths. Record the
image digest, engine version, launch settings, client location, other GPU load,
and cache conditions. The example varies the seed between concurrency levels
to reduce exact prompt reuse; it does not establish a cold-cache benchmark.

Setup verified on DGX Spark ARM64 with AIPerf `0.12.0` and uv-managed Python
`3.12.12`. ARM64 requires a C compiler to build the `crick` dependency; using
system Python without its development headers failed with `Python.h` missing.
The managed Python retry built successfully.

The live comparison on 2026-09-13 passed all 96 measured requests and 12 warmups.
The client ran on the Spark through loopback, with thinking disabled by the
model's default template. Actual input lengths were 521–522 tokens after chat
formatting; all outputs were 128 tokens.

| Concurrency | TTFT p50 | Request latency p50 | ITL mean | Aggregate output tokens/s |
| --- | --- | --- | --- | --- |
| 1 | 154.91 ms | 6.540 s | 50.29 ms | 19.56 |
| 2 | 231.03 ms | 5.548 s | 41.81 ms | 46.17 |
| 4 | 400.35 ms | 5.748 s | 42.10 ms | 89.04 |

Concurrency 4 delivered 4.55 times the measured concurrency-1 throughput,
with a longer wait for the first token. This is one short synthetic comparison,
not a sustained capacity or application-workload qualification. Prefix caching
remained enabled, but cache-hit counts were unavailable because the recipe does
not enable SGLang's cache-report field. See the
[benchmark record](../../docs/experiments/gemma-4-e4b-it/sglang/dgx-spark/2026-09-13T22-08-12Z-aiperf-concurrency-baseline.md)
for versions, timing, commands, artifacts, and limitations.

A follow-up sweep used 96 measured requests and 12 warmups per setting, keeping
the same workload and `MAX_RUNNING_REQUESTS=4`:

| Client concurrency | Aggregate output tokens/s | Request latency p50 / p95 |
| --- | --- | --- |
| 4 | 89.28 | 5.733 / 5.765 s |
| 6 | 89.09 | 5.772 / 11.535 s |
| 8 | 89.03 | 11.494 / 11.541 s |
| 12 | 89.10 | 17.224 / 17.295 s |

All 384 measured requests and 48 warmups passed. Throughput plateaued around
89 output tokens/s, varying by less than 0.3% across these settings. Scheduler
logs confirmed four active requests with two queued at client concurrency 6,
and eight queued at concurrency 12. This is the ceiling of the current
four-active-request configuration, not a measurement of the Spark's maximum
capacity with a larger server batch. Testing that requires a separate sweep
after raising `MAX_RUNNING_REQUESTS` and recreating the service. See the
[plateau experiment](../../docs/experiments/gemma-4-e4b-it/sglang/dgx-spark/2026-09-13T22-45-13Z-aiperf-configured-throughput-plateau.md).

References: [AIPerf profiling guide](https://docs.nvidia.com/aiperf/getting-started/profiling-with-ai-perf),
[CLI options](https://docs.nvidia.com/aiperf/reference/command-line-options),
[SGLang sampling parameters](https://docs.sglang.io/basic_usage/sampling_params.html).

## Source Settings

The launch command follows the official model card and SGLang cookbook:

- one GPU (`--tp 1`)
- Triton attention for correct bidirectional image-token attention
- `gemma4` reasoning and tool-call parsers
- trusted repository code

The initial qualification does not enable the optional Gemma 4 assistant model
for NEXTN speculative decoding. That keeps startup and compatibility variables
isolated while the base service is established.

The tested image resolved to
`sha256:326c8aa85e4ac705f9e7ed17ea19ac079851a56c97cfc87bb9a9715a968baf41`
and its SGLang base to digest
`sha256:616a3e97f45191af975896cfa644279096cb31bd408a071c2e99ca7209c3cafe`.
The cold start downloaded one 15.99 GB safetensors file. SGLang reported 15.56
GB of weight memory, allocated BF16 hybrid-attention KV pools, and retained
14.18 GB after decode CUDA-graph capture.

On shutdown, this SGLang development build drains requests and Compose removes
the service, but the engine logs an NCCL process-group warning followed by a
`SystemExit: 0` and Starlette cancellation traceback. Verify container removal
and port closure rather than interpreting that cleanup traceback as a running
service; the observation is preserved in the experiment journal.

Sources:

- [Google model card](https://huggingface.co/google/gemma-4-E4B-it)
- [SGLang Gemma 4 cookbook](https://docs.sglang.io/cookbook/autoregressive/Google/Gemma4)

Observed deployment experiments are kept in the
[DGX Spark SGLang experiment journal](../../docs/experiments/gemma-4-e4b-it/sglang/dgx-spark/README.md).
