set -e
nvcc -O3 -arch=sm_121 /work/scripts/bandwidth.cu -o /work/calibration/bandwidth
/work/calibration/bandwidth 40 > /work/calibration/bandwidth-unprofiled.jsonl
/opt/nvidia/nsight-systems/2025.3.2/bin/nsys profile --trace=cuda --sample=none --cpuctxsw=none --gpu-metrics-devices=all --gpu-metrics-frequency=1000 --output=/work/calibration/bandwidth-nsys /work/calibration/bandwidth 40 > /work/calibration/bandwidth-nsys.log 2>&1
/opt/nvidia/nsight-compute/2025.3.1/ncu --target-processes all --kernel-name bw_copy --launch-skip 5 --launch-count 1 --cache-control none --clock-control none --metrics gpu__time_duration.sum,lts__d_sectors_fill_sysmem.sum,lts__t_sectors_aperture_sysmem_op_write.sum,sm__ops_path_tensor_src_fp4_dst_fp32.sum --export /work/calibration/bandwidth-ncu /work/calibration/bandwidth 1 > /work/calibration/bandwidth-ncu.log 2>&1
