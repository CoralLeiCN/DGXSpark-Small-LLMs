# 2026-09-27T15:04:30Z — Hardware pilot: qualify NVTX dependency and retry profiling

Run ID: `RUN-0040`

- Status: open (dependency/build recovered; diagnostic server restarting)
- Phase: profiler startup, Docker build and dependency qualification
- Related: [normal baseline completed](2026-09-27T15-00-27Z-hardware-pilot-baseline-complete.md)
- Environment: GB10 SM12.1, driver580.173.02, CUDA13.0, SGLang0.0.0.dev1+g5f55db35e, Python3.12.3; Nsight Systems2025.3.2 and Compute2025.3.1
- Artifacts: [2026-09-27T13-56-21Z-mtp2-hardware-pilot](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T13-56-21Z-mtp2-hardware-pilot/)

## Observed failures and evidence

The first Nsight Systems server emitted:

```text
An SGLANG_ENABLE_NVTX_* flag is set, but the `nvtx` package is missing.
NVTX markers are disabled; torch profiler spans still emit.
```

This would lose the intended phase/batch annotations despite enabling both
scheduler and operation NVTX flags. The sequence was deliberately stopped before
capture. Its container exited143 at14:58:54UTC, OOMKilled=false; no successful
profile collection is claimed. Logs and original scripts remain in profiles/nsys/.
Startup also logged failure to obtain GPU memory capacity from nvidia-smi and
successfully selected torch.cuda.mem_get_info fallback, reporting124610MiB.

The initial diagnostic Dockerfile used the bare local image ID in FROM:

```text
docker build --pull=false -f scripts/Dockerfile.profiling-v2 ...
FROM sha256:110ad45e7872397f337ea5714e6c97c400852938a9b8f258bcc27cab07182b0c
pull access denied ... docker.io/library/sha256:110ad45...
```

BuildKit interpreted it as a registry/tag reference. Image inspection verified
local tag dgxspark/qwen3.8-27b-nvfp4-sglang:0.1.0 resolves to that exact ID.
The v3 Dockerfile uses the verified local tag and retains --pull=false. Its
nvtx installation succeeded, but the subsequent qualification command omitted
`python` after `uv run`, producing `unexpected argument '-c' found`.

The v4 Dockerfile corrects that invocation to `uv run ... python -c ...`.
Build succeeded, installed only nvtx==0.2.16 with --no-deps, and successfully
imported /opt/sglang/lib/python3.12/site-packages/nvtx/__init__.py. All three
Dockerfiles and build logs are retained. Package source/version is
[NVIDIA NVTX on PyPI](https://pypi.org/project/nvtx/0.2.16/).

## Verified change and retry

The resulting diagnostic-only image is
sha256:3081c11204b7dd0f3010900bf96244fc11712ca0c37ed92cb97f3c4ee1e8165e.
Its parent remains the pinned baseline image; model/engine dependencies and
serving flags are unchanged. Normal baseline measurements used the parent image.
The small annotation dependency is confined to the model's Docker environment.

profiles-v2.py writes new profiles/<mode>-v2 directories and uses new container
names. orchestrate-v3.py sequences nsys, ncu-fp4 and ncu-fp8, retains30-minute
status snapshots, and cleans up all its containers. It is running under
nvfp4-hw-pilot-profiles-v3-20260927.service with a6-hour limit and ExecStopPost.
At this entry the annotated server is starting; actual profile/batch coverage
still requires verification. The960-request baseline is complete and not rerun.

## Lesson

Qualify optional annotation dependencies in the actual serving interpreter
before lengthy profiling startup. Verify local base-image identity and use a
Docker-compatible FROM reference. Preserve the normal-performance image and
record profiling-only instrumentation differences explicitly.
