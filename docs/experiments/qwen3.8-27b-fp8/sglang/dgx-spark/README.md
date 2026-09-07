# Qwen3.8 27B FP8 — SGLang — DGX Spark Experiment Journal

Deployment recipe:
[`models/qwen3.8-27b-fp8/sglang/targets/dgx-spark/`](../../../../../models/qwen3.8-27b-fp8/sglang/targets/dgx-spark/)

Follow the [journal guide](../../../README.md). Each row links to one immutable
experiment turn; later turns link back to the observations they continue.

Runs recorded: 5

Next run ID: `RUN-0006`

| Run ID | Time (UTC) | Status | Outcome |
| --- | --- | --- | --- |
| `RUN-0001` | 2026-09-04T00:19:32Z | open | [Cold download exceeded the health-check grace period](2026-09-04T00-19-32Z-cold-download-health-timeout.md) |
| `RUN-0002` | 2026-09-04T01:15:47Z | resolved | [Host API passed after retry outside the network sandbox](2026-09-04T01-15-47Z-host-api-validation.md) |
| `RUN-0003` | 2026-09-04T08:42:53Z | resolved | [API connection reset during warm-cache startup](2026-09-04T08-42-53Z-api-reset-during-startup.md) |
| `RUN-0004` | 2026-09-07T12:40:39Z | open | [Concurrent model startup distorts available cache budget](2026-09-07T12-40-39Z-concurrent-start-memory-profiling.md) |
| `RUN-0005` | 2026-09-07T12:47:42Z | resolved | [Sequential startup qualifies 45 percent allocation](2026-09-07T12-47-42Z-reduced-memory-qualified.md) |
