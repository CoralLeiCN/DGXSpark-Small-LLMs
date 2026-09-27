# 2026-09-27T13:24:43Z — Final NVFP4 summary with aligned MTP=2

Run ID: `RUN-0033`

- Status: resolved
- Phase: offline analysis; no new inference
- Repo revision: `89611e1`, dirty with experiment documentation
- Hardware: DGX Spark, NVIDIA GB10
- Derived artifacts: [2026-09-27T13-24-43Z-final-aligned-mtp-summary](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/reports/2026-09-27T13-24-43Z-final-aligned-mtp-summary/README.md)

**MTP=3 had the fastest observed low-concurrency results; the aligned MTP=2 run had the highest three-trial averages at c16–c48.** At high concurrency the historical MTP-disabled baseline remained ahead. Small differences between MTP variants are not established wins, because the three passes have different prompt-cache reuse and appreciable variation.

This summary uses the September 27 MTP=2 rerun in place of its older September 25 single-trial result. It includes **100 measured trials and 14,064 requests**: 10 baseline trials/3,840 requests plus 30 trials/3,408 requests for each of MTP=1,2,3. Qualification and warmup are excluded. The older MTP=2 run remains archived; including it brings the completed sweeps to 110 measured trials/17,904 requests.

All included measured trials completed without recorded request errors or cancellation. The aligned MTP=2 round finished at **2026-09-27 12:18:25 UTC (13:18:25 BST)**. Its serving container, driver and monitor stopped; the preceding rounds had already stopped. This is offline analysis; no services were started.

**Observed throughput peaks** — MTP=1/2/3 values are arithmetic means of three passes with different cache conditions; the baseline has one trial. The peak is the largest observed point, not a proven optimum.

| Configuration | Concurrency | SGLang estimated TFLOPS/GPU | Total output tokens/s | Mean response time (s) |
| --- | ---: | ---: | ---: | ---: |
| MTP disabled | 64 | 49.89 | 221.74 | 36.94 |
| MTP=1 | 48 | 26.77 | 240.66 | 25.68 |
| MTP=2 | 48 | 26.26 | 246.72 | 24.60 |
| MTP=3 | 48 | 26.14 | 239.11 | 25.25 |

**Total output tokens/s at every concurrency** — all measured requests in each trial divided by profile duration; these are aggregate rates, not a per-user rate. Three-pass means are descriptive.

| Concurrency | MTP disabled | MTP=1 | MTP=2 aligned | MTP=3 |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 12.03 | 18.74 | 22.28 | 23.40 |
| 2 | 22.63 | 34.64 | 40.32 | 42.60 |
| 4 | 41.97 | 62.01 | 70.94 | 73.39 |
| 8 | 73.90 | 104.10 | 115.82 | 117.23 |
| 16 | 119.37 | 156.07 | 171.46 | 166.34 |
| 32 | 171.96 | 215.22 | 232.67 | 221.38 |
| 48 | 202.79 | 240.66 | 246.72 | 239.11 |
| 56 | 211.19 | 214.84 | 211.68 | 213.41 |
| 64 | 221.74 | 204.06 | 207.48 | 214.05 |
| 72 | 220.49 | 204.92 | 211.37 | 207.05 |

**Mean full-response time in seconds** — submission to final response, including waiting and generation.

| Concurrency | MTP disabled | MTP=1 | MTP=2 aligned | MTP=3 |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 10.64 | 6.83 | 5.74 | 5.47 |
| 2 | 11.31 | 7.38 | 6.28 | 5.97 |
| 4 | 12.20 | 8.21 | 7.12 | 6.89 |
| 8 | 13.85 | 9.73 | 8.56 | 8.54 |
| 16 | 17.15 | 12.90 | 11.56 | 11.67 |
| 32 | 23.81 | 18.98 | 17.44 | 17.96 |
| 48 | 30.29 | 25.68 | 24.60 | 25.25 |
| 56 | 33.30 | 32.97 | 33.28 | 32.81 |
| 64 | 36.94 | 38.72 | 38.15 | 36.92 |
| 72 | 39.25 | 41.86 | 40.85 | 41.61 |

**Mean SGLang estimated TFLOPS/GPU** — the same counter-delta method is used for all configurations.

| Concurrency | MTP disabled | MTP=1 | MTP=2 aligned | MTP=3 |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 2.70 | 2.00 | 2.37 | 2.50 |
| 2 | 5.09 | 3.68 | 4.30 | 4.54 |
| 4 | 9.44 | 6.48 | 7.41 | 7.75 |
| 8 | 16.62 | 10.75 | 11.95 | 12.21 |
| 16 | 26.85 | 15.86 | 17.30 | 17.02 |
| 32 | 38.62 | 21.06 | 22.74 | 21.90 |
| 48 | 45.60 | 26.77 | 26.26 | 26.14 |
| 56 | 47.49 | 42.37 | 41.88 | 42.19 |
| 64 | 49.89 | 41.47 | 42.27 | 43.63 |
| 72 | 49.63 | 41.73 | 42.88 | 42.73 |

**First-pass throughput** — sampled cached-prompt fractions are zero for every MTP=1/2/3 first pass. Historical baseline fractions are verified zero at c48–c72; some lower-concurrency counter endpoints are unavailable. This diagnostic reduces the repeated-prompt effect but has only one observation per setting and retains baseline configuration differences.

| Concurrency | MTP disabled | MTP=1 | MTP=2 aligned | MTP=3 |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 12.03 | 18.58 | 21.78 | 22.91 |
| 2 | 22.63 | 33.90 | 39.51 | 41.67 |
| 4 | 41.97 | 58.77 | 66.94 | 70.54 |
| 8 | 73.90 | 96.21 | 106.64 | 109.57 |
| 16 | 119.37 | 138.51 | 149.05 | 148.38 |
| 32 | 171.96 | 176.15 | 189.24 | 185.16 |
| 48 | 202.79 | 194.97 | 199.46 | 193.29 |
| 56 | 211.19 | 202.85 | 203.11 | 206.02 |
| 64 | 221.74 | 195.47 | 200.92 | 204.14 |
| 72 | 220.49 | 198.68 | 203.33 | 204.23 |

**The aligned MTP=2 run confirms the cache effect at c48:**

| Trial | Cached prompt tokens | Output tokens/s | Mean response (s) | Estimated TFLOPS/GPU |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 0.00% | 199.46 | 30.04 | 44.84 |
| 2 | 85.13% | 263.38 | 22.44 | 18.80 |
| 3 | 94.53% | 277.31 | 21.33 | 15.13 |

Its c48 mean is 246.72 tokens/s with a sample standard deviation of 41.52 across the three different cache conditions. The mean exceeds MTP=1 by only 2.52%, so this is not evidence of a reliable winner. On first passes, c48 rates were 202.79 disabled, 194.97 MTP=1, 199.46 MTP=2, 193.29 MTP=3. The apparent peak advantage in the pooled MTP means includes avoided prompt computation.

SGLang estimated TFLOPS counts approximate model work over the interior measured scrape interval. It does not measure total hardware FLOPs or MFU and does not fully charge speculative draft/rejected-verification work. As cached prompt computation is avoided, this estimate can fall while output throughput improves.

**What is now aligned:** all three MTP variants use three trials of `max(64, 3C)` requests, `max(8, C)` warmups before trial1, seed 42+C, identical generated inputs, retained cache across repeats, admission 64, 256 Mamba slots, static fraction 0.90, float32 Mamba state, FP8 KV and extra_buffer_lazy. All 30 new MTP=2 input hashes matched corresponding MTP=1/3 artifacts. Model/tokenizer revision 482ca0f3832238542f8f5295dde86b5f22711d80, image 110ad45e7872397f337ea5714e6c97c400852938a9b8f258bcc27cab07182b0c, SGLang 0.0.0.dev1+g5f55db35e and AIPerf 0.12.0 are unchanged. All use streaming text chat, 512 synthetic input target, 128 forced output tokens and thinking disabled.

**Remaining comparison limits:** available KV capacity is 683,856/395,653/83,041 tokens for MTP=1/2/3; actual cache reuse and thermal conditions still differ. c72 exceeds admission 64. The MTP-disabled baseline retains admission 72, 360 slots, static fraction 0.70, the older cache strategy, one 384-request trial and 96 warmups per point, and its archive does not independently pin the server-weight revision. It has not been rerun under the new protocol. Therefore this is a deployment comparison, not a fully controlled MTP-only ablation.

**Practical interpretation for this measured workload:**

- At c1–c8, MTP=3 had the highest observed mean throughput. At c1 its mean response was 5.47s versus 5.74s MTP=2, 6.83s MTP=1 and 10.64s disabled. The first-pass results also favor MTP=3 at these low concurrencies.
- At c16–c48, MTP=2 had the highest observed means. c32 delivered 232.67 tokens/s at 17.44s mean response, about 94% of its c48 throughput with about 29% less response time. This is a useful measured tradeoff for repeated-prompt traffic, not a general production optimum.
- At c48 the three MTP means were close relative to cache-driven variation. MTP=1 remains competitive; the data do not establish a clear universal winner.
- At c56, all means were near 211–215 tokens/s. At c64–c72 the historical disabled baseline remained highest. Increasing concurrency beyond 48 brought no higher pooled MTP throughput in these sweeps.

**Verification and artifacts:** new MTP=2 client aggregates agree with saved per-trial summaries; all 30 trials have expected request counts, no recorded errors/cancellation, matching input hashes and verified telemetry/FLOPs in the driver. Earlier extracted metrics retain their original source manifest. This report preserves a normalized 100-row CSV/JSON, 40-point summaries, source hashes, the generating script and links to raw data. No new inference or production-quality claim is made.

- [Aligned MTP=2 archive](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T10-59-11Z-mtp2-aligned/README.md)
- [Earlier full report](/home/coral/repos/DGXSpark-Small-LLMs/docs/experiments/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-26T08-06-38Z-mtp-disabled-1-2-3-final-report.md)
- [Normalized trial data](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/reports/2026-09-27T13-24-43Z-final-aligned-mtp-summary/trial-metrics.csv)
- [Summary data](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/reports/2026-09-27T13-24-43Z-final-aligned-mtp-summary/comparison-summary.json)
- [Source manifest](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/reports/2026-09-27T13-24-43Z-final-aligned-mtp-summary/source-manifest.json)

**Lesson:** consistent seeds and trial counts match the input procedure; measured cache state must accompany the performance comparison. Separate first and repeat passes when cache reuse changes.
