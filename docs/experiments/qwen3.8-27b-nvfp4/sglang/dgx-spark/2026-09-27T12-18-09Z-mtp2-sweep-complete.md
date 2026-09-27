# 2026-09-27T12:18:09Z — NVFP4 MTP=2: full three-trial concurrency sweep completed

Run ID: `RUN-0030`

- Status: resolved
- Phase: inference / benchmark / lifecycle
- Repo revision: `89611e1`, dirty with experiment documentation
- Host/GPU: DGX Spark, NVIDIA GB10, driver `580.173.02`, aarch64
- Image: `sha256:110ad45e7872397f337ea5714e6c97c400852938a9b8f258bcc27cab07182b0c`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`; AIPerf `0.12.0`, Python 3.12
- Model: `nvidia/Qwen3.8-27B-NVFP4`, revision `482ca0f3832238542f8f5295dde86b5f22711d80`
- Artifacts: [2026-09-27T10-59-11Z-mtp2-aligned](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T10-59-11Z-mtp2-aligned/)
- Related turns: [MTP=2 launch](2026-09-25T20-24-59Z-mtp2-c72-round.md); see this target index for the MTP=1/3 launch and subsequent events.

## Verification

All ten concurrencies completed three successful measured trials with `max(64, 3 × concurrency)` requests per trial. Native AIPerf confidence/variability exports and per-trial metric-window summaries are retained; benchmark checksums are saved. Table values are descriptive equal-weight means of mixed cache conditions, not stable-performance estimates. See the external `cache-trial-report.md` for each first/repeat pass and measured reuse. c72 is client load above admission64.

| Concurrency | SGLang estimated TFLOPS/GPU | Total output tokens/s | Mean response time (s) |
| ---: | ---: | ---: | ---: |
| 1 | 2.37 | 22.28 | 5.74 |
| 2 | 4.30 | 40.32 | 6.28 |
| 4 | 7.41 | 70.94 | 7.12 |
| 8 | 11.95 | 115.82 | 8.56 |
| 16 | 17.30 | 171.46 | 11.56 |
| 32 | 22.74 | 232.67 | 17.44 |
| 48 | 26.26 | 246.72 | 24.60 |
| 56 | 41.88 | 211.68 | 33.28 |
| 64 | 42.27 | 207.48 | 38.15 |
| 72 | 42.88 | 211.37 | 40.85 |

Estimated TFLOPS uses counter deltas between scrapes inside each measured request window; it is a model estimate, not hardware FLOPs. The comparison with the earlier MTP=2/admission72 sweep also changes memory allocation and sampling protocol. This round aligns admission64, 256 slots, request counts, seeds, warmup and repeat policy with MTP=1/3; available KV capacity can still differ with drafting steps.

## Lesson

Match per-concurrency sample counts and preserve individual trials and phase boundaries for interpretable comparisons.
