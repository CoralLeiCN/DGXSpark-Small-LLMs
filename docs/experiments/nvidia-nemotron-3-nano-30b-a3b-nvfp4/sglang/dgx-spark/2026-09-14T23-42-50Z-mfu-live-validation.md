# 2026-09-14T23:42:50Z — Sequential MFU live validation

Run ID: `RUN-0011`

- Status: resolved
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
  "run_id": "RUN-0011",
  "started": "2026-09-14T23:42:50.724893+00:00",
  "status": "resolved",
  "artifact": "/tmp/inferpack-mfu-all/2026-09-14T23-42-50Z-nvidia-nemotron-3-nano-30b-a3b-nvfp4",
  "journal": "/home/coral/.codex/worktrees/0e76/DGXSpark-Small-LLMs/docs/experiments/nvidia-nemotron-3-nano-30b-a3b-nvfp4/sglang/dgx-spark/2026-09-14T23-42-50Z-mfu-live-validation.md",
  "image": "dgxspark/nemotron-3-nano-30b-a3b-nvfp4-sglang:0.1.0",
  "image_id": "sha256:85e7f2c4f796a805251ba7da2f0886cfa85d26af1f25898cfd02b19626fe00a3",
  "ready_seconds": 173.301454,
  "manifest_validation": "passed",
  "chat_requests": 3,
  "prometheus_tflops": [
    {
      "metric": {
        "engine_type": "unified",
        "environment": "dev",
        "instance": "127.0.0.1:30000",
        "job": "sglang",
        "model": "nvidia-nemotron-3-nano-30b-a3b-nvfp4",
        "model_name": "nemotron-3-nano",
        "moe_ep_rank": "0",
        "pp_rank": "0",
        "tp_rank": "0"
      },
      "value": [
        1789429567.897,
        "0.005016035198675627"
      ]
    }
  ],
  "grafana_tflops": [
    {
      "metric": {
        "engine_type": "unified",
        "environment": "dev",
        "instance": "127.0.0.1:30000",
        "job": "sglang",
        "model": "nvidia-nemotron-3-nano-30b-a3b-nvfp4",
        "model_name": "nemotron-3-nano",
        "moe_ep_rank": "0",
        "pp_rank": "0",
        "tp_rank": "0"
      },
      "value": [
        1789429567.901,
        "0.005016811915182079"
      ]
    }
  ],
  "counter_before": {
    "sglang:estimated_flops_per_gpu_total{engine_type=\"unified\",model_name=\"nemotron-3-nano\",moe_ep_rank=\"0\",pp_rank=\"0\",tp_rank=\"0\"}": 252408299520.0
  },
  "counter_after": {
    "sglang:estimated_flops_per_gpu_total{engine_type=\"unified\",model_name=\"nemotron-3-nano\",moe_ep_rank=\"0\",pp_rank=\"0\",tp_rank=\"0\"}": 1421513719808.0
  },
  "stop_returncode": 0,
  "warnings": [
    "[2026-09-14 23:43:01] Failed to get GPU memory capacity from nvidia-smi. Falling back to torch.cuda.mem_get_info(). Reported total GPU memory per device (MiB): [124610], using min: 124610 MiB.",
    "[2026-09-14 23:43:13] Ignore import error when loading sglang.srt.models.mimo_audio: Can not import FA3 in sgl_kernel. Please check your installation.",
    "[2026-09-14 23:43:13] Ignore import error when loading sglang.srt.models.mimo_v2: Can not import FA3 in sgl_kernel. Please check your installation.",
    "[2026-09-14 23:43:13] Ignore import error when loading sglang.srt.models.mimo_v2_asr: Can not import FA3 in sgl_kernel. Please check your installation.",
    "[2026-09-14 23:43:13] Ignore import error when loading sglang.srt.models.mimo_v2_nextn: Can not import FA3 in sgl_kernel. Please check your installation.",
    "[2026-09-14 23:46:09] ERROR:    Traceback (most recent call last):",
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
    "StartedAt": "2026-09-14T23:42:50.857400211Z",
    "FinishedAt": "2026-09-14T23:46:12.342722147Z"
  }
}
```

## Diagnosis And Verification

This retries [RUN-0010](2026-09-14T23-36-34Z-mfu-live-validation.md), which reached readiness but exhausted all 512 output tokens in reasoning and returned no final content. The previous 512-token budget workaround was insufficient for this observed request. The manifest now sets `validation.enable_thinking: false`; shared validation sends the request-level chat-template toggle with greedy Chat Completions sampling. Normal server defaults remain unchanged. The cached tokenizer template and [NVIDIA's model card](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4) support disabling reasoning. Regression tests verify the request, preserve other endpoint defaults, reject invalid manifest values, and continue to reject empty final content. The repository suite passed 92 tests with seven opt-in skips before this live retry.


The model completed its configured API validation and additional inference checks. The estimated FLOP counter increased, and the tracked TFLOPS panel query returned finite positive values directly through Prometheus and through Grafana. These are telemetry smoke checks, not peak throughput or estimator accuracy benchmarks.

The GPU-capacity warning uses SGLang’s existing torch.cuda.mem_get_info fallback. A missing torchcodec warning limits audio inputs; audio is outside this validation. Shutdown cancellation traces, when present with exit code zero, follow the existing ASGI lifespan shutdown behaviour. Final exit and OOM state are recorded above.

The temporary model ran alone using the recipe defaults, cached weights and cache volumes, with metrics enabled and its API bound to loopback port 30000. It was stopped after the check. Full local logs and results are retained in the artifact directory above.

## Lesson

Verify metric collection under actual model requests and through the dashboard data source; support for a launch flag alone is insufficient.
