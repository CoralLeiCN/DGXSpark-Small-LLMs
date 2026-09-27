# 2026-09-26T06:54:00Z — NVFP4 MTP=1 results and repeated-trial cache effects

Run ID: `RUN-0024`

- Status: resolved
- Phase: inference / benchmark / lifecycle
- Repo revision: `89611e1`, dirty with experiment documentation
- Host/GPU: DGX Spark, NVIDIA GB10, driver `580.173.02`, aarch64
- Image: `sha256:110ad45e7872397f337ea5714e6c97c400852938a9b8f258bcc27cab07182b0c`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`; AIPerf `0.12.0`, Python 3.12
- Model: `nvidia/Qwen3.8-27B-NVFP4`, revision `482ca0f3832238542f8f5295dde86b5f22711d80`
- Artifacts: [2026-09-26T00-12-44Z-mtp1-mtp3](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-26T00-12-44Z-mtp1-mtp3/)
- Related turns: [MTP=2 launch](2026-09-25T20-24-59Z-mtp2-c72-round.md); see this target index for the MTP=1/3 launch and subsequent events.

## Completed workload

Follow-up analysis of [RUN-0021](2026-09-26T03-02-55Z-mtp1-sweep-complete.md).
The completed NVFP4 MTP=1 configuration uses one drafting step, EAGLE top-k1,
two verification positions, admission64, and 256 float32 persistent Mamba slots.
All ten concurrencies completed three trials: 3,408 measured requests in total,
with no request errors. Input target512 tokens, output128, streaming chat,
temperature0, thinking disabled. Each trial uses `max(64, 3*C)` measured requests;
`max(8, C)` warmups occur before trial1. Identical generated inputs and native
cache state are retained between trials. All services and the monitor have stopped.

## Final observed averages

Values below are equal-weight arithmetic means of the three completed trials.
They are descriptive averages across the cache conditions actually observed,
not proof that all trials sampled one stable operating condition.

| Concurrency | SGLang estimated TFLOPS/GPU | Total output tokens/s | Mean response time (s) |
| ---: | ---: | ---: | ---: |
| 1 | 2.00 | 18.74 | 6.83 |
| 2 | 3.68 | 34.64 | 7.38 |
| 4 | 6.48 | 62.01 | 8.21 |
| 8 | 10.75 | 104.10 | 9.73 |
| 16 | 15.86 | 156.07 | 12.90 |
| 32 | 21.06 | 215.22 | 18.98 |
| 48 | 26.77 | 240.66 | 25.68 |
| 56 | 42.37 | 214.84 | 32.97 |
| 64 | 41.47 | 204.06 | 38.72 |
| 72 | 41.73 | 204.92 | 41.86 |

c72 is client load above admission64. Response time means full request latency,
not time to first token. Estimated TFLOPS is the SGLang model-FLOPs counter delta
per second per GPU between scrapes inside the measured request window; edge
fractions are excluded. It is not measured hardware FLOPs or MFU. More estimated
FLOPs need not mean more useful output when cache reuse changes the amount of
prompt processing.

## Interpretation and trial variability

The highest observed mean is **240.66 output tokens/s at c48**, with 25.68s mean
response time. c32 delivers 215.22 tokens/s (89.4% of that peak) at 18.98s mean
response time. The c56–c72 means add latency without exceeding c48's throughput.
These observations identify candidates for a follow-up under a controlled cache
condition; they do not establish a statistically reliable optimum.

At c48 the three trials produced **194.97, 248.25, and 278.75 tokens/s**; sample
standard deviation42.40, coefficient of variation17.6%. Raw SGLang counters show
that prompt reuse changed across those trials. The cached-prompt fractions below
are counter deltas over the sampled measured interval, not averages of the
`cache_hit_rate` gauge. Saved scrape boundaries make the calculation reproducible.

| Concurrency | Trial | Cached prompt fraction | Output tokens/s | Estimated TFLOPS/GPU |
| ---: | ---: | ---: | ---: | ---: |
| 48 | 1 | 0.0% | 194.97 | 43.88 |
| 48 | 2 | 74.8% | 248.25 | 22.13 |
| 48 | 3 | 96.2% | 278.75 | 14.31 |
| 64 | 1 | 0.0% | 195.47 | 43.92 |
| 64 | 2 | 33.0% | 224.62 | 37.31 |
| 64 | 3 | 0.0% | 192.09 | 43.17 |

At c1, the same calculation changes from0% in trial1 to97.7% in trials2/3,
while estimated TFLOPS falls from4.18 to about0.92. At c32, cache reuse similarly
changes from0% to96.6–97.3%. The later c64 trial loses this reuse. These observations
show that identical seeds and an unchanged cache policy did **not** produce
identical cache conditions across repeated trials. Cache reuse is an important
contributor to the observed differences; these data do not isolate all effects,
such as temperature, eviction, and scheduling. AIPerf's confidence files are
retained, but pooling these trials does not establish stationary repeatability.

The higher estimated TFLOPS at c56–c72 must therefore not be presented as better
output performance. The new MTP=1 average must also not be directly called an
MTP speedup over the earlier MTP-disabled or MTP=2 results, which used different
admission, memory/cache allocation, and sampling protocols.

## Reproduction and artifacts

```bash
uv run --offline --no-project --python 3.12 <suite-archive>/analyze-mtp1-results.py <suite-archive>
```

`mtp1/round-summary.json` and `benchmark/cN/verified-summary.json` preserve the
original per-trial summaries. `mtp1/cache-trial-analysis.json` adds the raw
counter endpoints and derived prompt-reuse fractions. No benchmark artifacts
were replaced, and no serving containers were restarted for this analysis.
All 30 client exports, GPU/SGLang exports, and positive estimated-TFLOPS values
were checked in the completion audit; both variants' benchmark checksum manifests
passed. This follow-up adds interpretation rather than changing historical results.

## Lesson and policy clarification

For future repeatability claims, verify measured cache conditions as well as
fixed seeds. Choose and record either consistently primed measured prompts,
equivalent fresh-cache trials, or a deliberate mixture reported by condition.
The shared benchmarking policy now makes this repository rule explicit. Existing
completed runs retain their declared protocol and must be interpreted accordingly.
