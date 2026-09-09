# 2026-09-09T22:24:22Z — Grafana remote access narrowed to Tailscale

Run ID: `RUN-0009`

- Status: resolved
- Phase: monitoring container configuration
- Related turns: [Shared monitoring qualified](2026-09-09T22-19-44Z-shared-monitoring-qualified.md)
- Repo revision: `75d9507`, dirty; `codex/shared-inference-monitoring`
- Host/GPU: remote DGX Spark; no GPU changes
- Container: `grafana/grafana:13.2.1`; Prometheus `3.13.3`
- Engine/model: existing Gemma 4 26B A4B SGLang service unchanged; no inference repeated

## Command

```bash
docker compose -f monitoring/compose.yaml up -d --no-deps --wait --wait-timeout 60 grafana
```

## Error Or Observation

The user could not reach the remote host through a browser-local localhost URL.
Automatic approval review rejected the initial proposed `0.0.0.0` Grafana bind
because it would expose authenticated HTTP on every IPv4 interface. That command
was not executed. This was an approval boundary, not a Grafana startup failure.

## Diagnosis

The deployed Grafana port was bound to the remote host's loopback. The browser
needed a reachable address. The host also has a private Tailscale interface,
allowing narrower remote access without exposing the LAN interface.

## Fix Or Change

Added independent `GRAFANA_BIND_ADDRESS` configuration. Set the ignored local
`.env` to the host's Tailscale IPv4 address and recreated Grafana only. The narrower
operation was approved. Login stays enabled, data stays in its persistent volume,
and Prometheus remains on loopback. Updated the operational guide and spec.

## Verification

```bash
curl -fsS --max-time 10 http://100.127.217.100:3000/api/health
docker compose -f monitoring/compose.yaml ps
```

Grafana reports database `ok`, version `13.2.1`, and healthy status with port
`100.127.217.100:3000`. Prometheus is healthy on `127.0.0.1:9090`.
The client must connect to the same tailnet; its connectivity was not inspected.

## Lesson

Remote browser URLs must use a reachable server address. Separate Grafana's
bind setting from Prometheus so remote dashboard access does not also expose
the unauthenticated metrics service.

## Next Step

Open the dashboard from a client connected to the host's tailnet.
