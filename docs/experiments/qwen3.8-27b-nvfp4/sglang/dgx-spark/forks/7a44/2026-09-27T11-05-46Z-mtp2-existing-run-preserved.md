# 2026-09-27T11:05:46Z — MTP=2 existing aligned run verified; duplicate preparation not launched

Run ID: `RUN-0029`

- Status: resolved
- Phase: inference / benchmark / lifecycle
- Repo revision: `89611e1`, dirty with experiment documentation
- Host/GPU: DGX Spark, NVIDIA GB10, driver `580.173.02`, aarch64
- Image: `sha256:110ad45e7872397f337ea5714e6c97c400852938a9b8f258bcc27cab07182b0c`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`; AIPerf `0.12.0`, Python 3.12
- Model: `nvidia/Qwen3.8-27B-NVFP4`, revision `482ca0f3832238542f8f5295dde86b5f22711d80`
- Artifacts: [2026-09-27T11-00-03Z-mtp2-aligned](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T11-00-03Z-mtp2-aligned/)
- Related turns: [MTP=2 launch](../../2026-09-25T20-24-59Z-mtp2-c72-round.md); see this target index for the MTP=1/3 launch and subsequent events.

## Observation and error

The proposed monitor launch returned:

```text
Failed to start transient timer unit: Unit qwen-nvfp4-mtp2-aligned-20260927-monitor.timer was already loaded or has a fragment file.
```

The saved exact command is in `/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T11-00-03Z-mtp2-aligned/start-services-commands.json`; its output
is in `start-services.log`. The command used `systemd-run --user` with a30-minute
timer and this directory's monitor.py. It exited1 before the loop reached the
main benchmark service launch. No container or inference was started from this
preparation, and no existing service was stopped or changed.

## Diagnosis and verified resolution

Read-only `systemctl --user cat/show` found an already-running aligned MTP=2
experiment from [2026-09-27T10-59-11Z-mtp2-aligned](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T10-59-11Z-mtp2-aligned/), launched11:01:08 UTC and managed in
`/home/coral/repos/DGXSpark-Small-LLMs`. Its own container has suffix`-aligned`.
The existing plan matches three trials, max(64,3C), initial max(8,C) warmup,
admission64,256 Mamba slots, and per-trial cache reporting. Its30-minute timer,
eight-hour bound, and ExecStopPost cleanup are installed. Startup health returned
200 and API qualification was in progress at the check. A completed sweep is not
claimed. Preserve this active experiment; do not run a duplicate on the GPU.

An offline check of this preparation's unused cache extractor also found that
requiring one prompt-token series incorrectly returned unavailable fractions:
the saved metrics have separate streaming/non-streaming labels. The check
failed with `TypeError: type NoneType doesn't define __round__ method` before
any performance data were written. The active experiment's independently saved
extractor sums the series before taking deltas, so it is unaffected. This unused
driver remains unqualified and is explicitly disabled; no inference retry is needed.

## Status and lesson

This branch's RUN-0028 preparation is superseded by the existing active run.
This directory retains only audit/preparation evidence; authoritative run status
and future metrics live in the linked active directory. The completed offline
FLOPs/bandwidth audit remains valid and separate. Check host service ownership
immediately before launch, including after switching worktrees; aggregate labeled
counters deliberately instead of silently rejecting valid multi-series metrics.
