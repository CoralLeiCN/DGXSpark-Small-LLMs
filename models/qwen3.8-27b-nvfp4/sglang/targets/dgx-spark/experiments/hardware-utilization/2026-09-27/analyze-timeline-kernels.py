"""Quantify visible eager-kernel time without inventing CUDA graph node coverage."""
import json
from pathlib import Path
import sqlite3
import sys

root = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2]).resolve()
timelines = json.loads((root/'analysis/nsys/timeline-analysis.json').read_text())
rows = []
for timeline in timelines:
    source = Path(timeline['source'])
    db = sqlite3.connect(f'file:{source}?mode=ro', uri=True)
    records = db.execute('''
        SELECT s.value, COUNT(*), SUM(k.end-k.start)
        FROM CUPTI_ACTIVITY_KIND_KERNEL k JOIN StringIds s ON s.id=k.demangledName
        GROUP BY s.value ORDER BY SUM(k.end-k.start) DESC
    ''').fetchall()
    scatter = [r for r in records if r[0] == '_fused_mamba_state_scatter_with_mask_kernel']
    assert len(scatter) == 1
    name, count, nanoseconds = scatter[0]
    intervals = db.execute('''
        SELECT k.start,k.end FROM CUPTI_ACTIVITY_KIND_KERNEL k
        JOIN StringIds s ON s.id=k.demangledName
        WHERE s.value=? ORDER BY k.start
    ''', (name,)).fetchall()
    assert all(a[1] <= b[0] for a, b in zip(intervals, intervals[1:])), 'Use an interval union if scatter kernels overlap'
    assert intervals[0][0] >= timeline['window_start_ns'] and intervals[-1][1] <= timeline['window_end_ns']
    rows.append(dict(concurrency=timeline['concurrency'], source=str(source),
                     visible_scatter_count=count, visible_scatter_seconds=nanoseconds/1e9,
                     visible_scatter_window_percent=nanoseconds/1e9/timeline['window_seconds']*100,
                     visible_eager_top10=[dict(name=n, count=c, seconds=d/1e9) for n,c,d in records[:10]],
                     caveat='Eager kernels only; graph trace aggregates do not reveal their individual nodes. Not a full model kernel ranking.'))
    db.close()
with output.open('x') as stream:
    stream.write(json.dumps(dict(validation='passed', rows=rows), indent=2)+'\n')
print(json.dumps(dict(validation='passed', output=str(output))))
