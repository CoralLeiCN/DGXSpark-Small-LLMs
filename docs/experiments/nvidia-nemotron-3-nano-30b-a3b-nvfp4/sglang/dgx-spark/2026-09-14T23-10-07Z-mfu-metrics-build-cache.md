# 2026-09-14T23:10:07Z — MFU settings aligned; dependency cache recovered

Run ID: `RUN-0009`

- Status: resolved (image rebuilt; live MFU validation deferred to benchmark)
- Phase: preflight / build
- Related turns: [prior service qualification](2026-09-03T21-54-10Z-service-ready.md)
- Repo revision: `7de7cfe89bc196ed2e2921096edba7c0b0b8bc79`, dirty with metrics alignment
- Host: DGX Spark ARM64; no GPU workload started
- Base: `nvcr.io/nvidia/pytorch:26.02-py3`
- Engine: SGLang `0.5.15.post1`, Torch `2.11.0`, Python 3.12
- Model: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4`; no weights loaded
- Previous model image: `dgxspark/nemotron-3-nano-30b-a3b-nvfp4-sglang:0.1.0`, ID prefix `e67bb0b31486`

## Compatibility And Change

Inspected the cached image through a temporary container with no network or GPU
allocation. Its `sglang/srt/server_args.py` supports `enable_mfu_metrics`,
`observability/metrics_collector.py` defines the counter
`sglang:estimated_flops_per_gpu_total`, and the scheduler metrics reporter
updates estimated work for prefill and decode.

The pack now adds `--enable-mfu-metrics` whenever normal metrics are enabled,
preserving extra arguments and avoiding duplicate flags. The other five packs
use the same launch behaviour; their images were inspected separately.
Model-specific versions, memory settings, and launch flags remain in each pack.
The shared TFLOPS panel uses the counter's per-second rate divided by `1e12`.
The generic attention/MLP estimator does not fully model Nemotron's hybrid
MoE/Mamba work, so it is not a calibrated hardware throughput measurement.

## Command And Observed Build Interruption

```bash
docker build --network none \
  -t dgxspark/nemotron-3-nano-30b-a3b-nvfp4-sglang:0.1.0 \
  models/nvidia-nemotron-3-nano-30b-a3b-nvfp4/sglang/targets/dgx-spark
```

The offline build did not reuse the `uv pip install` layer. It entered dependency
resolution and printed `Using Python 3.12.3 environment at: /usr`, then made no
further visible progress. Interrupted this invocation rather than waiting for
the configured network retries with networking disabled. Exit code was 130:

```text
#9 CANCELED
ERROR: failed to build: failed to solve: Canceled: context canceled
```

This was an operator cancellation, not an observed dependency incompatibility.

## Diagnosis, Fix, And Verification

Retried using the normal build network mode:

```bash
docker build \
  -t dgxspark/nemotron-3-nano-30b-a3b-nvfp4-sglang:0.1.0 \
  models/nvidia-nemotron-3-nano-30b-a3b-nvfp4/sglang/targets/dgx-spark
```

The exact same dependency-install step reported `CACHED`. Only the updated
script copy and chmod layers ran, and the build exited 0. Changing the build
network mode was sufficient to cross the cache boundary; no dependency or
model-serving configuration change was needed.

New image:
`sha256:85e7f2c4f796a805251ba7da2f0886cfa85d26af1f25898cfd02b19626fe00a3`.
Both Gemma images and both embedding images also rebuilt successfully with
their aligned launch scripts. Shell syntax checks passed for all six packs,
and the existing monitoring-start suite passed all 29 checks:

```bash
UV_CACHE_DIR=/tmp/inferpack-uv-cache uv run --python 3.12 --no-sync \
  pytest -q tests/test_start_monitoring.py
```

No new repository tests, model loads, health probes, or inference requests were
performed. Only Qwen3.8 has live MFU-counter validation from the preceding work;
Nemotron and the other newly aligned packs need it during their future benchmarks.

## Lesson And Next Step

Changing Docker build networking can invalidate a cached dependency layer.
Use the recipe's normal build mode to reuse its established cache; an offline
build is not proof that all needed dependency metadata is cached for that mode.
During the next Nemotron benchmark, verify counter increments and the shared
Prometheus rate query after inference begins.
