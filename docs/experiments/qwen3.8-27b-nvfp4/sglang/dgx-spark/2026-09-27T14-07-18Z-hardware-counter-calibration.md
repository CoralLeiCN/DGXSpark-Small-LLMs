# 2026-09-27T14:07:18Z — Hardware counter access and GB10 calibration

Run ID: `RUN-0034`

- Status: resolved
- Repo: `f3f1d2e`, dirty with experiment documentation
- Host: DGX Spark / GB10 SM12.1 (gb20b), driver580.173.02
- Runtime: SGLang0.0.0.dev1+g5f55db35e, AIPerf0.12.0, Python3.12
- Image: `sha256:110ad45e7872397f337ea5714e6c97c400852938a9b8f258bcc27cab07182b0c`
- Model/native head/tokenizer revision: `482ca0f3832238542f8f5295dde86b5f22711d80`
- Tools: Nsight Compute2025.3.1 and Systems2025.3.2; CUDA13.0
- Artifacts: [2026-09-27T13-56-21Z-mtp2-hardware-pilot](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T13-56-21Z-mtp2-hardware-pilot/)

## Observations, failures and fixes

No running Docker containers were present before this experiment; GPU utilization
was0% at36C. The user authorized the profiling plan with c1,c8,c64 baseline only.
Raw calibration commands, sources, logs and reports are in the external archive.

`docker run --rm --gpus all --cap-add=PERFMON ... nsys profile --gpu-metrics-devices=help`
succeeded, resolving the earlier host permission limitation. The supported set is
gb20b. The captured report exports19 GPU metrics (clocks, activity, tensor pipeline,
warps), but no DRAM bandwidth counter. This is observed installed-tool coverage.

The first detailed calibration command was:

```text
docker run --rm --gpus all --cap-add=PERFMON ... ncu --kernel-name bw_copy --launch-skip 5 --launch-count 1 --cache-control none --clock-control none --metrics gpu__time_duration.sum,lts__d_sectors_fill_sysmem.sum,lts__t_sectors_aperture_sysmem_op_write.sum,sm__ops_path_tensor_src_fp4_dst_fp32.sum ...
ERR_NVGPUCTRPERM - The user does not have permission to access NVIDIA GPU Performance Counters
```

The same target collection with `--cap-add=SYS_ADMIN` succeeded in a temporary
container. Host profiling policy and drivers were unchanged. The exact complete
commands are `calibration/bandwidth.command.txt` and
`calibration/bandwidth-ncu-sysadmin.command.txt`. Nsight Compute and Systems had
different effective capability requirements in this installed stack.

A source-inspection shell also reported `/bin/bash: rg: command not found` inside
the image. The subsequent uv/Python file read succeeded; source snapshots and both
attempt logs remain in preflight/. This was a tooling failure, not inference.

## Calibration verification

The CUDA benchmark uses512MiB arrays, exceeding the24MiB L2. Read checksums and
write/copy endpoint checks passed. Three unprofiled trials measured read227.35–230.16,
write193.61–197.89 and copy208.81–209.90 decimalGB/s. These short, automatically
clocked samples are observed pattern-specific effective bandwidth references,
not proof of the maximum sustainable whole-system bandwidth. Profiled timing is
excluded. Do not interpret the slow replay wall time as ordinary bandwidth.

The captured copy's L2/system-memory sector counts, at32bytes/sector, match its
known512MiB input/output traffic within0.11%. This validates a GPU traffic proxy
for this pattern, not complete physical LPDDR traffic or CPU/SoC attribution.

Dense CUTLASS NVFP4 GEMMs used known dimensions and a BF16-reference slice check
(relative RMSE below0.25). Large4096-cubed unprofiled GEMMs measured319.59–326.52
effectiveTFLOPS. The hardware FP4 operation counter returned137438953472,
exactly2*4096^3. The combinedFP4/FP6 counter was0, so overlapping metric families
must not be blindly summed. Selected raw values/units are in calibration/validation.json.
This confirms executed-FP4 counting for this kernel; it does not establish complete
FLOP coverage of a mixed-precision serving workload.

## Lesson and next step

Validate access, units and known-work counts before inferring utilization. Use
scoped profiling containers and retain explicit metric coverage. The normal c1,c8,c64
baseline follows; diagnostics stay separate and all owned services stop afterward.
