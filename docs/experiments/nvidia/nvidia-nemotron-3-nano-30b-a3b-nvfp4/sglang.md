# NVIDIA Nemotron 3 Nano 30B A3B NVFP4 — SGLang Experiment Journal

Deployment recipe:
[`models/nvidia/nvidia-nemotron-3-nano-30b-a3b-nvfp4/sglang/`](../../../../models/nvidia/nvidia-nemotron-3-nano-30b-a3b-nvfp4/sglang/)

Use the entry format and investigation workflow in the
[journal guide](../../README.md). This file is an append-only record of
observed failed experiments for this model and engine.

## 2026-09-03T21:11:30Z — Restricted shell could not access the NVIDIA driver

- Status: resolved
- Phase: preflight
- Repo revision: `c520931` (`dirty`)
- Host/GPU: DGX Spark, NVIDIA GB10, driver `580.173.02`, ARM64
- Container: `nvcr.io/nvidia/pytorch:26.02-py3`
  (`sha256:c0e6c0b168faa1be027564e9a004e842c342e22ea51903d5fc7b9008850398d0`)
- Engine: SGLang `0.5.15.post1`
- Model: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4`, NVFP4

### Command

```bash
nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version \
  --format=csv,noheader
```

### Error

```text
NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver.
Make sure that the latest NVIDIA driver is installed and running.
```

### Diagnosis

- Symptom: `nvidia-smi` failed in the restricted command environment, and no
  `/dev/nvidia*` nodes or systemd bus were visible there.
- Root cause: the command sandbox isolated host GPU devices and the system bus;
  the host NVIDIA driver was not broken.
- Evidence: the restricted environment could read the loaded NVIDIA kernel
  modules and driver version but could not see device nodes. Repeating the
  checks with host-level access detected the GB10, reported driver `580.173.02`,
  and showed `nvidia-persistenced.service` as active. Docker also reported an
  ARM64 server and found the required cached base image.

### Fix

Run host GPU and Docker setup commands with host-level device and daemon access.
No driver restart or recipe change was required.

### Verification

```bash
nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version \
  --format=csv,noheader
systemctl is-active nvidia-persistenced.service
docker info --format 'server={{.ServerVersion}} architecture={{.Architecture}}'
docker image inspect nvcr.io/nvidia/pytorch:26.02-py3
```

The host-level checks reported an NVIDIA GB10, an active persistence daemon,
Docker `29.2.1` on ARM64, and the cached `26.02-py3` base image.

### Lesson

When `nvidia-smi` fails, first distinguish a host driver failure from execution
isolation. Compare device-node visibility and repeat the check in the same
host-level context that will operate Docker before restarting drivers or
changing an inference recipe.

### Follow-ups

- Continue preflight, build, startup, and inference commands with host-level
  Docker and GPU access.

## 2026-09-03T21:12:57Z — SGLang could not read GPU capacity from `nvidia-smi`

- Status: workaround
- Phase: engine startup
- Repo revision: `c520931` (`dirty`)
- Host/GPU: DGX Spark, NVIDIA GB10, driver `580.173.02`, ARM64
- Container: `dgxspark/nemotron-3-nano-30b-a3b-nvfp4-sglang:0.1.0`
- Engine: SGLang `0.5.15.post1`
- Model: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4`, NVFP4

### Command

```bash
scripts/deploy-nemotron-nano
```

### Error

```text
Failed to get GPU memory capacity from nvidia-smi. Falling back to
torch.cuda.mem_get_info(). Reported total GPU memory per device (MiB):
[124610], using min: 124610 MiB.
```

### Diagnosis

- Symptom: SGLang's `nvidia-smi` capacity probe did not return usable memory
  figures during startup.
- Root cause: on this GB10 unified-memory system, the host `nvidia-smi` query
  reports GPU memory total and free as `N/A`, so SGLang cannot use that probe to
  determine capacity.
- Evidence: the host query detected the GB10 and driver but returned `[N/A]`
  for both memory fields. SGLang's Torch fallback reported 124,610 MiB, and the
  model launcher independently calculated 121.69 GiB with
  `torch.cuda.mem_get_info()`.

### Fix

No code change was required because SGLang automatically falls back to Torch.
The recipe's 60 GiB budget calculation also deliberately uses Torch instead of
parsing `nvidia-smi`.

### Verification

```bash
scripts/logs nvidia/nvidia-nemotron-3-nano-30b-a3b-nvfp4 \
  --engine sglang --no-follow
```

Startup continued with a static fraction of `0.493058` calculated from 121.69
GiB, then loaded all five NVFP4 weight shards.

### Lesson

Do not assume `nvidia-smi` exposes discrete-VRAM capacity on a unified-memory
DGX Spark. Use a CUDA-aware runtime query such as `torch.cuda.mem_get_info()`
and retain a tested fallback in engine tooling.

### Follow-ups

- Treat this warning as expected while Torch reports a valid capacity and the
  calculated memory fraction remains within `(0, 1)`.

## 2026-09-03T21:16:19Z — Health probe reset while JIT compilation was running

- Status: open
- Phase: health check
- Repo revision: `c520931` (`dirty`)
- Host/GPU: DGX Spark, NVIDIA GB10, driver `580.173.02`, ARM64
- Container: `dgxspark/nemotron-3-nano-30b-a3b-nvfp4-sglang:0.1.0`
- Engine: SGLang `0.5.15.post1`
- Model: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4`, NVFP4

### Command

```bash
curl --silent --show-error --max-time 5 \
  http://127.0.0.1:30000/health
```

### Error

```text
curl: (56) Recv failure: Connection reset by peer
```

### Diagnosis

- Symptom: the published port accepted and then reset the request while Docker
  still reported `health=starting`.
- Root cause: the API was not ready because the scheduler was compiling the
  initial FlashInfer FP4 kernels.
- Evidence: the container was running with zero restarts, and its process tree
  showed active Ninja, `nvcc`, and `cicc` workers under the SGLang scheduler.

### Fix

Do not send validation traffic until Docker reports the service healthy. The
Compose health check already allows a 30-minute first-start period for model
loading and kernel compilation.

### Verification

Pending successful engine startup after the compilation-memory fix below.

### Lesson

An exposed TCP port does not mean a model server is ready. Gate inference
validation on the engine health endpoint, especially on first startup when JIT
compilation can take several minutes.

### Follow-ups

- Append the healthy endpoint result after the engine starts successfully.

## 2026-09-03T21:18:43Z — Parallel FlashInfer FP4 compilation exhausted memory

- Status: open
- Phase: engine startup
- Repo revision: `c520931` (`dirty`)
- Host/GPU: DGX Spark, NVIDIA GB10, 121.69 GiB unified memory, driver
  `580.173.02`, ARM64
- Container: `dgxspark/nemotron-3-nano-30b-a3b-nvfp4-sglang:0.1.0`
- Engine: SGLang `0.5.15.post1`, FlashInfer `0.6.12`
- Model: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4`, revision
  `6efb4a2a1c1fa277ce7b3df7a1416255011b1c99`, NVFP4

### Command

```bash
scripts/deploy-nemotron-nano
```

### Error

```text
subprocess.CalledProcessError: Command ['ninja', '-v', '-C',
'/root/.cache/flashinfer/0.6.12/121a/cached_ops/fp4_gemm_cutlass_sm120',
'-f', '.../build.ninja'] returned non-zero exit status 137.
...
FAILED: [code=137] ...fp4_gemm_cutlass...cuda.o
Killed
ninja: build stopped: subcommand failed.
```

### Diagnosis

- Symptom: the scheduler died during first-run FlashInfer FP4 GEMM compilation,
  after weights and runtime caches had initialized successfully.
- Root cause: Ninja launched many memory-heavy CUDA compiler processes in
  parallel. Their aggregate use exhausted the GB10's unified memory while the
  60 GiB SGLang allocation was resident, so the kernel killed compiler workers.
- Evidence: Docker recorded `OOMKilled=true`; the container process tree showed
  Ninja compiling 18 targets concurrently and several `cicc` workers each using
  roughly 3–4.5 percent of 121.69 GiB. The installed FlashInfer source reads
  `MAX_JOBS` and passes it to Ninja as `-j`.

### Fix

Set the recipe default to `MAX_JOBS=1` so FlashInfer JIT compilation is serial.
Add named Docker volumes for `/root/.cache/flashinfer` and
`/root/.cache/sglang` so compiled kernels and autotuning results survive
container recreation.

### Verification

Pending a rebuilt container, healthy endpoint, and successful inference request.

### Lesson

On unified-memory inference systems, the model allocation and build-time
compiler processes compete for the same capacity. Limit JIT build concurrency
explicitly; CPU count is not a safe default for CUDA template compilation.

### Follow-ups

- Rebuild and start with `MAX_JOBS=1`.
- Confirm Ninja uses one worker, Docker reaches `healthy`, and the validation
  request returns a completion.

### Follow-up — 2026-09-03T21:37:58Z

`MAX_JOBS=1` successfully compiled and linked the 17-object FP4 GEMM extension
without an OOM. The next required fused-MoE extension contained 96 object
targets, making full serialization unnecessarily slow. Its active compiler used
about 2.1 GiB while approximately 54 GiB remained available. The default was
therefore raised to `MAX_JOBS=4`, still far below the unbounded 18-way compile
that exhausted memory. Completed artifacts remained in the named volume for the
next start.

### Follow-up — 2026-09-03T21:54:10Z

With `MAX_JOBS=4`, Ninja compiled and linked all 96 fused-MoE objects without an
OOM. FlashInfer autotuning completed, SGLang captured prefill and decode CUDA
graphs, and Docker reached `healthy` with zero restarts and `OOMKilled=false`.
The final default is four workers, and both JIT/autotuning caches remain mounted
as named volumes.

## 2026-09-03T21:54:10Z — Follow-up to the startup health reset

- Status: resolved
- Phase: health check
- Repo revision: `c520931` (`dirty`)
- Host/GPU: DGX Spark, NVIDIA GB10, driver `580.173.02`, ARM64
- Container: `dgxspark/nemotron-3-nano-30b-a3b-nvfp4-sglang:0.1.0`
- Engine: SGLang `0.5.15.post1`
- Model: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4`, NVFP4

### Command

```bash
curl --fail --silent --show-error http://127.0.0.1:30000/health
```

### Error

This follows up the connection reset recorded at `2026-09-03T21:16:19Z`.

### Diagnosis

The earlier reset was a readiness race during first-start JIT compilation, not
an API or network configuration failure. SGLang had not started Uvicorn yet.

### Fix

Wait for Docker health rather than using port publication as the readiness
signal. The compilation-memory fix allowed startup to finish.

### Verification

SGLang reported that it was ready at `21:54:06Z`, and `/health` returned HTTP
200 at `21:54:10Z`. Docker then reported the container as healthy.

### Lesson

Keep first-start health grace periods long enough for model loading, JIT
compilation, autotuning, and graph capture; validate only after readiness.

### Follow-ups

- None.

## 2026-09-03T21:55:31Z — Detokenizer heartbeat timed out on the first API request

- Status: resolved
- Phase: health check
- Repo revision: `c520931` (`dirty`)
- Host/GPU: DGX Spark, NVIDIA GB10, driver `580.173.02`, ARM64
- Container: `dgxspark/nemotron-3-nano-30b-a3b-nvfp4-sglang:0.1.0`
- Engine: SGLang `0.5.15.post1`
- Model: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4`, NVFP4

### Command

```bash
scripts/validate nvidia/nvidia-nemotron-3-nano-30b-a3b-nvfp4 \
  --engine sglang --timeout 300
```

### Error

```text
Health check failed. Server couldn't get a response from detokenizer for last
20 seconds. tic start time: 21:55:11. last_heartbeat time: 21:54:40
```

### Diagnosis

- Symptom: SGLang emitted an internal health warning during the first external
  OpenAI-compatible chat request after startup.
- Root cause: not conclusively isolated. The timing indicates that first-request
  work delayed the detokenizer heartbeat; neither the scheduler nor container
  crashed.
- Evidence: the request began prefill at `21:55:34Z` and returned HTTP 200 at
  `21:55:36Z`. `/health` returned 200 again at `21:55:52Z`, and Docker retained
  zero restarts with `OOMKilled=false`.

### Fix

No runtime change was needed. The Compose health check's retries tolerated the
transient first-request warning, and subsequent requests completed normally.

### Verification

```bash
curl --fail --silent --show-error http://127.0.0.1:30000/health
scripts/validate nvidia/nvidia-nemotron-3-nano-30b-a3b-nvfp4 \
  --engine sglang --timeout 300
```

Both commands succeeded, and the final validation completed in about eight
seconds with non-empty output.

### Lesson

A single engine-internal heartbeat warning during first-request warmup is not
equivalent to a dead service. Use retry thresholds plus container restart and
OOM evidence before declaring the deployment unhealthy.

### Follow-ups

- Revisit only if the heartbeat warning repeats after warmup or causes Docker's
  health state to become unhealthy.

## 2026-09-03T21:55:36Z — Validation returned reasoning but no final answer

- Status: resolved
- Phase: inference
- Repo revision: `c520931` (`dirty`)
- Host/GPU: DGX Spark, NVIDIA GB10, driver `580.173.02`, ARM64
- Container: `dgxspark/nemotron-3-nano-30b-a3b-nvfp4-sglang:0.1.0`
- Engine: SGLang `0.5.15.post1`
- Model: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4`, revision
  `6efb4a2a1c1fa277ce7b3df7a1416255011b1c99`, NVFP4

### Command

```bash
scripts/validate nvidia/nvidia-nemotron-3-nano-30b-a3b-nvfp4 \
  --engine sglang --timeout 300
```

### Error

```text
Reasoning:
...the model's analysis...

Response:

```

The endpoint returned HTTP 200, so the original validator exited successfully
despite the empty final content.

### Diagnosis

- Symptom: `reasoning_content` was present but final `content` was empty.
- Root cause: the hard-coded 128-token validation budget was consumed by this
  reasoning model before it produced the final answer.
- Evidence: repeating the same request with `max_tokens=512` returned a valid
  haiku using 337 completion tokens, of which 316 were reasoning tokens.

### Fix

Add model-specific `validation.max_tokens` support to the manifest loader and
set this recipe to 512. Make the validator fail when a successful HTTP response
contains no final text, preventing future false-positive checks.

### Verification

```bash
uv run --python 3.12 python -m unittest discover -s tests -v
scripts/validate nvidia/nvidia-nemotron-3-nano-30b-a3b-nvfp4 \
  --engine sglang --timeout 300
```

Both regression tests passed. The updated validator returned a non-empty haiku
in about eight seconds, and the final health check reported HTTP 200 with zero
container restarts and `OOMKilled=false`.

### Lesson

For reasoning models, budget output tokens for both hidden reasoning and final
content. A 200 response is not sufficient validation: assert that the expected
final response field is non-empty.

### Follow-ups

- None.
