import json, sys
import torch
from flashinfer import nvfp4_quantize, mm_fp4, SfLayout

torch.manual_seed(42)
profile = len(sys.argv)>1 and sys.argv[1]=='profile'
shapes=[(4096,4096,4096)] if profile else [(64,4096,4096),(512,4096,4096),(4096,4096,4096)]
for m,n,k in shapes:
    a=torch.randn((m,k),device='cuda',dtype=torch.bfloat16)
    b=torch.randn((n,k),device='cuda',dtype=torch.bfloat16)
    ag=(448*6)/a.float().abs().max();bg=(448*6)/b.float().abs().max()
    aq,asc=nvfp4_quantize(a,ag,sfLayout=SfLayout.layout_128x4,do_shuffle=False)
    bq,bsc=nvfp4_quantize(b,bg,sfLayout=SfLayout.layout_128x4,do_shuffle=False)
    alpha=1/(ag*bg)
    def gemm():return mm_fp4(aq,bq.T,asc,bsc.T,alpha,torch.bfloat16,backend='cutlass')
    for _ in range(10):out=gemm()
    torch.cuda.synchronize()
    ref=a[:8].float()@b[:128].float().T
    rel=((out[:8,:128].float()-ref).square().mean()/ref.square().mean()).sqrt().item()
    assert rel<0.25,rel
    if profile:
        torch.cuda.cudart().cudaProfilerStart()
        out=gemm();torch.cuda.synchronize()
        torch.cuda.cudart().cudaProfilerStop()
        print(json.dumps({'m':m,'n':n,'k':k,'expected_dense_flops':2*m*n*k,'relative_rmse':rel,'profile_only':True}),flush=True)
    else:
        for trial in [1,2,3]:
            start=torch.cuda.Event(enable_timing=True);end=torch.cuda.Event(enable_timing=True)
            reps=100;start.record()
            for _ in range(reps):out=gemm()
            end.record();end.synchronize();ms=start.elapsed_time(end)
            print(json.dumps({'m':m,'n':n,'k':k,'trial':trial,'repeats':reps,'milliseconds':ms,'effective_dense_TFLOPS':2*m*n*k*reps/ms/1e9,'relative_rmse':rel,'backend':'cutlass'}),flush=True)
