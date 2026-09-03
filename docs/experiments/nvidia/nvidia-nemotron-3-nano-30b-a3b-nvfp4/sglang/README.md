# NVIDIA Nemotron 3 Nano 30B A3B NVFP4 — SGLang Experiment Journal

Deployment recipe:
[`models/nvidia/nvidia-nemotron-3-nano-30b-a3b-nvfp4/sglang/`](../../../../../models/nvidia/nvidia-nemotron-3-nano-30b-a3b-nvfp4/sglang/)

Follow the [journal guide](../../../README.md). Each row links to one immutable
experiment turn; later turns link back to the observations they continue.

Runs recorded: 8

Next run ID: `RUN-0009`

| Run ID | Time (UTC) | Status | Outcome |
| --- | --- | --- | --- |
| `RUN-0001` | 2026-09-03T21:11:30Z | resolved | [Restricted shell could not access the NVIDIA driver](2026-09-03T21-11-30Z-restricted-shell-gpu-access.md) |
| `RUN-0002` | 2026-09-03T21:12:57Z | workaround | [SGLang used Torch when `nvidia-smi` exposed no memory capacity](2026-09-03T21-12-57Z-gpu-capacity-fallback.md) |
| `RUN-0003` | 2026-09-03T21:16:19Z | open | [Health probe ran before JIT startup was ready](2026-09-03T21-16-19Z-health-before-readiness.md) |
| `RUN-0004` | 2026-09-03T21:18:43Z | open | [Unbounded FlashInfer compilation exhausted memory](2026-09-03T21-18-43Z-flashinfer-jit-oom.md) |
| `RUN-0005` | 2026-09-03T21:37:58Z | workaround | [Serialized JIT avoided OOM but exposed excessive build time](2026-09-03T21-37-58Z-serialized-jit-follow-up.md) |
| `RUN-0006` | 2026-09-03T21:54:10Z | resolved | [Four-worker JIT completed and the service became healthy](2026-09-03T21-54-10Z-service-ready.md) |
| `RUN-0007` | 2026-09-03T21:55:31Z | resolved | [First-request detokenizer heartbeat timed out transiently](2026-09-03T21-55-31Z-detokenizer-heartbeat.md) |
| `RUN-0008` | 2026-09-03T21:55:36Z | resolved | [Validation returned reasoning but no final answer](2026-09-03T21-55-36Z-empty-validation-content.md) |
