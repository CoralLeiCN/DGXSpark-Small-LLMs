# 2026-09-27T16:05:09Z — Full-range warmup OOM; bound hardware capture to selected kernels

Run ID: `RUN-0046`

- Status: open
- Phase: inference warmup / profiling
- Related turn: [KV-cap attempt, RUN-0045](2026-09-27T15-54-02Z-hardware-pilot-fixed-mamba-budget-kv-cap.md)
- Repo: `f3f1d2e`, dirty; GB10 SM12.1, driver580.173.02, CUDA13.0.
- Image: `sha256:7c694cc214888ed37c1eba40e3be4d8e82c6516faeaf4ccb23d0833369169b92`; SGLang `0.0.0.dev1+g5f55db35e`, FlashInfer0.6.17, AIPerf0.12.0, Nsight Compute2025.3.1.0.
- Model: `nvidia/Qwen3.8-27B-NVFP4`, revision `482ca0f3832238542f8f5295dde86b5f22711d80`, MTP2/top-k1/3 verification positions.

The exact failed command is archived in `profiles/ncu-fp4-v7/container-id.log.command.txt`; the driver was:

```bash
uv run --offline --no-project --python 3.12 scripts/profiles-v7.py ARTIFACT_ROOT ncu-fp4
```

The 65,536-token KV cap passed readiness at15:58:49UTC with admission64, Mamba256 and static fraction0.90. The first c1 warmup then failed:

```text
Triton kernel ... device-loaded after serving started (free device mem: 0.38 GiB)
Subprocess scheduler_0 (pid=123) crashed with exit code -9.
```

Docker recorded `OOMKilled=true`, exit9 at15:59:09UTC. The client failed and the orchestrator stopped; no completed application-range inference data exists. This establishes that reducing KV storage alone did not supply enough headroom for this profiler mode. The exact allocation responsible for the excess was not isolated. Health200 was insufficient qualification: actual inference must succeed too.

The recovery uses `profiles-v8.py` / `orchestrate-v9.py`, preserving all preceding attempts. It retains the diagnostic KV cap, admission, MTP and state settings, but uses kernel replay with node-level graph profiling, `--profile-from-start off`, and the already calibrated single-pass FP4/time/system-memory proxy counter set. It filters actual NVFP4 CUTLASS GEMMs and `_fused_mamba_state_scatter_with_mask_kernel` observed in the completed Systems traces. `--filter-mode per-launch-config --launch-count 1` limits collection to the first matching launch for each distinct launch configuration across the session. Forward annotations establish observed phase and batch; CUDA graphs remain enabled.

This deliberately narrows scope: selected kernel samples cannot establish whole-step TFLOPS, whole-server MFU, or physical DRAM utilization. Filters persist across captures; a phase with no new shape has missing counter coverage, not zero work. Six prefill/decode capture opportunities at c1/c8/c64 retain their own logs and actual shapes. These single diagnostic samples are a declared exception to normal performance-trial counts and will not supply client latency comparisons.

The recovery also runs the prepared known-work FP8 calibration before serving. It does not claim FP8 inference coverage. A two-hour systemd runtime bound and `ExecStopPost` cleanup protect shutdown. The normal nine-trial benchmark and three successful Systems traces remain valid. Verification of this recovery is pending in a later turn.

Artifacts: [external pilot archive](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T13-56-21Z-mtp2-hardware-pilot/).
