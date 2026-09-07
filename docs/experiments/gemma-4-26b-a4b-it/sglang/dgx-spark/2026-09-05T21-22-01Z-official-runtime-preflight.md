# 2026-09-05T21:22:01Z — Official runtime image restored GPU preflight semantics

Run ID: `RUN-0001`

- Status: resolved
- Phase: preflight
- Related turns: `none`
- Repo revision: `4fe8345` plus uncommitted Gemma recipe changes
- Host/GPU: DGX Spark, NVIDIA GB10, ARM64, 124610 MiB unified memory reported by PyTorch, Linux `6.17.0-1031-nvidia`
- Container: initial override `dgxspark/qwen3.8-27b-fp8-sglang:0.1.0` (`sha256:1fe48564cd63becc4d5f4246ac6cd96fe84ac711e1aae51c7290fcb4b9d83a98`); corrected base `lmsysorg/sglang:dev-qwen38-27b-dflash2` (`sha256:616a3e97f45191af975896cfa644279096cb31bd408a071c2e99ca7209c3cafe`)
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, PyTorch `2.13.0+cu130`, Transformers `5.12.1`, CUDA 13.0
- Model: `google/gemma-4-26B-A4B-it`, initially cached at revision `47b6801b24d15ff9bcd8c96dfaea0be9ed3a0301`, BF16

## Command

The first Docker inspection ran inside the restricted workspace sandbox. After
Docker access was granted, two image-format probes used fields omitted by this
Docker API. The first deployment then overrode the base with another model's
finished recipe image:

```bash
docker info --format 'server={{.ServerVersion}} arch={{.Architecture}}'
docker image inspect <image> --format '...{{.Parent}}...'
docker image inspect <image> --format '...{{json .Config.Cmd}}...'
SGLANG_BASE_IMAGE=dgxspark/qwen3.8-27b-fp8-sglang:0.1.0 \
  scripts/deploy google/gemma-4-26b-a4b-it --engine sglang
```

## Error Or Observation

```text
permission denied while trying to connect to the docker API at unix:///var/run/docker.sock
template parsing error: ... map has no entry for key "Parent"
template parsing error: ... map has no entry for key "Cmd"
KeyboardInterrupt in docker.gpu_available after the preflight probe stalled
```

The derived Qwen recipe image has `ENTRYPOINT ["/opt/dgxspark/start.sh"]`.
Docker therefore passed the preflight's intended `python3 -c ...` CUDA probe as
arguments to the Qwen launcher instead of executing Python directly.

## Diagnosis

- Symptom: Docker was initially inaccessible; after access was granted, the GPU
  preflight hung when a finished model recipe image was supplied as the base.
- Root cause: the workspace sandbox does not expose the Docker socket, Docker
  29 omits unset inspection fields from its formatting map, and a finished
  model image is not interchangeable with its raw runtime base because it owns
  a model-serving entrypoint.
- Evidence: the same Docker queries succeeded with authorized host access;
  supported inspection fields rendered normally; image history showed the Qwen
  entrypoint; interrupting the stalled deploy produced a stack in
  `docker.gpu_available`; and no accidental Qwen container remained afterward.

## Fix Or Change

Docker operations were rerun with authorized host-daemon access and inspection
was limited to present fields. The official SGLang base tag was restored from
Docker Hub. All layers were already present, and Docker resolved the base to
digest `sha256:616a3e97f45191af975896cfa644279096cb31bd408a071c2e99ca7209c3cafe`.
The deployment retry used that raw runtime image rather than the completed Qwen
recipe image.

## Verification

```bash
docker pull lmsysorg/sglang:dev-qwen38-27b-dflash2
scripts/deploy google/gemma-4-26b-a4b-it --engine sglang
```

The pull reported every layer as already present. The retry's preflight ran the
intended Python probe and reported Docker server `29.2.1`, CUDA `13.0.3`, and
`NVIDIA GB10`; the image then built and the Gemma container started.

## Lesson

Shared GPU preflight requires a raw runtime base whose command can be replaced.
Do not substitute a completed model recipe image with its own entrypoint for a
base image merely because the underlying SGLang packages are compatible.

## Next Step

Load the cached Gemma checkpoint and qualify the OpenAI-compatible API.
