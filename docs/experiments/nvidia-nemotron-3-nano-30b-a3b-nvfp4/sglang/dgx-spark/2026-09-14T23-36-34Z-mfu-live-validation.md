# 2026-09-14T23:36:34Z — Sequential MFU live validation

Run ID: `RUN-0010`

- Status: open
- Phase: container startup / inference / metrics
- Repo revision: `7de7cfe89bc196ed2e2921096edba7c0b0b8bc79`, dirty with MFU changes
- Host/GPU: DGX Spark GB10, driver `580.173.02`
- Model: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4`

## Command

```bash
docker run -d --name inferpack-mfu-model-check --gpus all --ipc host --shm-size 32gb --ulimit memlock=-1 --ulimit stack=67108864 -p 127.0.0.1:30000:30000 -e CONTEXT_LENGTH=32768 -e GPU_MEMORY_BUDGET_GIB=60 -e HF_HUB_DISABLE_IMPLICIT_TOKEN=1 -e HF_TOKEN= -e INFERPACK_ENABLE_METRICS=1 -e MAX_JOBS=4 -e MEM_FRACTION_STATIC= -e MODEL_ID=nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4 -e SERVED_MODEL_NAME=nemotron-3-nano -e SGLANG_CONTAINER_PORT=30000 -e SGLANG_EXTRA_ARGS= -e HF_HUB_OFFLINE=1 -v /home/coral/.cache/huggingface:/root/.cache/huggingface -v dgxspark-nemotron-3-nano_flashinfer-cache:/root/.cache/flashinfer -v dgxspark-nemotron-3-nano_sglang-cache:/root/.cache/sglang dgxspark/nemotron-3-nano-30b-a3b-nvfp4-sglang:0.1.0
```

## Observations

```json
{
  "model": "nvidia-nemotron-3-nano-30b-a3b-nvfp4",
  "run_id": "RUN-0010",
  "started": "2026-09-14T23:36:34.469941+00:00",
  "status": "open",
  "artifact": "/tmp/inferpack-mfu-all/2026-09-14T23-36-34Z-nvidia-nemotron-3-nano-30b-a3b-nvfp4",
  "journal": "/home/coral/.codex/worktrees/0e76/DGXSpark-Small-LLMs/docs/experiments/nvidia-nemotron-3-nano-30b-a3b-nvfp4/sglang/dgx-spark/2026-09-14T23-36-34Z-mfu-live-validation.md",
  "image": "dgxspark/nemotron-3-nano-30b-a3b-nvfp4-sglang:0.1.0",
  "image_id": "sha256:85e7f2c4f796a805251ba7da2f0886cfa85d26af1f25898cfd02b19626fe00a3",
  "ready_seconds": 193.69071,
  "error": "RuntimeError('validation returned no final content (finish_reason=length, completion_tokens=512)')",
  "stop_returncode": 0,
  "warnings": [
    "[2026-09-14 23:36:52] Failed to get GPU memory capacity from nvidia-smi. Falling back to torch.cuda.mem_get_info(). Reported total GPU memory per device (MiB): [124610], using min: 124610 MiB.",
    "[2026-09-14 23:37:05] Ignore import error when loading sglang.srt.models.mimo_audio: Can not import FA3 in sgl_kernel. Please check your installation.",
    "[2026-09-14 23:37:05] Ignore import error when loading sglang.srt.models.mimo_v2: Can not import FA3 in sgl_kernel. Please check your installation.",
    "[2026-09-14 23:37:05] Ignore import error when loading sglang.srt.models.mimo_v2_asr: Can not import FA3 in sgl_kernel. Please check your installation.",
    "[2026-09-14 23:37:05] Ignore import error when loading sglang.srt.models.mimo_v2_nextn: Can not import FA3 in sgl_kernel. Please check your installation.",
    "[2026-09-14 23:40:02] ERROR:    Traceback (most recent call last):",
    "Traceback (most recent call last):",
    "asyncio.exceptions.CancelledError"
  ],
  "final_state": {
    "Status": "exited",
    "Running": false,
    "Paused": false,
    "Restarting": false,
    "OOMKilled": false,
    "Dead": false,
    "Pid": 0,
    "ExitCode": 0,
    "Error": "",
    "StartedAt": "2026-09-14T23:36:34.647396087Z",
    "FinishedAt": "2026-09-14T23:40:04.657472234Z"
  }
}
```

## Diagnosis And Verification

Validation failed as recorded above; diagnosis and corrective verification remain open.

The GPU-capacity warning uses SGLang’s existing torch.cuda.mem_get_info fallback. A missing torchcodec warning limits audio inputs; audio is outside this validation. Shutdown cancellation traces, when present with exit code zero, follow the existing ASGI lifespan shutdown behaviour. Final exit and OOM state are recorded above.

The temporary model ran alone using the recipe defaults, cached weights and cache volumes, with metrics enabled and its API bound to loopback port 30000. It was stopped after the check. Full local logs and results are retained in the artifact directory above.

## Lesson

Verify metric collection under actual model requests and through the dashboard data source; support for a launch flag alone is insufficient.
