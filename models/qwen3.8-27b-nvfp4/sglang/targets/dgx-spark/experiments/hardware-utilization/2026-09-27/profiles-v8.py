"""Bounded first-launch kernel samples; not complete steps or whole-server utilization.

CUDA graphs stay enabled. Select actual NVFP4 GEMMs and Mamba state scatter
identified in the completed Systems trace. Filters persist across all six ranges.
A range with no new launch configuration has no newly captured sample.
"""
from pathlib import Path
import importlib.util, json, os, re, shlex, signal, subprocess, sys, time, traceback

ROOT=Path(sys.argv[1]).resolve()
MODE=sys.argv[2]
assert MODE in ['ncu-selected']
spec=importlib.util.spec_from_file_location('pilot',ROOT/'scripts/baseline-v3.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
base.ENV['UV_CACHE_DIR']='/home/coral/.cache/uv'
DIR=ROOT/'profiles'/(MODE+'-v8')
PROFILE_IMAGE=json.loads((ROOT/'preflight/profiling-image-v6.json').read_text())['Id']
NAME='nvfp4-hw-pilot-'+MODE+'-v8-20260927'
NSYS='/opt/nvidia/nsight-systems/2025.3.2/bin/nsys'
NCU='/opt/nvidia/nsight-compute/2025.3.1/ncu'
CHILD=None
TELEMETRY=None
SHAPE_OFFSET=0

def event(phase,**kw):
    obj={'at_utc':base.utc(),'phase':phase,'mode':MODE,**kw};base.save(DIR/'status.json',obj)
    with (DIR/'events.jsonl').open('a') as f:f.write(json.dumps(obj)+'\n')
    print(json.dumps(obj),flush=True)
def state():
    p=subprocess.run(['docker','inspect','--format','{{json .State}}',NAME],text=True,capture_output=True,timeout=20)
    if p.returncode:
        if 'no such object' in p.stderr.lower():return None
        raise RuntimeError(p.stderr)
    return json.loads(p.stdout)
def run(cmd,log,timeout=1800):base.run(cmd,log,timeout)
def cleanup():
    global CHILD, TELEMETRY
    if CHILD and CHILD.poll() is None:
        os.killpg(CHILD.pid,signal.SIGTERM)
        try:CHILD.wait(20)
        except subprocess.TimeoutExpired:os.killpg(CHILD.pid,signal.SIGKILL);CHILD.wait()
    CHILD=None
    calibration_name=NAME+'-calibration'
    cp=subprocess.run(['docker','inspect','--format','{{.State.Running}}',calibration_name],text=True,capture_output=True,timeout=20)
    if cp.returncode==0 and cp.stdout.strip()=='true':
        subprocess.run(['docker','stop','--timeout','30',calibration_name],capture_output=True,timeout=60)
    s=state()
    if s and s['Running']:
        # End the server normally so its parent profiler can finalize reports.
        p=subprocess.run(['docker','exec',NAME,'ps','-eo','pid,args'],text=True,capture_output=True,timeout=20)
        ids=[]
        for line in p.stdout.splitlines():
            m=re.match(r'^\s*(\d+)\s+(?:\S*/)?python3(?:\.12)? -m sglang\.launch_server\b',line)
            if m:ids.append(m[1])
        base.save(DIR/'server-pids-for-shutdown.json',{'pids':ids})
        if len(ids)==1:
            subprocess.run(['docker','exec',NAME,'kill','-TERM',ids[0]],capture_output=True,timeout=20)
            deadline=time.monotonic()+120
            while time.monotonic()<deadline:
                s=state()
                if not s or not s['Running']:break
                time.sleep(2)
        s=state()
        if s and s['Running']:run(['docker','stop','--timeout','90',NAME],DIR/'shutdown.log',120)
    s=state()
    if s:run(['docker','logs','--timestamps',NAME],DIR/'server-final.log',60)
    base.save(DIR/'shutdown-verification.json',{'at_utc':base.utc(),'container':NAME,'state':s,'stopped':s is None or not s['Running']})
    if TELEMETRY is not None:
        TELEMETRY.terminate()
        try:TELEMETRY.wait(10)
        except subprocess.TimeoutExpired:TELEMETRY.kill();TELEMETRY.wait()
        TELEMETRY=None
    if s and s['Running']:raise RuntimeError('Profiler container did not stop')
def launch():
    if state() is not None:raise RuntimeError('Refuse container reuse')
    if not json.loads((ROOT/'baseline-v3/shutdown-verification.json').read_text())['stopped']:
        raise RuntimeError('Baseline has not stopped')
    if json.loads((ROOT/'baseline-v3/status.json').read_text())['phase']!='completed-and-stopped':
        raise RuntimeError('Baseline has not completed successfully')
    cmd=shlex.split((ROOT/'baseline-v3/container-id.log.command.txt').read_text())
    cmd[cmd.index('--name')+1]=NAME
    extra_index=next(i for i,v in enumerate(cmd) if v.startswith('SGLANG_EXTRA_ARGS='))
    cmd[extra_index]+=' --max-total-tokens 65536'
    assert cmd[-1]==base.IMAGE;cmd=cmd[:-1]
    profiler=NSYS if MODE=='nsys' else NCU
    cmd+=['--cap-add='+('PERFMON' if MODE=='nsys' else 'SYS_ADMIN'),
        '-v',str(ROOT)+':/work','-v','/opt/nvidia/nsight-systems:/opt/nvidia/nsight-systems:ro',
        '-v','/opt/nvidia/nsight-compute:/opt/nvidia/nsight-compute:ro',
        '-e','SGLANG_ENABLE_NVTX_SCHEDULER=1','-e','SGLANG_ENABLE_NVTX_OPERATIONS=1',
        '-e',f'PILOT_FORWARD_SHAPES_PATH=/work/profiles/{MODE}-v8/forward-shapes.jsonl',
        '--entrypoint',profiler,PROFILE_IMAGE]
    if MODE=='nsys':
        options=['profile','--trace=cuda,nvtx','--sample=none','--cpuctxsw=none',
            '--gpu-metrics-devices=all','--gpu-metrics-frequency=1000',
            '--capture-range=cudaProfilerApi','--capture-range-end=repeat:3','--kill=none',
            '--output=/work/profiles/nsys-v7/inference']
    else:
        precision='fp4'
        # One precision counter per session keeps the requested set small.
        metrics=f'gpu__time_duration.sum,sm__ops_path_tensor_src_{precision}_dst_fp32.sum,lts__d_sectors_fill_sysmem.sum,lts__t_sectors_aperture_sysmem_op_write.sum'
        options=['--target-processes','all','--replay-mode','kernel','--profile-from-start','off','--graph-profiling','node',
            '--kernel-name-base','demangled','--kernel-name','regex:cutlass::device_kernel.*float_e2m1_t|_fused_mamba_state_scatter_with_mask_kernel',
            '--filter-mode','per-launch-config','--launch-count','1','--cache-control','none','--clock-control','none','--nvtx',
            '--metrics',metrics,'--export',f'/work/profiles/{MODE}-v8/inference',
            '--log-file',f'/work/profiles/{MODE}-v8/ncu.log']
    cmd+=options+['/opt/dgxspark/start.sh'];run(cmd,DIR/'container-id.log',120)
    deadline=time.monotonic()+1200
    while time.monotonic()<deadline:
        s=state()
        if not s or not s['Running']:raise RuntimeError(f'Profiler server exited during startup: {s}')
        try:
            base.request('/health',timeout=5);info=json.loads(base.request('/get_server_info'))
            assert [s['effective_max_running_requests_per_dp'] for s in info['internal_states']]==[64]
            assert [s['memory_usage']['token_capacity'] for s in info['internal_states']]==[65536]
            assert info['mem_fraction_static']==0.90 and info['max_mamba_cache_size']==256
            base.save(DIR/'server-info-ready.json',info);return
        except (OSError,ValueError):time.sleep(5)
    raise TimeoutError('Profiler server readiness exceeded 20 minutes')
def flush(label):
    response=base.request('/flush_cache?timeout=30',{},timeout=45)
    assert response.startswith('Cache flushed.'),response
    (DIR/f'{label}-flush.txt').write_text(base.utc()+'\n'+response)
def arm(label,one_step):
    body={'activities':['CUDA_PROFILER'],'start_step':1,'profile_id':label,
        'output_dir':f'/work/profiles/{MODE}-v8/api/{label}','detailed_annotations':True}
    if one_step:body['num_steps']=1
    base.save(DIR/f'{label}-profile-request.json',body)
    response=base.request('/start_profile',body,timeout=180)
    (DIR/f'{label}-profile-response.txt').write_text(response)
    event('capture-armed',label=label,one_scheduler_iteration=one_step)
def start_client(c,label):
    global CHILD
    cmd=base.command(c,max(8,3*c),DIR/'clients'/label,42+c)
    cmd+=['--request-timeout-seconds','900']
    (DIR/f'{label}.log.command.txt').write_text(shlex.join(cmd)+'\n')
    with (DIR/f'{label}.log').open('w') as f:
        CHILD=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,env=base.ENV,start_new_session=True)
    return CHILD
def finish_client(label):
    global CHILD
    rc=CHILD.wait(timeout=1800);CHILD=None
    if rc:raise RuntimeError(f'Client failed {rc}: {label}')
    paths=[p for p in (DIR/'clients'/label).rglob('profile_export_aiperf.json') if 'phases' not in p.parts]
    assert len(paths)==1,paths
    data=json.loads(paths[0].read_text());assert not data.get('error_summary') and not data.get('was_cancelled'),data.get('error_summary')
    (DIR/f'{label}-metrics-after.prom').write_text(base.request('/metrics'))
    event('capture-client-completed',label=label,request_count=data['request_count']['avg'])
def wait_running(c,label,full_batch=False):
    deadline=time.monotonic()+180
    while time.monotonic()<deadline:
        if CHILD.poll() is not None:raise RuntimeError('Client ended before the capture could be armed')
        text=base.request('/metrics',timeout=15);m=base.counters(text)
        running=m.get('sglang:num_running_reqs',0);queue=m.get('sglang:num_queue_reqs',0)
        if running>0 and (not full_batch or (running>=c and queue==0)):
            (DIR/f'{label}-metrics-at-trigger.prom').write_text(text)
            event('capture-load-detected',label=label,observed_running=running,observed_queue=queue);return
        time.sleep(0.25)
    raise TimeoutError(f'No suitable running batch at c{c}')
def ncu_log_size():return (DIR/'ncu.log').stat().st_size if (DIR/'ncu.log').exists() else 0
def save_ncu_log_segment(label,offset):
    with (DIR/'ncu.log').open('rb') as f:f.seek(offset);data=f.read()
    (DIR/f'{label}-ncu-segment.log').write_bytes(data)
    if b'==ERROR==' in data:raise RuntimeError(f'NCU error in {label}')
    # Filters persist across ranges: a previously sampled launch shape is not
    # sampled again. Retain empty segments; they are missing coverage, not zeros.
    base.save(DIR/f'{label}-capture-count.json',{'profiling_messages':len(re.findall(rb'Profiling ',data)),'selection':'First matching launch per distinct launch configuration over the whole session.'})
    shapes_path=DIR/'forward-shapes.jsonl'
    with shapes_path.open('rb') as f:f.seek(SHAPE_OFFSET);shapes=[json.loads(line) for line in f.read().splitlines() if line]
    base.save(DIR/f'{label}-forward-shapes.json',shapes)
    expected='step[EXTEND ' if label.endswith('prefill') else 'step[TARGET_VERIFY '
    assert any(s['shape'].startswith(expected) for s in shapes),(label,shapes)
def main():
    global TELEMETRY, SHAPE_OFFSET
    if DIR.exists():raise RuntimeError('Refuse to overwrite profiler attempt')
    DIR.mkdir();event('startup')
    try:
        run([base.UV,'tool','run','--managed-python','--python','3.12','--from','aiperf==0.12.0','aiperf','--version'],DIR/'client-version.log',60)
        if MODE=='ncu-selected':
            event('fp8-counter-calibration')
            calibration_cmd=['docker','run','--rm','--name',NAME+'-calibration','--network','none','--gpus','all',
                '--cap-add=SYS_ADMIN','--entrypoint','/bin/bash','-v',str(ROOT)+':/work',
                '-v','/opt/nvidia/nsight-compute:/opt/nvidia/nsight-compute:ro',base.IMAGE,'/work/scripts/calibrate-fp8.sh']
            run(calibration_cmd,ROOT/'calibration/fp8-driver.log',600)
        telemetry_cmd=['nvidia-smi','--query-gpu=timestamp,utilization.gpu,power.draw,temperature.gpu,clocks.current.sm,clocks.current.memory','--format=csv','--loop-ms=1000']
        (DIR/'gpu-clocks-power.csv.command.txt').write_text(shlex.join(telemetry_cmd)+'\n')
        with (DIR/'gpu-clocks-power.csv').open('w') as f:
            TELEMETRY=subprocess.Popen(telemetry_cmd,stdout=f,stderr=subprocess.STDOUT)
        launch()
        for c in [1,8,64]:
            event('diagnostic-warmup',concurrency=c)
            run(base.command(c,max(8,c),DIR/'clients'/f'c{c}-warmup',1042+c),DIR/f'c{c}-warmup.log',1200)
            if MODE=='nsys':
                label=f'c{c}-timeline';flush(label);arm(label,False);start_client(c,label)
                wait_running(c,label);deadline=time.monotonic()+25
                while CHILD.poll() is None and time.monotonic()<deadline:time.sleep(0.25)
                response=base.request('/stop_profile',{},timeout=180)
                (DIR/f'{label}-stop-response.txt').write_text(response);finish_client(label)
            else:
                for phase in ['prefill','decode']:
                    label=f'c{c}-{phase}';flush(label);offset=ncu_log_size()
                    shapes_path=DIR/'forward-shapes.jsonl';SHAPE_OFFSET=shapes_path.stat().st_size if shapes_path.exists() else 0
                    if phase=='prefill':arm(label,True)
                    start_client(c,label)
                    if phase=='decode':wait_running(c,label,True);arm(label,True)
                    finish_client(label);save_ncu_log_segment(label,offset)
        event('captures-completed')
    except BaseException as error:
        (DIR/'failure.txt').write_text(traceback.format_exc());event('failed',error=str(error));raise
    finally:cleanup()
    reports=list(DIR.glob('*.nsys-rep' if MODE=='nsys' else '*.ncu-rep'))
    required=3 if MODE=='nsys' else 1
    if len(reports)!=required or not all(p.stat().st_size>1024 for p in reports):
        event('failed',error='Missing or empty hardware profile reports',reports=[str(p) for p in reports])
        raise RuntimeError('Missing or empty hardware profile reports after shutdown')
    if MODE!='nsys':
        run([base.UV,'run','--offline','--no-project','--python','3.12',str(ROOT/'scripts/extract-ncu.py'),str(reports[0]),str(DIR/'counters.json')],DIR/'counter-extraction.log',300)
        counters=json.loads((DIR/'counters.json').read_text())
        assert 1 <= counters['action_count'] <= 256,counters['action_count']
        assert any(a.get('tensor_TFLOPS_by_counter',{}).get('sm__ops_path_tensor_src_fp4_dst_fp32.sum',0)>0 for a in counters['actions'])
        assert all(a['metrics']['profiler__replayer_passes']['value']==1 for a in counters['actions']), 'Traffic must use the calibrated single-pass metric set'
    event('completed-and-stopped')

if __name__=='__main__':
    def terminated(signum,frame):raise InterruptedError(f'signal {signum}')
    signal.signal(signal.SIGTERM,terminated);signal.signal(signal.SIGINT,terminated)
    if len(sys.argv)>3 and sys.argv[3]=='cleanup':
        if DIR.exists():cleanup()
    else:main()
