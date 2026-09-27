"""Summarize saved GPU timelines, including graph activities and eager kernels.

Usage: uv run --no-project --python 3.12 analyze-nsys.py EXPORTED_DIR OUTPUT.json
No GPU work. This capture has scheduler NVTX, not detailed forward-mode NVTX.
"""
from bisect import bisect_right
from collections import defaultdict
import json
from pathlib import Path
import sqlite3
import statistics
import sys


def merged(intervals):
    result = []
    for start, end in sorted(intervals):
        if result and start <= result[-1][1]:
            result[-1][1] = max(result[-1][1], end)
        else:
            result.append([start, end])
    return result


def duration(intervals):
    return sum(b-a for a, b in merged(intervals))


def analyze(path):
    db = sqlite3.connect('file:'+str(path)+'?mode=ro', uri=True)
    tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    operations = []
    table_counts = {}
    for table in ['CUPTI_ACTIVITY_KIND_GRAPH_TRACE', 'CUPTI_ACTIVITY_KIND_KERNEL',
                  'CUPTI_ACTIVITY_KIND_MEMCPY', 'CUPTI_ACTIVITY_KIND_MEMSET']:
        if table not in tables:
            continue
        rows = db.execute(f'SELECT start,end,correlationId,globalPid FROM {table} WHERE end>start').fetchall()
        table_counts[table] = len(rows)
        operations.extend((a, b, corr, pid, table) for a, b, corr, pid in rows)
    assert operations and table_counts.get('CUPTI_ACTIVITY_KIND_GRAPH_TRACE', 0) > 0
    start = min(r[0] for r in operations)
    end = max(r[1] for r in operations)
    busy = duration((r[0], r[1]) for r in operations)
    assert 0 < busy <= end-start
    result = dict(window_start_ns=start, window_end_ns=end, window_seconds=(end-start)/1e9,
                  gpu_busy_seconds=busy/1e9, gpu_busy_percent=100*busy/(end-start), activity_counts=table_counts)
    result['activity_union_seconds'] = {t: duration((a, b) for a, b, _, _, kind in operations if kind == t)/1e9
                                        for t in table_counts}
    metric_rows = db.execute('SELECT g.timestamp,t.metricName,g.value FROM GPU_METRICS g '
                            'JOIN TARGET_INFO_GPU_METRICS t USING(typeId,metricId) '
                            'WHERE g.timestamp>=? AND g.timestamp<=?', (start, end))
    metrics = defaultdict(list)
    for timestamp, name, value in metric_rows:
        if name.endswith('[Throughput %]'):
            assert 0 <= value <= 100, (name, value)
            metrics[name].append((timestamp, value))
    result['activity_metrics'] = {}
    for name, pairs in metrics.items():
        pairs.sort()
        values = [v for _, v in pairs]
        gaps = [b[0]-a[0] for a, b in zip(pairs, pairs[1:])]
        result['activity_metrics'][name] = dict(sample_mean=statistics.mean(values), min=min(values), max=max(values),
                                               samples=len(values), median_sample_spacing_ns=statistics.median(gaps),
                                               max_sample_spacing_ns=max(gaps))
    names = dict(db.execute('SELECT id,value FROM StringIds'))
    ranges = defaultdict(list)
    for a, b, tid, text, textid in db.execute('SELECT start,end,globalTid,text,textId FROM NVTX_EVENTS WHERE end>start'):
        name = text if text is not None else names.get(textid, '')
        if name == 'scheduler.run_batch':
            ranges[tid].append((a, b))
    assert ranges, 'Scheduler annotations missing'
    for spans in ranges.values():
        spans.sort()
    starts = {tid: [s[0] for s in spans] for tid, spans in ranges.items()}
    runtime = {(tid >> 24, corr): (a, b, tid) for a, b, corr, tid in
               db.execute('SELECT start,end,correlationId,globalTid FROM CUPTI_ACTIVITY_KIND_RUNTIME')
               if tid is not None and corr is not None}
    projected = defaultdict(list)
    unmatched = []
    for a, b, corr, pid, kind in operations:
        launch = runtime.get((pid >> 24, corr)) if pid is not None else None
        if launch:
            cpu_a, cpu_b, tid = launch
            index = bisect_right(starts.get(tid, []), cpu_a)-1
            if index >= 0 and cpu_b <= ranges[tid][index][1]:
                projected[(tid, index)].append((a, b))
                continue
        unmatched.append((a, b))
    steps = []
    for (tid, index), intervals in projected.items():
        a, b = ranges[tid][index]
        steps.append(dict(cpu_start_ns=a, cpu_end_ns=b, gpu_start_ns=min(x for x, _ in intervals),
                          gpu_end_ns=max(y for _, y in intervals), gpu_busy_ns=duration(intervals),
                          gpu_activity_count=len(intervals), phase='unlabeled'))
    result['scheduler_steps'] = sorted(steps, key=lambda x: x['cpu_start_ns'])
    result['gpu_activity_outside_scheduler_projection_union_seconds'] = duration(unmatched)/1e9
    result['scope'] = ('GPU activity union includes graph traces, eager kernels and copies without double counting overlap. '
                       'Window spans first to last GPU activity, not the full client trial. '
                       'Throughput-percent fields are pipeline/activity metrics, not arithmetic or physical DRAM utilization. '
                       'Clock fields have invalid signed values under MHz labels and are excluded; independent NVML clock samples are retained. '
                       'Only scheduler NVTX is present in these captures; forward modes and batch sizes are not inferred from client concurrency.')
    db.close()
    return result


if __name__ == '__main__':
    source, output = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    rows = [dict(concurrency=c, source=str(source/f'c{c}.sqlite'), **analyze(source/f'c{c}.sqlite')) for c in (1, 8, 64)]
    with output.open('x') as stream:
        stream.write(json.dumps(rows, indent=2)+'\n')
    print(json.dumps([dict(concurrency=r['concurrency'], seconds=r['window_seconds'], gpu_busy_percent=r['gpu_busy_percent'],
                           tensor_active_percent=r['activity_metrics']['Tensor Active [Throughput %]']['sample_mean']) for r in rows]))
