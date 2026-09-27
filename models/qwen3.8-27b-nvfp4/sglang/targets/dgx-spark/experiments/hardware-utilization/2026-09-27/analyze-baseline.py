"""Validate and summarize the nine saved normal trials; no endpoint/GPU access.

Usage: uv run --no-project --python 3.12 analyze-baseline.py ROOT OUTPUT_DIR
OUTPUT_DIR must be new. Raw artifacts are never modified.
"""
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import sys


def jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def prom(text, required_label=None):
    values = {}
    for line in text.splitlines():
        if line.startswith('#') or (required_label and required_label not in line):
            continue
        match = re.match(r'([^\s{]+)(?:\{.*\})?\s+([^\s]+)', line)
        if match:
            name, value = match.groups()
            values[name] = values.get(name, 0) + float(value)
    return values


def summary(values):
    return dict(mean=statistics.mean(values), sample_stddev=statistics.stdev(values),
                min=min(values), max=max(values))


def main(root, output):
    rows = json.loads((root/'baseline-v3/trial-summary.json').read_text())
    assert json.loads((root/'baseline-v3/status.json').read_text())['phase'] == 'completed-and-stopped'
    assert {(r['concurrency'], r['trial']) for r in rows} == {(c, t) for c in (1, 8, 64) for t in (1, 2, 3)}
    assert len(rows) == 9 and sum(r['request_count'] for r in rows) == 960
    sources = []

    def remember(path):
        sources.append(dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))

    for row in rows:
        export = Path(row['export'])
        directory = export.parent
        data = json.loads(export.read_text())
        remember(export)
        n = max(64, 3*row['concurrency'])
        assert row['request_count'] == data['request_count']['avg'] == n
        assert not data['error_summary'] and not data['was_cancelled']
        requests = [r for r in jsonl(directory/'profile_export.jsonl')
                    if r['metadata']['benchmark_phase'] == 'profiling']
        assert len(requests) == n
        assert all(r['metrics']['output_sequence_length']['value'] == 128 for r in requests)
        start = min(r['metadata']['request_start_ns'] for r in requests)
        end = max(r['metadata']['request_end_ns'] for r in requests)
        assert (start, end) == (row['measurement_start_ns'], row['measurement_end_ns'])
        for name in ('profile_export.jsonl', 'inputs.json', 'metrics-before.prom', 'metrics-after.prom',
                     'gpu_telemetry_export.jsonl', 'server_metrics_export.jsonl'):
            remember(directory/name)
        before = (directory/'metrics-before.prom').read_text()
        after = (directory/'metrics-after.prom').read_text()
        b, a = prom(before), prom(after)
        for metric in ('prompt_tokens_histogram', 'uncached_prompt_tokens_histogram'):
            assert a['sglang:'+metric+'_count'] - b['sglang:'+metric+'_count'] == n
        prompt = a['sglang:prompt_tokens_histogram_sum'] - b['sglang:prompt_tokens_histogram_sum']
        uncached = a['sglang:uncached_prompt_tokens_histogram_sum'] - b['sglang:uncached_prompt_tokens_histogram_sum']
        assert prompt == uncached == data['input_sequence_length']['sum']
        assert row['cached_prompt_fraction'] == 0
        row['mean_ttft_ms'] = data['time_to_first_token']['avg']
        row['mean_inter_token_latency_ms'] = data['inter_token_latency']['avg']
        row['p95_response_seconds'] = data['request_latency']['p95']/1000
        row['mean_input_tokens'] = data['input_sequence_length']['avg']
        row['measurement_seconds'] = (end-start)/1e9
        for target, metric, label in [
            ('mean_queue_seconds', 'sglang:queue_time_seconds', None),
            ('mean_prefill_forward_seconds', 'sglang:per_stage_req_latency_seconds', 'stage="prefill_forward"'),
        ]:
            bb, aa = prom(before, label), prom(after, label)
            count = aa[metric+'_count'] - bb[metric+'_count']
            assert count == n, (target, count, n)
            row[target] = (aa[metric+'_sum']-bb[metric+'_sum'])/count
        row['spec_verify_calls_delta'] = a['sglang:spec_verify_calls_total']-b['sglang:spec_verify_calls_total']
        gpu = [r for r in jsonl(directory/'gpu_telemetry_export.jsonl') if start <= r['timestamp_ns'] <= end]
        assert gpu
        for key, target in [('nvidia_power_usage', 'gpu_power_w'), ('nvidia_temperature', 'gpu_temperature_c'),
                            ('nvidia_gpu_utilization', 'gpu_active_percent'), ('nvidia_sm_utilization', 'nvml_sm_utilization_percent')]:
            values = [r['telemetry_data'][key] for r in gpu]
            assert all(math.isfinite(v) for v in values)
            row[target+'_sample_mean'] = statistics.mean(values)
            row[target+'_max'] = max(values)
        server = [r for r in jsonl(directory/'server_metrics_export.jsonl') if start <= r['timestamp_ns'] <= end]
        for metric, target in [('sglang:num_running_reqs', 'maximum_sampled_running_requests'),
                               ('sglang:num_queue_reqs', 'maximum_sampled_queued_requests')]:
            values = [sum(v['value'] for v in r['metrics'][metric]) for r in server if metric in r['metrics']]
            assert values
            row[target] = max(values)
        flops = [(r['timestamp_ns'], sum(x['value'] for x in r['metrics']['sglang:estimated_flops_per_gpu']))
                 for r in server if 'sglang:estimated_flops_per_gpu' in r['metrics']]
        flops.sort()
        assert len(flops) >= 2 and all(y[1] >= x[1] for x, y in zip(flops, flops[1:]))
        estimate = (flops[-1][1]-flops[0][1])/((flops[-1][0]-flops[0][0])/1e9)/1e12
        assert math.isclose(estimate, row['sglang_estimated_tflops_per_gpu'], rel_tol=1e-12)

    metrics = ['output_tokens_per_second', 'mean_response_seconds', 'sglang_estimated_tflops_per_gpu',
               'mean_ttft_ms', 'mean_inter_token_latency_ms', 'p95_response_seconds', 'mean_input_tokens',
               'mean_queue_seconds', 'mean_prefill_forward_seconds', 'measurement_seconds',
               'gpu_power_w_sample_mean', 'gpu_temperature_c_sample_mean', 'gpu_temperature_c_max',
               'gpu_active_percent_sample_mean', 'nvml_sm_utilization_percent_sample_mean',
               'maximum_sampled_running_requests', 'maximum_sampled_queued_requests', 'spec_verify_calls_delta']
    aggregates = []
    for c in (1, 8, 64):
        trials = [r for r in rows if r['concurrency'] == c]
        assert len({r['inputs_sha256'] for r in trials}) == 1
        aggregates.append(dict(concurrency=c, trials=3, measured_requests_per_trial=max(64, 3*c),
                               metrics={key: summary([r[key] for r in trials]) for key in metrics}))
    output.mkdir(parents=True, exist_ok=False)
    result = dict(validation='passed', measured_requests=960, trial_count=9, trials=rows, aggregates=aggregates,
                  notes=['Trial statistics are descriptive, not convergence or confidence claims.',
                         'SGLang TFLOPS are model-operation estimates, not hardware instruction counts.',
                         'GPU sample means use samples within the client measurement window; NVML utilization is activity, not memory bandwidth.',
                         'c1 trial1 survived a verifier failure; remaining trials followed a server restart with the same configuration.',
                         'Per-trial p95 values are summarized, not pooled into a combined p95.'],
                  sources=sources)
    (output/'baseline-analysis.json').write_text(json.dumps(result, indent=2)+'\n')
    with (output/'baseline-trials.csv').open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=['concurrency', 'trial', 'request_count', *metrics], extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    lines = ['| Concurrency | SGLang estimated TFLOPS/GPU | Total output tokens/s | Mean response time (s) |',
             '| ---: | ---: | ---: | ---: |']
    for row in aggregates:
        m = row['metrics']
        lines.append('| '+str(row['concurrency'])+' | '+' | '.join(
            f"{m[k]['mean']:.3f} ± {m[k]['sample_stddev']:.3f}"
            for k in ['sglang_estimated_tflops_per_gpu', 'output_tokens_per_second', 'mean_response_seconds'])+' |')
    (output/'baseline-table.md').write_text('\n'.join(lines)+'\n\nMean ± sample standard deviation over three trials.\n')
    print(json.dumps(dict(validation='passed', measured_requests=960, output=str(output))))


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
