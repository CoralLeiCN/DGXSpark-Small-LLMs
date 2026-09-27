set -eu
/opt/nvidia/nsight-compute/2025.3.1/ncu \
  --target-processes all --profile-from-start off --replay-mode app-range \
  --app-replay-buffer memory --cache-control none --clock-control none \
  --metrics gpu__time_duration.sum,sm__ops_path_tensor_src_fp4_dst_fp32.sum,lts__d_sectors_fill_sysmem.sum,lts__t_sectors_aperture_sysmem_op_write.sum \
  --export /work/calibration/fp4-app-range \
  /opt/sglang/bin/uv run --offline --no-project --python /opt/sglang/bin/python /work/scripts/fp4.py profile
