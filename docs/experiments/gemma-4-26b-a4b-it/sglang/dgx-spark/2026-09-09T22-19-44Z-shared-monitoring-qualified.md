# 2026-09-09T22:19:44Z — Shared Prometheus and Grafana qualified with Gemma

Run ID: `RUN-0008`

- Status: resolved
- Phase: inference and monitoring validation
- Related turns: [Latency metric mismatch](2026-09-09T22-17-09Z-monitoring-latency-metric-mismatch.md), [Host preflight](2026-09-09T22-08-47Z-monitoring-host-preflight.md)
- Repo revision: `75d9507`, dirty; branch `codex/shared-inference-monitoring`
- Host/GPU: DGX Spark, aarch64, NVIDIA GB10
- Container: `dgxspark/gemma-4-26b-a4b-it-sglang:0.1.0`, ID `sha256:4bde4f8674ed491b836729305fac25eb42c3122357750ccbe77b5867b5c2a13d`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, PyTorch `2.13.0+cu130`, Transformers `5.12.1`
- Model: `google/gemma-4-26B-A4B-it`, revision `4d7ae4984b7db7de8f8457170b3f1a419ee76d52`, BF16
- Prometheus: `prom/prometheus:v3.13.3`, ARM64, digest `sha256:6976aa8a60fec930796ce5772b8d12da7a318a5daa8d40d69c5c7819a05eeed7`
- Grafana: `grafana/grafana:13.2.1`, ARM64, digest `sha256:f772d434e8fab0049deb2b1b30abd43342bcfca1537614aa8d36080232cf4283`

## Command

```bash
curl -fsS http://127.0.0.1:30000/metrics | rg '^sglang:inter_token_latency_seconds_(sum|count)'
uv run --no-project --python 3.12 python /tmp/inferpack-monitoring-verify.py
docker compose -f monitoring/compose.yaml ps
```

The temporary validation script repeats the prior turn's three non-streaming
chat requests and uses local credentials without printing them. Requests ask for
about 100 words explaining sky color, leaf color changes, and Moon phases, with
`max_tokens=160`, `temperature=0`, and thinking disabled. It compares output
counters, verifies an `up=1` dev target, and queries all ten provisioned dashboard
expressions through Grafana's Prometheus data-source proxy. Grafana reloaded the
corrected dashboard from disk before the test; the model was not restarted.

## Error Or Observation

The runtime exports `sglang:inter_token_latency_seconds`, with nonzero sum/count
observations after the first test. It does not export the dashboard's previous
`sglang:time_per_output_token_seconds` name. After correction, all ten panels
returned finite values through Grafana. The earlier latency-panel failure is
resolved.

## Diagnosis

The missing panel was a metric-name compatibility issue, not a scrape, network,
authentication, or model failure. Direct `/metrics` inspection established the
available histogram. Both the token-counter delta and queried rate now agree
across the model exporter, Prometheus, and Grafana.

## Fix Or Change

The dashboard's final panel now uses the mean of
`sglang:inter_token_latency_seconds` and is labelled **Inter-token latency (mean)**.
The monitoring guide records this pinned-runtime assumption. One shared stack
uses environment/model filters; only the selected Gemma service is configured,
with `environment=dev`. No artificial prod endpoint is registered.

## Verification

- Existing repository inference validation: `DGX Spark Gemma ready`.
- Promtool configuration, monitoring YAML/JSON, and Compose validation passed.
- Grafana login, database, file-provisioned dashboard, and Prometheus data source passed.
- Counter before final requests: 364; after: 713; delta: 349.
- Final API output counts: 115 + 118 + 116 = 349, exactly matching the counter delta.
- Request wall times: 4.892, 5.039, and 4.925 seconds.
- Prometheus and Grafana proxy both reported 4.628571 output tokens/second over a 2-minute rate window.
- This rate includes idle time and earlier requests; it is a monitoring observation, not a sustained-throughput benchmark.
- All ten panel queries passed with dev/model filters, including both latency histograms.
- A prod selector returned no target, as expected.
- Prometheus, Grafana, and Gemma are left running and healthy; Gemma has zero restarts and no OOM.

Persistent named volumes and restart policies are configured. This turn did not
perform a destructive storage test or a host reboot. Local credentials remain
in ignored `monitoring/.env`, and neither commands nor this journal contain them.

## Lesson

Validate dashboard semantics through the same Grafana data-source path users
rely on, and compare exporter counter deltas with actual API usage. Keep runtime
metric-name differences in the operational guide rather than silently showing
empty panels.

## Next Step

None for the resolved validation. Add a real prod endpoint to target discovery
when a production service is available.
