"""Authorized fresh-cache MTP=2 pilot. Host runs only stdlib and isolated AIPerf."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, re, shlex, signal, statistics, subprocess, sys, time, traceback, urllib.request

ROOT = Path(sys.argv[1]).resolve()
NAME = 'nvfp4-hw-pilot-baseline-v2-20260927'
IMAGE = 'sha256:110ad45e7872397f337ea5714e6c97c400852938a9b8f258bcc27cab07182b0c'
REV = '482ca0f3832238542f8f5295dde86b5f22711d80'
UV = '/home/coral/.local/bin/uv'
ENV = dict(os.environ, UV_OFFLINE='1', HF_HUB_OFFLINE='1', HF_HUB_DISABLE_IMPLICIT_TOKEN='1')
ACTIVE = None

def utc(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def save(path, obj):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(obj,indent=2)+'\n'); temporary.replace(path)
def event(phase, **kw):
    obj={'at_utc':utc(),'phase':phase,**kw}
    save(ROOT/'baseline-v2/status.json',obj)
    with (ROOT/'baseline-v2/events.jsonl').open('a') as f:f.write(json.dumps(obj)+'\n')
    print(json.dumps(obj),flush=True)
def run(cmd, log, timeout=1800):
    global ACTIVE
    log=Path(log);log.parent.mkdir(parents=True,exist_ok=True)
    log.with_suffix(log.suffix+'.command.txt').write_text(shlex.join(cmd)+'\n')
    with log.open('w') as f:
        ACTIVE=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,env=ENV,start_new_session=True)
        try:
            rc=ACTIVE.wait(timeout)
            if rc:raise RuntimeError(f'exit {rc}: {log}')
        finally:
            if ACTIVE.poll() is None:
                os.killpg(ACTIVE.pid,signal.SIGTERM)
                try:ACTIVE.wait(20)
                except subprocess.TimeoutExpired:os.killpg(ACTIVE.pid,signal.SIGKILL);ACTIVE.wait()
            ACTIVE=None
def request(endpoint, body=None, timeout=60):
    req=urllib.request.Request('http://127.0.0.1:30000'+endpoint,
        data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=timeout) as r:return r.read().decode()
def state():
    p=subprocess.run(['docker','inspect','--format','{{json .State}}',NAME],text=True,capture_output=True,timeout=20)
    if p.returncode:
        if 'no such object' in p.stderr.lower():return None
        raise RuntimeError(p.stderr)
    return json.loads(p.stdout)
def cleanup():
    s=state()
    if s and s['Running']:
        run(['docker','stop','--timeout','90',NAME],ROOT/'baseline-v2/shutdown.log',120)
    s=state()
    if s:
        run(['docker','logs','--timestamps',NAME],ROOT/'baseline-v2/server-final.log',60)
    save(ROOT/'baseline-v2/shutdown-verification.json',{'at_utc':utc(),'container':NAME,'state':s,'stopped':s is None or not s['Running']})
    if s and s['Running']:raise RuntimeError('Owned baseline container still running')
def launch():
    if state() is not None:raise RuntimeError('Refuse to reuse baseline container')
    args=['docker','run','-d','--name',NAME,'--restart','no','--gpus','all','--ipc','host','--shm-size','32gb',
        '--ulimit','memlock=-1','--ulimit','stack=67108864','--volumes-from','models-qwen3-8-27b-nvfp4-sglang-targets--f59869da15d4-sglang-1',
        '-p','127.0.0.1:30000:30000']
    settings={'HF_HUB_DISABLE_IMPLICIT_TOKEN':'1','HF_HUB_OFFLINE':'1','MODEL_ID':'nvidia/Qwen3.8-27B-NVFP4',
        'SERVED_MODEL_NAME':'qwen3.8-27b-nvfp4','CONTEXT_LENGTH':'32768','MEM_FRACTION_STATIC':'0.90',
        'MAX_RUNNING_REQUESTS':'64','MAX_MAMBA_CACHE_SIZE':'256','CHUNKED_PREFILL_SIZE':'2048','INFERPACK_ENABLE_METRICS':'1',
        'SGLANG_EXTRA_ARGS':f'--revision {REV} --speculative-draft-model-revision {REV} --speculative-algorithm EAGLE --speculative-num-steps 2 --speculative-eagle-topk 1 --speculative-num-draft-tokens 3 --mamba-radix-cache-strategy extra_buffer_lazy --max-mamba-cache-size 256 --mamba-full-memory-ratio 4.59'}
    for k,v in settings.items():args+=['-e',f'{k}={v}']
    args+=[IMAGE];run(args,ROOT/'baseline-v2/container-id.log',120)
    deadline=time.monotonic()+900
    while time.monotonic()<deadline:
        s=state()
        if not s or not s['Running']:raise RuntimeError(f'Container exited during startup: {s}')
        try:
            request('/health',timeout=5)
            info=json.loads(request('/get_server_info'))
            limits=[x['effective_max_running_requests_per_dp'] for x in info['internal_states']]
            if limits!=[64]:raise RuntimeError(f'Admission mismatch: {limits}')
            save(ROOT/'baseline-v2/server-info-ready.json',info);return
        except (OSError,ValueError):time.sleep(5)
    raise TimeoutError('Server readiness exceeded 15 minutes')
def command(c,n,dest,seed):
    return [UV,'tool','run','--managed-python','--python','3.12','--from','aiperf==0.12.0','aiperf','profile',
        '--url','http://127.0.0.1:30000','--model','qwen3.8-27b-nvfp4','--tokenizer','nvidia/Qwen3.8-27B-NVFP4',
        '--tokenizer-revision',REV,'--endpoint-type','chat','--endpoint','/v1/chat/completions','--streaming',
        '--use-legacy-max-tokens','--use-server-token-count','--synthetic-input-tokens-mean','512','--synthetic-input-tokens-stddev','0',
        '--output-tokens-mean','128','--output-tokens-stddev','0','--extra-inputs',
        '{"temperature":0,"ignore_eos":true,"chat_template_kwargs":{"enable_thinking":false}}',
        '--header','X-Inferpack-Experiment-Tag:nvfp4-hardware-pilot-20260927','--concurrency',str(c),
        '--request-count',str(n),'--random-seed',str(seed),'--server-metrics','http://127.0.0.1:30000/metrics',
        '--server-metrics-formats','json','csv','jsonl','--gpu-telemetry','pynvml','--ui-type','none','--artifact-dir',str(dest)]
def counters(prom):
    result={}
    for line in prom.splitlines():
        if line.startswith('#'):continue
        m=re.match(r'([^\s{]+)(?:\{.*\})?\s+([^\s]+)',line)
        if m:
            try:result[m[1]]=result.get(m[1],0)+float(m[2])
            except ValueError:pass
    return result
def flush(label):
    result=request('/flush_cache?timeout=30',{},timeout=45)
    if not result.startswith('Cache flushed.'):raise RuntimeError(result)
    (ROOT/'baseline-v2'/f'{label}-flush.txt').write_text(utc()+'\n'+result)
def validate(dest,count,before=None,after=None):
    exports=[p for p in dest.rglob('profile_export_aiperf.json') if 'phases' not in p.parts]
    if len(exports)!=1:raise RuntimeError(f'Expected one export, found {exports}')
    p=exports[0]; data=json.loads(p.read_text())
    assert data['request_count']['avg']==count,(p,data.get('request_count'))
    assert not data.get('error_summary') and not data.get('was_cancelled'),p
    requests=[json.loads(line) for line in p.with_name('profile_export.jsonl').read_text().splitlines()]
    requests=[r for r in requests if r['metadata']['benchmark_phase']=='profiling']
    assert len(requests)==count
    begin=min(r['metadata']['request_start_ns'] for r in requests);end=max(r['metadata']['request_end_ns'] for r in requests)
    rows=[json.loads(line) for line in p.with_name('server_metrics_export.jsonl').read_text().splitlines()]
    samples=[];steps=set();positions=set()
    for r in rows:
        m=r['metrics'];steps.update(x['value'] for x in m.get('sglang:spec_num_steps',[]));positions.update(x['value'] for x in m.get('sglang:spec_num_draft_tokens',[]))
        values=m.get('sglang:estimated_flops_per_gpu',[])
        if begin<=r['timestamp_ns']<=end and values:
            assert len(values)==1
            samples.append((r['timestamp_ns'],values[0]['value']))
    assert steps=={2} and positions=={3},(steps,positions)
    assert len(samples)>=2
    samples.sort();assert all(b[1]>=a[1] for a,b in zip(samples,samples[1:]))
    gpu=[json.loads(line) for line in p.with_name('gpu_telemetry_export.jsonl').read_text().splitlines()]
    gpu=[r for r in gpu if begin<=r['timestamp_ns']<=end]
    assert gpu
    keys=set().union(*(r['telemetry_data'] for r in gpu))
    assert {'nvidia_gpu_utilization','nvidia_temperature','nvidia_power_usage'}<=keys,keys
    dt=(samples[-1][0]-samples[0][0])/1e9;assert dt>0
    values={'output_tokens_per_second':data['output_token_throughput']['avg'],'mean_response_seconds':data['request_latency']['avg']/1000,
        'sglang_estimated_tflops_per_gpu':(samples[-1][1]-samples[0][1])/dt/1e12,
        'measurement_start_ns':begin,'measurement_end_ns':end,'flops_interval_seconds':dt,
        'flops_start':samples[0],'flops_end':samples[-1],'gpu_samples':len(gpu),'gpu_metric_keys':sorted(keys),
        'request_count':count,'export':str(p)}
    inputs=json.loads(p.with_name('inputs.json').read_text());values['inputs_sha256']=hashlib.sha256(json.dumps(inputs,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if before is not None:
        b=counters(before);a=counters(after)
        for metric in ['sglang:prompt_tokens_total','sglang:cached_tokens_total']:
            assert metric in b and metric in a,metric
            values[metric+'_delta']=a[metric]-b[metric]
        prompt=values['sglang:prompt_tokens_total_delta'];cached=values['sglang:cached_tokens_total_delta']
        assert prompt>0 and cached>=0,(prompt,cached)
        values['cached_prompt_fraction']=cached/prompt
        assert cached==0,('Fresh-cache protocol violated',cached,prompt)
    save(dest/'verified-summary.json',values);return values
def main():
    results=[]
    try:
        event('startup');launch()
        q=ROOT/'baseline-v2/qualification';q.mkdir()
        event('inference-qualification')
        run([UV,'run','--offline','--no-project','--python','3.12',str(ROOT/'scripts/smoke.py'),str(q),'64','2'],q/'smoke.log',600)
        flush('preflight')
        d=ROOT/'baseline-v2/telemetry-preflight';event('telemetry-preflight')
        run(command(1,4,d,4201),ROOT/'baseline-v2/telemetry-preflight.log',600);validate(d,4)
        for c in [1,8,64]:
            event('warmup',concurrency=c,requests=max(8,c))
            d=ROOT/'baseline-v2'/f'c{c}-warmup'
            run(command(c,max(8,c),d,1042+c),ROOT/'baseline-v2'/f'c{c}-warmup.log',1200)
            for trial in [1,2,3]:
                label=f'c{c}-trial{trial}';flush(label)
                d=ROOT/'baseline-v2'/f'c{c}'/f'trial{trial}';before=request('/metrics');start=utc()
                event('measured-trial',concurrency=c,trial=trial,requests=max(64,3*c))
                run(command(c,max(64,3*c),d,42+c),ROOT/'baseline-v2'/f'{label}.log',1800)
                after=request('/metrics');(d/'metrics-before.prom').write_text(before);(d/'metrics-after.prom').write_text(after)
                row=validate(d,max(64,3*c),before,after);row.update(concurrency=c,trial=trial,started_at_utc=start,ended_at_utc=utc())
                previous=[r for r in results if r['concurrency']==c]
                assert not previous or all(r['inputs_sha256']==row['inputs_sha256'] for r in previous),'Input mismatch'
                results.append(row);save(ROOT/'baseline-v2/trial-summary.json',results)
                event('trial-completed',**row)
        aggregate=[]
        for c in [1,8,64]:
            rows=[r for r in results if r['concurrency']==c];obj={'concurrency':c,'trials':len(rows)}
            for k in ['output_tokens_per_second','mean_response_seconds','sglang_estimated_tflops_per_gpu']:
                v=[r[k] for r in rows];obj[k]={'mean':statistics.mean(v),'sample_stddev':statistics.stdev(v),'min':min(v),'max':max(v)}
            aggregate.append(obj)
        save(ROOT/'baseline-v2/summary.json',aggregate);event('measurements-completed',trials=len(results),requests=sum(r['request_count'] for r in results))
    except BaseException as e:
        (ROOT/'baseline-v2/failure.txt').write_text(traceback.format_exc());event('failed',error=str(e));raise
    finally:cleanup()
    event('completed-and-stopped',trials=len(results))

if __name__=='__main__':
    def terminated(signum,frame):raise InterruptedError(f'signal {signum}')
    signal.signal(signal.SIGTERM,terminated);signal.signal(signal.SIGINT,terminated)
    if len(sys.argv)>2 and sys.argv[2]=='cleanup':cleanup()
    else:main()
