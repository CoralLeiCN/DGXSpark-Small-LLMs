# 2026-09-09T22:09:18Z — Status inspection requires host access

Run ID: `RUN-0005`

- Status: resolved
- Phase: preflight
- Related turns: [Earlier host-access observation](2026-09-09T22-08-47Z-monitoring-host-preflight.md)
- Repo revision: `75d9507c01e340b3f0873856449ff9301b44e130`, dirty
- Host/GPU: DGX Spark target; GPU not queried in this inspection
- Container: `dgxspark/gemma-4-26b-a4b-it-sglang:0.1.0`
- Engine: SGLang; installed version not queried
- Model: `google/gemma-4-26B-A4B-it`; revision and dtype not queried

## Command

```bash
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
```

## Error Or Observation

```text
permission denied while trying to connect to the docker API at unix:///var/run/docker.sock
```

## Diagnosis

The sandbox could not access Docker. The same read-only command succeeded with
approved host execution, confirming an access boundary rather than an engine failure.

## Fix Or Change

Repeated Docker inspection with approved host access. This investigation made
no runtime changes.

## Verification

The command first reported the Gemma container healthy and up three hours.
During subsequent inspection the service changed to starting; the final
`docker ps --filter name=dgxspark-gemma-4-26b-a4b-it-sglang-1` reported it up
15 seconds with host port 30000 published. The cause of the intervening runtime
change was not investigated. Starting is not an observed health-check failure.
Container environment confirmed context 32768, memory fraction 0.75, and maximum
running requests 4. No inference request was made.

## Lesson

Use approved host access for Docker inspection and refresh status when concurrent
runtime changes make earlier observations stale.

## Next Step

None for the resolved inspection permission failure.
