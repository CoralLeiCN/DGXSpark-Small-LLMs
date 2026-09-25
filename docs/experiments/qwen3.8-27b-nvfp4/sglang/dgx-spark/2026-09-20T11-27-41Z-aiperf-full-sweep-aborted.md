# 2026-09-20T11:27:41Z — AIPerf full sweep stopped after c1

Run ID: `RUN-0002`

- Status: workaround
- Phase: inference
- Related turns: [Initial API qualification](2026-09-16T23-43-33Z-initial-api-qualification.md)
- Repo revision: `03fef1fa2114c30d915d6d8d40244e18e435d0b5`, dirty (telemetry and benchmark-runner changes)
- Host/GPU: DGX Spark, one NVIDIA GB10
- Container: `dgxspark/qwen3.8-27b-nvfp4-sglang:0.1.0` from `lmsysorg/sglang:dev-qwen38-27b-dflash2`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, Torch `2.13.0+cu130`
- Model: `nvidia/Qwen3.8-27B-NVFP4`, NVFP4; server launch left `revision=None`

## Command

```bash
QWEN_NVFP4_EXPERIMENT_TAG=nvfp4-c72-effective33-20260920 \
  models/qwen3.8-27b-nvfp4/sglang/targets/dgx-spark/benchmark-aiperf.sh
```

## Error Or Observation

```text
The default sweep began at c1 with 96 warmups and 384 measured requests.
The c1 phase was stopped before completion because that serial workload made
the full ten-point sweep impractical for the interactive benchmark session.
Its partial artifacts have a start event only; no AIPerf failure was observed.
```

## Diagnosis

- Symptom: the default low-to-high sweep spends disproportionate wall-clock time at c1 because every request is serialized.
- Root cause: runner defaults were designed for a capacity sweep but the fixed 384-request workload is too large for a live interactive run at its lowest concurrency.
- Evidence: the partial artifact directory is `models/qwen3.8-27b-nvfp4/sglang/targets/dgx-spark/artifacts/nvfp4-c72-effective33-20260920-Zn2fpj/`; its `experiment-events.jsonl` contains only the c1 start event.

## Fix Or Change

Stopped the incomplete c1 profile and performed a new, separately tagged c72-only profile in `RUN-0003`. No serving configuration was changed while the model was running.

## Verification

```bash
QWEN_NVFP4_EXPERIMENT_TAG=nvfp4-c72-effective33-targeted-20260920 \
  QWEN_NVFP4_TOKENIZER_REVISION=482ca0f3832238542f8f5295dde86b5f22711d80 \
  models/qwen3.8-27b-nvfp4/sglang/targets/dgx-spark/benchmark-aiperf.sh 72
```

The replacement profile completed; see `RUN-0003`.

## Lesson

For an interactive maximum-load check, invoke the intended high concurrency explicitly. Reserve the full low-to-high sweep for a scheduled capacity experiment or reduce the c1 request count.

## Next Step

Run a scheduled sweep with a request count scaled to each concurrency, then compare the client result with the server's effective admission cap.
