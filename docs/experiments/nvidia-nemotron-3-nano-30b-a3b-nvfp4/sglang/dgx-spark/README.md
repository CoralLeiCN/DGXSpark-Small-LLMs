# NVIDIA Nemotron 3 Nano 30B A3B NVFP4 — SGLang — DGX Spark Experiment Journal

Deployment recipe:
[`models/nvidia-nemotron-3-nano-30b-a3b-nvfp4/sglang/targets/dgx-spark/`](../../../../../models/nvidia-nemotron-3-nano-30b-a3b-nvfp4/sglang/targets/dgx-spark/)

Follow the [journal guide](../../../README.md). Each row links to one immutable
experiment turn; later turns link back to the observations they continue.

Resolved issues: [implemented fixes and established workarounds](../../../../RESOLVED_ISSUES.md).

Runs recorded: 3

Next run ID: `RUN-0012`

| Run ID | Time (UTC) | Status | Outcome |
| --- | --- | --- | --- |
| `RUN-0003` | 2026-09-03T21:16:19Z | open | [Health probe ran before JIT startup was ready](2026-09-03T21-16-19Z-health-before-readiness.md) |
| `RUN-0006` | 2026-09-03T21:54:10Z | resolved | [Four-worker JIT completed and the service became healthy](2026-09-03T21-54-10Z-service-ready.md) |
| `RUN-0007` | 2026-09-03T21:55:31Z | resolved | [First-request detokenizer heartbeat timed out transiently](2026-09-03T21-55-31Z-detokenizer-heartbeat.md) |
