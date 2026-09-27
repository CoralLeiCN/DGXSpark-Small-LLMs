"""Export completed diagnostic timelines for offline inspection, without GPU work.

Usage: uv run --no-project --python 3.12 export-nsys.py PROFILE_DIR OUTPUT_DIR
"""
from pathlib import Path
import hashlib
import json
import shlex
import sqlite3
import subprocess
import sys

source = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2]).resolve()
assert json.loads((source/'status.json').read_text())['phase'] == 'completed-and-stopped'
assert json.loads((source/'shutdown-verification.json').read_text())['stopped']
reports = sorted(source.glob('*.nsys-rep'))
assert len(reports) == 3
output.mkdir(parents=True, exist_ok=False)
manifest = []
for c, report in zip((1, 8, 64), reports):
    assert report.name == f'inference.{(1, 8, 64).index(c)+1}.nsys-rep'
    assert report.stat().st_size > 1024
    destination = output/f'c{c}.sqlite'
    cmd = ['/opt/nvidia/nsight-systems/2025.3.2/bin/nsys', 'export', '--type=sqlite',
           '--output='+str(destination), str(report)]
    (output/f'c{c}.command.txt').write_text(shlex.join(cmd)+'\n')
    with (output/f'c{c}.export.log').open('w') as log:
        subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=600)
    connection = sqlite3.connect('file:'+str(destination)+'?mode=ro', uri=True)
    tables = [r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    assert {'NVTX_EVENTS', 'GPU_METRICS', 'TARGET_INFO_GPU_METRICS'} <= set(tables), tables
    with report.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    manifest.append(dict(concurrency=c, source=str(report), sha256=digest, sqlite=str(destination), tables=tables))
    connection.close()
(output/'exports.json').write_text(json.dumps(manifest, indent=2)+'\n')
print(json.dumps(dict(exported=3, output=str(output))))
