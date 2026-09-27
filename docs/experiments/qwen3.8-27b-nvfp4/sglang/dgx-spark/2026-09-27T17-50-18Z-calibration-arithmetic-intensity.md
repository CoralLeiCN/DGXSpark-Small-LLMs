# 2026-09-27T17:50:18Z — Calibration table with arithmetic intensity

Run ID: `RUN-0048`

- Status: resolved
- Phase: report analysis; no new GPU experiment
- Related report: [hardware-utilization pilot, RUN-0047](2026-09-27T16-23-13Z-hardware-utilization-final-report.md)

This is the updated **Hardware limits and local calibration** table requested by
the user. Performance values come from RUN-0047; arithmetic intensity is calculated
from the calibration's data formats and matrix dimensions. This follow-up preserves
the append-only experiment journal.

## Hardware limits and local calibration

NVIDIA specifies **273 GB/s LPDDR5x bandwidth** and **up to 1 PFLOP/s FP4 with sparsity** for Spark. The serving kernels here use dense block-scaled FP4. An approximate **500 dense FP4 TFLOPS** reference is inferred by dividing the advertised sparse figure by the usual 2× structured-sparsity factor; it is not an independently published, measured dense Spark guarantee. [Spark hardware specifications](https://docs.nvidia.com/dgx/dgx-spark/hardware.html), [NVIDIA's explanation of the sparse/dense factor](https://developer.nvidia.com/blog/structured-sparsity-in-the-nvidia-ampere-architecture-and-applications-in-search-engines/).

| Unprofiled calibration | Mean ± sample SD | Observed range | Ideal arithmetic intensity (FLOP/byte) | Comparison |
| --- | ---: | ---: | ---: | --- |
| Streaming read | 229.14 ± 1.55 GB/s | 227.35–230.16 GB/s | ≈0.25 | 83.9% of 273 GB/s using logical streaming bytes |
| Streaming write | 195.39 ± 2.23 GB/s | 193.61–197.89 GB/s | 0 | 71.6% of 273 GB/s using logical streaming bytes |
| Streaming copy, read+write | 209.53 ± 0.63 GB/s | 208.81–209.90 GB/s | 0 | 76.8% of 273 GB/s using logical read+write bytes |
| Dense NVFP4 GEMM, M=64/N=4096/K=4096 | 46.15 ± 2.43 TFLOPS | 43.36–47.85 TFLOPS | 212.43 | 9.2% of inferred 500 TFLOPS |
| Dense NVFP4 GEMM, M=512/N=4096/K=4096 | 299.76 ± 16.39 TFLOPS | 281.46–313.08 TFLOPS | 1,159.93 | 60.0% of inferred 500 TFLOPS |
| Dense NVFP4 GEMM, M=4096/N=4096/K=4096 | 323.46 ± 3.53 TFLOPS | 319.59–326.52 TFLOPS | 2,621.44 | 64.7% of inferred 500 TFLOPS |
| Dense FP8 GEMM, M=4096/N=4096/K=4096 | 179.66 ± 1.59 TFLOPS | 177.83–180.62 TFLOPS | 2,048.00 | Separate precision; do not divide by the FP4 limit |

Arithmetic intensity is useful floating-point operations divided by ideal logical
input/output bytes. For GEMMs, count a multiply-add as two FLOPs, read each input
once, and write the BF16 output once, without reading an existing output matrix.
Quantization is outside the timed GEMM, matching the calibration scripts.

- **NVFP4:** `I = 2MNK / [0.5625(MK + KN) + 2MN]`. Each input element uses
  half a byte plus one byte of block scale per 16 elements. See
  [NVIDIA's NVFP4 format description](https://developer.nvidia.com/blog/introducing-nvfp4-for-efficient-and-accurate-low-precision-inference/).
- **FP8:** `I = 2MNK / [MK + KN + 2MN]`. This calibration uses one-byte
  inputs with per-tensor scales, rather than NVFP4's per-block scales.
- The few bytes of global scales, alignment padding, intermediate traffic and
  repeated loads are excluded. In particular, the NVFP4 M=64 scale buffer uses
  128-row alignment: counting its extra allocated scale bytes would give
  **212.09**, rather than **212.43 FLOP/byte**. Allocated padding is not necessarily
  transferred, so the table consistently uses logical bytes.
- Streaming read performs approximately one float addition per four bytes,
  plus small warp-reduction overhead. Write and copy perform no floating-point
  arithmetic; integer address calculations are not FLOPs.

For the **4096³ NVFP4 GEMM**, the calculation is **137,438,953,472 FLOPs /
52,428,800 bytes = 2,621.44 FLOP/byte**: 9 MiB for each scaled input and 32 MiB
for the BF16 output.

Spark's corresponding **hardware balance**, or roofline transition, is approximately
**1,831.50 FLOP/byte** using the inferred dense FP4 reference
`500e12 / 273e9`. Using the advertised sparse FP4 figure gives **3,663.00 FLOP/byte**;
that sparse reference is not applicable to these dense GEMMs. These are hardware
compute-to-bandwidth ratios, distinct from the workload intensities in the table.

The 4096³ NVFP4 GEMM is above the dense transition in this ideal roofline model.
The intensity column is not measured DRAM traffic and does not establish the
actual kernel bottleneck: cache reuse, repeated tile loads and other overhead
change the effective ratio. The original report's physical-bandwidth limitations
continue to apply.

Each calibration has three short trials. Memory arrays are 512 MiB, larger than the 24 MiB L2 cache. GEMM quantization occurs outside the timed multiplication, and numerical checks compare to FP32 reference products from the BF16 source inputs. Clocks were automatic and these were not thermal soaks. Treat the results as pattern-specific local references, not universal sustained ceilings. The logical bandwidth formula follows [NVIDIA's effective-bandwidth definition](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html#bandwidth).


Validation: the densities were recalculated with Python 3.12 via `uv`; all seven
performance rows were checked against RUN-0047. No services were started and no
new performance measurements were taken.
