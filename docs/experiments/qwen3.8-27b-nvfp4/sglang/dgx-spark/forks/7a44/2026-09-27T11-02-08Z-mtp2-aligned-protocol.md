# 2026-09-27T11:02:08Z — NVFP4 MTP=2: protocol aligned with MTP=1/3, prepared for launch

Run ID: `RUN-0028`

- Status: open
- Phase: inference / benchmark / lifecycle
- Repo revision: `89611e1`, dirty with experiment documentation
- Host/GPU: DGX Spark, NVIDIA GB10, driver `580.173.02`, aarch64
- Image: `sha256:110ad45e7872397f337ea5714e6c97c400852938a9b8f258bcc27cab07182b0c`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`; AIPerf `0.12.0`, Python 3.12
- Model: `nvidia/Qwen3.8-27B-NVFP4`, revision `482ca0f3832238542f8f5295dde86b5f22711d80`
- Artifacts: [2026-09-27T11-00-03Z-mtp2-aligned](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T11-00-03Z-mtp2-aligned/)
- Related turns: [MTP=2 launch](../../2026-09-25T20-24-59Z-mtp2-c72-round.md); see this target index for the MTP=1/3 launch and subsequent events.

## Request and current status

The user authorized aligning MTP=2 with the newer MTP=1/3 settings after checking
AIPerf guidance. This entry records the declared plan before launch. Earlier
MTP=2 and all original results remain unchanged. Host preflight found no running
containers, GPU idle at 36 C, driver580.173.02, and the existing pinned image/cache
mounts available. The new driver passed Python syntax and shell syntax checks.
Qualification and measured results are not yet claimed; follow subsequent entries.

## Guidance and declared protocol

[AIPerf guidance](https://docs.nvidia.com/aiperf/dev/tutorials/metrics-analysis/multi-run-confidence-reporting)
recommends three trials for exploration, five for standard benchmarking, consistent
workloads/seeds, and separate initial warmup. The
[NIM worked example](https://docs.nvidia.com/nim/benchmarking/llm/1.0.0/step-by-step.html)
uses three times concurrency. Our 64-request floor and max(8,C) warmup are repository
choices, not universal NVIDIA prescriptions.

- Concurrency1,2,4,8,16,32,48,56,64,72; three trials at each.
- Each measured trial uses max(64,3*C):64,64,64,64,64,96,144,168,192,216.
- Initial warmup max(8,C), omitted in trials2/3:3,408 measured +320 warmup requests.
- AIPerf0.12.0; input target512, forced output128, streaming, temperature0,
  thinking disabled, ignore EOS, seed42+C; no convergence stopping or cooldown.
- Admission64 and256 Mamba slots, float32 state, lazy native cache, static0.90,
  FP8 e4m3 KV, context32768, chunked prefill2048. Client c72 exceeds admission.
- MTP=2 means EAGLE two drafting steps, top-k1, three verification positions.
- Same pinned image, target/draft/tokenizer revision as MTP=1/3. Exact command
  is `/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T11-00-03Z-mtp2-aligned/mtp2/launch.sh`; runtime allocations are saved during qualification.

## Cache condition and comparison limit

To align the historical procedure, retain the native cache and replay the same
prompts across three trials. This deliberately mixes first exposure and later
replays. It is allowed by the shared rules only with explicit per-condition
reporting: per-trial cache fractions and results are primary; pooled averages
are descriptive and native confidence intervals cannot establish steady-state
repeatability. Identical policy does not guarantee equal cache reuse, especially
when speculative state allocation changes available cache capacity. Save ordered
payload hashes and compare them with MTP=1/3 inputs at corresponding points.

This is an exploratory deployment comparison, not a controlled MTP-only ablation.
No additional MTP=1/3 or disabled sweep is authorized by this alignment request.

## Metrics and lifecycle

Preserve every client, GPU and SGLang export, generated inputs, commands and logs
under [2026-09-27T11-00-03Z-mtp2-aligned](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T11-00-03Z-mtp2-aligned/), outside Git. Verify all five API checks and a c4
three-trial telemetry preflight (8 measured requests/trial,4 initial warmups)
before the full sweep. This qualification count is explicitly not a performance
sample. Compute TFLOPS using interior scrape counter deltas, checking resets.
Record cache counters, NVML activity limitations, and that physical DRAM GB/s is
unmeasured; see [2026-09-27T11-02-08Z-flops-bandwidth-accounting.md](2026-09-27T11-02-08Z-flops-bandwidth-accounting.md).

Driver unit:qwen-nvfp4-mtp2-aligned-20260927.service; eight-hour safety limit.
Finally/ExecStopPost stop the owned container on completion or failure. A30-minute
systemd timer inspects state and stops itself when cleanup is verified. No live
profiling will perturb the comparable client measurements. All exceptions are
journaled, and completed artifacts are checksummed.
