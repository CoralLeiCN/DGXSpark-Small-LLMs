# 2026-09-27T14:11:53Z — Hardware pilot: omitted warmup flag replaces invalid zero

Run ID: `RUN-0036`

- Status: open (retry starting)
- Phase: AIPerf preflight / container lifecycle
- Related: [baseline launch](2026-09-27T14-07-18Z-hardware-pilot-baseline-launch.md)
- Environment: same pinned image/model/SGLang as launch; AIPerf0.12.0, Python3.12, GB10 driver580.173.02
- Artifacts: [2026-09-27T13-56-21Z-mtp2-hardware-pilot](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T13-56-21Z-mtp2-hardware-pilot/)

## Failure and diagnosis

The server started with admission64 and passed all five API checks. Available
KV capacity was393055 tokens; record this actual allocation alongside the historical
395653-token MTP=2 allocation. The separate AIPerf telemetry preflight failed before
sending its requests:

```text
aiperf profile ... --concurrency 1 --warmup-request-count 0 --request-count 4 ...
warmup_request_count: Input should be greater than 0
```

The driver incorrectly assumed explicit zero was accepted to disable warmup.
This CLI accepts a positive count when the option is supplied. The first owned
container stopped cleanly (exit0, no OOM); baseline/shutdown-verification.json
confirms it. No baseline measured trials ran. Full commands, error and smoke
responses remain unchanged under baseline/.

## Fix, retry and verification

The v2 command omits --warmup-request-count. Separate warmup invocations and the
fresh-cache reset before each measured trial are retained. scripts/baseline-v2.py
parsed successfully and was launched under nvfp4-hw-pilot-baseline-v2-20260927.service
with the same cleanup hooks. New outputs use baseline-v2/ and a distinct container.
At this entry the retry is starting; successful telemetry collection is still pending.
The normal protocol remains nine trials/960 requests at c1,c8,c64.

## Lesson

Check the pinned benchmark CLI's disabling semantics: an omitted optional count
can be valid when explicit zero is rejected. Keep the failed attempt and require
telemetry qualification before committing to measured trials.
