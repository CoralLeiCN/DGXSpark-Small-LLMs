"""Verify known-work hardware counters and summarize unprofiled calibrations.

Usage: uv run --no-project --python 3.12 analyze-calibration.py ROOT OUTPUT.json
Requires completed FP4 and FP8 calibration reports and installed Nsight Compute.
"""
import hashlib
import json
from pathlib import Path
import statistics
import sys

sys.path.insert(0, '/opt/nvidia/nsight-compute/2025.3.1/extras/python')
import ncu_report


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.startswith('{')]


def distribution(values):
    return dict(mean=statistics.mean(values), sample_stddev=statistics.stdev(values),
                min=min(values), max=max(values))


def report_counters(path, names):
    report = ncu_report.load_report(str(path))
    values = {name: [] for name in names}
    for ri in range(report.num_ranges()):
        section = report.range_by_idx(ri)
        for ai in range(section.num_actions()):
            action = section.action_by_idx(ai)
            for name in names:
                metric = action.metric_by_name(name)
                if metric is not None:
                    values[name].append(dict(value=metric.value(), unit=metric.unit(), action=action.name()))
    assert all(values.values()), values
    return values


def main(root, output):
    cal = root/'calibration'
    used = []
    result = dict(scope='Short unprofiled, automatically clocked microbenchmarks; pattern-specific references, not proven sustained ceilings.')
    bwfile = cal/'bandwidth-unprofiled.jsonl'
    rows = read_rows(bwfile)
    used.append(bwfile)
    assert rows[0]['buffer_bytes'] > rows[0]['l2_bytes']
    result['bandwidth_effective_GBps'] = {}
    for pattern in ('read', 'write', 'copy'):
        group = [r for r in rows if r.get('pattern') == pattern]
        assert len(group) == 3 and all(r['valid'] for r in group)
        result['bandwidth_effective_GBps'][pattern] = distribution([r['effective_GBps'] for r in group])
    byte_metrics = ['lts__d_sectors_fill_sysmem.sum', 'lts__t_sectors_aperture_sysmem_op_write.sum']
    bwr = cal/'bandwidth-ncu-sysadmin.ncu-rep'
    used.append(bwr)
    counters = report_counters(bwr, byte_metrics)
    result['copy_proxy_validation'] = {}
    for metric, values in counters.items():
        assert len(values) == 1 and values[0]['unit'] == 'sector'
        byte_count = values[0]['value']*32
        ratio = byte_count/rows[0]['buffer_bytes']
        assert abs(ratio-1) < .005, (metric, ratio)
        result['copy_proxy_validation'][metric] = dict(proxy_bytes=byte_count, known_bytes=rows[0]['buffer_bytes'], ratio=ratio)
    for precision, limit in [('fp4', .25), ('fp8', .1)]:
        path = cal/f'{precision}-unprofiled.jsonl'
        rows = read_rows(path)
        used.append(path)
        assert all(r['relative_rmse'] < limit for r in rows)
        groups = {}
        for m, n, k in sorted({(r['m'], r['n'], r['k']) for r in rows}):
            group = [r for r in rows if (r['m'], r['n'], r['k']) == (m, n, k)]
            assert len(group) == 3
            groups[f'{m}x{n}x{k}'] = distribution([r['effective_dense_TFLOPS'] for r in group])
        result[precision+'_effective_dense_TFLOPS'] = groups
        report = cal/f'{precision}-ncu.ncu-rep'
        used.append(report)
        name = f'sm__ops_path_tensor_src_{precision}_dst_fp32.sum'
        counters = report_counters(report, [name, 'profiler__replayer_passes'])
        operations = sum(v['value'] for v in counters[name])
        assert operations == 2*4096**3, (precision, operations)
        result[precision+'_operation_validation'] = dict(measured_operations=operations, expected_operations=2*4096**3,
                                                       replayer_passes=counters['profiler__replayer_passes'])
    result['traffic_scope'] = 'L2 system-memory fills and write requests validated for a streaming copy, not physical LPDDR-controller bytes. Write requests can hit cache/coalesce; do not label their sum DRAM utilization.'
    result['sources'] = []
    for path in used:
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        result['sources'].append(dict(path=str(path), sha256=digest))
    result['validation'] = 'passed'
    with output.open('x') as stream:
        stream.write(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(validation='passed', output=str(output))))


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
