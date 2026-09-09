# 2026-09-09T23:13:53Z — Mixed stream modes expose dashboard aggregation gap

Run ID: `RUN-0010`

- Status: open
- Phase: inference validation
- Related turns: [Initial monitoring qualification](2026-09-09T22-19-44Z-shared-monitoring-qualified.md)
- Repo revision: `75d9507`, dirty, branch `codex/shared-inference-monitoring`
- Host/GPU: DGX Spark, NVIDIA GB10, ARM64
- Container: `dgxspark/gemma-4-26b-a4b-it-sglang:0.1.0`
- Engine: existing SGLang `0.0.0.dev1+g5f55db35e`
- Model: `google/gemma-4-26B-A4B-it`, revision `4d7ae4984b7db7de8f8457170b3f1a419ee76d52`, BF16
- Monitoring: Prometheus 3.13.3, Grafana 13.2.1

## Command

```bash
INFERPACK_MONITORING_TESTS=1 uv run --python 3.12 --env-file monitoring/.env pytest models/gemma-4-26b-a4b-it/sglang/targets/dgx-spark/tests/test_monitoring.py -v -s
```

## Error Or Observation

The live test failed after 56.25 seconds because a dashboard query returned a
non-finite value. Direct Prometheus inspection showed **Time to first token
(mean)** contained an active non-streaming series with value 2.175871 and an
idle streaming series with value NaN. Both had the same dashboard legend.
Output counters were similarly split: non-streaming 1227 and streaming 13.
Inference, counter advancement, and positive throughput checks passed before
the failed finite-value assertion. Ordinary tests passed: 10 passed, 5 skipped.

## Diagnosis

This runtime adds `is_streaming` labels to token and TTFT metrics. After streaming
traffic had occurred, the dashboard queried the two modes separately but omitted
the mode from its legend. Dividing zero histogram rates for an idle mode produced
NaN even when another mode was active. Initial qualification had only one mode.

## Fix Or Change

Aggregate token counters and rates by environment, model, and instance. Calculate
latency from aggregated histogram sums/counts and filter out zero observation
rates. The updated queries have been written; verification follows in a new turn.
The model and monitoring services remain running without a restart.

## Verification

Direct exporter and Prometheus inspection confirmed separate stream labels.
Live validation of the corrected queries remains pending.

## Lesson

Dashboard aggregation must account for exporter labels added by real traffic.
Combine histogram sums and counts before division, and treat idle latency as
missing data rather than zero or an undefined value.

## Next Step

Add query regression coverage for active/idle stream modes and rerun live validation.
