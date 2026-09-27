"""Export native-unit counters and NVTX provenance without running GPU work."""
from pathlib import Path
import json,sys,hashlib
sys.path.insert(0,'/opt/nvidia/nsight-compute/2025.3.1/extras/python')
import ncu_report

source=Path(sys.argv[1]);destination=Path(sys.argv[2])
report=ncu_report.load_report(str(source));actions=[]
for ri in range(report.num_ranges()):
    stream=report.range_by_idx(ri)
    for ai in range(stream.num_actions()):
        action=stream.action_by_idx(ai);metrics={}
        for name in action.metric_names():
            if (name=='gpu__time_duration.sum' or name.startswith('sm__ops_path_tensor_') and name.endswith('.sum')
                or name in ['lts__d_sectors_fill_sysmem.sum','lts__t_sectors_aperture_sysmem_op_write.sum',
                    'profiler__replayer_passes','device__attribute_clock_rate','device__attribute_memory_clock_rate',
                    'device__attribute_multiprocessor_count','launch__context_id','launch__stream_id']):
                m=action.metric_by_name(name);metrics[name]={'value':m.value(),'unit':m.unit()}
        nvtx=[];state=action.nvtx_state()
        if state:
            for domain_id in state.domains():
                domain=state.domain_by_id(domain_id)
                nvtx.append({'domain':domain.name(),'push_pop_ranges':domain.push_pop_ranges(),'start_end_ranges':domain.start_end_ranges()})
        row={'range_index':ri,'action_index':ai,'name':action.name(),'workload_type':action.workload_type(),'metrics':metrics,'nvtx':nvtx}
        duration=metrics.get('gpu__time_duration.sum')
        if duration and duration['value']>0:
            assert duration['unit']=='ns',duration
            seconds=duration['value']/1e9;row['gpu_seconds']=seconds
            row['tensor_TFLOPS_by_counter']={k:v['value']/seconds/1e12 for k,v in metrics.items() if k.startswith('sm__ops_path_tensor_')}
            for metric,field in [('lts__d_sectors_fill_sysmem.sum','sysmem_read_fill_proxy_GBps'),('lts__t_sectors_aperture_sysmem_op_write.sum','sysmem_write_request_proxy_GBps')]:
                if metric in metrics:
                    assert metrics[metric]['unit']=='sector',metrics[metric]
                    row[field]=metrics[metric]['value']*32/seconds/1e9
        actions.append(row)
with source.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
result={'source':str(source),'sha256':digest,'range_count':report.num_ranges(),'action_count':len(actions),
        'scope':'Hardware operations for selected precision(s), not all arithmetic. Traffic is GPU L2/system-memory fill/request proxy, not physical DRAM controller bandwidth. Per-entity rates use profiler GPU duration; not normal serving-wall-time utilization.',
        'actions':actions}
destination.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'source':str(source),'action_count':len(actions),'destination':str(destination)}))
