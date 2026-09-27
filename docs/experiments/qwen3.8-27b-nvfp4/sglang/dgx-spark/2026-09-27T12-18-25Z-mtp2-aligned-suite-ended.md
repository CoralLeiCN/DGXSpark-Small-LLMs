# 2026-09-27T12:18:25Z — NVFP4 aligned MTP=2 sweep ended and shutdown was checked

Run ID: `RUN-0031`

- Status: resolved
- Phase: inference / benchmark / lifecycle
- Repo revision: `89611e1`, dirty with experiment documentation
- Host/GPU: DGX Spark, NVIDIA GB10, driver `580.173.02`, aarch64
- Image: `sha256:110ad45e7872397f337ea5714e6c97c400852938a9b8f258bcc27cab07182b0c`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`; AIPerf `0.12.0`, Python 3.12
- Model: `nvidia/Qwen3.8-27B-NVFP4`, revision `482ca0f3832238542f8f5295dde86b5f22711d80`
- Artifacts: [2026-09-27T10-59-11Z-mtp2-aligned](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T10-59-11Z-mtp2-aligned/)
- Related turns: [MTP=2 launch](2026-09-25T20-24-59Z-mtp2-c72-round.md); see this target index for the MTP=1/3 launch and subsequent events.

## Observed result

```json
{
  "outcomes": [
    {
      "mtp": 2,
      "status": "completed"
    }
  ],
  "all_stopped": true
}
```

## Verification and lesson

See `shutdown-verification.json` for final Docker states and per-variant logs for graceful shutdown. Only containers owned by this suite are stopped; all previous experiment services were stopped before launch. Preserve raw metrics and shutdown evidence together when running unattended experiments.
