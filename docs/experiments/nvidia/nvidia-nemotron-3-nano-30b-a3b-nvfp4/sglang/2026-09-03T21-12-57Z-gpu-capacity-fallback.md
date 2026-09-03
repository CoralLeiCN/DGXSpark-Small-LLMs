# 2026-09-03T21:12:57Z — SGLang could not read GPU capacity from `nvidia-smi`

Run ID: `RUN-0002`

- Status: workaround
- Phase: engine startup
- Related turns: none
- Repo revision: `c520931` (`dirty`)
- Host/GPU: DGX Spark, NVIDIA GB10, driver `580.173.02`, ARM64
- Container: `dgxspark/nemotron-3-nano-30b-a3b-nvfp4-sglang:0.1.0`
- Engine: SGLang `0.5.15.post1`
- Model: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4`, NVFP4

## Command

```bash
scripts/deploy-nemotron-nano
```

## Error Or Observation

```text
Failed to get GPU memory capacity from nvidia-smi. Falling back to
torch.cuda.mem_get_info(). Reported total GPU memory per device (MiB):
[124610], using min: 124610 MiB.
```

## Diagnosis

- Symptom: SGLang's `nvidia-smi` capacity probe did not return usable memory
  figures during startup.
- Root cause: on this GB10 unified-memory system, the host `nvidia-smi` query
  reports GPU memory total and free as `N/A`, so SGLang cannot use that probe to
  determine capacity.
- Evidence: the host query detected the GB10 and driver but returned `[N/A]`
  for both memory fields. SGLang's Torch fallback reported 124,610 MiB, and the
  model launcher independently calculated 121.69 GiB with
  `torch.cuda.mem_get_info()`.

## Fix Or Change

No code change was required because SGLang automatically falls back to Torch.
The recipe's 60 GiB budget calculation also deliberately uses Torch instead of
parsing `nvidia-smi`.

## Verification

```bash
scripts/logs nvidia/nvidia-nemotron-3-nano-30b-a3b-nvfp4 \
  --engine sglang --no-follow
```

Startup continued with a static fraction of `0.493058` calculated from 121.69
GiB, then loaded all five NVFP4 weight shards.

## Lesson

Do not assume `nvidia-smi` exposes discrete-VRAM capacity on a unified-memory
DGX Spark. Use a CUDA-aware runtime query such as `torch.cuda.mem_get_info()`
and retain a tested fallback in engine tooling.

## Next Step

Treat this warning as expected while Torch reports a valid capacity and the
calculated memory fraction remains within `(0, 1)`.
