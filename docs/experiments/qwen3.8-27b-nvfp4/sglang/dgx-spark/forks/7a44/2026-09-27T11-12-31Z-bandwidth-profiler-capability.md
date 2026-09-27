# 2026-09-27T11:12:31Z — GB10 bandwidth profiling: installed capabilities and access limits

Run ID: `RUN-0030`

- Status: open
- Phase: offline profiler capability inspection; no profiling collection or inference launched
- Repo revision: `89611e1`, dirty with documentation
- Host/GPU: DGX Spark, GB10, driver580.173.02, aarch64
- Tools: Nsight Compute2025.3.1.0; Nsight Systems2025.3.2.474
- Related turn: [FLOPs/bandwidth audit](2026-09-27T11-02-08Z-flops-bandwidth-accounting.md)

## Observation

The user requested possible methods and their limitations. The existing aligned
MTP=2 run remained healthy and in c1 at the initial read-only status check. No
profiler was attached, no driver policy changed, and no additional load generated.

```bash
ncu --version
nsys --version
nsys profile --gpu-metrics-devices=help
nsys profile --gpu-metrics-devices=all --gpu-metrics-set=help
sudo -n /usr/local/cuda/bin/nsys profile --gpu-metrics-devices=help
sudo -n /usr/local/cuda/bin/nsys profile --gpu-metrics-devices=all --gpu-metrics-set=help
ncu --query-metrics --chip gb20b
```

```text
Blackwell GB20B | NVIDIA GB10 PCI[000f:01:00.0] - Insufficient privilege,
see https://developer.nvidia.com/ERR_NVGPUCTRPERM
sudo: a password is required
```

An offline targeted metric query identified `dram__bytes_read`,
`dram__bytes_write`, and `dram__throughput` as invalid or without suffixes.
The full gb20b catalogue in the installed Nsight Compute version has no dram__
or dramc__ entries. It does expose L2/system-memory metrics, including
`lts__d_sectors_fill_sysmem` and `lts__t_bytes`. Catalogue availability is not
proof that runtime collection works or that a counter measures physical LPDDR
traffic. L2 requests/fills must not silently substitute for DRAM-controller bytes.

Nsight Compute also warned that the sandbox could not deploy its default section
files under Documents, then successfully used its installed stock sections.
No HOME override or host configuration change was made.

## Diagnosis, attempted fix, and verification

The live Nsight Systems capability query was blocked by performance-counter
permissions. Its generic message lists no supported devices but explicitly gives
insufficient privilege as the reason; it does not establish unsupported hardware.
A noninteractive administrator retry required a password. No credentials were
requested, no global permissions relaxed, and no driver reload was attempted.
Offline catalogue inspection succeeded and established an additional version-specific
limitation: standard discrete-GPU DRAM metrics cannot simply be assumed on GB10.
Physical bandwidth remains unmeasured. Access and supported runtime metrics must
be established before a separate profiling experiment.

## Possible approaches and limitations

- Nsight Systems: single-pass timeline and supported GPU/SoC sampling to correlate
  memory activity with prefill, decode, draft and verify. Counters are device-level,
  short events can be averaged away, and throughput percentages have hardware-specific
  definitions. A displayed activity percentage is not automatically bytes/time.
- Nsight Compute: selected representative kernels/ranges, cache traffic, misses,
  stalls and compute pipelines. Detailed collection may replay kernels, serialize
  launches and alter hardware cache state; profiled latency must remain separate
  from the ordinary AIPerf results. Available counters vary by chip/version.
- Memory-controller/SoC PMU counters, if actually exposed: best direct route to
  shared LPDDR traffic. Availability and CPU/GPU attribution are unverified here.
  Unified memory means system activity can contribute; GPU traffic is not necessarily
  total memory-controller traffic.
- Large-buffer read/write/copy microbenchmarks: determine an attainable bandwidth
  reference under declared clocks, temperature and access pattern. They measure
  that workload, not inference bandwidth. Use buffers larger than cache, meaningful
  verified work, correct asynchronous timing, and explicit read+write accounting.
  Keep this load out of the running comparison.

Report actual memory-controller bytes divided by elapsed time only when those
bytes are measured. Separately report active-kernel and full-window averages;
do not sum percentages or double-count overlapping kernel time. Compare to both
273GB/s specification and a measured pattern-specific reference if available.
Neither low bandwidth nor unused bandwidth alone proves optimizable throughput:
latency/dependencies, cache hits, compute work, or launch/scheduler gaps can limit it.

Sources checked2026-09-27:
- [Nsight Systems GPU metrics](https://docs.nvidia.com/nsight-systems/UserGuide/index.html#gpu-metrics)
- [Nsight Compute profiling and replay](https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html)
- [NVIDIA counter access](https://developer.nvidia.com/ERR_NVGPUCTRPERM)
- [CUDA bandwidth definitions](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html#bandwidth)
- [DGX Spark UMA](https://docs.nvidia.com/dgx/dgx-spark-porting-guide/optimization.html#memory-reporting-on-uma-systems-including-dgx-spark)

Lesson: verify the target's counter catalogue and actual access before promising
hardware bandwidth utilization. A supported profiler product does not imply
that every familiar DRAM metric is available on a unified-memory GPU.
