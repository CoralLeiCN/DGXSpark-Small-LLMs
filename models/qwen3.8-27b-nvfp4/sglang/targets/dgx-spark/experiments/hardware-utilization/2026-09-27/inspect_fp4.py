from pathlib import Path
import inspect
import flashinfer
from sglang.srt.layers.quantization.fp4_utils import fp4_quantize
print("quantize",inspect.signature(fp4_quantize))
print("mm_fp4",inspect.signature(flashinfer.mm_fp4))
print(flashinfer.mm_fp4.__doc__[:5500])
for rel in ["srt/layers/quantization/fp4_utils.py","srt/utils/nvtx_utils.py","srt/model_executor/step_span_utils.py"]:
 p=Path("/sgl-workspace/sglang/python/sglang")/rel
 Path("/work/preflight/"+p.name).write_text(p.read_text())
