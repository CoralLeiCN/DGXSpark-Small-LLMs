# DGX Spark NVFP4 performance gaps, research findings and next steps

- Research date: **2026-09-27**
- Scope: Qwen3.8 27B NVFP4, SGLang, one DGX Spark GB10 (SM12.1)
- Status: **Research and proposed follow-up only. No implementation or new GPU experiments were performed for this document.**
- Measured baseline: [MTP=2 performance and hardware-utilization report](2026-09-27-mtp2-hardware-utilization.md)

Our large dense NVFP4 calibration achieves **323.46 TFLOPS**, approximately
**64.7% of an inferred 500-TFLOPS dense reference**. Online research identifies
plausible improvements in kernel selection, data movement and launch overhead.
It does not establish how much faster our exact workload can run. NVIDIA's new
Rust kernel projects add a credible experimental implementation option, but
there is no demonstrated Rust speedup over our baseline.

## Measured gap and appropriate references

NVIDIA specifies **up to 1 PFLOP/s FP4 with sparsity** and **273 GB/s memory
bandwidth** for Spark. Our calibration is dense. The approximate **500 dense
FP4 TFLOPS** reference divides the sparse headline by the usual 2× structured
sparsity factor; it is not a guaranteed measured GEMM rate.
[NVIDIA hardware specifications](https://docs.nvidia.com/dgx/dgx-spark/hardware.html),
[NVIDIA's sparse/dense explanation](https://developer.nvidia.com/blog/exploiting-ampere-structured-sparsity-with-cusparselt/).

| Measurement or reference | Dense FP4 TFLOPS | Fraction of approximate 500-TFLOPS reference | Higher throughput than our mean |
| --- | ---: | ---: | ---: |
| Our 4096 × 4096 × 4096 GEMM, three-trial mean | 323.46 | 64.7% | Baseline |
| Our best trial at the same shape | 326.52 | 65.3% | 0.9% |
| Community CUTLASS result, 4096 × 14336 × 4096 | 356 | 71.2% | 10.1% |
| Another community CUTLASS result at that rectangular shape | ~375 | ~75.0% | ~15.9% |
| Inferred dense hardware reference | ~500 | 100% | ~54.6% |

Our measurements are preserved in the
[validated calibration analysis](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T13-56-21Z-mtp2-hardware-pilot/analysis/calibration-analysis-v2.json).
The **356-TFLOPS** result is a February 2026 firsthand community report using
CUDA 13.1 and CUTLASS 4.4.0. It is not an NVIDIA-certified benchmark.
[Original report](https://forums.developer.nvidia.com/t/sm121-cutlass-kernel-optimization-results-nvfp4-356-tflops-moe-grouped-gemm-on-dgx-spark/359960).
The **~375-TFLOPS** result is another author's reported CUTLASS measurement,
with code available in
[nvfp4bench](https://github.com/secYOUre/nvfp4bench).

The external measurements use a different matrix shape, software and timing
protocol. They show that higher dense GEMM rates have been reported on GB10;
they do **not** establish a 10–16% improvement available for our 4096³ case.
Nor are they demonstrated sustained ceilings for our machine.

The gap calculation is:

```text
Absolute shortfall:       500 - 323.4567 = 176.5433 TFLOPS
Shortfall / reference:    176.5433 / 500 = 35.3%
Uplift to reference:      500 / 323.4567 - 1 = 54.6%
```

The last two percentages use different denominators. A 35.3% shortfall from
peak does not mean that increasing current throughput by 35.3% reaches peak.

## What the baseline measures

The [retained calibration script](../../../../../models/qwen3.8-27b-nvfp4/sglang/targets/dgx-spark/experiments/hardware-utilization/2026-09-27/fp4.py)
uses FlashInfer **0.6.17**, `nvfp4_quantize`, and `mm_fp4(..., backend='cutlass')`
with BF16 output. Inputs are quantized before timing. Each shape has ten warmup
calls and three trials of 100 calls timed with CUDA events. The environment
used CUDA 13.0 and driver 580.173.02, automatic clocks, and short trials.

| M, with N=K=4096 | Mean ± sample SD, TFLOPS | Ideal arithmetic intensity, FLOP/byte |
| ---: | ---: | ---: |
| 64 | 46.15 ± 2.43 | 212.43 |
| 512 | 299.76 ± 16.39 | 1,159.93 |
| 4096 | 323.46 ± 3.53 | 2,621.44 |

Shape strongly affects throughput. These M values are matrix dimensions,
not client concurrency; prefill, ordinary decode and speculative verification
produce different matrix shapes.

For 4096³, the ideal traffic budget is 9 MiB for each packed input including
block scales, plus 32 MiB for BF16 output: **50 MiB total**. Useful work is
`2MNK = 137,438,953,472 FLOPs`. The separately profiled FP4 calibration's hardware
counter matched that operation count. The byte-budget derivation and timing
limitations are in the [baseline report](2026-09-27-mtp2-hardware-utilization.md#reference-and-derivation-of-the-50-mib-byte-budget).

The ideal bandwidth roof is `2621.44 × 273 / 1000 = 715.65 TFLOPS`, above the
approximate compute reference. Thus, this ideal model does not explain the
entire shortfall as a bandwidth limit. Repeated tile loads, cache behavior,
scale handling, synchronization and stores can reduce actual efficiency.
The 50 MiB budget is not measured physical traffic, and the real bottleneck
has not been established.

## Research findings

### Exact-shape autotuning is the first candidate

Our calibration explicitly chooses CUTLASS and does not request autotuning.
FlashInfer documents that tuning profiles candidate implementations and their
kernel configurations; otherwise it uses a cached selection or fallback.
The version 0.6.17 SM120-family CUTLASS fallback uses a 128 × 128 × 128 tile.
This identifies an untested opportunity, not proof that the fallback is poor.
[FlashInfer autotuning](https://docs.flashinfer.ai/autotuning.html),
[version 0.6.17 CUTLASS dispatch](https://github.com/flashinfer-ai/flashinfer/blob/v0.6.17/csrc/fp4_gemm_cutlass_sm120.cu).

Compare tuned CUTLASS with supported cuDNN configurations. Treat `b12x` as an
additional explicit candidate: version 0.6.17 supports it on SM121 but deliberately
excludes GB10 from automatic preference because CUTLASS/cuDNN are usually faster
there. The backend named `cute-dsl` in that version targets SM100/SM103; it is
not interchangeable with `b12x` or NVIDIA's separate cuTile Rust project.
[Version-specific backend requirements and selection](https://github.com/flashinfer-ai/flashinfer/blob/v0.6.17/flashinfer/gemm/gemm_base.py).

### Kernel scheduling and data reuse can improve useful throughput

Colfax demonstrates SM120 NVFP4 improvements from threadblock scheduling for
cache reuse, load/store overlap, scale-load bank-conflict reduction, tile
selection and autotuning. Its combined improvement at 4096³ is **6%**, with
larger gains at some other shapes. Those results use an RTX PRO 6000, whose
memory bandwidth, cache and SM count differ from GB10. The techniques are
relevant research leads; the percentage gains are not Spark predictions.
[Colfax implementation and results, August 2026](https://research.colfax-intl.com/optimizing-an-nvfp4-blockscaled-gemm-on-rtx-pro-6000-blackwell-gpu-sm120/).

GB10 requires kernels appropriate to SM12.1. Datacenter Blackwell examples
using `tcgen05`, TMEM or two-SM MMA are not evidence of an applicable GB10
implementation. Native FP4 execution is already present in our calibration;
this is not an observed BF16 fallback problem.

### Launch overhead and operating conditions remain unquantified

The calibration repeats calls from Python, does not pass a reusable `out`
buffer, and does not use CUDA graph replay. Graph replay can reduce repeated
submission overhead. Its gain depends on gaps between kernels; it does not
make unchanged GPU instructions execute faster. Our large GEMM averages about
425 microseconds, so launch overhead may matter more for shorter shapes.
Normal serving already used CUDA graphs.
[NVIDIA CUDA Graph explanation](https://developer.nvidia.com/blog/cuda-graphs/).

Automatic clocks and short trials also leave sustained thermal/power behavior
unresolved. Temperature alone does not establish throttling. Future comparisons
need matched operating conditions and recorded clocks/power, with short-run
and sustained results reported separately.

### Peak instruction throughput is distinct from complete GEMM throughput

The nvfp4bench author reports approximately **511 dense TFLOPS** and
**1,014–1,022 sparse TFLOPS** using register-resident matrix instructions that
largely remove operand-memory traffic. That demonstrates a route to exercising
the arithmetic units near the headline reference, not a full GEMM at that rate.
Its sparse figure represents dense-equivalent work, including skipped zeros.
[Original methodology and observations](https://forums.developer.nvidia.com/t/gb10-really-does-hit-1-pflop-nvfp4-2-4-sparse-measured-with-an-open-source-tool-to-reproduce-it/373618).

Our primary objective is more useful work per second. Report these separately:

| Quantity | Meaning | Limitation |
| --- | --- | --- |
| Useful GEMM TFLOPS | `2MNK / elapsed_seconds / 1e12` | Keep shape, output dtype and timing scope matched |
| Executed hardware TFLOPS | Supported operation counter divided by its matching time interval | Can include padded or discarded work; counters cover specific arithmetic paths |
| SGLang estimated TFLOPS | Engine-modeled FLOP-counter delta per second | Not complete GPU instruction accounting or hardware utilization |
| Accepted output tokens/s | Client-visible serving throughput | Compare at matched workload, latency and quality |

Our FP8 calibration already illustrated the distinction: padded tile execution
increased hardware-counted operations above useful `2MNK`. Similarly, more
speculative drafting or rejected verification can raise executed work without
raising accepted-token throughput.

Structured sparsity is a separate model optimization. Using the sparse peak
requires eligible sparse operands and compatible kernels. Pruning a dense
model requires accuracy validation and potentially retraining; it is not a
drop-in speed setting for this checkpoint.
[NVIDIA structured-sparsity workflow](https://developer.nvidia.com/blog/?p=34218).

## NVIDIA CUDA Rust: relevant findings

NVIDIA's **8 September 2026** announcement introduces two native Rust kernel
projects. Rust is therefore an option for authoring GPU computation itself,
as well as managing existing CUDA kernels from the CPU.
[NVIDIA announcement](https://developer.nvidia.com/blog/introducing-cuda-rust-two-tracks-for-writing-gpu-kernels/).

| Project | Programming model | Relevance and current limitations |
| --- | --- | --- |
| `cuda-oxide` | Per-thread SIMT Rust compiled to PTX, with explicit memory/thread control | Potential custom-kernel route; early alpha, pinned nightly compiler, and incomplete low-precision feature coverage |
| `cutile-rs` | Rust tile operations compiled through CUDA Tile IR | Concrete NVFP4 candidate; stable Rust 1.89+, with FP4 operations requiring Tile IR 13.3 or newer |

The current [cuda-oxide feature matrix](https://nvlabs.github.io/cuda-oxide/appendix/supported-features.html)
marks FP8/FP6/FP4 support partial. Its datacenter Blackwell examples alone do
not establish a tuned GB10 NVFP4 path. NVIDIA recommends starting with Tile
when explicit SIMT control is unnecessary and describes both projects as
early-stage rather than production-ready.

cuTile Rust documents packed FP4 storage, FP8 block scales and `mmaf_scaled`.
Its example uses one scale per 16 values and FP32 accumulation/output. Our
baseline uses BF16 output, so directly comparing the example unchanged would
change the output traffic. Input scale layouts and global scaling must also
be matched; FlashInfer's 128×4 swizzled scale buffers are not automatically
interchangeable with the tutorial's logical scale tensors.
[NVFP4 tutorial and example](https://nvlabs.github.io/cutile-rs/main/tutorials/11-nvfp4-inference.html).

The [compatibility matrix](https://nvlabs.github.io/cutile-rs/main/reference/compatibility.html)
includes `sm_121` and requires Tile IR 13.3+ for FP4/block-scaled operations.
Our CUDA 13.0 calibration environment therefore cannot be reused unchanged for
that route. Select a compatible compiler, assembler and driver combination;
the toolkit requirement alone does not prove a host driver upgrade is needed.

The project also publishes a
[DGX Spark inference tutorial](https://nvlabs.github.io/cutile-rs/main/tutorials/12-dgx-spark-inference.html)
with measurements using CUDA 13.4 and a 580-series driver. Those results concern
16-bit Qwen3 models, not our Qwen3.8 NVFP4 configuration or matched GEMM shapes.
They establish practical Rust-kernel execution on Spark, not a speedup over
323 TFLOPS. Grout is a research reference here; supported repository serving
engines remain SGLang and vLLM.

**Assessment:** include cuTile Rust as an experimental kernel candidate alongside
existing CUDA implementations. Choosing Rust does not by itself increase Tensor
Core throughput. Any gain must come from a better generated kernel, reduced
memory traffic, fusion or lower measured host overhead.

## Open gaps

| Gap | Evidence currently available | What remains unknown |
| --- | --- | --- |
| Exact-shape dense GEMM ceiling | 323.46 TFLOPS at 4096³; differently shaped community results | Best validated kernel/backend for our shapes and environment |
| Kernel versus caller overhead | CUDA-event timing of repeated Python calls | Fraction recoverable with reusable output and graph replay |
| Sustained compute rate | Three short trials with automatic clocks | Stable rate over longer operation and contribution of clock/power changes |
| Physical memory bandwidth | Streaming references and calibrated L2/system-memory proxies | Whole-controller bytes and whole-serving-window LPDDR utilization |
| Full inference work attribution | Selected kernels and separate activity timelines | Complete prefill/draft/verify/state-copy time and arithmetic accounting |
| Rust NVFP4 performance on GB10 | Native-operation documentation and separate Spark inference examples | Correctness, generated instructions and matched throughput for our GEMM |
| Endpoint benefit | C1/C8/C64 baseline with client and engine metrics | Whether a kernel improvement increases accepted-token throughput |

The installed profiling tools exposed no usable physical DRAM-byte counter path.
L2 read fills and write requests can be affected by caching and coalescing; their
sum must not be divided by 273 GB/s to claim physical bandwidth utilization.
Likewise, SGLang's C64 estimate of 45.53 TFLOPS does not establish 9.1% hardware
utilization or an elevenfold serving optimization opportunity.

## Proposed next steps, not executed

The ordering below prioritizes explaining the existing result before adding
another compiler environment. A failed or inconclusive stage should retain its
evidence rather than silently changing the comparison.

| Order | Proposed work | Evidence needed to advance |
| --- | --- | --- |
| 1 | Reproduce the current baseline and separate kernel time from caller overhead | Same quantized inputs and three shapes; eager versus reusable-output versus graph variants changed separately; repeated results with clocks and temperatures |
| 2 | Tune CUTLASS and compare supported cuDNN candidates; include explicit `b12x` where supported | Correct outputs and a reproducible improvement at matched shape, dtype, cache policy and timing scope; save selected tactics |
| 3 | Profile the best current implementation to identify the remaining cost | Bounded kernel evidence for arithmetic, data movement, stalls and launch gaps; separate unprofiled performance from profiler timing |
| 4 | Evaluate cuTile Rust NVFP4 in a separate pinned container | Correct handling of packed values, block/global scales and BF16 output; native GB10 FP4 instruction/counter evidence; matched comparison to the tuned baseline |
| 5 | If a useful improvement exists, assess integration into the existing SGLang pack and repeat endpoint measurements | Accepted-token throughput and latency improve under the existing protocol, without a correctness/quality regression |

For stage 4, compare the established kernel again in the newer CUDA environment
as well. Otherwise a toolkit improvement can be misattributed to Rust. Inspect
format conversion or repacking costs and report them separately; do not hide a
required per-request conversion outside an end-to-end timing claim. A full Rust
serving-engine rewrite is not required to investigate a Rust kernel.

### Measurement and validation requirements

- For GEMM comparisons, retain M=64/512/4096 with N=K=4096, the same quantized
  operands and scales, FP32 accumulation and BF16 output. Keep quantization
  outside the GEMM timing as in the baseline; report quantize-plus-GEMM separately
  if relevant to serving. Different shapes are additional results, not replacements.
- Validate candidate arithmetic against a reference using the same quantized
  values. Distinguish kernel correctness from quantization error relative to the
  original BF16 inputs. An all-ones example alone is insufficient qualification.
- Pin source commits, images, compiler/library versions and kernel selections.
  Document warmup, repetitions, cache state and thermal conditions before running.
  Separate tuning/compilation time, short-run throughput and sustained throughput.
- Preserve useful FLOPs, supported executed-operation counters, timing boundaries,
  clock/power/temperature samples and profiler replay details. Unsupported metrics
  stay explicitly unavailable. Keep register-resident instruction tests separate
  from complete GEMM and serving results.
- Resolve physical-bandwidth claims only with a supported GB10 counter method
  validated against known-byte workloads. Until then retain qualified proxies
  and avoid a numerical whole-system bandwidth-utilization claim.

Any endpoint follow-up must follow [the shared benchmarking rules](../../../../BENCHMARKING.md)
and preserve the requested **concurrency 1, 8 and 64 only**:

| Client concurrency | Measured requests per trial, `max(64, 3C)` | Exploratory trials | Total measured requests |
| ---: | ---: | ---: | ---: |
| 1 | 64 | 3 | 192 |
| 8 | 64 | 3 | 192 |
| 64 | 192 | 3 | 576 |

That is **960 measured requests per configuration**, plus separately excluded
warmup. Three-times-concurrency comes from NVIDIA's worked method; the 64-request
floor is the repository's choice. Retain MTP=2, the model/tokenizer revision,
input/output lengths, sampling, admission/state/KV settings and verified fresh
cache conditions for a matched comparison. Disclose any required configuration
changes instead of attributing the entire difference to the kernel.

Save AIPerf aggregates and per-request exports, timestamped SGLang metrics
(including estimated FLOPs, queueing, cache and speculative acceptance), and
available GPU telemetry in a fresh external artifact directory under
`/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/`.
Keep raw metrics and profiler binaries outside Git. Retain runners and validators,
record actual attempts and failures in new append-only experiment entries, and
stop the services owned by the experiment when the round finishes.
