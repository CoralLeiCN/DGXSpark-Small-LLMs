# 2026-09-14T23:18:02Z — Sequential MFU live validation

Run ID: `RUN-0002`

- Status: open
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
  "run_id": "RUN-0002",
  "started": "2026-09-14T23:18:02.740169+00:00",
  "status": "open",
  "artifact": "/tmp/inferpack-mfu-all/2026-09-14T23-18-02Z-qwen3-embedding-8b",
  "journal": "/home/coral/.codex/worktrees/0e76/DGXSpark-Small-LLMs/docs/experiments/qwen3-embedding-8b/sglang/dgx-spark/2026-09-14T23-18-02Z-mfu-live-validation.md",
  "image": "dgxspark/qwen3-embedding-8b-sglang:0.1.0",
  "image_id": "sha256:b60cc4d552b3a5555880e9699f68ae38a769f0c7c56475bdfeafdd23d501b6e1",
  "error": "<HTTPError 503: 'Service Unavailable'>",
  "stop_returncode": 0,
  "warnings": [
    "[2026-09-14 23:18:17] Failed to get GPU memory capacity from nvidia-smi. Falling back to torch.cuda.mem_get_info(). Reported total GPU memory per device (MiB): [124610], using min: 124610 MiB.",
    "[2026-09-14 23:19:59] Initialization failed. warmup error: Traceback (most recent call last):",
    "ConnectionRefusedError: [Errno 111] Connection refused",
    "Traceback (most recent call last):",
    "urllib3.exceptions.NewConnectionError: HTTPConnection(host='127.0.0.1', port=30000): Failed to establish a new connection: [Errno 111] Connection refused",
    "Traceback (most recent call last):",
    "urllib3.exceptions.MaxRetryError: HTTPConnectionPool(host='127.0.0.1', port=30000): Max retries exceeded with url: /encode (Caused by NewConnectionError(\"HTTPConnection(host='127.0.0.1', port=30000): Failed to establish a new connection: [Errno 111] Connection refused\"))",
    "Traceback (most recent call last):",
    "requests.exceptions.ConnectionError: HTTPConnectionPool(host='127.0.0.1', port=30000): Max retries exceeded with url: /encode (Caused by NewConnectionError(\"HTTPConnection(host='127.0.0.1', port=30000): Failed to establish a new connection: [Errno 111] Connection refused\"))"
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
    "StartedAt": "2026-09-14T23:18:03.017124972Z",
    "FinishedAt": "2026-09-14T23:19:59.993445044Z"
  }
}
```

## Diagnosis And Verification

Validation failed as recorded above; diagnosis and corrective verification remain open.

The temporary model ran alone using the recipe defaults, cached weights and cache volumes, with metrics enabled and its API bound to loopback port 30000. It was stopped after the check. Full local logs and results are retained in the artifact directory above.

## Lesson

Verify metric collection under actual model requests and through the dashboard data source; support for a launch flag alone is insufficient.
