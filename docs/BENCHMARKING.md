# Shared Inference Benchmarking Rules

These rules apply to all new inference performance experiments: every model,
quantization, speculative-decoding setting, supported engine (SGLang or vLLM),
hardware target, model-specific runner, and ad hoc benchmark command. They govern
benchmark planning and reporting; unit tests, API smoke checks, and quality or
accuracy evaluations retain the sample sizes appropriate to their purpose.

Sources checked: **2026-09-27**. The NVIDIA guidance adopted below is identified
separately from this repository's choices. A recipe-specific historical default
does not override this policy for a new experiment.

## Request counts and warmup

NVIDIA's [NIM benchmarking walkthrough](https://docs.nvidia.com/nim/benchmarking/llm/1.0.0/step-by-step.html)
uses measured requests equal to **three times concurrency** and recommends a
warming load before the sweep. This is a worked benchmarking method, not a
guarantee of stable results for every workload or reliable tail percentiles.

For a new exploratory sweep, use this repository's default per measured trial:

```text
C = client concurrency
measured_requests = max(64, 3 * C)
```

The **64-request floor is a repository choice**, not an NVIDIA requirement. It
avoids relying on only 3, 6, or 12 requests at c1, c2, or c4. Do not require the
same total request count at every concurrency merely for symmetry.

| Concurrency | Measured requests per trial |
| --- | ---: |
| 1, 2, 4, 8, 16 | 64 |
| 32 | 96 |
| 48 | 144 |
| 56 | 168 |
| 64 | 192 |
| 72 | 216 |

Warmup is separate and excluded from measurements. Complete model loading,
kernel compilation, and API qualification before timed traffic. Select and
record warmup sufficient for the tested workload, admission limit, and GPU
temperature/power to settle; there is no universal NVIDIA warmup count adopted
here. Do not carry a costly fixed warmup count into every future sweep without
checking its purpose. Repeated trials on the same ready configuration may share
the initial warmup; rewarm after a restart, configuration change, or cooldown
that changes the initial state.

Different counts, duration-based runs, soak tests, and exact baseline reproduction
remain valid when the chosen protocol and reason are recorded before launch.
Long requests may need more time; tail latency and failure-rate investigations
may need more samples. Do not infer strong P95/P99 or rare-failure conclusions
from the exploratory minimum alone.

## Repeated trials and stopping criteria

Adopt NVIDIA's [AIPerf confidence-reporting guidance](https://docs.nvidia.com/aiperf/dev/tutorials/metrics-analysis/multi-run-confidence-reporting):

- Use **3 trials** for exploratory comparisons, **5** for standard validation,
  and **10** when resolving small differences or seeking higher precision.
- A single initial pass may locate promising settings, but label its results
  preliminary. Repeat selected settings before declaring a performance winner.
- Report the number of successful trials and variability, including confidence
  intervals where available. Record failed trials as well.
- Adaptive convergence may stop repeated trials early. Declare the metric,
  statistic, convergence method, threshold, confidence level, and maximum trials
  before running. Require at least three successful trials for a convergence
  claim. Reaching the maximum without convergence is an inconclusive stability
  result, not evidence that the criterion passed.

Warmup need not repeat between identical trials on a stable server. Verify that
the pinned AIPerf version implements the intended options and inspect the emitted
configuration. NVIDIA's development documentation can describe newer features.
Convergence of one selected metric does not establish convergence of all metrics,
especially tail percentiles, GPU telemetry, or estimated TFLOPS.

Repository cache-state rule: identical seeds and an unchanged cache policy do
not guarantee equivalent measured cache conditions. Verify prompt reuse from
engine counters for each trial. For repeatability claims, consistently prime
the measured prompts or establish equivalent fresh-cache conditions before
each trial; record the method. If trials deliberately mix cache conditions,
report those conditions separately and label any combined mean descriptive.
Do not interpret its confidence interval as evidence of steady-state stability.
The NVFP4 MTP=1 follow-up observed large changes in prompt reuse between trials
despite identical generated inputs; completed runs retain their original protocol.

## Comparing configurations

Follow NVIDIA's [Dynamo comparison guidance](https://docs.nvidia.com/dynamo/dev/cli/operations/benchmarking-with-ai-perf):
change one deployment setting at a time and preserve the workload, concurrency,
and request count for the matched comparison.

For this repository, that means **match counts at each corresponding concurrency
across configurations**, such as MTP disabled versus MTP=1 versus MTP=2. Counts
may differ between c1 and c64. Keep inputs or their generation policy, seeds,
input/output lengths, sampling, thinking mode, streaming, warmup, cache policy,
trial/stopping rules, and client placement matched. Pin and record model/tokenizer
revisions, image/runtime versions, and the benchmark client version.

When enabling MTP also requires different cache sizing or memory settings,
disclose all changes and call it a configuration comparison; do not attribute
the entire difference solely to MTP. Record requested client concurrency and
the effective server admission limit separately.

## Metrics and artifacts

The following are repository requirements for every performance run:

- Save the exact command, resolved counts for each concurrency/trial, warmup and
  measurement boundaries, UTC timestamps, workload settings, and exit/error state.
- Preserve client aggregates and per-request data, generated inputs or a
  reproducible dataset reference, GPU telemetry, and available engine metrics.
  Verify actual exports with a small preflight before committing to a long run.
- Collect GPU utilization, temperature, power, and energy where supported. Save
  SGLang or vLLM metrics appropriate to the installed version, including queueing,
  cache use, admission, and speculative acceptance when available. Record missing
  or unsupported telemetry explicitly; missing measurements are not zero.
  In the pinned SGLang build, a zero-reuse workload may never emit a labeled
  cached-token counter. When available, verify reuse from the difference between
  total-prompt and uncached-prompt histogram sum deltas, requiring both histogram
  count deltas to match the completed request count over the same interval.
  This supplies independent evidence; absence of the cached-token series alone
  does not establish zero reuse.
- When the engine exposes estimated FLOPs, retain timestamped raw counters and
  compute estimated TFLOPS/GPU as `delta(FLOPs/GPU) / seconds / 1e12` over the
  measured phase. Check counter resets, units, aggregation, and accounting for
  draft/verification work. Label estimates distinctly from hardware FLOPs/MFU.
  SGLang's Prometheus `sglang:estimated_flops_per_gpu_total` appears as
  `sglang:estimated_flops_per_gpu` in the observed AIPerf JSONL exports.
- Do not interpret estimated read/write-byte counters as measured DRAM traffic.
  Inspect their implementation: the observed SGLang estimator uses server dtype
  sizes and charges weight reads per token, without modeling packed NVFP4 weights
  or their reuse across a batch. Preserve these estimates with their limitations;
  do not divide their rates by hardware bandwidth to claim utilization.
  NVIDIA [NVML memory utilization](https://docs.nvidia.com/deploy/nvml-api/api/structnvmlUtilization__t.html)
  measures the fraction of time memory is active, not achieved GB/s. An all-zero
  activity series during inference does not establish zero traffic. A bandwidth
  headroom claim requires supported hardware byte counters and a defined time
  interval, with prefill/decode distinguished. Keep intrusive profiling separate
  from the benchmark used for client latency and throughput comparisons.
- Save raw artifacts in a dedicated directory outside Git and disposable
  worktrees, normally `$HOME/inference-artifacts/<model>/<engine>/<hardware>/`.
  Use a unique experiment directory and retain every trial and failed attempt.
  Keep journal/report links to that directory; do not overwrite earlier data.

For embedding or other non-generation workloads, select suitable task metrics;
output-token throughput and speculative acceptance may not apply.

## Applying the rules to existing runners

The Gemma E4B, Qwen3.8 FP8, and Qwen3.8 NVFP4 `benchmark-aiperf.sh` scripts retain
their established reproduction defaults. They do **not** automatically enforce
this new policy. Before using them for a new sweep, resolve the per-concurrency
budget and supply supported overrides, update the runner, or issue equivalent
pinned AIPerf commands. The FP8 runner's existing `auto` formula is also a
different historical protocol; do not assume the word `auto` selects this policy.

Keep an already-started sweep's declared settings fixed. Apply a protocol change
to a separately identified round. Completed journals remain immutable. Record
experiment changes and observed failures under the
[experiment journal rules](experiments/README.md), including justified exceptions
to this policy. A documented exception does not itself require additional user
approval when the experiment is already authorized.
