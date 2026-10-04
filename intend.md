# Serving intent

The system should provide useful, reliable inference to individual users under
concurrent load. **Maximum total token throughput is not the sole objective.**
Serving capacity is valuable when users receive acceptable generation speed,
waiting time and response latency, including users receiving the slowest service.

This document defines the intent for serving decisions across models, inference
engines and hardware targets. [The benchmarking guide](docs/BENCHMARKING.md)
defines how to measure and compare those decisions.

## What to optimize

Choose configurations that meet the workload's user-experience and correctness
requirements, then improve sustainable capacity and resource efficiency within
those requirements. A higher aggregate tokens/s number alone does not establish
a better production configuration.

For interactive generation, consider the following together at every tested
concurrency:

- **Per-user decode speed:** the lowest observed request-average rate, the mean,
  and the distribution where the sample size supports it.
- **Time to first token and queueing:** how long users wait before an answer
  starts, including requests waiting above the server's admission limit.
- **Full-response latency:** how long users wait for the complete answer,
  including slow responses rather than only the mean.
- **Reliability and output quality:** successful completions, errors, timeouts,
  cancellations and relevant correctness or quality checks.
- **Aggregate throughput:** total useful output completed by the service,
  interpreted alongside all the user-level measurements above.

For embedding and other workloads, apply the same intent using their relevant
per-request latency, correctness and throughput metrics.

## How to select a serving configuration

Define the intended workload and acceptable user-level service targets before
claiming production suitability. This document does not set a universal minimum
decode rate or latency threshold. If targets have not been specified, report
the measured tradeoffs and leave suitability unqualified.

Choose concurrency and server admission from the range that satisfies those
targets. A throughput peak is an observation, not an automatic admission setting.
When added concurrency produces little extra capacity but materially increases
waiting or slows individual users, favor the lower-concurrency operating point
unless the workload's stated targets justify the tradeoff. Distinguish client
concurrency, effective server admission and queued requests in the assessment.

Evaluate performance changes together with their quality implications. Changes
to quantization, recurrent-state precision, runtime or speculative decoding must
retain the relevant quality evidence and disclose what remains unqualified.

## Checkpoint provenance and optimization intent

Prefer official upstream weights and traceable tooling. For the Qwen NVFP4
work, retain NVIDIA's official target as the primary model and Inco's official
BF16 DFlash2 drafter as the reference. Investigate whether a reproducible local
NVFP4 conversion of that drafter can reduce memory use and improve individual
decode performance without sacrificing quality or reliability. NVIDIA Model
Optimizer is the intended conversion tool; the resulting weights would be our
derived artifact, not an official NVIDIA or Inco release.

Keep the target fixed when measuring a drafter change. Record source revisions,
conversion code, calibration data and output checksums so that the derivation can
be inspected and repeated. Preserve existing MTP and BF16 DFlash2 profiles for
switching and comparison. A different target, such as RadixArk, is a separate
comparison with its own matched baseline.

Lower memory use is useful evidence, but does not by itself demonstrate faster
decoding or justify deployment. Judge a derived drafter by acceptance, task
quality, reliability and the same user-level performance priorities above.
The [two-checkpoint build spec](models/qwen3.8-27b-nvfp4/sglang/targets/dgx-spark/quantized-drafter-spec.md)
covers creation of max-calibrated and Local-Hessian NVFP4 drafters with minimal
loading/generation checks. Performance evaluation and serving selection follow
later; producing the checkpoints alone does not qualify either for deployment.

## How to interpret the evidence

Report the slowest observed user's decode rate at every concurrency alongside
aggregate throughput. A request-average decode rate excludes time before the
first token, so it must be accompanied by waiting and full-response metrics.

An observed minimum is not a guaranteed service floor. State request counts,
selected trials, cache conditions and configuration differences; retain each
trial's minimum when reporting the lowest request across multiple trials. Tail
claims and production guarantees require evidence appropriate to those claims.
