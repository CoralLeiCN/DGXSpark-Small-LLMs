# 2026-09-14T23:24:32Z — Sequential MFU live validation

Run ID: `RUN-0007`

- Status: resolved
- Phase: container startup / inference / metrics
- Repo revision: `7de7cfe89bc196ed2e2921096edba7c0b0b8bc79`, dirty with MFU changes
- Host/GPU: DGX Spark GB10, driver `580.173.02`
- Model: `TomoroAI/tomoro-colqwen3-embed-4b`

## Command

```bash
docker run -d --name inferpack-mfu-model-check --gpus all --ipc host --shm-size 32gb --ulimit memlock=-1 --ulimit stack=67108864 -p 127.0.0.1:30000:30000 -e CONTEXT_LENGTH=8192 -e HF_HUB_DISABLE_IMPLICIT_TOKEN=1 -e HF_TOKEN= -e INFERPACK_ENABLE_METRICS=1 -e MAX_RUNNING_REQUESTS=2 -e MEM_FRACTION_STATIC=0.25 -e MODEL_ID=TomoroAI/tomoro-colqwen3-embed-4b -e MODEL_REVISION=13517a29e8c5e408f7f2684337ed407df3acb212 -e SERVED_MODEL_NAME=tomoro-colqwen3-embed-4b -e SGLANG_CONTAINER_PORT=30000 -e SGLANG_EXTRA_ARGS= -e HF_HUB_OFFLINE=1 -v /home/coral/.cache/huggingface:/root/.cache/huggingface -v dgxspark-tomoro-colqwen3-embed-4b_sglang-cache:/root/.cache/sglang -v dgxspark-tomoro-colqwen3-embed-4b_triton-cache:/root/.triton dgxspark/tomoro-colqwen3-embed-4b-sglang:0.1.0
```

## Observations

```json
{
  "model": "tomoro-colqwen3-embed-4b",
  "run_id": "RUN-0007",
  "started": "2026-09-14T23:24:32.608170+00:00",
  "status": "resolved",
  "artifact": "/tmp/inferpack-mfu-all/2026-09-14T23-24-32Z-tomoro-colqwen3-embed-4b",
  "journal": "/home/coral/.codex/worktrees/0e76/DGXSpark-Small-LLMs/docs/experiments/tomoro-colqwen3-embed-4b/sglang/dgx-spark/2026-09-14T23-24-32Z-mfu-live-validation.md",
  "image": "dgxspark/tomoro-colqwen3-embed-4b-sglang:0.1.0",
  "image_id": "sha256:f43e07fea8397b4cf610d9be0ea275364442bc35870169290a92d153544e3347",
  "ready_seconds": 86.825532,
  "manifest_validation": "passed",
  "live_service_tests": "......Validated 3 normalized vector(s), 320 dimensions each\n.Validated 7 normalized vector(s), 320 dimensions each\n.\n8 passed in 0.24s",
  "reference_tests": "[ERROR] `cache_position` is part of ColQwen3.forward's signature, but not documented. Make sure to add it to the docstring of the function in /root/.cache/huggingface/modules/transformers_modules/test_text_and_image_match_refe0/05a396fd4bb59f89/modeling_colqwen3.py.\ntext: shape=(17, 320), mean_cosine=0.999651, min_cosine=0.999368\nimage: shape=(75, 320), mean_cosine=0.997614, min_cosine=0.967261\n.\n=============================== warnings summary ===============================\ntests/test_reference.py::test_text_and_image_match_reference\n  /opt/sglang/lib/python3.12/site-packages/transformers/processing_utils.py:928: DeprecationWarning: __array__ implementation doesn't accept a copy keyword, so passing copy=False failed. __array__ must implement 'dtype' and 'copy' keyword arguments. To learn more, see the migration guide https://numpy.org/devdocs/numpy_2_0_migration_guide.html#adapting-to-changes-in-the-copy-keyword\n    tokenizer_input = np.array(tokenizer_input)\n\n-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html\n1 passed, 1 warning in 47.88s",
  "prometheus_tflops": [
    {
      "metric": {
        "engine_type": "unified",
        "environment": "dev",
        "instance": "127.0.0.1:30000",
        "job": "sglang",
        "model": "tomoro-colqwen3-embed-4b",
        "model_name": "tomoro-colqwen3-embed-4b",
        "moe_ep_rank": "0",
        "pp_rank": "0",
        "tp_rank": "0"
      },
      "value": [
        1789428429.239,
        "0.003507882534315154"
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
        "model": "tomoro-colqwen3-embed-4b",
        "model_name": "tomoro-colqwen3-embed-4b",
        "moe_ep_rank": "0",
        "pp_rank": "0",
        "tp_rank": "0"
      },
      "value": [
        1789428429.245,
        "0.0035081550441255498"
      ]
    }
  ],
  "counter_before": {
    "sglang:estimated_flops_per_gpu_total{engine_type=\"unified\",model_name=\"tomoro-colqwen3-embed-4b\",moe_ep_rank=\"0\",pp_rank=\"0\",tp_rank=\"0\"}": 101762334720.0
  },
  "counter_after": {
    "sglang:estimated_flops_per_gpu_total{engine_type=\"unified\",model_name=\"tomoro-colqwen3-embed-4b\",moe_ep_rank=\"0\",pp_rank=\"0\",tp_rank=\"0\"}": 997396512768.0
  },
  "stop_returncode": 0,
  "warnings": [
    "[2026-09-14 23:24:48] Failed to get GPU memory capacity from nvidia-smi. Falling back to torch.cuda.mem_get_info(). Reported total GPU memory per device (MiB): [124610], using min: 124610 MiB.",
    "[2026-09-14 23:24:53] torchcodec is not installed; audio inputs will fail at request time",
    "[2026-09-14 23:24:53] Ignore import error when loading sglang.srt.multimodal.processors.mimo_v2: No module named 'torchcodec'",
    "[2026-09-14 23:24:57] torchcodec is not installed; audio inputs will fail at request time",
    "[2026-09-14 23:24:57] Ignore import error when loading sglang.srt.multimodal.processors.mimo_v2: No module named 'torchcodec'"
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
    "StartedAt": "2026-09-14T23:24:32.742977012Z",
    "FinishedAt": "2026-09-14T23:27:13.477191819Z"
  }
}
```

## Diagnosis And Verification

The model completed its configured API validation and additional inference checks. The estimated FLOP counter increased, and the tracked TFLOPS panel query returned finite positive values directly through Prometheus and through Grafana. These are telemetry smoke checks, not peak throughput or estimator accuracy benchmarks.

The GPU-capacity warning uses SGLang’s existing torch.cuda.mem_get_info fallback. A missing torchcodec warning limits audio inputs; audio is outside this validation. Shutdown cancellation traces, when present with exit code zero, follow the existing ASGI lifespan shutdown behaviour. Final exit and OOM state are recorded above.

The temporary model ran alone using the recipe defaults, cached weights and cache volumes, with metrics enabled and its API bound to loopback port 30000. It was stopped after the check. Full local logs and results are retained in the artifact directory above.

## Lesson

Verify metric collection under actual model requests and through the dashboard data source; support for a launch flag alone is insufficient.
