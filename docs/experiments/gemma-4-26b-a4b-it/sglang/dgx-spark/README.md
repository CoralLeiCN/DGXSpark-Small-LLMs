# Gemma 4 26B A4B IT — SGLang — DGX Spark Experiment Journal

Deployment recipe:
[`models/gemma-4-26b-a4b-it/sglang/targets/dgx-spark/`](../../../../../models/gemma-4-26b-a4b-it/sglang/targets/dgx-spark/)

Follow the [journal guide](../../../README.md). Each row links to one immutable
experiment turn; later turns link back to the observations they continue.

Runs recorded: 11

Next run ID: `RUN-0012`

| Run ID | Time (UTC) | Status | Outcome |
| --- | --- | --- | --- |
| `RUN-0001` | 2026-09-05T21:22:01Z | resolved | [Official runtime image restored GPU preflight semantics](2026-09-05T21-22-01Z-official-runtime-preflight.md) |
| `RUN-0002` | 2026-09-05T21:22:36Z | resolved | [Gemma text API qualified on DGX Spark](2026-09-05T21-22-36Z-text-api-qualified.md) |
| `RUN-0003` | 2026-09-05T21:23:15Z | workaround | [Service removed despite shutdown cleanup traceback](2026-09-05T21-23-15Z-shutdown-cleanup-traceback.md) |
| `RUN-0004` | 2026-09-09T22:08:47Z | resolved | [Monitoring host preflight requires host access](2026-09-09T22-08-47Z-monitoring-host-preflight.md) |
| `RUN-0005` | 2026-09-09T22:09:18Z | resolved | [Status inspection requires host access](2026-09-09T22-09-18Z-status-inspection-host-access.md) |
| `RUN-0006` | 2026-09-09T22:13:51Z | resolved | [Health connection refused during model initialization](2026-09-09T22-13-51Z-health-before-model-ready.md) |
| `RUN-0007` | 2026-09-09T22:17:09Z | open | [One latency panel has no matching metric](2026-09-09T22-17-09Z-monitoring-latency-metric-mismatch.md) |
| `RUN-0008` | 2026-09-09T22:19:44Z | resolved | [Shared monitoring qualified; all ten panels passed](2026-09-09T22-19-44Z-shared-monitoring-qualified.md) |
| `RUN-0009` | 2026-09-09T22:24:22Z | resolved | [Grafana remote access narrowed to Tailscale](2026-09-09T22-24-22Z-grafana-tailnet-access.md) |
| `RUN-0010` | 2026-09-09T23:13:53Z | open | [Mixed stream modes expose dashboard aggregation gap](2026-09-09T23-13-53Z-mixed-stream-monitoring.md) |
| `RUN-0011` | 2026-09-09T23:17:37Z | resolved | [Monitoring PR tests pass with mixed stream modes](2026-09-09T23-17-37Z-monitoring-pr-validation.md) |
