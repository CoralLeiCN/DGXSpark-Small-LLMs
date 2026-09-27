# 2026-09-27T11:07:37Z — NVFP4 aligned MTP=2: startup, telemetry and initial inputs verified

Run ID: `RUN-0029`

- Status: resolved
- Phase: inference / benchmark / lifecycle
- Repo revision: `89611e1`, dirty with experiment documentation
- Host/GPU: DGX Spark, NVIDIA GB10, driver `580.173.02`, aarch64
- Image: `sha256:110ad45e7872397f337ea5714e6c97c400852938a9b8f258bcc27cab07182b0c`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`; AIPerf `0.12.0`, Python 3.12
- Model: `nvidia/Qwen3.8-27B-NVFP4`, revision `482ca0f3832238542f8f5295dde86b5f22711d80`
- Artifacts: [2026-09-27T10-59-11Z-mtp2-aligned](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T10-59-11Z-mtp2-aligned/)
- Related turns: [MTP=2 launch](2026-09-25T20-24-59Z-mtp2-c72-round.md); see this target index for the MTP=1/3 launch and subsequent events.

## Observed qualification

The new server completed startup and all five API checks. Effective admission is64,
MTP drafting steps2, verification positions3, persistent Mamba slots256, static
fraction0.90, float32 Mamba state, FP8 e4m3 KV, and the declared pinned revision.
The saved server-info reports target KV capacity395,653 tokens, weight memory20.578,
KV memory12.074 and startup available memory9.887 in engine-reported units. This
capacity differs from MTP=1/3 and remains part of the deployment comparison.

All three c4 telemetry trials completed eight measured requests with no recorded
client errors/cancellation. GPU utilization, SM utilization, temperature, power,
energy, and advancing SGLang estimated FLOPs were saved. Separate per-trial measured
windows and counter endpoints are in `mtp2/telemetry-preflight/verified-summary.json`.
First/second short preflight cache fractions are unavailable due to missing counter
endpoints; third is97.71%. Missing counters are not zero, and these qualification
numbers are not full-sweep results. The preflight populates the counters before c1.

The full c1 sweep started at2026-09-27T11:05:54Z. Its first generated-input artifact
has the same canonical SHA256 as the corresponding historical MTP=1 and MTP=3
artifacts; `initial-input-verification.json` saves the comparison. Every subsequent
completed trial checks the same correspondence. A fresh monitor observation confirms
the driver is active and the owned container is running. Completion is not yet claimed.

## Inspection correction and existing warnings

A read-only diagnostic initially accessed `server_info['server_args']` and raised
`KeyError: 'server_args'`. Inspecting the saved response confirmed the argument fields
are top-level; the corrected read verified the settings above. This did not interrupt
the driver or inference. Inspect the pinned API schema before assuming nested fields.
The log retains optional torchcodec import warnings and FP8 KV fallback-scale warnings
seen in earlier rounds. A readiness503 during startup resolved before API qualification.

## Lifecycle and interpretation

The 30-minute local monitor is active; the first timer observation is due at11:31:08Z.
The driver and independent ExecStopPost stop only this round's container and logging
service on completion/error, verify shutdown, and run a final monitor check to stop
its timer. All raw data and later lifecycle outcomes remain in the external archive.
The first/repeat-pass procedure reproduces MTP=1/3; per-trial cache reuse must accompany
results. Descriptive pooled means do not establish stable-performance confidence.
