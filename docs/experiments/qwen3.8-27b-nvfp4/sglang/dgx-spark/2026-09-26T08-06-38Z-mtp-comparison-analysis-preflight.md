# 2026-09-26T08:06:38Z — Offline MTP comparison: source layout and missing-counter handling

Run ID: `RUN-0025`

- Status: resolved
- Phase: offline analysis / source inspection
- Repo revision: `89611e1`, dirty with experiment documentation
- Host/GPU: DGX Spark, NVIDIA GB10, driver `580.173.02`, aarch64
- Image: `sha256:110ad45e7872397f337ea5714e6c97c400852938a9b8f258bcc27cab07182b0c`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`; AIPerf `0.12.0`, Python 3.12
- Model: `nvidia/Qwen3.8-27B-NVFP4`, revision `482ca0f3832238542f8f5295dde86b5f22711d80`
- Artifacts: [2026-09-26T00-12-44Z-mtp1-mtp3](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-26T00-12-44Z-mtp1-mtp3/)
- Related turns: [MTP=2 launch](2026-09-25T20-24-59Z-mtp2-c72-round.md); see this target index for the MTP=1/3 launch and subsequent events.

## Scope and observed errors

Offline preparation for the requested four-configuration report; no inference
service was started and no benchmark was rerun. The image/engine above identify
the stopped MTP=3 container inspected for source provenance. Derived report files
are saved in [2026-09-26T08-06-38Z-mtp-disabled-1-2-3-comparison](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/reports/2026-09-26T08-06-38Z-mtp-disabled-1-2-3-comparison/).

The initial source-copy diagnostic used a historical filename that is absent
from this pinned engine layout:

```bash
docker cp inferpack-qwen38-nvfp4-mtp3-c64-20260926:/sgl-workspace/sglang/python/sglang/srt/managers/scheduler_metrics_mixin.py /tmp/nvfp4-mtp-scheduler-metrics.py
```

```text
Error response from daemon: Could not find the file .../managers/scheduler_metrics_mixin.py in container inferpack-qwen38-nvfp4-mtp3-c64-20260926
```

An initial plotting environment probe also omitted the Python executable after
`uv run --offline --no-project --python 3.12 --with matplotlib`, giving
`error: unexpected argument '-c' found`. This is an offline command-construction
error, not an engine/runtime incompatibility.

The first extraction attempt assumed cached-token counter endpoints were always
present. A historical export lacked an endpoint, producing:

```text
TypeError: unsupported operand type(s) for /: 'NoneType' and 'float'
```

## Diagnosis, corrections, and verification

Copy the existing managers directory from the stopped container, then search
its real layout with `rg`. The metric implementation is
`managers/scheduler_components/metrics_reporter.py`; the copy and source inspection
succeeded. Corrected commands:

```bash
docker cp inferpack-qwen38-nvfp4-mtp3-c64-20260926:/sgl-workspace/sglang/python/sglang/srt/managers /tmp/nvfp4-mtp-managers
uv run --offline --no-project --python 3.12 --with matplotlib python -c 'import matplotlib; print(matplotlib.__version__)'
```

Matplotlib3.11.2 loaded from the cached uv environment. Extraction now preserves
unavailable cache fractions as null, while validating present counters and
rejecting decreases. It successfully read80 measured trials and14,496 requests,
verified expected counts, zero recorded errors/cancellations, forced128-token
outputs, per-configuration speculative steps, and actual GPU/server exports.
Two figures were generated and visually inspected. No missing measurement was
converted to a fabricated zero. All320 primary input hashes are in the manifest.

## Lesson

Discover paths in the pinned engine instead of assuming an older source layout.
Treat missing historical metric endpoints explicitly, and distinguish analysis
tooling failures from inference failures. Keep the originals immutable while
recording the corrected extraction and resulting report in new entries.
