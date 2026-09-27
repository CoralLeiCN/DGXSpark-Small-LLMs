import importlib.util,sys
from pathlib import Path
print(sys.executable,sys.version)
p=Path(importlib.util.find_spec("sglang").origin).parent
print(p)
for name in ["srt/entrypoints/http_server.py","srt/managers/scheduler_components/profiler_manager.py","srt/layers/quantization/modelopt_quant.py","srt/managers/io_struct.py"]:
 src=p/name
 if src.exists():
  Path("/work/preflight/"+src.name).write_text(src.read_text())
  print("saved",name)
