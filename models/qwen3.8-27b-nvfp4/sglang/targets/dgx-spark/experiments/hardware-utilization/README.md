# DGX Spark hardware-utilization experiment scripts

The [2026-09-27 scripts](2026-09-27/) preserve the MTP=2 hardware-utilization
pilot's runners, qualification, validation, calibration and analysis code.
The user requested that these scripts be retained in the repository. Keep
successful and failed execution versions with their provenance; preserve raw
metrics, inputs, logs and profiler binaries in the external experiment archive.

Archive:
[`2026-09-27T13-56-21Z-mtp2-hardware-pilot`](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T13-56-21Z-mtp2-hardware-pilot/).
The archive's `status.json`, per-attempt status files and journal entries record
actual progress and results. Script presence alone does not establish completion.

## Execution and validation

| Script | Role |
| --- | --- |
| `baseline.py` | First attempt, retained with its rejected explicit-zero warmup option. |
| `baseline-v2.py` | Second attempt; completed c1 trial1, then rejected a missing lazy cache-counter series. |
| `baseline-v3.py` | Retains that successful trial, validates cache reuse from paired prompt histograms, and runs the remaining eight trials. |
| `smoke.py` | Five API checks and effective admission/speculation qualification. |
| `orchestrate.py` through `orchestrate-v9.py` | Original and resumed sequencing of baseline completion, profiling, 30-minute status records and shutdown. |
| `profiles.py` through `profiles-v8.py` | Preserved attempts. v3 completed Systems captures; v5–v7 application-range attempts failed under memory pressure. v8 selects bounded kernel samples with actual shape checks, telemetry and cleanup. |
| `Dockerfile.profiling-v2` through `-v6`, `enable-forward-nvtx.py`, `log-forward-shapes.py` | Preserved build attempts, pinned NVTX0.2.16, forward annotations and diagnostic-only shape logging. |
| `bandwidth.cu`, `calibrate-bandwidth.sh` | Known-byte read/write/copy calibration and profiler collection. |
| `fp4.py`, `calibrate-fp4.sh` | Dense NVFP4 GEMMs, numerical checks, timing and operation-counter validation. |
| `fp8.py`, `calibrate-fp8.sh` | Dense FP8 GEMMs and corresponding counter validation. |
| `calibrate-app-range.sh` through `calibrate-app-range-v3.sh` | Preserved CLI qualifications and successful known-work application-range counter calibration. |
| `extract-ncu.py` | Offline extraction of native-unit counters and NVTX provenance from a saved `.ncu-rep`. |
| `analyze-baseline.py` | Revalidates the nine normal trials from saved exports and produces per-trial CSV, aggregate JSON and a Markdown table. |
| `analyze-calibration.py`, `analyze-calibration-v2.py` | Original logical-operation assertion exposed FP8 tile padding; v2 validates the observed padded count explicitly and summarizes known-byte and GEMM calibrations. |
| `export-nsys.py`, `analyze-nsys.py` | Validate/export the three Systems reports and summarize GPU activity with CUDA graph coverage and overlap-aware timing. |
| `analyze-timeline-kernels.py` | Quantifies visible Mamba state-scatter time without claiming visibility into all CUDA graph nodes. |
| `analyze-selected-kernels.py`, `analyze-selected-kernels-v2.py` | Original prepared mapping and corrected per-stream/log mapping for selected hardware counters; retains missing coverage explicitly. |
| `record-shutdown.py`, `validate-pilot.py` | Records live container/unit/GPU/endpoint state; independently validates saved completion evidence and source hashes. |
| `inspect_image.py`, `inspect_fp4.py` | Source/API inspection in the pinned serving image. |

Normal measurements use concurrency **1, 8, 64**, three trials, and respectively
**64, 64, 192 requests per trial**: **960 measured requests**. Warmup and diagnostic
captures have separate outputs. Before each measured trial, the idle server's
cache is flushed. Total-prompt and uncached-prompt histogram sum deltas must match,
and both histogram count deltas must equal the completed request count. Validators
also check request errors/counts, expected MTP settings, actual GPU/server exports,
monotonic estimated-FLOPs counters and consistent input hashes.

Follow the repository's [benchmarking policy](../../../../../../../docs/BENCHMARKING.md)
and [experiment journal](../../../../../../../docs/experiments/qwen3.8-27b-nvfp4/sglang/dgx-spark/README.md).
The archive's exact launch commands include systemd `ExecStopPost` cleanup.

## Reproduction scope

These snapshots contain the exact experiment-specific image/model revisions,
container and systemd names, artifact layout and cache-volume reference.
`baseline-v3.py` expects the retained `baseline-v2/c1/trial1` artifacts;
`orchestrate-v2.py` waits for the v3 baseline. Existing containers/output directories
are deliberately rejected. A new round needs distinct names and an explicitly
declared recovery or fresh-run plan before launch.

Use `uv` with Python3.12 for the Python drivers. AIPerf0.12.0 runs in its isolated
uv tool environment; serving, Torch and FlashInfer dependencies remain inside the
pinned model container. Nsight binaries are mounted read-only. Nsight Systems
counter access worked with `PERFMON`; the installed Nsight Compute required
`SYS_ADMIN` on its temporary profiling container. Host profiling policy was
unchanged. Hardware profiles and calibration timings remain separate from normal
client performance measurements. The bounded Compute recovery caps diagnostic
KV capacity at65,536tokens while preserving admission64, Mamba256 and static
fraction0.90. Kernel samples are not complete scheduler steps or hardware MFU.
L2/system-memory byte proxies are not physical LPDDR-controller traffic.

For offline extraction, for example:

```bash
uv run --offline --no-project --python 3.12 \
  models/qwen3.8-27b-nvfp4/sglang/targets/dgx-spark/experiments/hardware-utilization/2026-09-27/extract-ncu.py \
  /absolute/path/to/capture.ncu-rep /absolute/path/to/counters.json
```

`source-manifest.json` records the archived script paths and SHA-256 hashes.
The script extractor labels Tensor Core operation coverage and L2/system-memory
traffic explicitly; its byte proxy is not a physical DRAM-controller measurement.

The final offline evidence check can be repeated without restarting services:

```bash
uv run --offline --no-project --python 3.12 \
  2026-09-27/validate-pilot.py ARTIFACT_ROOT \
  2026-09-27/source-manifest.json NEW_VALIDATION_OUTPUT.json
```

Run from this directory and replace `ARTIFACT_ROOT` with the archive above.
The output must be a new file. `record-shutdown.py` is the separate live check;
`validate-pilot.py` validates the timestamped shutdown observation already saved.
The archive also contains the script snapshots and manifest for use independently
of this worktree. The final report records the unavailable physical-DRAM and
whole-server hardware-utilization measurements.
