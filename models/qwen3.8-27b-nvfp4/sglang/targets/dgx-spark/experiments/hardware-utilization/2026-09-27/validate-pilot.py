"""Offline final evidence validation; never starts or stops a service.

uv run --offline --no-project --python 3.12 validate-pilot.py ROOT MANIFEST OUTPUT
The shutdown file is a timestamped observation, not a live service-status check.
"""
import hashlib
import json
from pathlib import Path
import sys


def load(path):
    return json.loads(path.read_text())


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(root, manifest_path, output):
    baseline = load(root/'analysis/baseline/baseline-analysis.json')
    assert baseline['validation'] == 'passed'
    assert baseline['measured_requests'] == 960 and baseline['trial_count'] == 9
    assert [(r['concurrency'], r['trials'], r['measured_requests_per_trial']) for r in baseline['aggregates']] == [(1,3,64),(8,3,64),(64,3,192)]
    for item in baseline['sources']:
        assert digest(Path(item['path'])) == item['sha256']
    for directory in ['baseline-v3', 'profiles/nsys-v3', 'profiles/ncu-selected-v8']:
        assert load(root/directory/'status.json')['phase'] == 'completed-and-stopped'
        assert load(root/directory/'shutdown-verification.json')['stopped']
    calibration = load(root/'analysis/calibration-analysis-v2.json')
    kernels = load(root/'analysis/selected/selected-kernels.json')
    assert calibration['validation'] == kernels['validation'] == 'passed'
    assert digest(Path(kernels['source'])) == kernels['source_sha256']
    for item in calibration['sources']:
        assert digest(Path(item['path'])) == item['sha256']
    timelines = load(root/'analysis/nsys/timeline-analysis.json')
    assert [x['concurrency'] for x in timelines] == [1,8,64]
    assert all(0 < x['gpu_busy_percent'] <= 100 for x in timelines)
    for item in load(root/'analysis/nsys/exports.json'):
        assert digest(Path(item['source'])) == item['sha256']
    shutdown = load(root/'final-shutdown-verification.json')
    assert shutdown['all_owned_containers_stopped']
    assert shutdown['all_owned_units_inactive']
    assert shutdown['gpu_compute_processes'] == []
    assert shutdown['endpoint_unavailable']
    manifest = load(manifest_path)
    for item in manifest['files']:
        assert digest(manifest_path.parent/item['file']) == item['sha256'], item['file']
        assert digest(Path(item['source'])) == item['sha256'], item['source']
    result = dict(validation='passed', measured_trials=9, measured_requests=960,
                  timelines=3, selected_kernel_samples=len(kernels['rows']),
                  retained_scripts=len(manifest['files']), shutdown_observed_at=shutdown['at_utc'],
                  limitations=['Physical DRAM bytes unavailable', 'Selected kernels do not establish whole-server hardware MFU',
                               'Whole-range inference profiling failed; artifacts retained', 'Only three exploratory normal trials per concurrency'])
    with output.open('x') as stream:
        stream.write(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main(*(Path(x).resolve() for x in sys.argv[1:4]))
