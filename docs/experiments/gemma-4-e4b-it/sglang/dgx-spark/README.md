# Gemma 4 E4B IT — SGLang — DGX Spark Experiment Journal

Deployment recipe:
[`models/gemma-4-e4b-it/sglang/targets/dgx-spark/`](../../../../../models/gemma-4-e4b-it/sglang/targets/dgx-spark/)

Follow the [journal guide](../../../README.md). Each row links to one immutable
experiment turn; later turns link back to the observations they continue.

Runs recorded: 8

Next run ID: `RUN-0009`

| Run ID | Time (UTC) | Status | Outcome |
| --- | --- | --- | --- |
| `RUN-0001` | 2026-09-05T23:07:59Z | resolved | [Gemma E4B text API qualified after cold download](2026-09-05T23-07-59Z-text-api-qualified.md) |
| `RUN-0002` | 2026-09-05T23:09:10Z | workaround | [Service removed despite shutdown cleanup traceback](2026-09-05T23-09-10Z-shutdown-cleanup-traceback.md) |
| `RUN-0003` | 2026-09-13T21:46:37Z | resolved | [AIPerf client setup qualified; live Gemma benchmark pending](2026-09-13T21-46-37Z-aiperf-client-preflight.md) |
| `RUN-0004` | 2026-09-13T22:00:25Z | workaround | [Gemma started and text validated for AIPerf](2026-09-13T22-00-25Z-gemma-started-for-aiperf.md) |
| `RUN-0005` | 2026-09-13T22:08:12Z | resolved | [AIPerf concurrency baseline: 96 measured requests passed](2026-09-13T22-08-12Z-aiperf-concurrency-baseline.md) |
| `RUN-0006` | 2026-09-13T22:45:13Z | resolved | [Throughput plateau confirmed at client concurrency 4, 6, 8, and 12](2026-09-13T22-45-13Z-aiperf-configured-throughput-plateau.md) |
| `RUN-0007` | 2026-09-13T23:04:38Z | workaround | [Worktree-owned Gemma stopped; no running containers or port 30000 listener](2026-09-13T23-04-38Z-worktree-service-stopped.md) |
| `RUN-0008` | 2026-09-14T23:27:13Z | resolved | [Sequential MFU live validation](2026-09-14T23-27-13Z-mfu-live-validation.md) |
