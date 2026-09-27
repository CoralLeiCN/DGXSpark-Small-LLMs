# 2026-09-27T15:54:02Z — Hardware pilot: preserve fixed Mamba memory and cap diagnostic KV capacity

Run ID: `RUN-0045`

- Status: open (allocator-informed retry starting)
- Phase: memory-pool configuration and startup validation
- Related: [profiling headroom attempt](2026-09-27T15-49-27Z-hardware-pilot-range-profiler-memory-headroom.md)
- Environment: same model/engine/tool pins as RUN-0040; diagnostic image7c694cc21488
- Artifacts: [archive](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T13-56-21Z-mtp2-hardware-pilot/)

The static-fraction0.75 retry failed before allocating its pools:

```text
ValueError: Loaded weights leave no GPU memory for the KV cache under
--mem-fraction-static=0.75. Raise --mem-fraction-static above0.236 ...
```

Docker reported exit9 at15:49:48UTC and OOMKilled=false. This was a deliberate
allocator rejection, not the kernel OOM kill observed in RUN-0044. The error's
suggested0.236 threshold is misleading for this hybrid model: its calculation
uses available/pre-load memory without including the Mamba subtraction that
caused the rejection.

## Source-grounded diagnosis

The pinned kv_cache_configurator.py was copied from the stopped container into
preflight/. _profile_available_bytes subtracts runtime slack and then
_handle_max_mamba_cache subtracts fixed Mamba and speculative intermediate state.
The explicit256-slot pool is preserved, and MTP2 reserves intermediates for64
requests and three verification positions. Baseline logs record36.14GB SSM,
0.71GB convolution,27.42GB intermediate SSM and0.30GB intermediate convolution.
Reducing the overall static budget below these fixed allocations leaves no KV
budget. The later user max_total_tokens constraint can cap only the KV pool.

## Revised diagnostic configuration

profiles-v7.py restores static fraction0.90 and adds --max-total-tokens65536.
It verifies actual65536-token capacity,256 Mamba slots and effective admission64
before any client runs. This reduces the discretionary KV allocation while
preserving model arithmetic, MTP settings and all state slots. The cap exceeds
the roughly64*(524+128)=41728 tokens in the intended active workload. Later
completed-prefix retention can differ; full-trial throughput from this diagnostic
configuration is not used as the normal benchmark.

orchestrate-v8.py runs the remaining FP4/FP8 captures with new
profiles/<mode>-v7 directories. Unit nvfp4-hw-pilot-profiles-v8-20260927.service
started only after the rejected attempt's shutdown was verified. At this entry
readiness and actual pool sizes are still pending. Normal baseline and Systems
results remain intact, with their original capacities and settings.

Lesson: hybrid-model memory budgets contain fixed state and verification buffers.
Use allocator evidence to reduce a discretionary pool; a smaller static fraction
can reject an otherwise feasible configuration before any allocation occurs.
