# Final performance reports

Consolidated final reports live under
`docs/reports/<model>/<engine>/<hardware>/<YYYY-MM-DD>-<topic>.md`.
The date identifies the experiment round. Update a report in place for clarifications,
corrected analysis, or added columns, with links to the supporting experiment entries.
Use a new report for a separate round or comparison.

The [experiment journals](../experiments/README.md) remain append-only evidence for
runs, failures, recovery and later observations. Final reports combine that evidence
into one maintained document. Raw client/engine/GPU metrics and profiler binaries
remain in the external artifact directories linked from each report.

| Date | Model | Engine | Hardware | Final report |
| --- | --- | --- | --- | --- |
| 2026-09-27 | Qwen3.8 27B NVFP4 | SGLang | DGX Spark | [MTP=2 performance and hardware utilization](qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27-mtp2-hardware-utilization.md) |

## Research and proposed follow-ups

Research companions live beside the measured reports. They distinguish external
findings and proposed work from completed experiments; their date is the research
date, and they do not create a new benchmark result.

| Date | Model / target | Research document |
| --- | --- | --- |
| 2026-10-04 | Qwen3.8 27B NVFP4 / SGLang / DGX Spark | [Quantized DFlash2 drafter: quantization approach and safety review](qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-10-04-quantized-drafter-review.md) |
| 2026-09-27 | Qwen3.8 27B NVFP4 / SGLang / DGX Spark | [NVFP4 performance gaps, CUDA Rust findings and next steps](qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27-nvfp4-performance-gaps-and-rust-research.md) |
