# Qwen3.8 27B NVFP4

This recipe serves NVIDIA's official
[`nvidia/Qwen3.8-27B-NVFP4`](https://huggingface.co/nvidia/Qwen3.8-27B-NVFP4)
checkpoint on one DGX Spark GPU through SGLang's OpenAI-compatible API.

The checkpoint is a mixed-precision ModelOpt build: MLP layers and the language
model head use NVFP4, while attention layers use FP8. It is approximately 22 GB
on disk and targets NVIDIA Blackwell hardware.

Status: experimental. On 2026-09-16 UTC, the cached NVIDIA revision
`dbb8f445b3145f8a4c18ddc769f032d57d32867c` loaded on a DGX Spark with no
restarts or OOMs. Health, model discovery, exact-text Responses API generation,
and parsed tool calling passed. Image and video requests, long-context capacity,
and broad production throughput remain unqualified.

**MTP (Multi-Token Prediction) is disabled in the current recipe defaults and
the 2026-09-20 NVFP4 benchmark results.** Those completed profiles used
ordinary, non-speculative decoding; their SGLang metrics report
`sglang:spec_num_steps=0` throughout. This includes the full c1–c72 sweep and
its 221.74 output tokens/s peak at c64. The FP8 MTP experiments are a separate
configuration; NVFP4 MTP results are identified separately.

On 2026-09-25, a separate [NVFP4 MTP=2 round](../../docs/experiments/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-25T20-24-59Z-mtp2-c72-round.md)
passed text/Responses API smoke checks and confirmed 72-request admission. Its
full c1–c72 sweep [completed successfully](../../docs/experiments/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-26T00-25-10Z-mtp2-sweep-completed.md),
and the service was stopped before the next round. Here **MTP=2 means two drafting steps**:
EAGLE, `--speculative-num-steps 2`, top-k 1, and three verification positions
(`--speculative-num-draft-tokens 3`). The native head comes from the same pinned
NVFP4 checkpoint. To accommodate its temporary state, this experiment uses
`extra_buffer_lazy`, 288 persistent Mamba slots, and static-memory fraction 0.90;
float32 Mamba state and FP8 KV precision are retained. These memory-setting
differences must accompany comparisons with the MTP-disabled baseline.
GPU telemetry and SGLang estimated-FLOPs/MTP exports were verified in a separate
short profile before launching the full sweep. Results and status are saved
[outside Git](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-25T20-24-59Z-mtp2-c72/README.md).
The cached image's older launcher requires explicit `--max-mamba-cache-size`
through `SGLANG_EXTRA_ARGS`; setting the newer environment variable alone does
not configure that older image.

The [MTP=3 then MTP=1 suite](../../docs/experiments/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-26T00-25-10Z-mtp13-suite-launch.md)
uses three trials per concurrency under the shared benchmarking rules. Both
variants use admission64 and 256 persistent Mamba slots to accommodate MTP=3's
larger temporary state. Client c72 is therefore an overload point. The suite
retains all client/GPU/SGLang metrics and estimated-TFLOPS summaries
[outside Git](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-26T00-12-44Z-mtp1-mtp3/README.md),
and stops its experiment services at completion or failure. Comparisons with the
earlier MTP=2 round must disclose the changed admission, cache, and sample counts.

Both rounds completed successfully and their services were stopped. The
[final comparison of MTP disabled, MTP=1, MTP=2, and MTP=3](../../docs/experiments/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-26T08-06-38Z-mtp-disabled-1-2-3-final-report.md)
contains all concurrency tables, trial variation, GPU/queue metrics, estimated
TFLOPS accounting, and charts. MTP=3 led the observed low-concurrency averages;
the disabled configuration led at c64–c72. Cache, admission, memory allocation,
sampling, and baseline checkpoint provenance limit causal comparisons.

The [September 27 MTP=2 rerun](../../docs/experiments/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T11-01-08Z-mtp2-aligned-launch.md)
aligns with MTP=1/3: three trials of `max(64, 3C)` requests per concurrency,
`max(8, C)` warmups before trial1, admission64, 256 Mamba slots, the same pinned
runtime/model and generated inputs, and retained native cache across repeat passes.
Its [dedicated archive](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T10-59-11Z-mtp2-aligned/README.md)
contains status, all raw metrics, and per-trial cache measurements. This deliberately
reproduces the earlier first/repeat-pass procedure; combined means do not establish
repeatability under one cache condition. First and repeat passes are reported
separately, and available cache capacity may still differ by MTP setting.

That aligned MTP=2 rerun completed all 30 trials and shut down automatically.
The [updated final summary](../../docs/experiments/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T13-24-43Z-final-aligned-mtp-summary.md)
replaces the earlier MTP=2 measurements in the current comparison: its highest
observed three-pass mean is 246.72 output tokens/s at c48, with 24.60s mean response
and 26.26 estimated TFLOPS/GPU. Its first c48 pass achieved 199.46 tokens/s with
zero measured prompt reuse; repeated passes reached 263.38 and 277.31 tokens/s.
MTP=3 still led the observed low-concurrency means. The disabled baseline has not
been rerun under the newer protocol, and pooled MTP means mix cache conditions.

The
[MTP=1 results and cache analysis](../../docs/experiments/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-26T06-54-00Z-mtp1-results-cache-assessment.md)
report a highest observed mean of 240.66 output tokens/s at c48, with 25.68s mean
response time. Prompt reuse changed between trials: c48 ranged from 194.97 to
278.75 tokens/s as measured cache reuse increased. These combined averages
describe the completed workload; they do not establish a stable optimum or an
isolated MTP speedup. Estimated TFLOPS also reflects the changing prompt workload.

The [metric-accounting audit](../../docs/experiments/qwen3.8-27b-nvfp4/sglang/dgx-spark/forks/7a44/2026-09-27T11-02-08Z-flops-bandwidth-accounting.md)
confirms that neither estimated FLOPs/bytes counters nor saved NVML activity
establish physical DRAM bandwidth or distance from its limit. The
[profiler capability check](../../docs/experiments/qwen3.8-27b-nvfp4/sglang/dgx-spark/forks/7a44/2026-09-27T11-12-31Z-bandwidth-profiler-capability.md)
records the installed GB10 counter and permission limitations. These notes retain
their original IDs in the [7a44 fork archive](../../docs/experiments/qwen3.8-27b-nvfp4/sglang/dgx-spark/forks/7a44/README.md).

On 2026-09-20 UTC, a synthetic streaming AIPerf profile completed with 72 client
connections and zero request errors. The former memory configuration admitted
only 33 running requests, so that profile remains a 72-client load test rather
than a 72-way admission result. A subsequent startup test with a 360-slot Mamba
cache and a 0.70 static-memory fraction admitted 72 requests; its performance
under c72 was then benchmarked in a full synthetic AIPerf sweep with no request
errors. Aggregate output throughput peaked at 221.74 tokens/s at c64 and was
220.49 tokens/s at c72; c72 minimum per-user decode throughput was 3.26
tokens/s/user. These are controlled 512-input/128-output synthetic results, not
general production capacity or quality qualification.

The [full concurrency performance report](../../docs/experiments/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-20T16-28-58Z-concurrency-performance-report.md)
explains each measured level, with latency, streaming, GPU telemetry, charts,
and an extracted CSV. At c72, sampled running requests peaked at 71 and five
of 384 measured requests took 62.69–80.07 seconds. This distinguishes the
configured 72-request limit from observed simultaneous execution and supports
choosing c64 over c72 for throughput on this specific workload.

The [TFLOPS concurrency assessment](../../docs/experiments/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-20T16-33-51Z-tflops-concurrency-assessment.md)
compares SGLang's estimated model TFLOPS directly with output throughput and
user latency. The estimate peaks at 49.84 TFLOPS/GPU at c64 and stays flat at
49.59 at c72; these values describe estimated model operations, not measured
hardware FLOPS or MFU.

The [queueing analysis](../../docs/experiments/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-20T16-50-31Z-queueing-below-admission-cap.md)
shows repeated queue fill/drain waves at c32 and c64 despite the 72-request
limit. A running-request ceiling does not guarantee immediate prompt processing;
the configured 2,048-token prefill chunks and scheduling operate separately.
The c72 median of one queued request remains a separate admission-boundary
observation whose exact mechanism is unconfirmed.

## Planned NVFP4 drafter checkpoints

The [two-checkpoint build spec](sglang/targets/dgx-spark/quantized-drafter-spec.md)
defines max-calibrated and Local-Hessian NVFP4 conversions of Inco's official BF16
DFlash2 drafter using NVIDIA Model Optimizer. It covers checkpoint creation,
provenance and minimal reload/generation checks; implementation remains pending.
Performance comparisons and serving-profile changes are separate follow-up work.

The [research and checkpoint review](../../docs/reports/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-10-04-quantized-drafter-review.md)
records the community conversion method, NVIDIA sources and verification limits.
[Serving intent](../../intend.md) defines the user-level performance priorities
for later evaluation.

## Deployment

Download the public checkpoint if it is not already cached:

```bash
scripts/download-qwen3.8-27b-nvfp4
```

Then deploy, validate, and stop it:

```bash
scripts/deploy qwen3.8-27b-nvfp4 --engine sglang --target dgx-spark
scripts/validate-responses qwen3.8-27b-nvfp4 --engine sglang --target dgx-spark --timeout 600
scripts/stop qwen3.8-27b-nvfp4 --engine sglang --target dgx-spark
```

The API listens on `http://localhost:30000/v1`. The model is public, so
`HF_TOKEN` is optional. The host cache defaults to `$HOME/.cache/huggingface`
and can be changed with `HF_CACHE_DIR`.

## Configuration

Copy `sglang/targets/dgx-spark/.env.example` to
`sglang/targets/dgx-spark/.env`, or export individual values before deployment.

| Variable | Default | Purpose |
| --- | --- | --- |
| `SGLANG_BASE_IMAGE` | `lmsysorg/sglang:dev-qwen38-27b-dflash2` | Qwen3.8-capable ARM64 SGLang image |
| `SGLANG_PORT` | `30000` | Host API port |
| `CONTEXT_LENGTH` | `32768` | Maximum admitted context |
| `MEM_FRACTION_STATIC` | `0.70` | SGLang static GPU-memory fraction |
| `MAX_RUNNING_REQUESTS` | `72` | Requested scheduler concurrency limit |
| `CHUNKED_PREFILL_SIZE` | `2048` | Chunked-prefill token count |
| `MAX_MAMBA_CACHE_SIZE` | `360` | Mamba state-cache slots (five per request) |
| `HF_CACHE_DIR` | `$HOME/.cache/huggingface` | Persistent model cache root |

The model card documents a 262K context limit. The initial 32K setting and 0.45
memory fraction are conservative DGX Spark defaults and can be raised after
workload-specific capacity testing. `MAX_RUNNING_REQUESTS=72` is a requested
limit, not an admission guarantee: with these settings on 2026-09-20, SGLang
reduced the effective limit to 33 because the Mamba state cache contained 169
slots and the model requires five slots per request (`floor(169 / 5) = 33`).
The allocation consumed 0.47 GB for convolution state and 23.91 GB for float32
SSM state. The current target defaults reserve 70% static GPU memory and set
`MAX_MAMBA_CACHE_SIZE=360`, providing the five slots required by each of 72
requests. The 2026-09-20 startup verification allocated 0.99 GB of convolution
state, 50.77 GB of float32 SSM state, 228,520 FP8 KV-cache tokens, and retained
29.76 GB after CUDA-graph capture while reporting `max_running_requests=72`.
Changing to bfloat16 Mamba SSM state remains an alternative but needs a separate
quality experiment.

At the qualified defaults, SGLang used 21.90 GB for weights, allocated 176,670
FP8 KV-cache tokens, and completed cold startup in 183.60 seconds. The Mamba
cache used 0.46 GB for convolution state and 23.62 GB for SSM state.

## Benchmark With AIPerf

New performance experiments must follow the repository-wide
[benchmarking rules](../../docs/BENCHMARKING.md). The runner's fixed 384 measured
requests and 96 warmups preserve the original baseline protocol. For a new
exploratory sweep, resolve per-concurrency counts and the trial plan from the
shared policy; already-started rounds keep their declared protocol.

The **MTP=2 hardware-utilization pilot** completed its normal inference
measurements on 2026-09-27 at client concurrency **1, 8, and 64**:

| Concurrency | Measured requests per trial | Trials | Total measured requests |
| --- | ---: | ---: | ---: |
| 1 | 64 | 3 | 192 |
| 8 | 64 | 3 | 192 |
| 64 | 192 | 3 | 576 |

This is nine trials and **960 measured requests**, with warmup excluded. The run
retained the pinned aligned MTP=2 configuration, 512-token input target and 128
forced output tokens. The idle cache was flushed before each measured trial;
paired prompt histograms verified zero cached prompt tokens. Hardware profiling uses
separate diagnostic captures so profiler overhead does not enter these normal
latency/throughput measurements. The [baseline completion record](../../docs/experiments/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T15-00-27Z-hardware-pilot-baseline-complete.md)
reports 21.808/106.644/202.545 output tokens/s at c1/c8/c64, respectively.
The [final hardware report](../../docs/reports/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27-mtp2-hardware-utilization.md)
adds calibrated bandwidth/GEMM references, GPU timelines and 12 selected kernel
samples. Physical DRAM utilization and whole-server hardware MFU remain
unavailable; all pilot services were stopped after validation.
The [updated calibration table](../../docs/reports/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27-mtp2-hardware-utilization.md#hardware-limits-and-local-calibration)
adds ideal arithmetic intensity in FLOP/byte, including NVFP4 block scales and
BF16 output traffic, alongside Spark's dense FP4 hardware balance.

The pilot's [retained execution and validation scripts](sglang/targets/dgx-spark/experiments/hardware-utilization/README.md)
include the original attempts, recovery runners, calibration code, profiler
drivers and offline analysis. Their manifest records the archived source hashes;
raw metrics and profiles remain in the dedicated external artifact directory.

The NVFP4 runner permits client concurrency through the recipe's requested
72-request scheduler cap; it does not assert that SGLang can admit all 72
simultaneously. It profiles streaming chat completions with 512
synthetic input tokens, 128 forced output tokens, deterministic sampling, and
NVML GPU telemetry. A no-argument run performs a sweep through 72:

```bash
models/qwen3.8-27b-nvfp4/sglang/targets/dgx-spark/benchmark-aiperf.sh
```

Run this only after recreating the service with `MAX_RUNNING_REQUESTS=72`,
confirming it is healthy, and checking its startup log for the effective
`max_running_requests` value. Pass individual concurrency levels to narrow the
sweep:

```bash
models/qwen3.8-27b-nvfp4/sglang/targets/dgx-spark/benchmark-aiperf.sh 56 64 72
```

Set one tag for a whole experiment (all selected concurrencies share it):

```bash
QWEN_NVFP4_EXPERIMENT_TAG=nvfp4-c72-baseline-01 \
  models/qwen3.8-27b-nvfp4/sglang/targets/dgx-spark/benchmark-aiperf.sh
```

Without an explicit tag, the runner creates a UTC timestamped tag. It sends the
tag as `X-Inferpack-Experiment-Tag` with every benchmark request and prints it
at startup.

For concurrency `N`, reports are saved under `<benchmark-root>/cN/`:
`profile_export_aiperf.json` and `profile_export_aiperf.csv` contain aggregate
metrics; `profile_export.jsonl` contains the per-request records, including
`output_token_throughput_per_user`. SGLang metrics are exported as
`server_metrics_export.json`, `server_metrics_export.csv`, and the raw-sample
`server_metrics_export.jsonl`. The console log is `<benchmark-root>/cN.log`.
`QWEN_NVFP4_BENCHMARK_ROOT` selects a new output directory; by default,
artifacts are saved under
`$HOME/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/<experiment-tag>-<suffix>/`.
This dedicated directory is outside the repository and disposable worktrees, so
raw metrics do not need to be committed to Git and survive worktree cleanup.
Existing output directories are not overwritten. This default applies to the
updated runner; older worktree copies can use `QWEN_NVFP4_BENCHMARK_ROOT` to
write to the same location explicitly.
The root `experiment.json` records the shared tag and benchmark configuration;
`experiment-events.jsonl` records the UTC start and finish of every profile.
Together, the tag, artifact hierarchy, and timestamps link AIPerf client data,
NVML telemetry, and SGLang server metrics into one experiment. SGLang's native
Prometheus labels are not modified per run, so use these recorded timestamps to
select the matching range from the durable Prometheus series.

The completed full c1–c72 sweep from 2026-09-20 is preserved locally at
`$HOME/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/nvfp4-admission72-full-20260920-21dGW0/`.
Its aggregate AIPerf report is `profile_export_aiperf.json`, per-request results
are `profile_export.jsonl`, GPU samples are `gpu_telemetry_export.jsonl`, and
SGLang samples are `server_metrics_export.jsonl`. The parent directory's
`experiment.json` and `experiment-events.jsonl` hold the shared tag and time
window. Each concurrency also retains separate warmup and profiling summaries.

The target archive contains both earlier experiment directories, including the
interrupted attempt, plus `reports/` with the performance reports, charts, CSV
and journal entries. All 232 original benchmark files and 13 report/journal
files were copied from worktree `8174` and the main checkout and verified by
SHA-256; the original files remain in place. Its `README.md` indexes the runs,
and `archive-2026-09-20-manifest.json` records source paths, file sizes and hashes.
Verify the saved import with:

```bash
cd "$HOME/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark"
sha256sum --check --quiet archive-2026-09-20-sha256.txt
```

The dated manifest covers the preserved 2026-09-20 files; subsequent benchmark
directories are separate. Historical report links may name the original
worktree, but the directory with the same experiment name in this archive
contains the preserved data. This is local storage on the same host, independent
of Prometheus retention; it is not an off-host backup.

### Telemetry And Estimated TFLOPS

The AIPerf runner requests client-side NVML GPU telemetry. Its available fields
(such as temperature, utilisation, and power) are retained with the AIPerf
artifacts under `<benchmark-root>/cN/`; inspect the generated reports after the
first GB10 run because available NVML fields vary by driver and GPU.

Estimated model TFLOPS are collected in two complementary places. The runner
requires `/metrics` to expose `sglang:estimated_flops_per_gpu_total` before it
starts and stores benchmark-window SGLang metrics in each profile's
`server_metrics_export.{json,csv,jsonl}`. Use the shared monitoring stack as
well when a durable time series beyond the AIPerf benchmark window is needed:

```bash
make start MODEL=qwen3.8-27b-nvfp4
```

This enables SGLang metrics and MFU estimation, registers the service with
Prometheus, and persists the sampled history in Prometheus's named data volume
(30-day default retention). Read the dashboard's estimated-TFLOPS panel or query:

```promql
rate(sglang:estimated_flops_per_gpu_total{job="sglang"}[1m]) / 1e12
```

This is an SGLang model-operation estimate, not measured GPU hardware TFLOPS or
a hardware MFU percentage. Wait for at least two Prometheus scrapes before
interpreting the rate.

## Source Settings

The launch command follows NVIDIA's SGLang example with tensor parallelism 1,
FP8 E4M3 KV cache, FlashInfer attention, 2,048-token chunked prefill, Qwen3
reasoning, the Qwen3 Coder tool parser, float32 Mamba state, the `extra_buffer`
Mamba radix strategy, a 360-slot Mamba cache, and a 0.70 static-memory fraction.

Sources:

- [NVIDIA model card](https://huggingface.co/nvidia/Qwen3.8-27B-NVFP4)
- [SGLang Qwen3.8 cookbook](https://docs.sglang.io/cookbook/autoregressive/Qwen/Qwen3.8-27B)

Deployment observations are kept in the
[DGX Spark SGLang experiment journal](../../docs/experiments/qwen3.8-27b-nvfp4/sglang/dgx-spark/README.md).
