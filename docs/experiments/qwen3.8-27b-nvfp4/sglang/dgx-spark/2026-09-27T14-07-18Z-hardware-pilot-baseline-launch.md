# 2026-09-27T14:07:18Z — MTP=2 fresh-cache c1/c8/c64 baseline launched

Run ID: `RUN-0035`

- Status: open
- Repo: `f3f1d2e`, dirty with experiment documentation
- Host: DGX Spark / GB10 SM12.1 (gb20b), driver580.173.02
- Runtime: SGLang0.0.0.dev1+g5f55db35e, AIPerf0.12.0, Python3.12
- Image: `sha256:110ad45e7872397f337ea5714e6c97c400852938a9b8f258bcc27cab07182b0c`
- Model/native head/tokenizer revision: `482ca0f3832238542f8f5295dde86b5f22711d80`
- Tools: Nsight Compute2025.3.1 and Systems2025.3.2; CUDA13.0
- Artifacts: [2026-09-27T13-56-21Z-mtp2-hardware-pilot](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T13-56-21Z-mtp2-hardware-pilot/)

## Declared protocol

The user selected client concurrency1,8,64 only. Use three trials of64,64,192
measured requests, respectively: nine trials/960 measured requests. Separate
warmup is max(8,C) requests before each concurrency, using a different seed.
Before every measured trial, call the idle server's `/flush_cache?timeout=30`;
require success and verify zero cached-prompt token deltas. This resets prefix/KV
and Mamba pools while retaining the loaded model and compiled kernels/graphs.
Measured inputs use seed42+C; require equal canonical input hashes across repeats.
The dataset target is512 input tokens,128 forced output tokens, streaming,
temperature0, ignoreEOS and thinking disabled. This fixes the earlier mixed-cache
comparison limitation and is a separately identified round.

Use the aligned MTP=2 serving configuration: admission64,256 Mamba slots,float32
state,extra_buffer_lazy,static fraction0.90,FP8 KV,32768 context,2048 prefill chunks;
EAGLE/two drafting steps/topk1/three verification positions. Versions are pinned
above. Five API checks and a four-request c1 telemetry preflight are qualification
exceptions, excluded from baseline results. Independent warmup exports are labeled.

## Launch and lifecycle

`systemd-run --user --unit=nvfp4-hw-pilot-baseline-20260927 ... uv run --offline --no-project --python 3.12 scripts/baseline.py <archive>`
was accepted. Full command and output are baseline/launch.command.txt and launch.log.
At this entry, startup is underway; readiness and performance are not yet claimed.
The driver saves per-request AIPerf data, raw GPU and SGLang exports, before/after
Prometheus snapshots, cache deltas, estimated-FLOPs measured-window deltas, inputs
and commands. Each measured trial is validated before the next begins.

The baseline container is exclusively owned by this experiment. Cleanup runs on
success, failure or cancellation, with a systemd ExecStopPost fallback and3h maximum
runtime. State/events in baseline/ track progress; final shutdown is recorded.
Nsight captures and microbenchmarks do not overlap the normal inference trials.
