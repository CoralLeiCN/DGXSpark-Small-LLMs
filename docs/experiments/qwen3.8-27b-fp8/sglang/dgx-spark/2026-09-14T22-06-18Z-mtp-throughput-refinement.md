# 2026-09-14T22:06:18Z — Intermediate concurrency checks retain the peak at 64

Run ID: `RUN-0018`

- Status: resolved (56 and 72 measured; second-seed confirmation follows)
- Phase: inference
- Related turns: [Matched peak bracket](2026-09-14T21-55-45Z-mtp-throughput-peak-bracket.md)
- Repo revision: `17d39b06860ea7159a3d4a3443053b4d79bf867e`, dirty
- Host/GPU: one DGX Spark GB10, Linux aarch64, driver `580.173.02`
- Container: `inferpack-qwen38-fp8-mtp-capacity96`, image
  `dgxspark/qwen3.8-27b-fp8-sglang:0.1.0`, ID
  `sha256:3c11adf54d4a220f587f361f48eee66b50a8e2b8c068db7484c598beb3684b62`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, FlashInfer `0.6.17`,
  torch `2.13.0+cu130`, transformers `5.12.1`
- Model: `Qwen/Qwen3.8-27B-FP8`, revision
  `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`

## Command And Conditions

Continued on the unchanged RUN-0016 server (FP8 native MTP three steps / top-k
one / four draft tokens, memory fraction 0.85, active cap 96, Mamba slots 384,
graph maximum 96, context 32768, prefill chunk 2048, BF16 KV/GDN state).

Ran the RUN-0017 shell loop with `for concurrency in 72 56`, retaining its
uv/AIPerf environment, 384 measured requests, 96 warmups, seed 3000, and a
successful idle-cache flush before each profile. Workload remained 512 target
input tokens / 128 forced output tokens, temperature zero, thinking disabled.
Artifacts use the same prefix with suffixes `-c72` and `-c56`.

## Results And Verification

| Concurrency | Output tokens/s | Median / p95 latency (s) | Median / p95 TTFT (s) | Mean per-user decode tokens/s |
| --- | --- | --- | --- | --- |
| 56 | 204.78 | 34.48 / 44.60 | 2.19 / 12.03 | 4.24 |
| 64 (RUN-0017) | 207.79 | 39.11 / 49.96 | 2.39 / 14.35 | 3.78 |
| 72 | 200.75 | 44.74 / 61.04 | 2.82 / 16.54 | 3.41 |

All 768 new measured requests and 192 warmups passed, with no errors or
cancellations and exactly 128 completion tokens per response. Actual input
lengths were 523–526. Inputs and measured conversation-ID multisets matched all
four RUN-0017 profiles; the shared input SHA256 remains
`6f6c35d182d422d5a72017dc2a199a5925bda7b6fadc8c179e240fd39a657392`.

Median client effective concurrency was exactly 56 and 72. Five-second
scheduler median active counts were 55.5 and 72, with zero median queue depth.
Sampled acceptance lengths were approximately 2.76 and 2.74. Cache-hit samples
were zero, and monitor collection had no errors. Minimum sampled available
host memory was 12,728 MiB across these measured phases. No inference failures
were observed; the server remains running for confirmation.

## Conclusion And Next Step

The refined sampled peak remains at 64. Relative to 64, 56 is only 1.45% lower
in aggregate throughput and has 11.84% lower median latency; 72 loses 3.39%
throughput while increasing latency. This is a narrow top around 56–64, not
proof of a unique best integer concurrency. Repeat both with seed 5000 and
the same profile sizes, reversing their relative order, before selecting the
best measured throughput setting.

## Artifacts And Lesson

The shared server artifact directory contains `refined.json`, confirming
matching inputs across all six profiles and collecting their monitor summaries,
plus the refinement driver and collection script. Per-request and aggregate
exports remain in each profile directory.

Near a broad peak, distinguish the measured winner from a lower-concurrency
setting that offers nearly the same throughput with less latency. Validate
small differences with repeated paired workloads.
