# Quantized DFlash2 drafter: quantization approach and pre-execution review

Reviewed on 2026-10-04 UTC at the user's request, before downloading weights or
starting the proposed RadixArk experiment. This is a static checkpoint review,
not a security certification, runtime qualification or benchmark.

**Assessment:** the inspected metadata and tensor structure show no apparent
malicious-code indicators. An isolated experiment is reasonable; numerical
integrity, quality and runtime stability remain unverified locally. This review
covers the drafter, not the proposed RadixArk target's weight contents.

## Identity and scope

- Repository: [maurienne-ai/Qwen3.8-27B-DFlash2-NVFP4-RTNcal](https://huggingface.co/maurienne-ai/Qwen3.8-27B-DFlash2-NVFP4-RTNcal).
- Revision: `bd7a934213c47a9e7ef69eef36bb3325f47fd1f1`.
- Community quantization of `incoai/Qwen3.8-27B-DFlash2`, not an NVIDIA or
  upstream Inco release. Publisher claims do not independently prove derivation.
- Weight file: `model.safetensors`, 1,550,153,248 bytes.
- Hub-reported SHA256: `2228b9b22e93a88d84556419c879448ab6c490ae65c4c0b166f4962190ddbf26`.
  This hash was recorded from metadata, **not verified against a full download**.

Public Hub APIs supplied the exact revision's complete file inventory, scan
statuses and JSON configs. HTTP range requests read only the first 19,208 bytes
of the weight file: its eight-byte length field and JSON tensor header. No
weight payload was downloaded, model loaded, credentials used or service started.

## Official release alternatives

Checked on 2026-10-04: Inco publishes an official
[GGUF drafter](https://huggingface.co/incoai/Qwen3.8-27B-DFlash2-GGUF)
with Q4_K_M (1.14 GB) and Q8_0 (2.06 GB) files. Its documented DFlash2
execution path uses llama.cpp; this does not establish compatibility with our
SGLang NVFP4 experiment. Do not describe all quantized drafters as community-only.

The official [SafeTensors drafter](https://huggingface.co/incoai/Qwen3.8-27B-DFlash2)
used by our existing SGLang profile is BF16. No official Inco or NVIDIA NVFP4
release of this drafter was found in the release pages and catalog searches
reviewed. The proposed NVFP4 checkpoint above is a community conversion; retaining
the existing BF16 drafter keeps the drafter weights on the upstream release.

## How the community checkpoint was produced

The publisher describes **post-training quantization with activation calibration**;
no additional gradient-based training is reported. Calibration measures value
ranges for lower-precision representation, rather than teaching new capabilities.

### Published approach

| Step | Publisher's description |
| --- | --- |
| Base | Official `incoai/Qwen3.8-27B-DFlash2` BF16 weights. |
| Calibration examples | Target-generated conversations: 460 conversations, 281,649 tokens; English/French chat, code, tool calls, mathematics and structured output. Thinking enabled for half. |
| Activation capture | Run the BF16 drafter during prefill and decode in eager mode; hooks on 20 runtime linear modules capture approximately 621K input rows per layer. |
| Scales and rounding | Activation scale and weight global scale use their respective maximum absolute value divided by `6 × 448`. Round weights to NVFP4, with groups of 16 and FP8 block scales. |
| Precision selection | Quantize 35 attention/MLP projections across five layers; activations use NVFP4 at runtime. Keep feature projection, convolutions, selector and normalization in BF16. |
| Export | SafeTensors in ModelOpt-compatible layout for SGLang. |

Source: the publisher's [quantization and calibration description](https://huggingface.co/maurienne-ai/Qwen3.8-27B-DFlash2-NVFP4-RTNcal#what-is-quantized),
reviewed on 2026-10-04 at revision `bd7a934213c47a9e7ef69eef36bb3325f47fd1f1`.
The [export configuration](https://huggingface.co/maurienne-ai/Qwen3.8-27B-DFlash2-NVFP4-RTNcal/blob/bd7a934213c47a9e7ef69eef36bb3325f47fd1f1/hf_quant_config.json)
records the NVFP4 scheme, group size and module exclusions.

### Reproducibility and verification limits

The [reproduction section](https://huggingface.co/maurienne-ai/Qwen3.8-27B-DFlash2-NVFP4-RTNcal#reproduce)
names `dflash_calib_hook.py`, `calib/build_prompts.py`, `calib/run_calib.py` and
`quantize-dflash2-gptq-nvfp4.py --rtn`. These are references to the publisher's
workflow, not scripts available in this repository or verified execution commands.

The [published checkpoint inventory](https://huggingface.co/maurienne-ai/Qwen3.8-27B-DFlash2-NVFP4-RTNcal/tree/bd7a934213c47a9e7ef69eef36bb3325f47fd1f1)
contains neither those scripts nor calibration records. Searches for the named
scripts found no public implementation. Exact prompts, generation settings,
source-weight revision and numerical derivation have not been independently
verified. The local tensor-header inspection confirms compatible storage
structure, not the construction history or numerical equivalence to upstream.
Do not call this an independently reproduced conversion.

## NVIDIA references for producing NVFP4 checkpoints

Researched on 2026-10-04. These primary sources describe NVIDIA tooling and
methods related to the community conversion. They do not establish that Inco's
Qwen DFlash2 checkpoint has an NVIDIA-qualified NVFP4 conversion recipe.

| Source | Method and relevance |
| --- | --- |
| [NVIDIA Model Optimizer](https://github.com/NVIDIA/Model-Optimizer) and its [current Hugging Face PTQ example](https://github.com/NVIDIA/Model-Optimizer/blob/main/examples/hf_ptq/README.md) | Official open-source tooling for calibration, quantization and checkpoint export. Current examples accept YAML recipes. This is a potential basis for a reproducible conversion from the upstream BF16 drafter. |
| [Optimizing LLMs for Performance and Accuracy with Post-Training Quantization](https://developer.nvidia.com/blog/optimizing-llms-for-performance-and-accuracy-with-post-training-quantization/) (2025-08-01) | The closest conceptual match to Maurienne's approach: collect representative activations, determine scales, quantize weights/activations and export, without additional model training. Similarity of method does not independently verify Maurienne's implementation. |
| [Improving NVFP4 Accuracy with Local-Hessian Weight Scales](https://nvidia.github.io/Model-Optimizer/announcements/local-hessian.html) (2026-09-09) | Selects each block scale using calibration-input statistics to reduce linear-layer output error. Keeps the NVFP4 representation and runtime operations unchanged. NVIDIA reports using this for its Qwen3.8-27B NVFP4 checkpoint; usefulness for this drafter remains unmeasured. |
| [Creating the NVIDIA Nemotron 3 Ultra NVFP4 Checkpoint](https://developer.nvidia.com/blog/creating-the-nvidia-nemotron-3-ultra-nvfp4-checkpoint-with-nvidia-model-optimizer/) (2026-06-26) | A worked conversion with selective precision and Four-Over-Six scaling: choose between two weight-block ranges according to reconstruction error. Demonstrates that an NVFP4 release can retain sensitive components at higher precision. |
| [AutoQuantize: A Fast Automatic Mixed-Precision Assignment](https://nvidia.github.io/Model-Optimizer/announcements/autoquantize.html) | Searches layer precision under a cost/bit budget. A possible later alternative to a fixed quantized-layer list. Its effective-bit objective is not a guarantee of lower user latency on DGX Spark. |
| [Quantization-Aware Distillation for NVFP4 Inference Accuracy Recovery](https://arxiv.org/abs/2601.20088), [NVIDIA report](https://research.nvidia.com/labs/nemotron/files/NVFP4-QAD-Report.pdf), and [QAT/QAD guide](https://nvidia.github.io/Model-Optimizer/guides/quantization_aware_training_and_distillation.html) | QAD performs training: a quantized student matches a frozen higher-precision teacher. It can recover quantization losses but requires additional compute and data. It is distinct from Maurienne's reported calibration-only conversion. |
| [Developing Nemotron 3.5 Lightning NVFP4 with QAD](https://developer.nvidia.com/blog/developing-nemotron-3-5-lightning-nvfp4-with-qad-using-nvidia-model-optimizer/) (2026-08-17) | Practical PTQ → distillation → export example. Its W4A16 recipe and model-specific choices must not be treated as a ready-made W4A4 DFlash2 recipe. |

### Direct relevance and limits for our drafter

The current [NVIDIA Qwen3.8-27B model card](https://huggingface.co/nvidia/Qwen3.8-27B-NVFP4#post-training-quantization)
describes NVFP4 MLP/head weights, FP8 attention, and Local-Hessian calibration.
This is evidence for the **target model**, not an official quantized DFlash2
release. It is the current online description, not a new qualification of our
cached checkpoint. The card specifies 2,048 calibration samples, while the linked
Local-Hessian reproduction example specifies `--calib_size 512`; reconcile that
discrepancy and pin the recipe/version before claiming an exact reproduction.

NVIDIA's [development changelog](https://github.com/NVIDIA/Model-Optimizer/blob/main/CHANGELOG.rst)
also lists DFlash2 training/export under `0.48.0 (2026-10-xx)`, using
`projector_type="dflash2"`. That entry does not establish released-package support
or successful NVFP4 export of the Inco checkpoint. ModelOpt's general support for
speculative models likewise needs architecture-specific verification here.

The [two-checkpoint build spec](../../../../../models/qwen3.8-27b-nvfp4/sglang/targets/dgx-spark/quantized-drafter-spec.md)
owns max-calibrated and Local-Hessian artifact creation, provenance and minimal
loading/generation checks. Performance evaluation is separate follow-up work. The
[Local-Hessian article](https://nvidia.github.io/Model-Optimizer/announcements/local-hessian.html#local-hessian-with-gptq)
distinguishes scale selection from GPTQ's rounding optimization; the community
card's unsuccessful GPTQ experiment therefore does not settle this comparison.
This proposed application is our inference from the sources, not a published
DFlash2 result.

A locally generated artifact would be our conversion of official weights using
NVIDIA tools, not an official NVIDIA/Inco release. Keep the target fixed when
comparing drafters and evaluate acceptance, quality, minimum per-user decode,
TTFT and aggregate throughput under the repository benchmark protocol. QAD is a
later option if measured PTQ losses justify training. No conversion, download or
inference experiment was performed for this research.

## Findings

| Check | Observation and limit |
| --- | --- |
| Repository files | Six files: SafeTensors weights, two JSON configurations, two Markdown documents and `.gitattributes`. No Python, shell, shared-library or pickle checkpoint files. |
| Config loading | No `auto_map`. Declares `DFlash2DraftModel`, registered by [SGLang v0.5.20](https://github.com/sgl-project/sglang/blob/v0.5.20/python/sglang/srt/models/dflash.py). No checkpoint-supplied implementation is indicated; boot without remote-code trust still needs qualification. |
| Upstream architecture | Removing `quantization_config` makes its parsed config identical to upstream revision `015e795645c74b1a0eeef3b570031fb62e769bc5`. |
| Tensor layout | All 186 tensors have consistent byte lengths, valid types and contiguous offsets ending at the declared file size. Against the cached upstream header, 35 linear weights have the expected packed shape and scale companions; 46 retain their original shape and dtype. No unexpected tensor names. This does not compare numerical values. |
| Hub scanning | Repository summary reports scans done with no files flagged. Per-file antivirus and Protect AI report no findings. JFrog remains queued for weights/config/README; VirusTotal is unscanned. Do not describe this as all scanners passing. |
| Known loading issue | The [reported vLLM producer-field error](https://huggingface.co/maurienne-ai/Qwen3.8-27B-DFlash2-NVFP4-RTNcal/discussions/1) is fixed in this revision's JSON. This is not evidence that our serving configuration has been tested. |

[SafeTensors](https://huggingface.co/docs/safetensors/index) avoids pickle's
arbitrary-code deserialization mechanism. It does not certify tensor behaviour,
publisher identity or the absence of loader/runtime vulnerabilities. Hub scan
results likewise do not establish model quality or exclude behavioural backdoors.

## Conditions for the experiment

Use the pinned revision and verify the full SHA256 after download. Load through
the pinned SGLang implementation with remote-code trust disabled, selected model
directories mounted read-only, no credentials, and offline operation. Keep the
experiment separate from the existing NVIDIA profiles.

Start qualification with the checkpoint's declared block size **8**. The
[publisher's card](https://huggingface.co/maurienne-ai/Qwen3.8-27B-DFlash2-NVFP4-RTNcal#usage-with-sglang)
specifies 8, while the [published Spark experiment](https://github.com/pangoleen/qwen3.8-27b-dgx-spark-dflash2)
uses 16. This review does not resolve that runtime-specific discrepancy.

Target verification is intended to preserve the target distribution under a
correct speculative implementation; it is not a security boundary or proof of
identical floating-point output. Published [quality limitations](https://github.com/pangoleen/qwen3.8-27b-dgx-spark-dflash2/blob/master/RESULTS.md#6-losslessness)
reinforce the need for local task-quality and stability checks. Later benchmarks
must retain minimum per-user decode, TTFT, response latency and errors alongside
aggregate throughput, following [serving intent](../../../../../intend.md).

## Evidence

The [review archive](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/reports/2026-10-04T15-57-18Z-quantized-drafter-review)
contains the API responses, configurations, tensor header, validation summaries,
source URLs and checksums. No inference experiment ID was assigned: no deployment
qualification, performance run or change to earlier measured results occurred.
