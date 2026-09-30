# Resolved Serving and Tooling Issues

Reviewed against the checked-in code on 2026-09-30. This document consolidates
superseded SGLang/DGX Spark troubleshooting entries. Dates below identify the
original observations; they are not new experiment runs. Benchmark results,
remaining failures, and qualifications with independent findings stay in the
[experiment journals](experiments/README.md).

## Execution access

These are established environment workarounds, not fixes to the serving code.
Across Nemotron (September 3), Qwen FP8 (September 4 and 14), Gemma (September 9,
13, and 16), and Tomoro (September 7), the same commands worked in an authorized
host execution context after sandboxed commands failed:

| Symptom | Confirmed remedy and boundary |
| --- | --- |
| Docker socket permission denied; GPU or netlink inspection unavailable | Run the required host inspection in an execution context authorized to access that resource. The observations did not require Docker group, socket-permission, or driver changes. |
| Host loopback connection refused while the container was healthy | Check the published API from the host network context. Qwen FP8 returned healthy, listed the correct model, and completed chat on September 4 at 01:15:47Z. |
| uv tool directory is read-only | Set `UV_TOOL_DIR` to a writable directory. Use a writable `UV_CACHE_DIR` and, when needed, `UV_PYTHON_INSTALL_DIR`; keep an already populated cache available for offline use. |
| DNS unavailable during AIPerf installation | Reuse the populated uv cache with offline mode. An empty temporary cache cannot satisfy an offline installation. |
| An isolated Docker build tried to download dependencies | On September 14, Nemotron's `--network none` rebuild was cancelled; the normal build reused its existing install layer successfully. This was a cache/build-context workaround, not a dependency fix. |

Repeat these checks only when needed for the substantive experiment. A recurrence
with the same cause and remedy belongs in its artifacts, not a separate journal.

## Runtime base and startup

Gemma's September 5 GPU preflight stalled after a finished Qwen recipe image was
used as `SGLANG_BASE_IMAGE`: its serving entrypoint consumed the intended Python
probe. The [Gemma manifest](../models/gemma-4-26b-a4b-it/manifest.yaml) and
[Compose default](../models/gemma-4-26b-a4b-it/sglang/targets/dgx-spark/compose.yaml)
use the raw `lmsysorg/sglang:dev-qwen38-27b-dflash2` runtime. Restoring it allowed
preflight, build, and startup to finish at 21:22:01Z. This fixes the recipe's
default; [GPU preflight](../src/inferpack/docker.py) still does not override an
arbitrary image's entrypoint.

Qwen FP8's cold download exceeded its original 30-minute health grace on
September 4. [Compose](../models/qwen3.8-27b-fp8/sglang/targets/dgx-spark/compose.yaml)
now allows 90 minutes. At 01:15:47Z the rendered configuration showed 90 minutes,
and the original container completed download and served a successful chat with
zero restarts and no OOM. That container was not recreated to test another cold
download under the new setting.

A published port still does not prove model readiness. The shared validator
sends requests immediately; these changes do not implement a general readiness
wait. Wait for healthy model responses before validation or measurement.

## Nemotron JIT and memory discovery

On September 3, SGLang 0.5.15.post1 / FlashInfer 0.6.12 launched 18 CUDA compiler
workers alongside the model allocation and was OOM-killed. `MAX_JOBS=1` completed
the FP4 extension but made the 96-object fused-MoE build too slow. The checked-in
[Compose recipe](../models/nvidia-nemotron-3-nano-30b-a3b-nvfp4/sglang/targets/dgx-spark/compose.yaml)
defaults to `MAX_JOBS=4` and persists both FlashInfer and SGLang caches.
The [successful startup](experiments/nvidia-nemotron-3-nano-30b-a3b-nvfp4/sglang/dgx-spark/2026-09-03T21-54-10Z-service-ready.md)
completed compilation, autotuning, and graph capture; health passed at 21:54:10Z
with zero restarts and no OOM. Four workers were qualified for this configuration,
not for every possible resident workload.

GB10's `nvidia-smi` memory fields returned `N/A`. SGLang's existing Torch fallback
worked, and the [launcher](../models/nvidia-nemotron-3-nano-30b-a3b-nvfp4/sglang/targets/dgx-spark/start.sh)
uses `torch.cuda.mem_get_info()` for its 60 GiB budget, validating that the derived
fraction lies within `(0, 1)`. The original reading was 121.69 GiB and fraction
0.493058. This warning did not require a driver fix. Qwen's September 14 telemetry
check independently confirmed working temperature, utilization, and power fields
despite unavailable memory fields; its idle sample was not a performance result.

## Nonempty validation responses

Nemotron could spend its entire completion budget on reasoning and return HTTP
200 with empty final content. Raising the budget from 128 to 512 tokens succeeded
on September 3 but failed again on September 14 at 23:36:34Z.

The [manifest](../models/nvidia-nemotron-3-nano-30b-a3b-nvfp4/manifest.yaml) now sets
`validation.max_tokens: 512` and `validation.enable_thinking: false`.
The [shared validator](../src/inferpack/cli.py) sends the request-level thinking
toggle with greedy sampling, rejects blank final content, and reports completion
length/finish reason on failure. It does not change normal serving defaults.
[Manifest validation](../src/inferpack/manifest.py) checks the option's type and
endpoint compatibility; [existing tests](../tests/test_validation_thinking.py)
cover the request and manifest behavior. The September 14 retry at 23:42:50Z
passed live inference and monitoring checks.

## Monitoring queries and MFU counters

The [dashboard](../monitoring/grafana/dashboards/inference.json) contains the
implemented query fixes:

- Use SGLang's `inter_token_latency_seconds`, rather than an absent
  `time_per_output_token_seconds` series.
- Aggregate streaming and non-streaming label variants before dividing latency
  sums by counts; omit latency when no observations exist.
- Treat a missing cached-token counter as zero only with completed-request
  evidence. Missing telemetry alone remains unknown.
- Apply `rate()` to `estimated_flops_per_gpu_total` and divide by `1e12`,
  retaining rank labels, environment/model filters, and counter-reset handling.

All seven [target launchers](../models/) add `--enable-metrics` and
`--enable-mfu-metrics` when repository monitoring is enabled, preserving other
launch arguments. [Launcher tests](../tests/test_start_monitoring.py) cover that
behavior; [PromQL tests](../monitoring/tests/test_dashboard_queries.py) cover the
query cases above.

Historical checks: all ten original panels passed on September 9 at 22:19:44Z;
mixed-mode validation passed at 23:17:37Z. A September 14 follow-up confirmed all
eleven then-existing panels using the recorded run time, since querying after
service removal made the live `up` check fail. Panel counts describe those
versions, not the current dashboard.

| September 14 live verification (UTC) | Result |
| --- | --- |
| Qwen3 Embedding, 23:20:51Z | Passed after the validation driver waited for model readiness; [detailed evidence](experiments/qwen3-embedding-8b/sglang/dgx-spark/2026-09-14T23-20-51Z-mfu-live-validation.md) remains in its journal. |
| Tomoro, 23:24:32Z | Inference/reference checks and estimated-FLOPs monitoring passed. |
| Gemma E4B, 23:27:13Z | Inference and estimated-FLOPs monitoring passed. |
| Gemma 26B, 23:30:13Z | Inference and estimated-FLOPs monitoring passed. |
| Nemotron, 23:42:50Z | Passed after the request-level thinking fix. |
| Qwen FP8, 23:46:12Z | Ordinary decoding inference and estimated-FLOPs monitoring passed. |

An earlier Qwen FP8 MTP check at 22:54:51Z confirmed an increasing FLOPs counter
and a nonzero dashboard rate. Its temporary bind-mounted launcher initially
failed with exit 126; invoking it through Bash worked. The production
[Dockerfile](../models/qwen3.8-27b-fp8/sglang/targets/dgx-spark/Dockerfile) already
sets the installed launcher executable. These counter checks measure SGLang's
model-work estimate, not hardware peak TFLOPS or achieved hardware utilization.

## Tomoro reference loading and image parity

On September 7, Transformers resolved a cached Python source symlink to a blob
and could not find adjacent `configuration_colqwen3.py`. The
[reference test](../models/tomoro-colqwen3-embed-4b/sglang/targets/dgx-spark/tests/test_reference.py)
copies `.py` files into a real local directory and symlinks other files, including
weights, from pinned snapshot `13517a29e8c5e408f7f2684337ed407df3acb212`.

After loading was fixed, image token cosine similarity still failed: minimum
0.915526 against a 0.95 threshold. The
[model adapter](../models/tomoro-colqwen3-embed-4b/sglang/targets/dgx-spark/tomoro_sglang/model.py)
uses Transformers' bilinear indices/weights, keeps positional interpolation
weights and accumulation in FP32, then casts the result to the vision dtype.
At [12:51:32Z](experiments/tomoro-colqwen3-embed-4b/sglang/dgx-spark/2026-09-07T12-51-32Z-image-parity-qualified-and-stopped.md),
image flattened cosine reached 0.997614 and minimum token cosine 0.967261;
text flattened cosine remained 0.999651. Input IDs, image grid, and pixel values
matched exactly. The retained qualification includes the live reference result.

## AIPerf client setup

Gemma's September 13 AIPerf setup failed building ARM64 `crick` with system
Python because `Python.h` was missing. Both the
[Gemma E4B](../models/gemma-4-e4b-it/sglang/targets/dgx-spark/benchmark-aiperf.sh)
and [Qwen FP8](../models/qwen3.8-27b-fp8/sglang/targets/dgx-spark/benchmark-aiperf.sh)
runners select uv-managed Python 3.12 and AIPerf 0.12.0. The managed interpreter
built the dependency successfully without a host Python package change.

On September 14, Qwen's offline tokenizer lookup rejected a filesystem path as
an invalid Hugging Face repo ID. Its runner uses `Qwen/Qwen3.8-27B-FP8` and pinned
revision `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`; the subsequent
[baseline](experiments/qwen3.8-27b-fp8/sglang/dgx-spark/2026-09-14T20-12-03Z-aiperf-concurrency-baseline.md)
completed. Offline operation still requires the matching cached tokenizer.
Use [current benchmarking rules](BENCHMARKING.md) for new runs; historical
runner request-count defaults do not supersede them.

## Mamba and diagnostic KV budgets

On September 20, Qwen NVFP4's fixed 360-slot Mamba cache left no KV budget under
static fraction 0.45. Its [launcher](../models/qwen3.8-27b-nvfp4/sglang/targets/dgx-spark/start.sh)
and [Compose defaults](../models/qwen3.8-27b-nvfp4/sglang/targets/dgx-spark/compose.yaml)
use fraction 0.70, admission 72, and the fixed cache configuration. The
[12:25:45Z qualification](experiments/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-20T12-25-45Z-mamba-cache-c72-startup.md)
confirmed effective admission 72.

For September 27 MTP=2 profiling, reducing static fraction to 0.75 also rejected
the allocation: fixed Mamba and speculative state still had to fit. The saved
[profiling runner](../models/qwen3.8-27b-nvfp4/sglang/targets/dgx-spark/experiments/hardware-utilization/2026-09-27/profiles-v8.py)
keeps fraction 0.90 and caps discretionary KV capacity at 65,536 tokens, checking
actual capacity and admission 64 before requests. This resolved pool allocation
for that diagnostic configuration. Whole-range profiler warmup still OOMed;
the [remaining failure and narrower capture](experiments/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T16-05-09Z-hardware-pilot-bounded-kernel-recovery.md)
are retained. These settings are not a universal profiler-memory fix.

## Hardware-pilot runner fixes

Environment: Qwen3.8 27B NVFP4 on GB10 SM12.1, driver 580.173.02, CUDA 13.0,
SGLang `0.0.0.dev1+g5f55db35e`, Python 3.12.3, Nsight Systems 2025.3.2,
and Nsight Compute 2025.3.1. Model/dependency pins are also recorded in the
[hardware report](reports/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27-mtp2-hardware-utilization.md).

The September 27 pilot's checked-in reproduction sources contain these fixes:

| Failure | Implemented correction |
| --- | --- |
| AIPerf rejected `--warmup-request-count 0` before measured trials | [Baseline v3](../models/qwen3.8-27b-nvfp4/sglang/targets/dgx-spark/experiments/hardware-utilization/2026-09-27/baseline-v3.py) omits the option for measured requests and runs warmup separately. |
| A completed c1 trial failed verification because a lazy cached-token counter was absent | The same runner subtracts uncached from total prompt histogram sums, verifies both count deltas against completed requests, then checks the fresh-cache result. The completed trial was preserved; the [final baseline](experiments/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T15-00-27Z-hardware-pilot-baseline-complete.md) retained all nine trials. |
| Profiling lacked the Python `nvtx` package; early build/import commands also failed | [Profiling Dockerfile v4](../models/qwen3.8-27b-nvfp4/sglang/targets/dgx-spark/experiments/hardware-utilization/2026-09-27/Dockerfile.profiling-v4) derives from the prepared local image, installs `nvtx==0.2.16` into the model interpreter, and verifies its import/version during build. |
| Offline AIPerf used an empty temporary cache | [Profiles v8](../models/qwen3.8-27b-nvfp4/sglang/targets/dgx-spark/experiments/hardware-utilization/2026-09-27/profiles-v8.py) selects the populated host cache and checks the exact client's version before starting the profiling service. The saved path is host-specific. |

The [hardware report](reports/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27-mtp2-hardware-utilization.md)
preserves the resulting measurements and profiler limitations. Historical source
versions and their checksum manifest remain unchanged for reproduction.
