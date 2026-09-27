"""Wait for the normal baseline, then run isolated profiler sessions in order."""
from pathlib import Path
from datetime import datetime,timezone
import json,os,signal,subprocess,sys,time,traceback
ROOT=Path(sys.argv[1]).resolve()
UV='/home/coral/.local/bin/uv'
MODES=['ncu-fp4','ncu-fp8']
assert json.loads((ROOT/'profiles/nsys-v3/status.json').read_text())['phase']=='completed-and-stopped'
CHILD=None
def utc():return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def record(phase,**fields):
    data={'at_utc':utc(),'phase':phase,**fields}
    tmp=ROOT/'status.json.tmp';tmp.write_text(json.dumps(data,indent=2)+'\n');tmp.replace(ROOT/'status.json')
    with (ROOT/'events.jsonl').open('a') as f:f.write(json.dumps(data)+'\n')
    print(json.dumps(data),flush=True)
def monitor():
    data={'at_utc':utc()}
    for name in ['baseline-v3/status.json',*[f'profiles/{mode}-v4/status.json' for mode in MODES]]:
        p=ROOT/name
        if p.exists():data[name]=json.loads(p.read_text())
    with (ROOT/'monitor-30min.jsonl').open('a') as f:f.write(json.dumps(data)+'\n')
def cleanup():
    global CHILD
    if CHILD and CHILD.poll() is None:
        os.killpg(CHILD.pid,signal.SIGTERM)
        try:CHILD.wait(180)
        except subprocess.TimeoutExpired:os.killpg(CHILD.pid,signal.SIGKILL);CHILD.wait()
    CHILD=None
    outcomes=[]
    for mode in MODES:
        name='nvfp4-hw-pilot-'+mode+'-v4-20260927'
        p=subprocess.run(['docker','inspect','--format','{{json .State}}',name],text=True,capture_output=True,timeout=20)
        if p.returncode and 'no such object' in p.stderr.lower():outcomes.append({'container':name,'created':False,'stopped':True});continue
        if p.returncode:raise RuntimeError(p.stderr)
        s=json.loads(p.stdout)
        if s['Running']:
            subprocess.run(['docker','stop','--timeout','90',name],capture_output=True,timeout=120)
            s=json.loads(subprocess.check_output(['docker','inspect','--format','{{json .State}}',name],text=True,timeout=20))
        outcomes.append({'container':name,'created':True,'stopped':not s['Running'],'state':s})
    (ROOT/'profiles-v4-shutdown-verification.json').write_text(json.dumps({'at_utc':utc(),'containers':outcomes},indent=2)+'\n')
    assert all(x['stopped'] for x in outcomes)
def main():
    global CHILD
    record('waiting-for-baseline');monitor();last=time.monotonic()
    try:
        deadline=time.monotonic()+10800
        while True:
            p=ROOT/'baseline-v3/status.json'
            s=json.loads(p.read_text()) if p.exists() else {}
            if s.get('phase')=='completed-and-stopped':break
            if s.get('phase')=='failed':raise RuntimeError('Baseline failed; profiling not started')
            if time.monotonic()>deadline:raise TimeoutError('Baseline wait exceeded three hours')
            if time.monotonic()-last>=1800:monitor();last=time.monotonic()
            time.sleep(5)
        for mode in MODES:
            record('profiling',mode=mode)
            cmd=[UV,'run','--offline','--no-project','--python','3.12',str(ROOT/'scripts/profiles-v4.py'),str(ROOT),mode]
            with (ROOT/f'{mode}-v4-driver.log').open('w') as f:
                CHILD=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
                deadline=time.monotonic()+7200
                while CHILD.poll() is None:
                    if time.monotonic()>deadline:raise TimeoutError(f'{mode} exceeded two hours')
                    if time.monotonic()-last>=1800:monitor();last=time.monotonic()
                    time.sleep(2)
                rc=CHILD.returncode;CHILD=None
                if rc:raise RuntimeError(f'{mode} failed with exit {rc}; see driver log')
        record('captures-completed-analysis-pending')
    except BaseException as e:
        (ROOT/'orchestration-v5-failure.txt').write_text(traceback.format_exc());record('failed',error=str(e));raise
    finally:cleanup();monitor()
if __name__=='__main__':
    def terminated(signum,frame):raise InterruptedError(f'signal {signum}')
    signal.signal(signal.SIGTERM,terminated);signal.signal(signal.SIGINT,terminated)
    if len(sys.argv)>2 and sys.argv[2]=='cleanup':cleanup()
    else:main()
