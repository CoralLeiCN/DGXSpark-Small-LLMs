# 2026-09-13T22:45:13Z — AIPerf throughput plateaus under the four-request server limit

Run ID: `RUN-0006`

- Status: resolved
- Phase: inference / performance validation
- Related turns: [initial concurrency baseline](2026-09-13T22-08-12Z-aiperf-concurrency-baseline.md),
  [server startup and versions](2026-09-13T22-00-25Z-gemma-started-for-aiperf.md)
- Repo revision: `0d0acca2289c8d0475ba3c8dab76b366e4f150da`, dirty with
  benchmark documentation and journals
- Host/GPU: one DGX Spark, Linux aarch64; client on the same host over loopback
- Container: `dgxspark/gemma-4-e4b-it-sglang:0.1.0`, same running container as
  RUN-0005; no restart or configuration change in this turn
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, torch `2.13.0+cu130`,
  transformers `5.12.1`, as recorded at startup
- Model: `google/gemma-4-E4B-it`, revision
  `ee0ef6023621cff504d758262d4e04895a5af4a2`, BF16
- Launch: context 32768, memory fraction 0.85, max running requests 4,
  TP 1, Triton attention, default non-thinking text generation
- Client: AIPerf `0.12.0`, uv `0.9.7`, managed CPython `3.12.12`

## Command And Stopping Rule

The user requested concurrency 6, 8, or 12 and continued increases until total
output throughput became stable. Kept the current endpoint configuration and
explicitly distinguished client concurrency from the four-active-request
scheduler limit. Reran concurrency 4 with the same larger sample as the new
settings to make comparisons consistent.

Used a practical stopping criterion of less than 5% throughput change across
two successive concurrency increases. Tested 12 as requested even after 4, 6,
and 8 satisfied that criterion. No higher client concurrency was needed once
12 confirmed the same throughput. This criterion is an operational heuristic,
not a statistical confidence test.

```bash
benchmark_root=/tmp/aiperf-gemma-e4b/2026-09-13T22-34-15Z-plateau
for concurrency in 4 6 8 12; do
  uv tool run --managed-python --python 3.12 --from aiperf==0.12.0 aiperf profile \
    --url http://127.0.0.1:30000 \
    --model gemma-4-e4b-it --tokenizer google/gemma-4-E4B-it \
    --endpoint-type chat --endpoint /v1/chat/completions \
    --streaming --use-legacy-max-tokens --use-server-token-count \
    --synthetic-input-tokens-mean 512 --synthetic-input-tokens-stddev 0 \
    --output-tokens-mean 128 --output-tokens-stddev 0 \
    --extra-inputs '{"temperature":0,"ignore_eos":true}' \
    --concurrency "$concurrency" --warmup-request-count 12 --request-count 96 \
    --random-seed "$((1000 + concurrency))" \
    --no-server-metrics --no-gpu-telemetry --ui-type none \
    --artifact-dir "$benchmark_root/c$concurrency" || break
done
```

The runner used the same isolated uv directories and disabled implicit Hugging
Face credentials as RUN-0005. Console output was saved to `c4.log`, `c6.log`,
`c8.log`, and `c12.log` beside the profile directories. Model-serving packages
remained in the model container.

## Results

| Client concurrency | Output tokens/s | Change from preceding setting | TTFT p50 / p95 (s) | Request latency p50 / p95 (s) | ITL mean (ms) | Measured duration (s) |
| --- | --- | --- | --- | --- | --- | --- |
| 4 | 89.2847 | baseline | 0.399 / 0.402 | 5.733 / 5.765 | 41.99 | 137.62 |
| 6 | 89.0859 | -0.22% | 0.405 / 6.172 | 5.772 / 11.535 | 42.08 | 137.93 |
| 8 | 89.0301 | -0.06% | 6.156 / 6.176 | 11.494 / 11.541 | 42.11 | 138.02 |
| 12 | 89.1000 | +0.08% | 11.888 / 11.950 | 17.224 / 17.295 | 42.07 | 137.91 |

All four profiles completed 96 measured requests and 12 warmups without errors
or cancellations. Every response contained exactly 128 server-reported output
tokens; each measured profile produced 12288 output tokens. Input lengths
ranged from 520 to 522 tokens after formatting. Aggregate throughput, rather
than the fixed total generated-token count, was the plateau measure.

Measured UTC windows were approximately 22:34:36–22:36:54 (c4),
22:37:18–22:39:36 (c6), 22:39:59–22:42:17 (c8), and
22:42:41–22:44:59 (c12). Exported local timestamps use Europe/London and are
one hour ahead of UTC on this date, as in RUN-0005.

## Diagnosis

Throughput varied by less than 0.3% across all four settings and stayed around
89 output tokens/s. Higher client concurrency increased queueing rather than
active batch size. Runtime logs directly showed:

```text
2026-09-13 22:38:18 Decode batch, #running-req: 4, ... #queue-req: 2
2026-09-13 22:44:02 Decode batch, #running-req: 4, ... #queue-req: 8
```

At concurrency 6, some requests started promptly and others waited for the
next batch, so the median alone understates the latency penalty; p95 exposes
it. At 12, median response time was roughly three times the concurrency-4
median with unchanged throughput.

This establishes the plateau of the existing `MAX_RUNNING_REQUESTS=4`
configuration. It does not establish maximum DGX Spark throughput with more
than four active requests. Testing that requires raising the server's limit,
recreating the service, and running a distinct comparison.

## Verification And Limits

Parsed all aggregate JSON exports and per-request JSONL records. Verified
384 measured requests plus 48 warmups, no errors or cancellations, and the
expected output count for every request. Gemma remained healthy on port 30000
after the sweep. No errors, exceptions, tracebacks, or HTTP 4xx/5xx matched
the benchmark-interval runtime logs. Qwen was not restarted.

A temporary summary helper initially tried to interpret the console filename
`c4.log` as a concurrency number. Filtering to directories before sorting
fixed that local analysis error; it did not affect AIPerf or serving, and the
corrected helper verified all four completed exports.

Each setting was measured once with fixed synthetic lengths and forced output
length (`ignore_eos`), after warmup. Prefix caching remained enabled; SGLang
logs showed cached prefix tokens, while AIPerf again warned that structured
cache-hit reporting was unavailable. Seeds differed between settings. GPU and
server telemetry were disabled, and background host activity was not quantified.
The result does not measure natural stopping, remote network latency, other
sequence lengths, or production sustained-load capacity.

## Artifacts

Local reports are under
`/tmp/aiperf-gemma-e4b/2026-09-13T22-34-15Z-plateau/`:

- `c4/`, `c6/`, `c8/`, `c12/`: aggregate JSON/CSV, per-request JSONL,
  inputs, phase exports, and logs
- `c4.log`, `c6.log`, `c8.log`, `c12.log`: console output and CLI settings
- `summary.json`: selected verified metrics

These temporary artifacts may be cleaned up; this journal preserves the
configuration and measured summary. The model README includes the main results.

## Lesson And Next Step

Check both client concurrency and the server's active-request limit when
interpreting a throughput plateau. Under the current settings, concurrency 4
achieves the measured ceiling with the lowest queueing latency. The requested
sweep is complete, and Gemma remains running with its original settings.
