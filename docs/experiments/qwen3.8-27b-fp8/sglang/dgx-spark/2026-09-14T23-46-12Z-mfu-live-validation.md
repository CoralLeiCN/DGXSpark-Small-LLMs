# 2026-09-14T23:46:12Z — Sequential MFU live validation

Run ID: `RUN-0024`

- Status: resolved
- Phase: container startup / inference / metrics
- Repo revision: `7de7cfe89bc196ed2e2921096edba7c0b0b8bc79`, dirty with MFU changes
- Host/GPU: DGX Spark GB10, driver `580.173.02`
- Model: `Qwen/Qwen3.8-27B-FP8`

## Command

```bash
docker run -d --name inferpack-mfu-model-check --gpus all --ipc host --shm-size 32gb --ulimit memlock=-1 --ulimit stack=67108864 -p 127.0.0.1:30000:30000 -e CHUNKED_PREFILL_SIZE=2048 -e CONTEXT_LENGTH=32768 -e HF_HUB_DISABLE_IMPLICIT_TOKEN=1 -e HF_TOKEN= -e INFERPACK_ENABLE_METRICS=1 -e MAX_MAMBA_CACHE_SIZE=16 -e MAX_RUNNING_REQUESTS=4 -e MEM_FRACTION_STATIC=0.45 -e MODEL_ID=Qwen/Qwen3.8-27B-FP8 -e SERVED_MODEL_NAME=qwen3.8-27b-fp8 -e SGLANG_CONTAINER_PORT=30000 -e SGLANG_EXTRA_ARGS= -e HF_HUB_OFFLINE=1 -v /home/coral/.cache/huggingface:/root/.cache/huggingface -v dgxspark-qwen3-8-27b-fp8_flashinfer-cache:/root/.cache/flashinfer -v dgxspark-qwen3-8-27b-fp8_sglang-cache:/root/.cache/sglang -v dgxspark-qwen3-8-27b-fp8_triton-cache:/root/.triton dgxspark/qwen3.8-27b-fp8-sglang:0.1.0
```

## Observations

```json
{
  "model": "qwen3.8-27b-fp8",
  "run_id": "RUN-0024",
  "started": "2026-09-14T23:46:12.711297+00:00",
  "status": "resolved",
  "artifact": "/tmp/inferpack-mfu-all/2026-09-14T23-46-12Z-qwen3.8-27b-fp8",
  "journal": "/home/coral/.codex/worktrees/0e76/DGXSpark-Small-LLMs/docs/experiments/qwen3.8-27b-fp8/sglang/dgx-spark/2026-09-14T23-46-12Z-mfu-live-validation.md",
  "image": "dgxspark/qwen3.8-27b-fp8-sglang:0.1.0",
  "image_id": "sha256:dcf597a9239d246c432f036a403e9f961133f38903074a025f320da935f135ff",
  "ready_seconds": 273.031605,
  "manifest_validation": "passed",
  "chat_requests": 3,
  "prometheus_tflops": [
    {
      "metric": {
        "engine_type": "unified",
        "environment": "dev",
        "instance": "127.0.0.1:30000",
        "job": "sglang",
        "model": "qwen3.8-27b-fp8",
        "model_name": "qwen3.8-27b-fp8",
        "moe_ep_rank": "0",
        "pp_rank": "0",
        "tp_rank": "0"
      },
      "value": [
        1789429907.87,
        "0.07238653957024427"
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
        "model": "qwen3.8-27b-fp8",
        "model_name": "qwen3.8-27b-fp8",
        "moe_ep_rank": "0",
        "pp_rank": "0",
        "tp_rank": "0"
      },
      "value": [
        1789429907.876,
        "0.07239298108655752"
      ]
    }
  ],
  "counter_before": {
    "sglang:estimated_flops_per_gpu_total{engine_type=\"unified\",model_name=\"qwen3.8-27b-fp8\",moe_ep_rank=\"0\",pp_rank=\"0\",tp_rank=\"0\"}": 7299055747072.0
  },
  "counter_after": {
    "sglang:estimated_flops_per_gpu_total{engine_type=\"unified\",model_name=\"qwen3.8-27b-fp8\",moe_ep_rank=\"0\",pp_rank=\"0\",tp_rank=\"0\"}": 25008640884736.0
  },
  "stop_returncode": 0,
  "warnings": [
    "[2026-09-14 23:46:30] Failed to get GPU memory capacity from nvidia-smi. Falling back to torch.cuda.mem_get_info(). Reported total GPU memory per device (MiB): [124610], using min: 124610 MiB.",
    "[2026-09-14 23:46:35] torchcodec is not installed; audio inputs will fail at request time",
    "[2026-09-14 23:46:35] Ignore import error when loading sglang.srt.multimodal.processors.mimo_v2: No module named 'torchcodec'",
    "[2026-09-14 23:46:39] torchcodec is not installed; audio inputs will fail at request time",
    "[2026-09-14 23:46:39] Ignore import error when loading sglang.srt.multimodal.processors.mimo_v2: No module named 'torchcodec'",
    "[2026-09-14 23:51:49] ERROR:    Traceback (most recent call last):",
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
    "StartedAt": "2026-09-14T23:46:12.852718567Z",
    "FinishedAt": "2026-09-14T23:51:51.121075462Z"
  }
}
```

## Diagnosis And Verification

The model completed its configured API validation and additional inference checks. The estimated FLOP counter increased, and the tracked TFLOPS panel query returned finite positive values directly through Prometheus and through Grafana. These are telemetry smoke checks, not peak throughput or estimator accuracy benchmarks.

The GPU-capacity warning uses SGLang’s existing torch.cuda.mem_get_info fallback. A missing torchcodec warning limits audio inputs; audio is outside this validation. Shutdown cancellation traces, when present with exit code zero, follow the existing ASGI lifespan shutdown behaviour. Final exit and OOM state are recorded above.

The temporary model ran alone using the recipe defaults, cached weights and cache volumes, with metrics enabled and its API bound to loopback port 30000. It was stopped after the check. Full local logs and results are retained in the artifact directory above.

## Lesson

Verify metric collection under actual model requests and through the dashboard data source; support for a launch flag alone is insufficient.
