# 2026-09-27T11:01:08Z — NVFP4 MTP=2: align exploratory sampling with MTP=1/3

Run ID: `RUN-0027`

- Status: open
- Phase: inference / benchmark / lifecycle
- Repo revision: `89611e1`, dirty with experiment documentation
- Host/GPU: DGX Spark, NVIDIA GB10, driver `580.173.02`, aarch64
- Image: `sha256:110ad45e7872397f337ea5714e6c97c400852938a9b8f258bcc27cab07182b0c`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`; AIPerf `0.12.0`, Python 3.12
- Model: `nvidia/Qwen3.8-27B-NVFP4`, revision `482ca0f3832238542f8f5295dde86b5f22711d80`
- Artifacts: [2026-09-27T10-59-11Z-mtp2-aligned](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T10-59-11Z-mtp2-aligned/)
- Related turns: [MTP=2 launch](2026-09-25T20-24-59Z-mtp2-c72-round.md); see this target index for the MTP=1/3 launch and subsequent events.

## Scope and checked guidance

The user requested that MTP=2 align with the newer MTP=1/3 settings after checking
AIPerf best practices. NVIDIA's [multi-run guidance](https://docs.nvidia.com/aiperf/dev/tutorials/metrics-analysis/multi-run-confidence-reporting)
documents three runs for exploration and five for standard benchmarking, consistent
inputs/seeds, and first-trial warmup. Its [NIM walkthrough](https://docs.nvidia.com/nim/benchmarking/llm/1.0.0/step-by-step.html)
uses three times concurrency. The 64-request floor and max(8,C) warmup remain
repository choices, not NVIDIA mandates. Sources rechecked 2026-09-27.

## Declared protocol and cache interpretation

Run MTP=2 alone, two drafting steps/top-k1/three verification positions, admission64,
256 Mamba slots, float32 state, extra_buffer_lazy, static fraction0.90, FP8 KV,
32768 context, 2048 prefill chunks, no ReplaySSM. This matches the MTP=1/3 deployment
choices except drafting steps and their resulting memory allocation. Save actual
KV capacity and effective admission at qualification. All model/tokenizer/image
versions stay pinned to the earlier rounds.

At c1,2,4,8,16,32,48,56,64,72, use three measured trials of max(64,3C) requests,
max(8,C) separate warmups before trial1, seed42+C, identical prompts across repeats,
512 synthetic input target, 128 forced output tokens, temperature0, no thinking,
streaming, no requested cooldown. Total3,408 measured +320 warmup requests.
Five API checks and a c4 three-trial telemetry preflight (8 measured per trial,
4 initial warmup, seed4204) are a separate qualification exception.

**Declared cache protocol:** retain native cache between repeated trials to reproduce
the completed MTP=1/3 procedure. This deliberately measures the first/repeat-pass
progression, not three equivalent cache states. Record cached/prompt counter deltas
for every trial; mark missing counters unavailable. Report first/repeat passes and
their observed reuse separately. Any pooled means/confidence exports are descriptive
and must not be treated as stable-performance confidence or an isolated MTP effect.
The new driver checks generated-input hashes against corresponding MTP=1/3 trials.
Three sampled concurrency points from the old rounds already have identical inputs.

## Preflight evidence and durable execution

Before launch, Docker had no running containers, port30000 had no listener, GB10
reported0% utilization and36C, and the artifact filesystem had2.6TB free. The pinned
ARM64 image and source cache volumes exist; cached AIPerf reports0.12.0. The launch
script passes bash syntax checking, and Python drivers parse. Offline cache analysis
is checked against saved trial data before installation. Full API/telemetry
qualification gates the measured sweep; startup success is not yet claimed here.

Exact commands, plan, raw client requests/inputs/aggregates, GPU telemetry, all
available SGLang exports, estimated-TFLOPS deltas, server logs, per-trial cache reports,
and checksums stay in this unique external archive. Historical data is untouched.
The systemd driver stops its owned container on completion, failure or cancellation;
ExecStopPost provides independent cleanup. A 30-minute timer records observations,
and a final monitor check stops the timer after verified shutdown. An eight-hour
runtime limit is a failure backstop, not the benchmark measurement duration.

## Interpretation and lesson

This round aligns MTP=2's sampling and repeated-prompt procedure with MTP=1/3.
Different available cache capacity, observed cache reuse and thermals still require
disclosure. The historical MTP-disabled round remains unmatched. Match both the
client procedure and measured server state before making a causal speedup claim.
