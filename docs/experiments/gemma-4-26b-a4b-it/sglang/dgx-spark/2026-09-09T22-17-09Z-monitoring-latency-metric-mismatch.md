# 2026-09-09T22:17:09Z — Monitoring works; one latency metric differs in the pinned runtime

Run ID: `RUN-0007`

- Status: open
- Phase: model load and inference validation
- Related turns: [Monitoring host preflight](2026-09-09T22-08-47Z-monitoring-host-preflight.md)
- Repo revision: `75d9507`, dirty; branch `codex/shared-inference-monitoring`
- Host/GPU: DGX Spark, aarch64, NVIDIA GB10; 124610 MiB unified memory
- Container: `dgxspark/gemma-4-26b-a4b-it-sglang:0.1.0`, ID `sha256:4bde4f8674ed491b836729305fac25eb42c3122357750ccbe77b5867b5c2a13d`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, PyTorch `2.13.0+cu130`, Transformers `5.12.1`
- Model: `google/gemma-4-26B-A4B-it`, revision `4d7ae4984b7db7de8f8457170b3f1a419ee76d52`, BF16
- Monitoring: Prometheus `3.13.3`, Grafana OSS `13.2.1`, official ARM64 images

## Command

```bash
uv run --python 3.12 infer serve gemma-4-26b-a4b-it --engine sglang --target dgx-spark
docker compose -f monitoring/compose.yaml run --rm --no-deps --entrypoint promtool prometheus check config /etc/prometheus/prometheus.yml
docker compose -f monitoring/compose.yaml up -d --wait --wait-timeout 90
uv run --python 3.12 infer validate gemma-4-26b-a4b-it --engine sglang --target dgx-spark --timeout 600
uv run --no-project --python 3.12 python /tmp/inferpack-monitoring-verify.py
```

The temporary verifier authenticates to local Grafana using the ignored `.env`
without logging credentials, sends three short non-streaming chat requests,
checks counters and positive rates, and queries each provisioned panel through
Grafana's Prometheus proxy. Each chat request uses temperature 0, max_tokens 160,
and `chat_template_kwargs={"enable_thinking": false}`.

## Error Or Observation

```text
AssertionError: ('Output token time (mean)', [])
```

The selected runtime also logs:

```text
Failed to get GPU memory capacity from nvidia-smi. Falling back to torch.cuda.mem_get_info().
torchcodec is not installed; audio inputs will fail at request time
```

The capacity fallback succeeds with 124610 MiB. Text-only validation does not
exercise the already-documented missing audio dependency. The server began
loading at 22:09:38Z and reported ready after warmup at 22:15:19Z. Prometheus
started during model loading, so initial scrape availability was not continuous.
The model's host port 30000 was restored by Compose recreation.

## Diagnosis

The model, metrics endpoint, Prometheus target, and Grafana data source all work.
The repository validation returned `DGX Spark Gemma ready`. The three requests
returned 117, 117, and 116 completion tokens in 5.064, 5.045, and 4.995 seconds.
The verifier confirmed an increasing output counter and a positive 2-minute
rate both directly in Prometheus and via Grafana. Nine dashboard queries passed;
the output-token-time query using `sglang:time_per_output_token_seconds` returned
no series. This suggests the dashboard assumes a metric absent from this build;
inspect the actual exporter before choosing a replacement.

## Fix Or Change

No latency-panel fix has been applied in this turn. Both monitoring containers
are healthy, and Gemma serves requests with `--enable-metrics`.

## Verification

Promtool configuration validation passed. Grafana's database, login, provisioned
dashboard, and data source passed. End-to-end monitoring validation remains
incomplete because the last latency panel has no matching series.

## Lesson

Qualify every dashboard query against the exact model runtime. Metric names and
availability can differ between SGLang builds even when token counters work.

## Next Step

Inspect exported latency metrics, correct the panel, and repeat validation in a
new journal turn. No GPU/model restart is needed for a dashboard-only change.
