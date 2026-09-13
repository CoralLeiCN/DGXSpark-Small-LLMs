# 2026-09-13T22:08:12Z — AIPerf concurrency baseline qualified

Run ID: `RUN-0005`

- Status: resolved
- Phase: inference / performance validation
- Related turns: [client setup](2026-09-13T21-46-37Z-aiperf-client-preflight.md),
  [live Gemma startup](2026-09-13T22-00-25Z-gemma-started-for-aiperf.md)
- Repo revision: `0d0acca2289c8d0475ba3c8dab76b366e4f150da`, dirty with
  benchmark documentation and journal changes
- Host/GPU: one DGX Spark, Linux aarch64; client on the same host via loopback
- Container: `dgxspark/gemma-4-e4b-it-sglang:0.1.0`, image
  `sha256:326c8aa85e4ac705f9e7ed17ea19ac079851a56c97cfc87bb9a9715a968baf41`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, torch `2.13.0+cu130`,
  transformers `5.12.1`
- Model: `google/gemma-4-E4B-it`, revision
  `ee0ef6023621cff504d758262d4e04895a5af4a2`, BF16, no speculative decoding
- Launch: TP 1, Triton attention, context 32768, memory fraction 0.85,
  maximum running requests 4, Gemma 4 reasoning/tool parsers, no extra flags
- Client: AIPerf `0.12.0`, uv `0.9.7`, uv-managed CPython `3.12.12`
- Client tokenizer: `google/gemma-4-E4B-it`, no revision override; metric token
  counts came from the server's streaming usage fields

## Command

Executed one sequential comparison of concurrency 1, 2, and 4. AIPerf ran in
an isolated uv tool environment. Local setup used writable directories
`UV_TOOL_DIR=/tmp/codex-aiperf-tools`,
`UV_CACHE_DIR=/tmp/codex-aiperf-uv-cache`, and
`UV_PYTHON_INSTALL_DIR=/tmp/codex-aiperf-python`, with
`HF_HUB_DISABLE_IMPLICIT_TOKEN=1`.

```bash
benchmark_root=/tmp/aiperf-gemma-e4b/2026-09-13T22-00-25Z
for concurrency in 1 2 4; do
  uv tool run --managed-python --python 3.12 --from aiperf==0.12.0 aiperf profile \
    --url http://127.0.0.1:30000 \
    --model gemma-4-e4b-it \
    --tokenizer google/gemma-4-E4B-it \
    --endpoint-type chat \
    --endpoint /v1/chat/completions \
    --streaming \
    --use-legacy-max-tokens \
    --use-server-token-count \
    --synthetic-input-tokens-mean 512 \
    --synthetic-input-tokens-stddev 0 \
    --output-tokens-mean 128 \
    --output-tokens-stddev 0 \
    --extra-inputs '{"temperature":0,"ignore_eos":true}' \
    --concurrency "$concurrency" \
    --warmup-request-count 4 \
    --request-count 32 \
    --random-seed "$((42 + concurrency))" \
    --no-server-metrics \
    --no-gpu-telemetry \
    --ui-type none \
    --artifact-dir "$benchmark_root/c$concurrency" || break
done
```

The executed Bash runner stopped on failure and saved each profile's console
output to `c1.log`, `c2.log`, or `c4.log` beside the artifact directories.

## Observation

All profiles exited successfully. Each completed four warmups and 32 measured
requests, with no errors, cancellations, or output-length mismatches. Actual
input lengths were 521–522 tokens after chat formatting; every measured output
contained 128 tokens, totaling 4096 output tokens per profile. Thinking followed
the server-detected default `enable_thinking=False`.

| Concurrency | TTFT p50 / p95 (ms) | Request latency p50 / p95 (s) | ITL mean (ms) | Aggregate output tokens/s | Requests/s | Measured duration (s) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 154.91 / 156.54 | 6.540 / 6.572 | 50.29 | 19.56 | 0.1528 | 209.43 |
| 2 | 231.03 / 232.79 | 5.548 / 5.564 | 41.81 | 46.17 | 0.3607 | 88.71 |
| 4 | 400.35 / 401.35 | 5.748 / 5.768 | 42.10 | 89.04 | 0.6956 | 46.00 |

Per-user decode throughput averaged 19.88, 23.92, and 23.76 tokens/s,
respectively. Aggregate output throughput includes all simultaneous responses
over the measured window; it is distinct from per-user decode speed.

Measured UTC windows were approximately 22:00:58–22:04:27 (c1),
22:04:46–22:06:15 (c2), and 22:06:27–22:07:13 (c4). AIPerf's exported
`start_time` and `end_time` strings are local Europe/London time without an
offset, one hour ahead of UTC on this date. The journal and artifact directory
timestamps use UTC.

## Diagnosis And Limits

Concurrency 4 produced 4.55 times the concurrency-1 aggregate throughput in
this comparison, at a higher TTFT. Concurrency 2 had the lowest measured
end-to-end latency. The measurements alone do not isolate the kernel-level
reason for the improved decode speed at batch sizes above one.

This is a short synthetic baseline with a fixed output length forced by
`ignore_eos`, not a natural-stopping, long-context, multimodal, or sustained
production-capacity benchmark. Each concurrency had one profile and 32 measured
requests; the reported tail percentiles have limited statistical support.
Warmups were excluded from profile metrics. The profile order was 1, 2, 4;
there was no randomized order or repeated-run confidence analysis.

SGLang's prefix cache remained enabled and was not flushed. Different seeds
(43, 44, 46) reduced exact prompt reuse between profiles. AIPerf warned:

```text
Token usage is reported but no prompt-cache read tokens were seen
(usage.prompt_tokens_details.cached_tokens absent).
```

The recipe does not enable `--enable-cache-report`, so cache-hit counts were
unavailable. This warning does not indicate failed inference and does not
establish that caching was absent. Server metrics and GPU telemetry were
explicitly disabled; no GPU utilization, power, temperature, or hardware
efficiency conclusions are supported. Qwen was stopped and Gemma was the only
running Docker container; host background activity was not independently
quantified. Loopback timing excludes a remote client's network latency.

## Verification And Artifacts

Parsed all three aggregate JSON exports and all per-request JSONL records.
Verified 96 measured requests plus 12 warmups, no errors or cancellations,
and exactly 128 server-reported output tokens per request. Post-benchmark
`GET /health` succeeded. Docker reported Gemma healthy on port 30000 and Qwen
exited. No error, exception, traceback, or HTTP 4xx/5xx matched the Gemma
runtime logs during the benchmark interval.

Local artifacts are under
`/tmp/aiperf-gemma-e4b/2026-09-13T22-00-25Z/`:

- `c1/`, `c2/`, `c4/`: aggregate `profile_export_aiperf.json` and CSV,
  per-request `profile_export.jsonl`, generated inputs, phase exports, and logs
- `c1.log`, `c2.log`, `c4.log`: console output and complete CLI settings
- `summary.json`: selected metrics extracted from the verified aggregate exports

Temporary artifacts are local and may be cleaned up; this journal preserves the
measured summary and configuration. The model README contains the reusable
benchmark command and links to this record.

## Lesson

Specify the served API model name separately from its Hugging Face tokenizer,
use streaming for TTFT/ITL, check actual token counts, and compare aggregate
throughput with per-user latency. More concurrent requests can improve GPU
batching while increasing time to the first token.

## Next Step

None for this baseline. Gemma was left running as requested; Qwen remains
stopped. A future capacity study should use representative workloads and
repeated, longer runs with explicit cache and telemetry conditions.
