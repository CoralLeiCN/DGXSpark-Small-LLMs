# 2026-09-13T21:46:37Z — AIPerf client setup qualified; Gemma endpoint pending

Run ID: `RUN-0003`

- Status: resolved (client setup and inspection access only; live benchmark pending)
- Phase: preflight
- Related turns: none
- Repo revision: `0d0acca2289c8d0475ba3c8dab76b366e4f150da`; initially clean,
  documentation changes added during this turn
- Host/GPU: DGX Spark target, Linux `aarch64`; GPU capacity not inspected
- Container: intended `dgxspark/gemma-4-e4b-it-sglang:0.1.0`; not running
- Engine: SGLang; no live Gemma engine version measured
- Model: intended `google/gemma-4-E4B-it`; no live revision measured
- Client: uv `0.9.7`, AIPerf `0.12.0`, crick `0.0.8`; successful setup uses
  uv-managed CPython `3.12.12`

## Command

```bash
docker ps --format '{{.Names}} {{.Status}} {{.Ports}}'
ss -ltn '( sport = :30000 )'
UV_CACHE_DIR=/tmp/codex-aiperf-uv-cache \
  uv tool run --python 3.12 --from aiperf==0.12.0 aiperf --version
```

## Error Or Observation

Restricted shell inspection failed:

```text
permission denied while trying to connect to the docker API at unix:///var/run/docker.sock
Cannot open netlink socket: Operation not permitted
```

The first AIPerf installation selected system Python 3.12 and failed building
its ARM64 crick dependency:

```text
crick/tdigest.c:51:10: fatal error: Python.h: No such file or directory
```

A later sandboxed CLI help check also needed a writable uv tool directory:

```text
error: Read-only file system (os error 30) at path "/home/coral/.local/share/uv/tools/<temporary-directory>"
```

## Diagnosis

- Docker/socket inspection was blocked by the execution sandbox. The same
  Docker command succeeded with approved host execution; this was not an
  inference engine failure.
- The compiler was available, but system Python development headers were
  missing. The build command included `/usr/include/python3.12`, and the
  managed-Python retry successfully built the same crick version.
- uv's default tool metadata directory was outside the sandbox's writable
  roots. Relocating it to `/tmp` allowed the offline help check.
- Approved Docker inspection found only
  `dgxspark-qwen3-8-27b-fp8-sglang-1`, healthy and publishing port 30000.
  Gemma E4B was not running. No health or inference request was sent to Qwen
  and no service was stopped or launched.

## Fix Or Change

Retried Docker inspection with approved host access. Retried AIPerf installation
with uv-managed Python 3.12, keeping the benchmark client separate from the
repository environment and the model container. Used a writable temporary uv
tool directory for the subsequent sandboxed check.

Added a Gemma README example for streaming chat at concurrency 1, 2, and 4,
with 512 input tokens, a 128-token generation limit, four warmup requests, and
32 measured requests per setting. Asked the user for an existing Gemma endpoint,
permission to temporarily replace Qwen, or commands only because switching the
currently running service would interrupt it.

## Verification

```bash
UV_CACHE_DIR=/tmp/codex-aiperf-uv-cache \
UV_PYTHON_INSTALL_DIR=/tmp/codex-aiperf-python \
  uv tool run --managed-python --python 3.12 --from aiperf==0.12.0 aiperf --version

UV_TOOL_DIR=/tmp/codex-aiperf-tools \
UV_CACHE_DIR=/tmp/codex-aiperf-uv-cache \
UV_PYTHON_INSTALL_DIR=/tmp/codex-aiperf-python \
  uv tool run --offline --managed-python --python 3.12 \
  --from aiperf==0.12.0 aiperf profile --help
```

Installation built crick successfully, installed 130 packages in an isolated
tool environment, and printed `0.12.0`. CLI help completed successfully and
confirmed benchmark options. README Bash blocks passed `bash -n`; `git diff
--check` passed. These are client setup and documentation checks, not a live
endpoint performance result.

## Lesson

On ARM64, verify both a C compiler and matching Python headers before installing
AIPerf. uv-managed Python supplied the missing headers without a system package
change. Identify the served model before benchmarking a shared default port;
an available endpoint may belong to another recipe.

## Next Step

Once the Gemma endpoint or service switch is selected, validate its model ID and
run the documented benchmark. No Gemma latency or throughput was measured in
this turn.
