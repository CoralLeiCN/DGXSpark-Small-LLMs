# 2026-09-27T14:29:32Z — Hardware pilot: retain successful c1 trial after cache-check failure

Run ID: `RUN-0038`

- Status: open (remaining trials resumed)
- Phase: metric validation and container lifecycle
- Related: [qualification/scheduling](2026-09-27T14-24-57Z-hardware-pilot-qualified-and-profiling-scheduled.md)
- Environment: same pinned image/model/SGLang/AIPerf as RUN-0035; GB10 driver580.173.02
- Artifacts: [2026-09-27T13-56-21Z-mtp2-hardware-pilot](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T13-56-21Z-mtp2-hardware-pilot/)

## Observed failure

The first normal c1 trial completed64 requests without errors, but the v2
post-run verifier raised:

```text
assert metric in b and metric in a, metric
AssertionError: sglang:cached_tokens_total
```

The suite stopped at14:24:22UTC, and its container exited cleanly at14:24:37UTC
without OOM. The waiting profiler master detected the failure and launched no
profilers. RUN-0037's in-progress wording reflected the earlier status read; the
precise saved event chronology shows that this verifier failure had already
occurred when that note was written. No successful nine-trial completion was claimed.

## Diagnosis and recovery evidence

Pinned source srt/observability/metrics_collector.py reports a cached-token series
only for positive source counts, while recording each completed request's total
prompt length and prompt_tokens-cached_tokens in paired histograms. Both sources
and saved Prometheus snapshots were inspected. An initial docker cp lookup of
srt/metrics/collector.py failed with `Could not find the file`; locating the
actual observability/metrics_collector.py and copying it succeeded. The source
snapshot is saved under preflight/. This path lookup failure is unrelated to
engine execution.

Before/after total and uncached prompt histogram sums were6537 and40077 in both
cases: delta33540 tokens, with count deltas64 in both histograms. Thus all64
requests had zero observed cached prompt tokens. Missing cached-token series
was not itself treated as zero. The completed trial's other checks passed:
21.7353 output tokens/s,5.88636s mean response and4.89226 SGLang estimatedTFLOPS.
These are one-trial results, not hardware TFLOPS or a final mean.

## Fix and resumed protocol

The v3 verifier uses paired histogram sum/count deltas. It now exercises this
cache check in the four-request qualification before measured trials. The existing
v2/c1/trial1 data is retained as measured trial1; only a new derived verification
summary was added. No raw exports or failed scripts were overwritten. The v3
summary includes that row and skips rerunning it. The remaining eight trials
continue the declared c1,c8,c64 protocol for960 total measured requests.

The server restarts with the same pinned flags, requalifies and rewarms after
restart. Record the restart/thermal/allocation difference when interpreting c1
trial variation; no statistical convergence claim is made. Fresh prompt-cache
conditions remain required for every trial.

New units: nvfp4-hw-pilot-baseline-v3-20260927.service and
nvfp4-hw-pilot-profiles-v2-20260927.service. Baseline outputs are baseline-v3/;
raw successful trial1 remains in baseline-v2/c1/trial1/. The profiler master waits
for baseline-v3 completion and shutdown. At this entry the resumed server is
starting; successful remaining trials are not yet claimed.

## Lesson

Validate metric coverage in qualification, including expected zero cases. Use
paired request histograms with matched counts as independent cache evidence
when a lazy counter has no series. This rule is now in docs/BENCHMARKING.md.
