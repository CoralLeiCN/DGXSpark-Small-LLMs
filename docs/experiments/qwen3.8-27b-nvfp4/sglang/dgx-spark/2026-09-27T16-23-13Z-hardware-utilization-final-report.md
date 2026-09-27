# 2026-09-27T16:23:13Z — MTP=2 hardware-utilization pilot and retained experiment scripts

Run ID: `RUN-0047`

- Status: workaround — bounded pilot completed; whole-range hardware utilization unavailable
- Phase: inference, hardware profiling, validation and shutdown
- Related turns: [normal baseline, RUN-0039](2026-09-27T15-00-27Z-hardware-pilot-baseline-complete.md), [timeline capture, RUN-0042](2026-09-27T15-25-54Z-hardware-pilot-timelines-and-forward-annotations.md), [bounded recovery, RUN-0046](2026-09-27T16-05-09Z-hardware-pilot-bounded-kernel-recovery.md)
- Repo: `f3f1d2e`, dirty; latest main `1e0117f` merged before this pilot.
- Hardware: one DGX Spark GB10, SM12.1, driver 580.173.02, CUDA 13.0.

The fresh-cache MTP=2 configuration delivered **21.81, 106.64 and 202.54 output tokens/s at concurrency 1, 8 and 64**. The GPU was active for about 99% of the separate timeline windows, while Tensor Core activity increased from 9.65% to 22.26%. This establishes a busy GPU with substantial non-Tensor-Core work; it does not establish saturation of peak compute or memory bandwidth.

**We cannot report whole-server physical DRAM utilization or complete hardware MFU from this pilot.** The installed GB10 counter sets do not expose physical memory-controller bytes. Whole-range Nsight Compute profiling exhausted memory, so the successful fallback collects selected kernels. The report retains that limitation rather than converting activity percentages or estimated bytes into unsupported utilization claims.

## Normal inference results

Three trials per concurrency; entries are mean ± sample standard deviation. SGLang TFLOPS come from the estimated-FLOPs counter delta over each measured interval. They include modeled work associated with the workload and are not GPU instruction counts.

| Concurrency | SGLang estimated TFLOPS/GPU | Total output tokens/s | Mean response time (s) |
| ---: | ---: | ---: | ---: |
| 1 | 4.909 ± 0.015 | 21.808 ± 0.063 | 5.866 ± 0.017 |
| 8 | 24.043 ± 0.220 | 106.644 ± 1.071 | 9.377 ± 0.089 |
| 64 | 45.533 ± 0.060 | 202.545 ± 0.394 | 38.507 ± 0.075 |

| Client concurrency | Requests per trial | Total measured requests | Mean TTFT | Mean inter-token latency | Mean queue wait | Mean prefill-forward latency |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 64 | 192 | 254 ms | 44.2 ms | 0.00019 s | 0.235 s |
| 8 | 64 | 192 | 781 ms | 67.7 ms | 0.0396 s | 0.558 s |
| 64 | 192 | 576 | 4,328 ms | 269.1 ms | 2.472 s | 1.388 s |

All **960 measured requests** completed without request errors, with 128 output tokens each and zero measured prompt reuse. Generated inputs matched across repeats at each concurrency. These are descriptive exploratory statistics, not a convergence or precise tail-latency claim. The mean of the three trial-specific P95 response times was 6.49 s, 10.64 s and 50.55 s; it is not a pooled P95.

C8 produces 4.89 times C1's throughput for 1.60 times the response time. Moving from C8 to C64 adds 1.90 times the throughput while increasing mean response time 4.11 times. C64 is the highest-throughput point tested here; these three points alone do not prove the exact location of a plateau. C8 offers a substantially better latency/throughput compromise for this workload.

Queueing remains possible with client concurrency equal to the admission limit. Requests arrive together, prefill is chunked, and the scheduler must allocate state and arrange work alongside ongoing decoding. An admission limit is a capacity ceiling, not a guarantee of immediate service. The measured queue wait and prefill time describe different server stages; they need not add exactly to client TTFT. The sampled running-request gauge is retained as emitted: the C8 trial maxima were 8–10. It is not used to redefine the client's configured concurrency.

NVML-reported mean power was 40.7 W, 49.7 W and 59.1 W; mean temperature was 70.0 °C, 75.6 °C and 75.8 °C. These are the reported GPU sensor values, not system wall power. Temperature reached 81 °C/83 °C/82 °C at least once respectively. We did not establish thermal throttling from temperature alone.

## Hardware limits and local calibration

NVIDIA specifies **273 GB/s LPDDR5x bandwidth** and **up to 1 PFLOP/s FP4 with sparsity** for Spark. The serving kernels here use dense block-scaled FP4. An approximate **500 dense FP4 TFLOPS** reference is inferred by dividing the advertised sparse figure by the usual 2× structured-sparsity factor; it is not an independently published, measured dense Spark guarantee. [Spark hardware specifications](https://docs.nvidia.com/dgx/dgx-spark/hardware.html), [NVIDIA's explanation of the sparse/dense factor](https://developer.nvidia.com/blog/structured-sparsity-in-the-nvidia-ampere-architecture-and-applications-in-search-engines/).

| Unprofiled calibration | Mean ± sample SD | Observed range | Comparison |
| --- | ---: | ---: | --- |
| Streaming read | 229.14 ± 1.55 GB/s | 227.35–230.16 GB/s | 83.9% of 273 GB/s using logical streaming bytes |
| Streaming write | 195.39 ± 2.23 GB/s | 193.61–197.89 GB/s | 71.6% of 273 GB/s using logical streaming bytes |
| Streaming copy, read+write | 209.53 ± 0.63 GB/s | 208.81–209.90 GB/s | 76.8% of 273 GB/s using logical read+write bytes |
| Dense NVFP4 GEMM, M=64/N=4096/K=4096 | 46.15 ± 2.43 TFLOPS | 43.36–47.85 TFLOPS | 9.2% of inferred 500 TFLOPS |
| Dense NVFP4 GEMM, M=512/N=4096/K=4096 | 299.76 ± 16.39 TFLOPS | 281.46–313.08 TFLOPS | 60.0% of inferred 500 TFLOPS |
| Dense NVFP4 GEMM, M=4096/N=4096/K=4096 | 323.46 ± 3.53 TFLOPS | 319.59–326.52 TFLOPS | 64.7% of inferred 500 TFLOPS |
| Dense FP8 GEMM, M=4096/N=4096/K=4096 | 179.66 ± 1.59 TFLOPS | 177.83–180.62 TFLOPS | Separate precision; do not divide by the FP4 limit |

Each calibration has three short trials. Memory arrays are 512 MiB, larger than the 24 MiB L2 cache. GEMM quantization occurs outside the timed multiplication, and numerical checks compare to FP32 reference products from the BF16 source inputs. Clocks were automatic and these were not thermal soaks. Treat the results as pattern-specific local references, not universal sustained ceilings. The logical bandwidth formula follows [NVIDIA's effective-bandwidth definition](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html#bandwidth).

The strong GEMM shape effect is directly measured: identical N and K with small M reaches only about 46 TFLOPS, while large M reaches 323 TFLOPS. Peak compute is therefore a poor direct predictor of token-generation speed at low batch sizes. Batching helps reuse weights and fill execution tiles; it also increases state movement and per-request latency.

The FP4 hardware counter matched exactly `2 × 4096³ = 137,438,953,472` operations for the calibration GEMM. The FP8 validator initially failed because it compared useful matrix work to hardware operations: the counter recorded 143,948,513,280. The observed kernel is `nvjet_sm121_qqtst_mma_192x160x128_2_48x80x128_tmaAB_bz_TNNN`; rounding the output to its 192×160 tiles gives `2 × 4224 × 4160 × 4096`, exactly the counter value. Padded-tile execution is the evidence-based interpretation, not a claim that the useful matrix became larger. The original validator and corrected `analyze-calibration-v2.py` are retained. The observed failing command was `uv run --offline --no-project --python 3.12 scripts/analyze-calibration.py ROOT OUTPUT.json`, with `AssertionError: ('fp8', 143948513280.0)`. The v2 rerun passed numerical, byte-counter and padded-operation checks. The reusable lesson is to distinguish useful matrix FLOPs from executed tile operations before interpreting a hardware counter.

Application-range calibration also collected the known FP4 operation count in one pass, but its 2.518 ms duration includes range boundaries/host overhead. Its 54.59 TFLOPS rate is not comparable to the isolated large-GEMM peak without that timing distinction.

## Serving timelines

| Client concurrency | Captured GPU activity span | GPU busy union | Tensor Active sample mean | SM Active sample mean | Visible Mamba scatter share of span |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 29.67 s | 98.94% | 9.65% | 88.58% | 1.33% |
| 8 | 27.14 s | 99.13% | 13.88% | 91.85% | 6.70% |
| 64 | 27.84 s | 99.45% | 22.26% | 97.07% | 12.57% |

GPU busy is the union of graph execution, eager kernels, memory copies and memory sets between first and last GPU activity. It is not a simple sum that double-counts overlap. Tensor/SM activity are sample means at approximately 1 ms intervals. Tensor Active does not measure achieved TFLOPS or bandwidth. NVIDIA documents these as distinct [GPU activity metrics](https://docs.nvidia.com/nsight-systems/UserGuide/index.html#gpu-metrics).

The visible `_fused_mamba_state_scatter_with_mask_kernel` consumed 0.394 s, 1.819 s and 3.499 s respectively. Its growing share is evidence that state movement becomes more significant as concurrency rises. It supports investigating state-copy cost, but does not by itself prove that the memory controller is saturated or that all remaining time is GEMM work. Most CUDA graph internals are aggregate graph records in these captures; the eager-kernel list is not a complete kernel ranking.

The successful Systems image emitted scheduler NVTX spans but lacked forward-mode spans. We therefore do not fabricate prefill/decode attribution for these full windows. A later diagnostic-only annotation patch supplies forward/batch labels for selected-kernel captures. Invalid signed clock fields in the Systems metric set were excluded; separate `nvidia-smi` clock/power CSVs are retained.

## Selected hardware counters and their interpretation

The bounded recovery completed all six capture opportunities and all 448 diagnostic requests without request errors. It exported **12 single-pass kernel samples**. All prefill captures caught the first arriving request: actual batch 1 and 524 tokens, even when client concurrency was 8 or 64. The persistent first-launch filter therefore produced no new prefill samples at C8/C64. Decode captures were armed only at full running batches 1/8/64 with an empty queue; forward labels independently confirmed those target-verification batches and 3/24/192 verification positions.

| Sample | Client C | Observed scope | Kernel time (ms) | Hardware FP4 TFLOPS | Read-fill proxy (GB/s) | Write-request proxy (GB/s) |
| ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 0 | 1 | Prefill, batch 1 / 524 tokens | 0.914 | 249.58 | 111.71 | 44.02 |
| 1 | 1 | Prefill, batch 1 / 524 tokens | 3.189 | 51.04 | 224.46 | 0.22 |
| 2 | 1 | Target verify, batch 1 | 0.472 | 48.35 | 212.91 | 0.51 |
| 3 | 1 | Target verify, batch 1 | 0.259 | 22.00 | 194.18 | 0.24 |
| 5 | 8 | Draft stage; batch label absent | 3.183 | 102.24 | 224.81 | 1.27 |
| 6 | 8 | Target verify, batch 8 | 0.479 | 23.84 | 210.03 | 3.58 |
| 8 | 64 | Draft stage; batch label absent | 3.457 | 94.14 | 207.14 | 9.58 |
| 9 | 64 | Target verify, batch 64 | 0.595 | 153.38 | 169.74 | 22.59 |
| 10 | 64 | Target verify, batch 64 | 0.612 | 55.97 | 216.66 | 3.27 |

The selected GEMMs range from 22.00 to 249.58 hardware FP4 TFLOPS, numerically 4.4–49.9% of the approximate 500 dense FP4 reference. These are individual-kernel rates, not whole-server utilization. They are different kernels and shapes, so their spread is not a matched concurrency speedup comparison. Draft kernels are identified by their own `draft` NVTX span; their per-kernel batch dimension is not labeled.

Several read-fill rates are around 207–225 GB/s, close to the 229 GB/s streaming-read reference. This is consistent with substantial memory pressure in those selected GEMMs. It does not measure the total physical controller traffic or establish sustained inference bandwidth saturation.

The three selected Mamba scatter samples took 0.027/0.167/1.190 ms at C1/C8/C64 and showed very little system-memory proxy traffic. They are much shorter than the mean visible scatter events in the Systems traces. These first-launch samples cannot represent all state copies or explain their aggregate bandwidth; data-dependent masking and cache behavior were not separately isolated. Their zero FP4 operation count is expected for a state-copy kernel, not evidence of no GPU work.

For each selected kernel, hardware FP4 TFLOPS is `sm__ops_path_tensor_src_fp4_dst_fp32.sum / kernel_seconds / 1e12`. It covers that precision and accumulation path only. It excludes other-precision Tensor Core work and scalar arithmetic, and may include padded tile operations. The model's draft and verification activity is not equivalent to accepted output-token work.

The installed `gb20b` Compute catalog exposes L2/system-memory counters, but no usable `dram__`, `dramc__` or `mcc__` byte counters. The Systems GPU metric set also has no DRAM bandwidth metric; its available SoC bandwidth option was not a GB10 solution in this installation. This describes the installed tools, not all future NVIDIA tooling.

We report **read-fill proxy bytes** as `lts__d_sectors_fill_sysmem.sum × 32` and **write-request proxy bytes** as `lts__t_sectors_aperture_sysmem_op_write.sum × 32`. In a known 512 MiB streaming copy these matched expected read/write bytes to within 0.103% and 0.026%. That qualification does not turn them into physical LPDDR measurements: write requests can hit L2 or coalesce, and CPU/other-SoC traffic is outside this scope. Do not sum these inference rates and divide by 273 GB/s to claim DRAM utilization.

Consequently, the remaining physical-bandwidth question needs a GB10-supported memory-controller counter path, validated on known-byte workloads, or a supported NVIDIA profiling update. The current evidence can identify expensive kernel families and compare their memory behavior, but cannot quantify whole-system LPDDR headroom. Likewise, dividing SGLang's 45.53 estimated TFLOPS by 500 would give 9.1% numerically, but **does not establish 9.1% hardware utilization or an 11× optimization opportunity**.

## Configuration, protocol and scope changes

- Model and tokenizer: `nvidia/Qwen3.8-27B-NVFP4`, pinned revision `482ca0f3832238542f8f5295dde86b5f22711d80`.
- Normal image: `sha256:110ad45e7872397f337ea5714e6c97c400852938a9b8f258bcc27cab07182b0c`; SGLang `0.0.0.dev1+g5f55db35e`, FlashInfer 0.6.17, AIPerf 0.12.0, Python 3.12.3 inside the serving image.
- MTP: EAGLE, two drafting steps, top-k 1, three verification positions. Effective admission 64, Mamba 256, float32 SSM, `extra_buffer_lazy`, ratio 4.59, FP8e4m3 KV, context 32768, chunked prefill 2048, static memory fraction 0.90. No replay-SSM workaround.
- Synthetic 512-token input target, actual average about 524 tokens after formatting; 128 forced output tokens, ignoreEOS, temperature 0, thinking disabled, streaming. No model-quality claim follows from this synthetic test.
- Measured requests `max(64,3C)`, three trials. Separate warmup `max(8,C)`, model/kernel initialization before measured traffic. Seeds 42+C measured and 1042+C warmup. Idle cache flush before every measured trial; total/uncached prompt histogram sums and counts verify zero reuse.
- C1 trial 1 was retained after an analysis failure; the remaining trials followed an identical-config server restart and rewarm. Temperature differences remain a limitation of interpreting the three trials as one uninterrupted steady-state run.
- Normal KV capacity was 391,869 tokens. Systems instrumentation reduced observed capacity to 343,661. Selected-kernel profiling explicitly capped KV at 65,536 tokens, leaving admission 64 and Mamba 256 unchanged. That cap exceeds the roughly 41,728 active prompt+output tokens of 64 requests at this workload size, but it is still a configuration difference.
- Successful Systems image: `sha256:3081c11204b7dd0f3010900bf96244fc11712ca0c37ed92cb97f3c4ee1e8165e`, adding NVTX 0.2.16. Selected-kernel image: `sha256:7c694cc214888ed37c1eba40e3be4d8e82c6516faeaf4ccb23d0833369169b92`, adding forward annotations and shape logging. These patches did not change model mathematics; instrumentation changes timing and memory consumption.
- Nsight Systems 2025.3.2.474 and Compute 2025.3.1.0. Systems worked with container `PERFMON`; Compute needed temporary-container `SYS_ADMIN`. Host profiling policy was not changed.
- The six short hardware capture opportunities are diagnostics, not repeated performance trials. Their client timing is excluded from the normal result table. Profiler replay and instrumentation affect execution, as described by [NVIDIA's profiling guide](https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html).

The repository's [benchmarking rules](../../../../BENCHMARKING.md) apply. Three times concurrency comes from NVIDIA's worked method; the 64-request floor and fresh-cache verification are repository choices. Three exploratory trials follow [AIPerf confidence-reporting guidance](https://docs.nvidia.com/aiperf/dev/tutorials/metrics-analysis/multi-run-confidence-reporting). This pilot is not a new matched MTP-disabled/1/2/3 comparison; historical rounds used different cache conditions.

## Failures, verification and retained deliverables

RUN-0035 through RUN-0046 retain the failed zero-warmup option, lazy cache-counter verifier, missing NVTX dependency, Dockerfile invocations, wrong offline client cache, missing forward annotations, intrusive complete-kernel capture, rejected application-range options, and profiler OOM/allocator failures. Failed and partial reports are preserved and excluded from complete-data claims. The selected-kernel recovery's verification is successful: all 448 diagnostic requests completed, all 12 sampled kernels required one replay pass, log-to-report kernel names matched exactly within the single CUDA stream, actual forward shapes were retained, and independent counter analysis passed.

All successful normal trials were independently revalidated from persisted AIPerf exports, engine counters and GPU samples. Calibration, timeline exports and selected-kernel analysis retain source hashes and explicit counter/timing semantics. At **16:20:23 UTC**, all 12 owned containers were stopped, all remaining pilot units were non-running, no GPU compute processes remained, and the endpoint was unavailable. Historical failed units retain their failure state as evidence. The final validator passed for all 9 normal trials, 3 timelines, 12 kernel samples, calibration sources and 50 retained source snapshots.

Scripts are retained in the repository at [the hardware-utilization experiment directory](../../../../../models/qwen3.8-27b-nvfp4/sglang/targets/dgx-spark/experiments/hardware-utilization/README.md), including runners, calibration programs, Docker instrumentation, validators, analyzers, failed recovery versions and a SHA-256 provenance manifest. They are exact experiment snapshots with pinned names and recovery dependencies; a new round needs a fresh artifact directory and container names. Dependencies remain in their model container or isolated AIPerf environment. No raw profiler binaries or run metrics are added to Git.

All raw data: [external pilot archive](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T13-56-21Z-mtp2-hardware-pilot/).

- [Normal trial CSV](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T13-56-21Z-mtp2-hardware-pilot/analysis/baseline/baseline-trials.csv) and [validated baseline JSON](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T13-56-21Z-mtp2-hardware-pilot/analysis/baseline/baseline-analysis.json).
- [Calibrations](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T13-56-21Z-mtp2-hardware-pilot/analysis/calibration-analysis-v2.json).
- [GPU timelines](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T13-56-21Z-mtp2-hardware-pilot/analysis/nsys/timeline-analysis.json) and [visible state-copy analysis](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T13-56-21Z-mtp2-hardware-pilot/analysis/nsys/visible-kernels.json).
- [Selected-kernel CSV](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T13-56-21Z-mtp2-hardware-pilot/analysis/selected/selected-kernels.csv), [validated capture provenance](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T13-56-21Z-mtp2-hardware-pilot/analysis/selected/selected-kernels.json), and [raw counters with full NVTX stacks](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T13-56-21Z-mtp2-hardware-pilot/profiles/ncu-selected-v8/counters.json).
- [Final status](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T13-56-21Z-mtp2-hardware-pilot/status.json) and [shutdown verification](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T13-56-21Z-mtp2-hardware-pilot/final-shutdown-verification.json) and [final validation](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T13-56-21Z-mtp2-hardware-pilot/analysis/final-validation.json).
