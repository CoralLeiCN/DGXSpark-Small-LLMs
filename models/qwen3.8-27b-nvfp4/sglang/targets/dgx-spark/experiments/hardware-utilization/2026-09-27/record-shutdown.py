"""Record live shutdown evidence for this pilot without mutating services."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import urllib.error
import urllib.request


def run(args):
    return subprocess.check_output(args, text=True, timeout=30).strip()


names = run(['docker', 'ps', '-a', '--filter', 'name=nvfp4-hw-pilot-', '--format', '{{.Names}}']).splitlines()
containers = []
for name in names:
    state = json.loads(run(['docker', 'inspect', '--format', '{{json .State}}', name]))
    containers.append(dict(name=name, state=state))
units = []
listing = run(['systemctl', '--user', 'list-units', '--all', '--plain', '--no-legend', '--no-pager', 'nvfp4-hw-pilot*'])
for line in listing.splitlines():
    parts = line.split()
    assert len(parts) >= 4, line
    units.append(dict(unit=parts[0], load=parts[1], active=parts[2], sub=parts[3]))
compute = run(['nvidia-smi', '--query-compute-apps=pid,process_name', '--format=csv,noheader,nounits'])
processes = [] if not compute else compute.splitlines()
try:
    with urllib.request.urlopen('http://127.0.0.1:30000/health', timeout=5) as response:
        unavailable = False
except urllib.error.HTTPError:
    unavailable = False  # A responding HTTP server is still present.
except urllib.error.URLError:
    unavailable = True
record = dict(at_utc=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
              containers=containers, units=units,
              all_owned_containers_stopped=all(not c['state']['Running'] for c in containers),
              all_owned_units_inactive=all(u['active'] not in ['active','activating','deactivating','reloading'] for u in units),
              gpu_compute_processes=processes, endpoint_unavailable=unavailable)
with Path(sys.argv[1]).open('x') as stream:
    stream.write(json.dumps(record, indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k not in ['containers','units']}))
assert record['all_owned_containers_stopped'] and record['all_owned_units_inactive'] and not processes and unavailable
