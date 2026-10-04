# Build two NVFP4 DFlash2 drafter checkpoints

Status: proposed, 2026-10-04. Neither checkpoint has been created.

## Goal

Produce two reproducible, loadable NVFP4 versions of Inco's official BF16
DFlash2 drafter using NVIDIA Model Optimizer. This spec covers checkpoint
creation and a minimal loading/generation check. Performance comparisons and
serving-profile changes are separate follow-up work.

## Shared inputs and format

- Source: `incoai/Qwen3.8-27B-DFlash2@015e795645c74b1a0eeef3b570031fb62e769bc5`.
- Calibration target: `nvidia/Qwen3.8-27B-NVFP4@482ca0f3832238542f8f5295dde86b5f22711d80`.
- Use the same fixed, representative calibration examples for both conversions.
  Run the BF16 drafter with the target's features and capture actual drafter
  inputs. Record the sample count, prompts, generation settings and seed before
  collection; retain the data or a reproducible reference.
- Quantize the 35 attention/MLP projections across five layers to NVFP4 W4A4:
  groups of 16, FP8 block scales and FP32 global scales. Keep feature projection,
  convolutions, selector and normalization in BF16.
- Export SafeTensors and ModelOpt-compatible configuration for SGLang, including
  the module exclusions and scale sharing required by its fused projections.

## Checkpoint 1: max-calibrated NVFP4

Artifact name: `dflash2-nvfp4-max`.

Use maximum-value calibration for activation and weight scales, then
round-to-nearest weight quantization. This is the simple PTQ baseline, following
the general approach described by the community conversion. It starts from the
official BF16 weights; it does not use the community checkpoint as an input.

Reference: [NVIDIA PTQ tutorial](https://developer.nvidia.com/blog/optimizing-llms-for-performance-and-accuracy-with-post-training-quantization/)
and [Maurienne's calibration description](https://huggingface.co/maurienne-ai/Qwen3.8-27B-DFlash2-NVFP4-RTNcal#calibration--the-part-that-matters).

## Checkpoint 2: Local-Hessian NVFP4

Artifact name: `dflash2-nvfp4-local-hessian`.

Use the same source, calibration corpus, quantized modules and output format as
checkpoint 1. Replace weight-scale selection with NVIDIA's Local-Hessian method,
which uses calibration inputs to minimize layer-output error. Keep round-to-nearest
rounding and the same activation-calibration policy; record any collection or
layerwise-execution differences required by the algorithm. No GPTQ or additional
training is included.

Reference: [NVIDIA Local-Hessian method and implementation](https://nvidia.github.io/Model-Optimizer/announcements/local-hessian.html).

## Build and completion requirements

1. Use a pack-specific conversion container. Pin ModelOpt, the model implementation
   and container/runtime versions; use Python 3.12 and `uv` for Python commands.
   Verify the loader reconstructs `DFlash2DraftModel` correctly before calibration.
2. Save two separate checkpoint directories outside Git. Each contains weights,
   configuration and a short provenance record: source revision/hashes, conversion
   recipe/command, environment, calibration reference and output hashes. Keep
   conversion code and recipes under this pack so both builds can be repeated.
3. Check tensor names/shapes, quantized packing/scales, finite values and preserved
   BF16 tensors. Reload each export and perform a minimal SGLang draft-and-verify
   generation check with the pinned target. Record the result and runtime used.

**Done:** both artifacts exist, have reproducible build records, and pass the
format/reload and generation checks. An unsupported loader/export path is an
unresolved build issue, not a successful checkpoint. Label outputs as local
derivatives, not official NVIDIA/Inco releases. Preserve upstream weights and the
existing MTP/BF16 DFlash2 profiles.

Benchmark sweeps, broad quality evaluation, production selection, RadixArk
comparisons and QAD are outside this build task. Later evaluation follows
[serving intent](../../../../../intend.md) and the
[benchmarking guide](../../../../../docs/BENCHMARKING.md), including the slowest
observed user at each concurrency.

Supporting sources: [ModelOpt conversion examples](https://github.com/NVIDIA/Model-Optimizer/blob/main/examples/hf_ptq/README.md)
and the [research review](../../../../../docs/reports/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-10-04-quantized-drafter-review.md).
