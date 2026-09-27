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
assert text.count(new) == 1, 'Expected the previously qualified NVTX default'
updated = text
compile(updated, str(path), 'exec')
needle = '    record = torch.autograd._profiler_enabled()'
assert updated.count(needle) == 1
logging = "    if debug_name.startswith('step[') and ('c_sq=' in debug_name or 'g_sq=' in debug_name):\n        import json, os, time\n        destination = os.environ.get('PILOT_FORWARD_SHAPES_PATH')\n        if destination:\n            with open(destination, 'a') as stream:\n                stream.write(json.dumps({'timestamp_ns': time.time_ns(), 'shape': debug_name}) + '\\n')\n"
updated = updated.replace(needle, logging + needle)
compile(updated, str(path), 'exec')
path.write_text(updated)
print(json.dumps(dict(path=str(path), before_sha256=hashlib.sha256(text.encode()).hexdigest(),
                      after_sha256=hashlib.sha256(updated.encode()).hexdigest())))
