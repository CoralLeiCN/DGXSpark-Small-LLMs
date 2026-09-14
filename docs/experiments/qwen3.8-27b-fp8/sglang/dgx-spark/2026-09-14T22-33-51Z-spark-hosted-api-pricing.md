# 2026-09-14T22:33:51Z — DGX Spark hosted API and rental price references

Run ID: `RUN-0021`

- Status: resolved
- Phase: pricing research and calculation; no new inference run
- Related turn: [Measured token rates and API value](2026-09-14T22-30-07Z-token-rates-api-value.md)
- Measurement basis: RUN-0019, one GB10, SGLang `0.0.0.dev1+g5f55db35e`,
  Qwen3.8 27B FP8 native MTP, concurrency 64, approximately 524 input / 128
  output tokens per request, thinking disabled

## Primary Sources Checked On 2026-09-14

[AxForge's model page](https://axforge.ai/models/qwen-3-8-27b/) explicitly
identifies DGX Spark GB10 hardware and the API model `qwen3.8-27b-nvfp4`.
Its advertised input/output rates are €0.29/€1.77 per million tokens, excluding
VAT. The deployed quantization is NVFP4, with a 131,072-token context setting
and four configured sequences per node. These settings differ from our FP8
capacity benchmark; the provider's performance and service equivalence were
not tested.

[AxForge's price list](https://axforge.ai/pricing/) also lists dedicated Spark
rental at €0.69/hour on demand, €0.66/hour for a week, €0.62/hour for bookings
of at least 28 days, and €0.55/hour for a year, before VAT. Dedicated managed
deployment adds a separately quoted management fee.

[GPUwerk's price list](https://gpuwerk.com/pricing/) lists one dedicated Spark
at $0.79/hour, billed per minute, excluding applicable tax. This is a machine
rental rate, not a per-token API price. At that hourly rate, 720 running hours
cost $568.80. Currency conversion was not applied to the euro-denominated
AxForge prices.

## Application To Our Measured Rates

RUN-0020 established 849.064900 input tokens/s and 207.352097 output tokens/s,
equivalent to 3.056633641 million input and 0.746467549 million output tokens
per hour at the measured workload.

```text
input value/hour  = 3.056633641 * €0.29 = €0.88642
output value/hour = 0.746467549 * €1.77 = €1.32125
combined/hour    = €2.20767
combined/day     = €52.98411
combined/30 days = €1,589.52335
```

These are gross API-spend equivalents using advertised prices. Daily/monthly
figures assume continuous useful traffic at the measured rate; long-duration
capacity was not validated. Free allowances and taxes are excluded. Revenue,
profit, and replacement savings require demand, cost, and service-equivalence
assumptions beyond the benchmark. No rental was purchased or service started.

## Lesson And Next Step

Distinguish per-token hosted API rates from hourly machine rental, retain the
quoted currency, and identify quantization differences before comparing value.
Next step: none for this price lookup.
