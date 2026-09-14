# 2026-09-14T23:20:51Z — Sequential MFU live validation

Run ID: `RUN-0003`

- Status: resolved
- Phase: container startup / inference / metrics
- Repo revision: `7de7cfe89bc196ed2e2921096edba7c0b0b8bc79`, dirty with MFU changes
- Host/GPU: DGX Spark GB10, driver `580.173.02`
- Model: `Qwen/Qwen3-Embedding-8B`

## Command

```bash
docker run -d --name inferpack-mfu-model-check --gpus all --ipc host --shm-size 32gb --ulimit memlock=-1 --ulimit stack=67108864 -p 127.0.0.1:30000:30000 -e CONTEXT_LENGTH=8192 -e HF_HUB_DISABLE_IMPLICIT_TOKEN=1 -e HF_TOKEN= -e INFERPACK_ENABLE_METRICS=1 -e MAX_RUNNING_REQUESTS=2 -e MEM_FRACTION_STATIC=0.40 -e MODEL_ID=Qwen/Qwen3-Embedding-8B -e MODEL_REVISION=1d8ad4ca9b3dd8059ad90a75d4983776a23d44af -e SERVED_MODEL_NAME=qwen3-embedding-8b -e SGLANG_CONTAINER_PORT=30000 -e SGLANG_EXTRA_ARGS= -e HF_HUB_OFFLINE=1 -v /home/coral/.cache/huggingface:/root/.cache/huggingface -v dgxspark-qwen3-embedding-8b_sglang-cache:/root/.cache/sglang -v dgxspark-qwen3-embedding-8b_triton-cache:/root/.triton dgxspark/qwen3-embedding-8b-sglang:0.1.0
```

## Observations

```json
{
  "model": "qwen3-embedding-8b",
  "run_id": "RUN-0003",
  "started": "2026-09-14T23:20:51.436198+00:00",
  "status": "resolved",
  "artifact": "/tmp/inferpack-mfu-all/2026-09-14T23-20-51Z-qwen3-embedding-8b",
  "journal": "/home/coral/.codex/worktrees/0e76/DGXSpark-Small-LLMs/docs/experiments/qwen3-embedding-8b/sglang/dgx-spark/2026-09-14T23-20-51Z-mfu-live-validation.md",
  "image": "dgxspark/qwen3-embedding-8b-sglang:0.1.0",
  "image_id": "sha256:b60cc4d552b3a5555880e9699f68ae38a769f0c7c56475bdfeafdd23d501b6e1",
  "ready_seconds": 111.952827,
  "manifest_validation": "passed",
  "live_service_tests": "Validated 1 normalized vector(s), 4096 dimensions each\n.relevant=0.622134, unrelated=0.135013\n.\n2 passed in 0.67s",
  "reference_tests": "reference cosine: [0.9997662305831909, 0.9998120665550232, 0.9998920559883118]\n.\n1 passed in 81.08s (0:01:21)",
  "prometheus_tflops": [
    {
      "metric": {
        "engine_type": "unified",
        "environment": "dev",
        "instance": "127.0.0.1:30000",
        "job": "sglang",
        "model": "qwen3-embedding-8b",
        "model_name": "qwen3-embedding-8b",
        "moe_ep_rank": "0",
        "pp_rank": "0",
        "tp_rank": "0"
      },
      "value": [
        1789428266.822,
        "0.0076391908755898364"
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
        "model": "qwen3-embedding-8b",
        "model_name": "qwen3-embedding-8b",
        "moe_ep_rank": "0",
        "pp_rank": "0",
        "tp_rank": "0"
      },
      "value": [
        1789428266.832,
        "0.007639932019330251"
      ]
    }
  ],
  "counter_before": {
    "sglang:estimated_flops_per_gpu_total{engine_type=\"unified\",model_name=\"qwen3-embedding-8b\",moe_ep_rank=\"0\",pp_rank=\"0\",tp_rank=\"0\"}": 222302896128.0
  },
  "counter_after": {
    "sglang:estimated_flops_per_gpu_total{engine_type=\"unified\",model_name=\"qwen3-embedding-8b\",moe_ep_rank=\"0\",pp_rank=\"0\",tp_rank=\"0\"}": 2445734117376.0
  },
  "stop_returncode": 0,
  "warnings": [
    "[2026-09-14 23:21:06] Failed to get GPU memory capacity from nvidia-smi. Falling back to torch.cuda.mem_get_info(). Reported total GPU memory per device (MiB): [124610], using min: 124610 MiB."
  ],
  "final_state": {
    "Status": "exited",
    "Running": false,
    "Paused": false,
    "Restarting": false,
    "OOMKilled": false,
    "Dead": false,
    "Pid": 0,
    "ExitCode": 137,
    "Error": "",
    "StartedAt": "2026-09-14T23:20:51.570241589Z",
    "FinishedAt": "2026-09-14T23:24:32.169148957Z"
  }
}
```

## Diagnosis And Verification

This retries [RUN-0002](2026-09-14T23-18-02Z-mfu-live-validation.md). That attempt queried health after the HTTP application started but before model warmup completed and received HTTP 503. Its immediate cleanup interrupted warmup, causing connection-refused errors and exit 137 with OOMKilled=false. The validation driver now waits for SGLang’s final "fired up and ready to roll" signal before querying health; no model or recipe change was needed.


The model completed its configured API validation and additional inference checks. The estimated FLOP counter increased, and the tracked TFLOPS panel query returned finite positive values directly through Prometheus and through Grafana. These are telemetry smoke checks, not peak throughput or estimator accuracy benchmarks.

The GPU-capacity warning uses SGLang’s existing torch.cuda.mem_get_info fallback. A missing torchcodec warning limits audio inputs; audio is outside this validation. Shutdown cancellation traces, when present with exit code zero, follow the existing ASGI lifespan shutdown behaviour. Final exit and OOM state are recorded above.

The temporary model ran alone using the recipe defaults, cached weights and cache volumes, with metrics enabled and its API bound to loopback port 30000. It was stopped after the check. Full local logs and results are retained in the artifact directory above.

## Lesson

Verify metric collection under actual model requests and through the dashboard data source; support for a launch flag alone is insufficient.
