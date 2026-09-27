# 2026-09-26T00:25:10Z — NVFP4 MTP=2: all ten profiles completed and service stopped

Run ID: `RUN-0015`

- Status: resolved
- Phase: inference / benchmark / lifecycle
- Repo revision: `89611e1`, dirty with experiment documentation
- Host/GPU: DGX Spark, NVIDIA GB10, driver `580.173.02`, aarch64
- Image: `sha256:110ad45e7872397f337ea5714e6c97c400852938a9b8f258bcc27cab07182b0c`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`; AIPerf `0.12.0`, Python 3.12
- Model: `nvidia/Qwen3.8-27B-NVFP4`, revision `482ca0f3832238542f8f5295dde86b5f22711d80`
- Artifacts: [2026-09-26T00-12-44Z-mtp1-mtp3](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-26T00-12-44Z-mtp1-mtp3/)
- Related turns: [MTP=2 launch](2026-09-25T20-24-59Z-mtp2-c72-round.md); see this target index for the MTP=1/3 launch and subsequent events.

## Observation

Follow-up to RUN-0014, observed on September 26. The sweep finished at
**2026-09-25T22:42:24Z**, exit status 0, after starting at 20:30:39Z.
All ten profiles have 384 measured requests, no error summary, and no cancellation.
This was the previously declared single-trial protocol: 96 warmups per concurrency.
The newly adopted sampling rules do not retroactively change this run.

| Concurrency | Total output tokens/s | Mean response time (s) |
| ---: | ---: | ---: |
| 1 | 21.83 | 5.86 |
| 2 | 39.30 | 6.51 |
| 4 | 67.78 | 7.53 |
| 8 | 106.45 | 9.57 |
| 16 | 149.66 | 13.53 |
| 32 | 188.43 | 21.45 |
| 48 | 197.78 | 30.39 |
| 56 | 203.78 | 34.52 |
| 64 | 203.80 | 39.64 |
| 72 | 203.01 | 43.89 |

The result archive is
[`2026-09-25T20-24-59Z-mtp2-c72`](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-25T20-24-59Z-mtp2-c72/).
It contains request records, client aggregates, GPU telemetry, SGLang metrics
including estimated-FLOPs counters, final server snapshots, and benchmark checksums.
The table is a completion summary, not a new matched comparison or TFLOPS analysis.

## Commands and verification

```bash
# From the MTP=2 artifact directory; observed exit status 0.
sha256sum --check --quiet benchmark-sha256.txt
docker stop --timeout 60 inferpack-qwen38-nvfp4-mtp2-c72-20260925
docker inspect --format '{{json .State}}' inferpack-qwen38-nvfp4-mtp2-c72-20260925
```

The container stopped at **2026-09-26T00:13:00.868519911Z**, exit 0, with
`Running=false`, `OOMKilled=false`. The preceding health checks were successful.
A final health request returned HTTP failure while intentional shutdown was
already in progress; this is a lifecycle observation, not a failed benchmark.
Shutdown state/logs are also preserved in this turn's MTP=1/3 suite archive as
`previous-mtp2-final-state.json`, `previous-mtp2-server-final.log`, and
`previous-mtp2-shutdown.log`.

## Diagnosis and next change

Throughput flattened around c56–c72 while response time increased. These are
single-trial observations; do not claim a statistically significant winner.
The user authorized NVFP4 MTP=1 and MTP=3 next, followed by service shutdown.
Those rounds use the new shared sampling policy and common admission64/cache256,
so comparison against this MTP=2 admission72/cache288 run must disclose both changes.

## Lesson

Keep a started protocol fixed, verify stored artifacts after completion, and
record later completion and shutdown in a new entry instead of rewriting launch history.
