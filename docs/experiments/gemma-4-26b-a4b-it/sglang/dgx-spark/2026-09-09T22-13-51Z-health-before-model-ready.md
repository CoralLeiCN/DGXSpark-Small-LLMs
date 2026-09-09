# 2026-09-09T22:13:51Z — Health connection refused during model initialization

Run ID: `RUN-0006`

- Status: resolved
- Phase: model load and health check
- Related turns: [Service starting during inspection](2026-09-09T22-09-18Z-status-inspection-host-access.md)
- Repo revision: `75d9507c01e340b3f0873856449ff9301b44e130`, dirty
- Host/GPU: DGX Spark target; engine reported 124610 MiB device memory
- Container: `dgxspark/gemma-4-26b-a4b-it-sglang:0.1.0`
- Engine: SGLang; installed version not queried in this turn
- Model: `google/gemma-4-26B-A4B-it`, cached revision `4d7ae4984b7db7de8f8457170b3f1a419ee76d52`; dtype auto, quantization unset
- Settings: context 32768, static memory fraction 0.75, maximum running requests 4, metrics enabled

## Command

```bash
# User's remote probe:
curl -f http://192.168.1.220:30000/health
# Diagnostic probes from the Spark and inside the container:
curl --silent --show-error --connect-timeout 3 --max-time 5 http://127.0.0.1:30000/health
curl --silent --show-error --connect-timeout 3 --max-time 5 http://192.168.1.220:30000/health
docker exec dgxspark-gemma-4-26b-a4b-it-sglang-1 curl --silent --show-error --connect-timeout 2 --max-time 3 http://127.0.0.1:30000/health
```

## Error Or Observation

```text
Remote/LAN: curl: (7) Failed to connect to 192.168.1.220 port 30000
Host loopback: curl: (56) Recv failure: Connection reset by peer
Container loopback: curl: (7) Failed to connect to 127.0.0.1 port 30000
Docker: running, health starting, Restarts=0
Started=2026-09-09T22:09:02.440576827Z
22:14:32 Load weight end. elapsed=292.96 s, mem usage=46.02 GB.
22:15:19 The server is fired up and ready to roll!
```

Startup also logged failure to obtain memory capacity through nvidia-smi and a
successful fallback to torch.cuda.mem_get_info(). Optional torchcodec imports
were unavailable. Neither prevented text-server readiness; audio was not tested.

## Diagnosis

SGLang had not opened its HTTP listener while loading and initializing the model.
Docker published port 30000 on all host IPv4/IPv6 interfaces, and host `ss`
showed listeners, but the internal API also refused connections. The scheduler
was active at approximately 98% CPU. Successful readiness after initialization
supports startup delay as the server-side cause. Remote client routing and
firewall behavior were not independently tested.

## Fix Or Change

Waited for initialization; made no runtime or configuration changes. Cached
weights took about 293 seconds to load, and total time from container start to
server readiness was about six minutes seventeen seconds.

## Verification

```bash
curl --silent --show-error --connect-timeout 2 --max-time 5 \
  --output /dev/null --write-out 'LAN HTTP %{http_code}\n' \
  http://192.168.1.220:30000/health
```

Final result from the Spark: `LAN HTTP 200`. Logs also showed successful health,
model listing, and chat requests from other callers; this investigation did not
submit a chat request. The user's remote retry remains unobserved.

## Lesson

A published Docker port does not establish application readiness. Check the
internal listener and startup logs before attributing connection refusal to LAN
configuration, and allow model initialization to finish before inference.

## Next Step

Retry the same health URL from the user's machine. Investigate the client-to-host
network path only if it still fails while the Spark's own LAN probe succeeds.
