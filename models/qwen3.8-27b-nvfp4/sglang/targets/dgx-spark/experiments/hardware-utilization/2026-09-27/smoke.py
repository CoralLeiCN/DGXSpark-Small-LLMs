import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

root = Path(sys.argv[1])
origin = 'http://127.0.0.1:30000'
results = []

def request(endpoint, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(origin + endpoint, data=data,
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=240) as response:
        return response.read().decode()

try:
    for endpoint, name in [('/get_server_info', 'server-info.json'),
                           ('/get_model_info', 'model-info.json'),
                           ('/metrics', 'metrics-before.prom')]:
        (root / name).write_text(request(endpoint))
    if len(sys.argv) > 2:
        info = json.loads((root / 'server-info.json').read_text())
        effective_limits = [state['effective_max_running_requests_per_dp']
                            for state in info['internal_states']]
        assert effective_limits and all(limit == int(sys.argv[2])
                                        for limit in effective_limits), effective_limits
        print(json.dumps({'effective_admission_limits': effective_limits}), flush=True)
    for prompt, expected in [
        ('Reply with exactly: DGX Spark ready', 'DGX Spark ready'),
        ('What is 17 multiplied by 19? Reply with only the integer.', '323'),
        ('Sort 9, 2, 5 ascending. Reply with only a JSON array.', '[2, 5, 9]'),
    ]:
        body = {'model': 'qwen3.8-27b-nvfp4',
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 128, 'temperature': 0,
                'chat_template_kwargs': {'enable_thinking': False}}
        response = json.loads(request('/v1/chat/completions', body))
        content = response['choices'][0]['message']['content'].strip()
        correct = (json.loads(content) == json.loads(expected)
                   if expected.startswith('[') else content == expected)
        results.append({'endpoint': '/v1/chat/completions', 'request': body,
                        'response': response, 'correct': correct})
        print(json.dumps({'output': content, 'correct': correct}), flush=True)
    body = {'model': 'qwen3.8-27b-nvfp4',
            'input': 'Reply with exactly this text and nothing else: DGX Spark NVFP4 ready',
            'max_output_tokens': 512, 'temperature': 0.6, 'top_p': 0.95,
            'store': False, 'chat_template_kwargs': {'enable_thinking': False}}
    response = json.loads(request('/v1/responses', body))
    content = '\n'.join(part['text'] for item in response.get('output', [])
                        if item.get('type') == 'message'
                        for part in item.get('content', [])
                        if part.get('type') == 'output_text').strip()
    correct = response.get('status') == 'completed' and content == 'DGX Spark NVFP4 ready'
    results.append({'endpoint': '/v1/responses', 'request': body,
                    'response': response, 'correct': correct})
    print(json.dumps({'output': content, 'correct': correct}), flush=True)
    # Configuration/acceptance gauges refresh on decode reporting intervals;
    # short exact-text replies can finish before the first interval.
    body = {'model': 'qwen3.8-27b-nvfp4',
            'messages': [{'role': 'user', 'content': 'Explain how a bicycle works.'}],
            'max_tokens': 256, 'temperature': 0, 'ignore_eos': True,
            'chat_template_kwargs': {'enable_thinking': False}}
    response = json.loads(request('/v1/chat/completions', body))
    correct = response['usage']['completion_tokens'] == 256
    results.append({'endpoint': '/v1/chat/completions', 'request': body,
                    'response': response, 'correct': correct})
    print(json.dumps({'forced_output_tokens': response['usage']['completion_tokens'],
                      'correct': correct}), flush=True)
    metrics = request('/metrics')
    (root / 'metrics-after.prom').write_text(metrics)
    steps = re.findall(r'^sglang:spec_num_steps\{[^\n]*\}\s+(\S+)', metrics, re.M)
    assert steps and all(float(value) == int(sys.argv[3]) for value in steps), steps
    verify = re.findall(r'^sglang:spec_verify_calls_total\{[^\n]*\}\s+(\S+)', metrics, re.M)
    assert verify and sum(map(float, verify)) > 0, verify
    assert all(result['correct'] for result in results), 'Inference smoke check failed'
finally:
    (root / 'smoke-results.json').write_text(json.dumps({
        'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
        'results': results,
    }, indent=2) + '\n')
