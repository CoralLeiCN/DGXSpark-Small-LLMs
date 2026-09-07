# NVIDIA Nemotron 3 Nano 30B A3B NVFP4

This recipe serves
[`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4`](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4)
on one DGX Spark GPU through SGLang's OpenAI-compatible API.

Status: experimental until the image build, model load, and validation request have
been completed on the target DGX Spark.

## Deployment

The default base image is `nvcr.io/nvidia/pytorch:26.02-py3`. It is selected
because it is already cached on the development DGX Spark and provides ARM64,
Python 3.12, CUDA 13.1, and the NVIDIA framework stack. Docker reuses the local
base layer and does not pull it again. The model image then installs the exact
stable Torch family required by its pinned SGLang release.

```bash
export HF_TOKEN=hf_example
scripts/deploy-nemotron-nano
scripts/logs nvidia-nemotron-3-nano-30b-a3b-nvfp4 --target dgx-spark
scripts/validate nvidia-nemotron-3-nano-30b-a3b-nvfp4 --target dgx-spark
```

`HF_TOKEN` is optional while the model remains public, but setting one avoids
anonymous Hugging Face rate limits. Model weights persist under
`$HF_CACHE_DIR`; the default is `$HOME/.cache/huggingface`.

The deployment listens on `http://localhost:30000`. Stop it with:

```bash
scripts/stop nvidia-nemotron-3-nano-30b-a3b-nvfp4 --target dgx-spark
```

If preflight reports a missing `/run/nvidia-persistenced/socket`, check and
restart the NVIDIA persistence daemon before deploying:

```bash
systemctl status nvidia-persistenced.service
sudo systemctl restart nvidia-persistenced.service
nvidia-smi
```

## Configuration

Copy `sglang/targets/dgx-spark/.env.example` to
`sglang/targets/dgx-spark/.env`, or export individual values before running a
script. The main tuning controls are:

| Variable | Default | Purpose |
| --- | --- | --- |
| `NVIDIA_PYTORCH_IMAGE` | `nvcr.io/nvidia/pytorch:26.02-py3` | Cached NVIDIA base image |
| `SGLANG_EXCLUDE_NEWER` | `2026-07-15T00:00:00Z` | Dependency resolution cutoff |
| `SGLANG_PORT` | `30000` | Host API port |
| `CONTEXT_LENGTH` | `32768` | Maximum context admitted by the server |
| `GPU_MEMORY_BUDGET_GIB` | `60` | SGLang model and cache memory target in GiB |
| `MEM_FRACTION_STATIC` | unset | Advanced direct fraction override |
| `MAX_JOBS` | `4` | Maximum concurrent FlashInfer JIT compiler jobs |
| `HF_CACHE_DIR` | `$HOME/.cache/huggingface` | Persistent model cache |
| `HF_HUB_DISABLE_IMPLICIT_TOKEN` | `1` | Ignore stale cached tokens for public reads |

The model supports longer contexts, but increasing `CONTEXT_LENGTH` increases
cache memory use. The launcher converts the 60 GiB target to SGLang's
device-relative `--mem-fraction-static` value. This controls model weights and
runtime caches; CUDA contexts and kernel compilation can use additional memory,
so it is not a hard container memory limit.

The first startup compiles FlashInfer FP4 kernels for the GB10. Compilation is
limited to four workers because unbounded parallel `nvcc` workers can exhaust
unified memory while the model and runtime caches are resident. Named Docker
volumes preserve the FlashInfer JIT and SGLang autotuning caches across container
recreation, so this cost is normally paid only once.

When using a valid `HF_TOKEN` for gated content, set
`HF_HUB_DISABLE_IMPLICIT_TOKEN=0`. The Nemotron checkpoint in this recipe is
public, so anonymous reads are the safer default.

## Source Settings

The launch command follows the model card and NVIDIA/SGLang cookbook:

- tensor parallel size `1`
- FlashInfer attention
- `qwen3_coder` tool parser
- `nemotron_3` reasoning parser
- trusted model repository code

The 60 GiB default leaves unified memory available to the host and kernel
compilation. The 32K initial context is a conservative repository default, not
a model limit. The model card documents 256K as its Hugging Face default and up
to 1M tokens with additional memory.

The model card's SGLang example uses the older parser name `nano_v3`. Pinned
SGLang `0.5.15.post1` exposes the same Nemotron parser as `nemotron_3`; the
startup script uses the accepted current name.

The validation request allows 512 output tokens because this reasoning model can
spend more than 128 tokens on `reasoning_content` before producing its final
answer. Repository validation fails when the API returns no final text, even if
the HTTP request itself succeeds.

Sources:

- [NVIDIA model card](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4)
- [NVIDIA Nemotron SGLang cookbook](https://github.com/NVIDIA-NeMo/Nemotron/blob/main/usage-cookbook/Nemotron-3-Nano/sglang_cookbook.ipynb)
- [NVIDIA DGX Spark SGLang playbook](https://github.com/NVIDIA/dgx-spark-playbooks)
- [NVIDIA PyTorch container catalog](https://catalog.ngc.nvidia.com/orgs/nvidia/-/containers/pytorch/-)

Observed deployment failures, diagnoses, and verified fixes are kept in the
[DGX Spark SGLang experiment journal](../../docs/experiments/nvidia-nemotron-3-nano-30b-a3b-nvfp4/sglang/dgx-spark/README.md).
