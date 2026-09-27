# 2026-09-26T03:02:55Z — NVFP4 MTP=1: full three-trial concurrency sweep completed

Run ID: `RUN-0021`

- Status: resolved
- Phase: inference / benchmark / lifecycle
- Repo revision: `89611e1`, dirty with experiment documentation
- Host/GPU: DGX Spark, NVIDIA GB10, driver `580.173.02`, aarch64
- Image: `sha256:110ad45e7872397f337ea5714e6c97c400852938a9b8f258bcc27cab07182b0c`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`; AIPerf `0.12.0`, Python 3.12
- Model: `nvidia/Qwen3.8-27B-NVFP4`, revision `482ca0f3832238542f8f5295dde86b5f22711d80`
- Artifacts: [2026-09-26T00-12-44Z-mtp1-mtp3](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-26T00-12-44Z-mtp1-mtp3/)
- Related turns: [MTP=2 launch](2026-09-25T20-24-59Z-mtp2-c72-round.md); see this target index for the MTP=1/3 launch and subsequent events.

## Verification

All ten concurrencies completed three successful measured trials with `max(64, 3 × concurrency)` requests per trial. Native AIPerf confidence/variability exports and per-trial metric-window summaries are retained; benchmark checksums are saved. Table values are equal-weight means of three trials. c72 is client load above admission64.

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

Estimated TFLOPS uses counter deltas between scrapes inside each measured request window; it is a model estimate, not hardware FLOPs. The comparison with the earlier MTP=2/admission72 sweep also changes memory allocation and sampling protocol.

## Lesson

Match per-concurrency sample counts and preserve individual trials and phase boundaries for interpretable comparisons.
