"""Validate bounded NCU samples and retain capture/forward provenance.

Usage: uv run --offline --no-project --python 3.12 SCRIPT ROOT OUTPUT_DIR
These samples cannot be summed into complete steps or whole-server utilization.
"""
import csv
import json
from pathlib import Path
import re
import sys


def main(root, output):
    source = root / 'profiles/ncu-selected-v8'
    assert json.loads((source/'status.json').read_text())['phase'] == 'completed-and-stopped'
    assert json.loads((source/'shutdown-verification.json').read_text())['stopped']
    info = json.loads((source/'server-info-ready.json').read_text())
    assert info['mem_fraction_static'] == .90 and info['max_mamba_cache_size'] == 256
    assert [x['effective_max_running_requests_per_dp'] for x in info['internal_states']] == [64]
    assert [x['memory_usage']['token_capacity'] for x in info['internal_states']] == [65536]
    data = json.loads((source/'counters.json').read_text())
    # NCU action indexes are per CUDA stream. Do not guess a global ordering
    # when more than one stream is present.
    assert data['range_count'] == 1, 'Multiple streams require explicit mapping'
    sys.path.insert(0, "/opt/nvidia/nsight-compute/2025.3.1/extras/python")
    import ncu_report
    report = ncu_report.load_report(data["source"])
    stream = report.range_by_idx(0)
    mapping = {}
    next_index = 0
    captures = []
    for c in [1, 8, 64]:
        for phase in ['prefill', 'decode']:
            label = f'c{c}-{phase}'
            log = (source/f'{label}-ncu-segment.log').read_text()
            names = re.findall(r'Profiling "(.*?)"(?: - \d+)?:', log)
            ids = list(range(next_index, next_index+len(names)))
            next_index += len(names)
            for action_id, name in zip(ids, names):
                raw = stream.action_by_idx(action_id)
                assert raw.name(raw.NameBase_DEMANGLED) == name, (action_id, name, raw.name(raw.NameBase_DEMANGLED))
            shapes = json.loads((source/f'{label}-forward-shapes.json').read_text())
            expected = 'EXTEND' if phase == 'prefill' else 'TARGET_VERIFY'
            assert any(s['shape'].startswith(f'step[{expected} ') for s in shapes)
            exports = [p for p in (source/'clients'/label).rglob('profile_export_aiperf.json') if 'phases' not in p.parts]
            assert len(exports) == 1
            client = json.loads(exports[0].read_text())
            assert client['request_count']['avg'] == max(8, 3*c)
            assert not client.get('error_summary') and not client.get('was_cancelled')
            for action_id in ids:
                assert action_id not in mapping
                mapping[action_id] = (c, phase)
            captures.append(dict(concurrency=c, trigger=phase, captured_actions=len(ids),
                                 shapes=shapes, interpretation='Missing coverage when zero; filters persist across ranges.'))
    assert set(mapping) == set(range(data['action_count']))
    rows = []
    for action in data['actions']:
        c, trigger = mapping[action['action_index']]
        metrics = action['metrics']
        assert metrics['profiler__replayer_passes']['value'] == 1
        assert action['gpu_seconds'] > 0
        fp4 = metrics['sm__ops_path_tensor_src_fp4_dst_fp32.sum']['value']
        raw = stream.action_by_idx(action['action_index'])
        name = raw.name(raw.NameBase_DEMANGLED)
        family = 'Mamba state scatter' if '_fused_mamba_state_scatter_with_mask_kernel' in name else 'NVFP4 CUTLASS GEMM'
        if family == 'NVFP4 CUTLASS GEMM':
            assert 'cutlass::device_kernel' in name and fp4 > 0
        else:
            assert fp4 == 0
        nvtx = [r for d in action['nvtx'] for kind in ['push_pop_ranges', 'start_end_ranges'] for r in d[kind]]
        forwards = [r for r in nvtx if r.startswith('step[')]
        rows.append(dict(action_index=action['action_index'], concurrency=c, trigger=trigger,
                         family=family, forward_nvtx='; '.join(forwards),
                         kernel_ms=action['gpu_seconds']*1e3, fp4_hardware_ops=fp4,
                         fp4_hardware_TFLOPS=fp4/action['gpu_seconds']/1e12,
                         sysmem_read_fill_proxy_GBps=action['sysmem_read_fill_proxy_GBps'],
                         sysmem_write_request_proxy_GBps=action['sysmem_write_request_proxy_GBps']))
    output.mkdir(parents=True, exist_ok=False)
    with (output/'selected-kernels.csv').open('x') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    result = dict(validation='passed', source=data['source'], source_sha256=data['sha256'],
                  scope=data['scope'], selection='First matching launch per launch configuration across the session; not a random or exhaustive sample.',
                  captures=captures, rows=rows)
    (output/'selected-kernels.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(validation='passed', actions=len(rows), output=str(output))))


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
