# 2026-09-14T22:54:51Z — Enable SGLang estimated model TFLOPS

Run ID: `RUN-0023`

- Status: resolved (estimated counter and Prometheus query verified)
- Phase: container startup / engine startup / model load / inference
- Related turns: [GPU telemetry](2026-09-14T22-48-06Z-gpu-telemetry-support.md),
  [MTP startup](2026-09-14T20-42-56Z-fp8-mtp-startup-qualified.md)
- Repo revision: `7de7cfe89bc196ed2e2921096edba7c0b0b8bc79`, dirty with telemetry documentation and this change
- Host/GPU: DGX Spark GB10, driver `580.173.02`
- Verification image: `dgxspark/qwen3.8-27b-fp8-sglang:0.1.0`, original image
  `sha256:3c11adf54d4a220f587f361f48eee66b50a8e2b8c068db7484c598beb3684b62`, with updated launch script mounted read-only
- Engine: same image as RUN-0012, SGLang `0.0.0.dev1+g5f55db35e`
- Model: cached `Qwen/Qwen3.8-27B-FP8`, revision `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`
- Configuration: TP 1, context 32768, memory fraction 0.45, four running requests,
  Mamba cache 16, prefill chunk 2048, native MTP steps 3 / top-k 1 / draft tokens 4

## Change And Estimator Boundary

Inspected `server_args.py`, `observability/metrics_collector.py`, and
`managers/scheduler_components/metrics_reporter.py` inside the existing image
using temporary `docker run --rm --network none --entrypoint sh` containers.
The image supports `--enable-mfu-metrics` and exports the Prometheus counter
`sglang:estimated_flops_per_gpu_total` (including the `_total` suffix).

The Qwen pack now automatically adds MFU metrics when normal metrics are enabled,
including through the shared start command. Other model packs are unchanged.
The shared dashboard adds `rate(counter[$__rate_interval]) / 1e12`, preserving
individual scheduler labels and existing model/environment filters. Missing
metrics remain absent instead of becoming zero.

Source inspection shows a simplified attention/MLP formula based on model
dimensions and token/context counts. This is an estimated model-operation rate,
not measured FP8 hardware throughput. Hybrid GDN and speculative draft/verify
work are not fully accounted for; do not interpret this as a calibrated hardware
MFU percentage. AIPerf server-metric collection remains disabled.

## Command And Initial Failure

```bash
docker run -d --name inferpack-qwen38-mfu-check \
  --gpus all --ipc host --shm-size 32gb \
  --ulimit memlock=-1 --ulimit stack=67108864 \
  --volumes-from dgxspark-qwen3-8-27b-fp8-sglang-1 \
  -v "$PWD/models/qwen3.8-27b-fp8/sglang/targets/dgx-spark/start.sh:/opt/dgxspark/start.sh:ro" \
  -p 127.0.0.1:30000:30000 \
  -e HF_HUB_DISABLE_IMPLICIT_TOKEN=1 -e HF_HUB_OFFLINE=1 \
  -e INFERPACK_ENABLE_METRICS=1 \
  -e 'SGLANG_EXTRA_ARGS=--speculative-algorithm EAGLE --speculative-num-steps 3 --speculative-eagle-topk 1 --speculative-num-draft-tokens 4' \
  dgxspark/qwen3.8-27b-fp8-sglang:0.1.0
```

The initial attempt exited 126 with:

```text
exec: "/opt/dgxspark/start.sh": permission denied
```

The read-only bind mount replaces the image's executable script with the
checkout's non-executable file. Removed only this failed temporary container
and repeated the command with `--entrypoint bash` before the image and
`/opt/dgxspark/start.sh` after it. The retry started successfully. The production
Dockerfile already applies `chmod 0755` during build.

The established nonfatal startup observations recurred:

```text
Failed to get GPU memory capacity from nvidia-smi. Falling back to torch.cuda.mem_get_info().
torchcodec is not installed; audio inputs will fail at request time
Ignore import error when loading sglang.srt.multimodal.processors.mimo_v2: No module named 'torchcodec'
```

As in RUN-0012, memory capacity uses the PyTorch fallback, and missing audio
support is outside the text verification scope.

## Build And Verification

```bash
docker build --network none -t dgxspark/qwen3.8-27b-fp8-sglang:0.1.0 \
  models/qwen3.8-27b-fp8/sglang/targets/dgx-spark
bash -n models/qwen3.8-27b-fp8/sglang/targets/dgx-spark/start.sh
UV_CACHE_DIR=/tmp/inferpack-uv-cache uv run --python 3.12 --no-sync pytest -q tests/test_start_monitoring.py
INFERPACK_MONITORING_TESTS=1 UV_CACHE_DIR=/tmp/inferpack-uv-cache \
  uv run --python 3.12 --no-sync pytest -q monitoring/tests/test_dashboard_queries.py
```

Build succeeded using the cached base; new image ID:
`sha256:dcf597a9239d246c432f036a403e9f961133f38903074a025f320da935f135ff`.
Shell syntax passed; 29 existing start-monitoring checks and the existing
Prometheus dashboard-query check passed. No repository tests were added.

A temporary Prometheus `prom/prometheus:v3.13.3` instance named
`inferpack-mfu-prom-check` listens only on `127.0.0.1:9095` and scrapes the
temporary Qwen endpoint every five seconds with model/environment labels.
Its config and the uv Python 3.12 verification script are under
`/tmp/inferpack-mfu-check/`.

The server was serving `/metrics` by 22:56:12 UTC. `/health` succeeded, followed
by one priming chat request and eight measured chat requests at concurrency four.
Each measured request used 26 input tokens and 96 forced output tokens, with
thinking disabled; all returned nonempty content. The eight requests completed
in 12.339 seconds. This validates telemetry, not response quality or peak TFLOPS.

```bash
UV_CACHE_DIR=/tmp/inferpack-uv-cache uv run --python 3.12 --no-sync \
  python /tmp/inferpack-mfu-check/verify.py
```

The counter rose from `1.135799959552e13` to `5.5101260038144e13` FLOPs.
It exported `engine_type="unified"`, `model_name="qwen3.8-27b-fp8"`,
`moe_ep_rank="0"`, `pp_rank="0"`, and `tp_rank="0"`. The panel legend uses
these observed rank labels. The actual dashboard expression with a one-minute
rate window returned `0.9848736448512001` estimated TFLOPS through Prometheus.
That window includes idle time and the priming request; it is not a peak or
inference-only throughput measurement. Full readings are in
`/tmp/inferpack-mfu-check/result.json`.

## Cleanup

Stopped both temporary containers after verification. As in
[RUN-0011](2026-09-14T20-12-24Z-benchmark-shutdown-cleanup.md), SGLang emitted
`SystemExit: 0` followed by `asyncio.exceptions.CancelledError` from the ASGI
lifespan handler during requested shutdown. Docker reported exit code `0` and
`OOMKilled=false`; this is the existing shutdown cancellation behaviour, not a
counter or inference failure. The temporary Prometheus container removes itself.
The updated image is built locally; normal model and monitoring services remain
stopped until started through the normal workflow.

## Lesson

Check metric names and estimation formulas in the exact model image, then
verify both inference counter increments and the Prometheus rate expression.
Hardware utilisation and estimated model FLOPS are distinct measurements.
