"""Diagnostic-only bridge for profile_range call sites in pinned SGLang.

Default calls (including ModelRunner.forward) otherwise emit Torch profiler
spans only. Honor the existing operation-NVTX flag at these call sites too.
No model math, serving settings, or normal baseline image is changed.
"""
from pathlib import Path
import hashlib
import json

path = Path('/sgl-workspace/sglang/python/sglang/srt/utils/nvtx_utils.py')
text = path.read_text()
old = 'def profile_range(\n    debug_name: str, *, color: Optional[str] = None, nvtx_enabled: bool = False\n):'
new = old.replace('nvtx_enabled: bool = False', 'nvtx_enabled: bool = NVTX_OPERATIONS_ENABLED')
assert text.count(old) == 1, 'Pinned instrumentation call site changed'
updated = text.replace(old, new)
compile(updated, str(path), 'exec')
path.write_text(updated)
print(json.dumps(dict(path=str(path), before_sha256=hashlib.sha256(text.encode()).hexdigest(),
                      after_sha256=hashlib.sha256(updated.encode()).hexdigest())))
