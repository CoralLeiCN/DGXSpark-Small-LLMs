# 2026-09-14T22:30:07Z — Input throughput and API-equivalent value of the measured peak

Run ID: `RUN-0020`

- Status: resolved
- Phase: analysis of existing inference exports; no new inference run
- Related turn: [Confirmed throughput peak](2026-09-14T22-17-48Z-mtp-throughput-peak-confirmed.md)
- Environment: unchanged RUN-0019 measurements, one DGX Spark GB10,
  SGLang `0.0.0.dev1+g5f55db35e`, Qwen3.8 27B FP8 with native MTP,
  model revision `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a`

## Method And Measured Rates

Read `profile_export_aiperf.json` and per-request exports for the two
concurrency-64 profiles in RUN-0019. Use arithmetic means of the reported
`input_token_throughput`, `output_token_throughput`, and `request_throughput`.
Verified input counts against each request's server-reported prompt-token usage.
Calculation used uv-managed Python 3.12; no service was started.

| Metric | Seed 3000 | Seed 5000 | Mean |
| --- | --- | --- | --- |
| Input tokens/s | 850.85634 | 847.27346 | **849.06490** |
| Output tokens/s | 207.79010 | 206.91409 | **207.35210** |
| Total tokens/s | 1058.64644 | 1054.18755 | **1056.41700** |
| Requests/s | 1.62336 | 1.61652 | **1.61994** |

Each profile contained 384 measured requests, after 96 excluded warmups.
Input totals were 201,267 and 201,268; each output total was 49,152.
Mean input length was approximately 524.13 tokens, with 128 output tokens.
These input rates average over the full mixed prefill/decode workload. They
do not measure isolated maximum prefill capacity.

## Price References And Calculation

Provider pages checked on 2026-09-14, prices in USD per million tokens:

- [Alibaba Model Studio official pricing](https://www.alibabacloud.com/help/en/model-studio/model-pricing):
  `qwen3.8-27b`, Singapore / International deployment, non-thinking and thinking,
  standard uncached input $0.50, output $3.00. The
  [QwenCloud model page](https://www.qwencloud.com/models/qwen3.8-27b) agrees.
- [EmpirioLabs model pricing](https://empiriolabs.ai/models/qwen3-8-27b):
  advertised current pay-as-you-go input $0.17, output $0.50.
  This provider was not benchmarked or qualified for service equivalence.

```text
input million tokens/hour = 849.064900275891 * 3600 / 1,000,000 = 3.05663364
output million tokens/hour = 207.35209707162835 * 3600 / 1,000,000 = 0.74646755
gross equivalent USD/hour = input_M/hour * input_price + output_M/hour * output_price
```

| Reference | Input value/hour | Output value/hour | Total/hour | Total/day | Total/30 days |
| --- | --- | --- | --- | --- | --- |
| Alibaba International | $1.53 | $2.24 | **$3.77** | $90.43 | $2,712.76 |
| EmpirioLabs advertised rates | $0.52 | $0.37 | **$0.89** | $21.43 | $642.86 |

Daily/monthly figures extrapolate 24/7 useful traffic at the measured workload
and rate; the short benchmark did not establish sustained monthly capacity.
At 50% equivalent full-load utilization, monthly gross values become $1,356.38
and $321.43. Idle gaps scale this model directly; serving at lower concurrency
requires the corresponding measured rate instead of assuming linear scaling.

These are API-spend equivalents or hypothetical gross billing at the stated
rates. Revenue requires paying demand; savings require replacing actual API
usage. Profit additionally subtracts electricity, hardware depreciation,
networking, operations, and other costs. Cache/batch discounts, free quotas,
promotions, regional rates, provider quantization/features, and workload changes
can alter the comparison. No hardware payback or profit is established here.

## Verification And Artifacts

The reported input rate equals request throughput times mean prompt length,
and input plus output rates equal reported total throughput in each profile.
No runtime or inference failures occurred in this analysis.
The calculation script and JSON are saved under the ignored pack directory
`artifacts/2026-09-14T22-30-07Z-token-economics/`.

## Lesson And Next Step

Price input and output separately using the same measured workload. Keep
API-equivalent gross value distinct from realized revenue, savings, and profit.
Next step: none for this requested rate and price comparison.
