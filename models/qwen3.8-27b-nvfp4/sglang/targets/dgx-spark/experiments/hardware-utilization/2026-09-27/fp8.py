import json,sys
import torch
torch.manual_seed(42)
profile=len(sys.argv)>1 and sys.argv[1]=='profile'
m=n=k=4096
a=torch.randn((m,k),device='cuda',dtype=torch.bfloat16)
b=torch.randn((n,k),device='cuda',dtype=torch.bfloat16)
sa=a.float().abs().max()/448;sb=b.float().abs().max()/448
aq=(a.float()/sa).to(torch.float8_e4m3fn)
bq=(b.float()/sb).to(torch.float8_e4m3fn).T
def gemm():
    out=torch._scaled_mm(aq,bq,scale_a=sa,scale_b=sb,out_dtype=torch.bfloat16)
    return out[0] if isinstance(out,tuple) else out
for _ in range(10):out=gemm()
torch.cuda.synchronize()
ref=a[:8].float()@b[:128].float().T
err=((out[:8,:128].float()-ref).square().mean()/ref.square().mean()).sqrt().item()
assert err<0.1,err
if profile:
    torch.cuda.cudart().cudaProfilerStart();out=gemm();torch.cuda.synchronize();torch.cuda.cudart().cudaProfilerStop()
    print(json.dumps({'m':m,'n':n,'k':k,'expected_dense_flops':2*m*n*k,'relative_rmse':err,'profile_only':True}),flush=True)
else:
    for trial in [1,2,3]:
        start=torch.cuda.Event(enable_timing=True);end=torch.cuda.Event(enable_timing=True)
        reps=100;start.record()
        for _ in range(reps):out=gemm()
        end.record();end.synchronize();ms=start.elapsed_time(end)
        print(json.dumps({'m':m,'n':n,'k':k,'trial':trial,'repeats':reps,'milliseconds':ms,'effective_dense_TFLOPS':2*m*n*k*reps/ms/1e9,'relative_rmse':err,'backend':'torch._scaled_mm'}),flush=True)
